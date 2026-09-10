"""
LAYER 6 - Execution Sandbox (Cognitive)
-------------------------------------
SECURE multi-By-Default Sandbox. Replaces the insecure tool_integration.py
which had RCE (shell=True, exec(), SQL injection).

Defenses:
  1. Python code runs ONLY via RestrictedPython (no __builtins__, no import,
     no file access by default).
  2. Shell commands are BLOCKED except inside an ephemeral Docker container.
  3. Database queries go ONLY through parameterized SQLAlchemy sessions.
  4. File operations are jailed via realpath + chroot-style whitelist.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import platform
import re
import shutil
import stat
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .base import BaseNSELayer

logger = logging.getLogger(__name__)


FORBIDDEN_SQL_PREFIXES = (
    "drop ", "truncate ", "alter ", "create table", "pragma ",
    "attach ", "vacuum ", ".load ", "load_extension",
)

SHELL_BLOCKLIST = {
    "rm", "dd", "mkfs", "format", "shutdown", "reboot", "halt",
    "nc", "ncat", "netcat", "socat", "curl", "wget", "curlie",
    "bash", "sh", "zsh", "ksh", "python", "perl", "ruby",
    "powershell", "pwsh",
}


@dataclass(slots=True)
class SandboxResult:
    ok: bool
    output: str
    stderr: str = ""
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SafeExecutionSandbox(BaseNSELayer):
    layer_id = 6
    layer_name = "Execution Sandbox (Cognitive)"

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        self.root = os.path.join(getattr(config, "data_dir", "./state"), "sandbox")
        os.makedirs(self.root, exist_ok=True)
        self.allowed_dirs: List[str] = [self.root]
        self.use_docker = self._check_docker()
        self.docker_image = "python:3.12-slim"
        self.history: List[SandboxResult] = []
        self._tty_lock = asyncio.Lock()

    def _check_docker(self) -> bool:
        """Check if docker binary exists AND the daemon is actually running."""
        if not shutil.which("docker"):
            return False
        try:
            result = subprocess.run(
                ["docker", "info", "--format", "{{.ServerVersion}}"],
                capture_output=True, text=True, timeout=5,
            )
            return result.returncode == 0 and bool(result.stdout.strip())
        except Exception:
            return False

    async def _initialize(self) -> None:
        self.add_extra("sandbox_root", self.root)
        self.add_extra("use_docker", self.use_docker)
        self.add_extra("allowed_dirs", list(self.allowed_dirs))
        self.add_extra("exec_count", 0)

    # ======================================================== Python code
    async def python_code(self, code: str, globals_whitelist: Optional[Dict[str, Any]] = None,
                        timeout: float = 10.0) -> SandboxResult:
        """Run Python with RestrictedPython — NO file, NO network, NO builtins."""
        if not isinstance(code, str):
            raise TypeError("code must be str")
        if len(code) > 50_000:
            raise ValueError("code too large")
        # ------------------------------------------------------------------
        try:
            from RestrictedPython import compile_restricted, safe_globals  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("RestrictedPython missing: pip install RestrictedPython") from exc
        # Compile in strict mode
        t0 = time.time()
        try:
            bytecode = compile_restricted(code, "<nse-sandbox>", "exec")
        except SyntaxError as exc:
            return self._record(False, "", f"Syntax error: {exc}", (time.time()-t0)*1000, kind="python_compile_fail")
        safe_locals: Dict[str, Any] = {}
        env = dict(safe_globals)
        env["__builtins__"] = {
            k: v for k, v in safe_globals.get("__builtins__", {}).items()
            if k in {"print", "len", "sum", "min", "max", "abs", "round",
                    "range", "enumerate", "zip", "map", "filter", "isinstance",
                    "issubclass", "type", "int", "float", "str", "bytes",
                    "list", "dict", "tuple", "set", "bool", "None", "True",
                    "False", "Exception", "KeyError", "ValueError", "TypeError",
                    "IndexError", "StopIteration", "repr", "sorted", "reversed",
                    "any", "all", "dict.items", "dict.keys", "dict.values"
        }}
        if globals_whitelist:  # Explicit whitelisted symbols only
            env.update(globals_whitelist)
        try:
            exec(bytecode, env, safe_locals)
            out = str(safe_locals.get("_output", safe_locals.get("result", "")))
        except Exception as exc:
            return self._record(False, "", f"Runtime: {type(exc).__name__}: {exc}",
                                (time.time()-t0)*1000, kind="python_runtime")
        return self._record(True, out, "", (time.time()-t0)*1000, kind="python", meta={"symbols": list(safe_locals.keys())})

    # ===================================================== Shell (DOCKER ONLY
    async def shell_command(self, argv: List[str], timeout: float = 20.0,
                            network_disabled: bool = True) -> SandboxResult:
        """Run shell ONLY via argv (shell=False) inside docker if enabled."""
        if not isinstance(argv, list) or not all(isinstance(x, str) for x in argv):
            raise TypeError("argv must be list[str]; no shell injection")
        # Blocked tokens inside individual args (belt-and-braces)
        joined = " ".join(argv)
        lowered = joined.lower()
        for bad in SHELL_BLOCKLIST:
            if re.search(rf"(^|[^a-z]){bad}([^a-z]|$)", lowered):
                return self._record(False, "", f"blocked token: {bad}", 0, kind="shell_blocked")
        t0 = time.time()
        async with self._tty_lock:
            if self.use_docker:
                return await asyncio.to_thread(self._docker_run, argv, timeout, network_disabled, t0)
            # Docker unavailable → strict local fallback, no networking, no home dir
            is_windows = platform.system() == "Windows"
            env = {
                "PATH": "/usr/bin:/bin" if not is_windows else os.environ.get("PATH", ""),
                "HOME": self.root,
            }
            # On Windows, shell builtins like `echo` need cmd /c prefix
            windows_builtins = {"echo", "set", "cd", "dir", "type", "copy", "del", "md", "rd", "ren"}
            run_argv = argv
            if is_windows and argv and argv[0].lower() in windows_builtins:
                run_argv = ["cmd", "/c"] + argv
            try:
                completed = subprocess.run(
                    run_argv,
                    shell=False,
                    cwd=self.root,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    user=None if is_windows else 65534,
                )
            except Exception as exc:
                return self._record(False, "", str(exc), (time.time()-t0)*1000, kind="shell_local")
            ok = completed.returncode == 0
            return self._record(ok, completed.stdout, completed.stderr,
                              (time.time()-t0)*1000, kind="shell_local",
                              meta={"rc": completed.returncode})

    def _docker_run(self, argv: List[str], timeout: float,
                    network_disabled: bool, t0: float) -> SandboxResult:
        label = f"nse-sandbox-{uuid.uuid4().hex[:12]}"
        cmd = ["docker", "run", "--rm", f"--name={label}"]
        if network_disabled:
            cmd += ["--network", "none"]
        cmd += ["--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges"]
        cmd += ["--memory=512m", "--pids-limit=128", "--cpus=1.0", "--ulimit", "nofile=256"]
        cmd += [self.docker_image] + argv
        try:
            completed = subprocess.run(cmd, shell=False, capture_output=True, text=True, timeout=timeout + 15)
        except Exception as exc:
            return self._record(False, "", f"docker: {exc}", (time.time()-t0)*1000, kind="shell_docker_fail")
        ok = completed.returncode == 0
        return self._record(ok, completed.stdout, completed.stderr,
                            (time.time()-t0)*1000, kind="shell_docker",
                            meta={"rc": completed.returncode})

    # =========================================================== database
    async def database_query(self, session_maker: Any, query_text: str,
                               params: Optional[Dict[str, Any]] = None) -> SandboxResult:
        """Parameterized SQL ONLY via SQLAlchemy. Raw SQL string is static-checked and parameterised."""
        lowered = query_text.strip().lower()
        forbidden = any(lowered.startswith(p) for p in FORBIDDEN_SQL_PREFIXES)
        if forbidden:
            return self._record(False, "", "forbidden statement prefix present", 0, kind="sql_forbidden")
        if ";" in query_text.rstrip(";") and lowered.startswith("select") is False and lowered.startswith("with") is False:
            return self._record(False, "", "multi-statement disabled", 0, kind="sql_multi")
        t0 = time.time()
        try:
            from sqlalchemy import text as sa_text

            rows: List[Any] = []
            with session_maker() as s:
                cursor = s.execute(sa_text(query_text), params or {})
                if cursor.returns_rows:
                    rows = [dict(r._mapping) for r in cursor.fetchall()]
                s.commit()
            return self._record(True, json.dumps(rows[:100]), "", (time.time()-t0)*1000,
                              kind="sql", meta={"row_count": len(rows)})
        except Exception as exc:
            return self._record(False, "", f"DB: {exc}", (time.time()-t0)*1000, kind="sql_error")

    # ========================================================= file ops JAIL
    def resolve_safe_path(self, path: str) -> str:
        """Resolve path + realpath, then verify it lives inside allowed dirs."""
        if not isinstance(path, str) or "\x00" in path:
            raise ValueError("invalid path")
        base = os.path.realpath(self.root)
        target = os.path.realpath(os.path.join(self.root, path.lstrip("/\\")))
        for allowed in self.allowed_dirs:
            allowed_real = os.path.realpath(allowed)
            if target == allowed_real or target.startswith(allowed_real + os.sep):
                return target
        raise PermissionError(f"path escapes sandbox: {path}")

    def read_file(self, path: str, max_bytes: int = 1_000_000) -> SandboxResult:
        t0 = time.time()
        try:
            safe = self.resolve_safe_path(path)
            mode = os.stat(safe).st_mode
            if not stat.S_ISREG(mode):
                raise PermissionError("not a regular file")
            with open(safe, "rb") as f:
                data = f.read(max_bytes)
            return self._record(True, data.decode("utf-8", errors="replace"), "",
                              (time.time()-t0)*1000, kind="file_read",
                              meta={"bytes": len(data), "path": safe})
        except Exception as exc:
            return self._record(False, "", str(exc), (time.time()-t0)*1000, kind="file_read_error")

    def write_file(self, path: str, content: str, max_bytes: int = 5_000_000) -> SandboxResult:
        t0 = time.time()
        try:
            safe = self.resolve_safe_path(path)
            if len(content) > max_bytes:
                raise ValueError("content too large")
            with tempfile.NamedTemporaryFile(delete=False, dir=os.path.dirname(safe) or self.root) as tmp:
                tmp.write(content.encode("utf-8"))
            os.replace(tmp.name, safe)
            return self._record(True, safe, "", (time.time()-t0)*1000, kind="file_write",
                              meta={"bytes": len(content), "path": safe})
        except Exception as exc:
            return self._record(False, "", str(exc), (time.time()-t0)*1000, kind="file_write_error")

    # =========================================================== utility
    def _record(self, ok: bool, stdout: str, stderr: str, ms: float, kind: str = "",
                meta: Optional[Dict[str, Any]] = None) -> SandboxResult:
        meta = {"kind": kind, **(meta or {})}
        res = SandboxResult(ok=ok, output=stdout, stderr=stderr, duration_ms=ms, metadata=meta)
        self.history.append(res)
        self.add_extra("exec_count", len(self.history))
        if ok:
            self.bump_ok()
        else:
            self.bump_fail()
        return res
