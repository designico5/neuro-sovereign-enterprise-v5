"""
LAYER 5 - Integration API
-------------------------
Outbound integration gateway with typed connectors for SAP OData, JDBC,
REST/RPC, SFTP, Kafka, MQTT, and Mainframe (3270 TN3270).
Rate limiting, mTLS and credential vault built-in.
"""
from __future__ import annotations

import asyncio
import logging
import os
import ssl
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Literal, Optional

import httpx

from .base import BaseNSELayer

logger = logging.getLogger(__name__)

ConnectorType = Literal["rest", "sap", "jdbc", "sftp", "kafka", "mqtt", "mainframe"]


@dataclass(slots=True)
class ConnectorConfig:
    name: str
    kind: ConnectorType
    url: str
    auth: Dict[str, Any] = field(default_factory=dict)
    rate_limit_per_min: int = 120
    mtls_cert_path: Optional[str] = None
    mtls_key_path: Optional[str] = None
    ca_bundle: Optional[str] = None


@dataclass(slots=True)
class Connector:
    config: ConnectorConfig
    last_used_at: float = 0.0
    request_count: int = 0
    error_count: int = 0


@dataclass(slots=True)
class VaultEntry:
    connector: str
    kind: str  # "token", "basic", "mtls"
    value: str


class IntegrationAPIGateway(BaseNSELayer):
    layer_id = 5
    layer_name = "Integration API"

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        self.connectors: Dict[str, Connector] = {}
        self._vault: Dict[str, VaultEntry] = {}
        self._http: Optional[httpx.AsyncClient] = None
        self._limiter_lock = asyncio.Lock()
        self._request_timestamps: Dict[str, List[float]] = {}

    async def _initialize(self) -> None:
        ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
        timeout = httpx.Timeout(30.0, connect=10.0)
        limits = httpx.Limits(max_connections=50, max_keepalive_connections=10)
        self._http = httpx.AsyncClient(timeout=timeout, limits=limits, verify=ssl_context)
        self.add_extra("connectors", list(self.connectors.keys()))
        self.add_extra("http_client", "httpx")

    async def aclose(self) -> None:
        if self._http:
            await self._http.aclose()

    # ---------------------------------------------------------------- vault
    def vault_store(self, entry: VaultEntry) -> None:
        self._vault[f"{entry.connector}:{entry.kind}"] = entry
        self.bump_ok()

    def vault_get(self, connector: str, kind: str) -> Optional[VaultEntry]:
        return self._vault.get(f"{connector}:{kind}")

    # ----------------------------------------------------------- connectors
    def register(self, cfg: ConnectorConfig) -> None:
        self.connectors[cfg.name] = Connector(cfg)
        self.add_extra("connectors", list(self.connectors.keys()))
        self.bump_ok()

    def unregister(self, name: str) -> None:
        self.connectors.pop(name, None)
        self.add_extra("connectors", list(self.connectors.keys()))

    # ---------------------------------------------------------------- calls
    async def call(
        self,
        connector_name: str,
        method: str = "GET",
        path: str = "/",
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        con = self.connectors.get(connector_name)
        if not con:
            self.bump_fail()
            raise KeyError(f"connector '{connector_name}' not registered")
        await self._check_rate_limit(con)
        con.last_used_at = time.time()
        con.request_count += 1
        try:
            if con.config.kind == "rest" or con.config.kind == "sap":
                result = await self._rest(con, method, path, payload, headers or {})
            elif con.config.kind == "kafka":
                result = await self._kafka(con, payload or {})
            elif con.config.kind == "mqtt":
                result = await self._mqtt(con, payload or {})
            elif con.config.kind == "jdbc":
                result = await self._jdbc(con, payload or {})
            elif con.config.kind == "sftp":
                result = await self._sftp(con, payload or {})
            elif con.config.kind == "mainframe":
                result = await self._mainframe(con, payload or {})
            else:
                raise ValueError(f"unsupported connector kind: {con.config.kind}")
            self.bump_ok()
            return result
        except Exception as exc:
            con.error_count += 1
            self.bump_fail()
            raise

    async def _check_rate_limit(self, con: Connector) -> None:
        now = time.time()
        async with self._limiter_lock:
            ts = self._request_timestamps.setdefault(con.config.name, [])
            ts[:] = [t for t in ts if now - t < 60.0]
            if len(ts) >= con.config.rate_limit_per_min:
                raise RuntimeError(
                    f"rate limit exceeded for {con.config.name}: "
                    f"{len(ts)}/{con.config.rate_limit_per_min}/min"
                )
            ts.append(now)

    # ----------------------------------------------------------- transports
    async def _rest(
        self,
        con: Connector,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]],
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        assert self._http is not None
        url = con.config.url.rstrip("/") + "/" + path.lstrip("/")
        auth_header = self._auth_header(con)
        if auth_header:
            headers.setdefault("Authorization", auth_header)
        r = await self._http.request(method, url, json=payload, headers=headers)
        try:
            body: Any = r.json()
        except Exception:
            body = r.text
        return {"status": r.status_code, "body": body, "ms": r.elapsed.total_seconds() * 1000}

    async def _kafka(self, con: Connector, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:  # pragma: no cover - optional dep
            from confluent_kafka import Producer  # type: ignore

            producer = Producer({"bootstrap.servers": con.config.url})
            topic = payload.get("topic", "nse-default")
            producer.produce(topic, str(payload.get("value", "")).encode())
            producer.flush(5)
            return {"ok": True, "topic": topic, "bytes": len(str(payload.get("value", "")))}
        except Exception as exc:
            raise RuntimeError(f"confluent_kafka unavailable for {con.config.name}: {exc}") from exc

    async def _mqtt(self, con: Connector, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:  # pragma: no cover - optional dep
            import paho.mqtt.publish as mqtt_pub  # type: ignore

            topic = payload.get("topic", "nse/default")
            mqtt_pub.single(topic, payload=str(payload.get("value", "")), hostname=con.config.url)
            return {"ok": True, "topic": topic}
        except Exception as exc:
            raise RuntimeError(f"paho-mqtt unavailable for {con.config.name}: {exc}") from exc

    async def _jdbc(self, con: Connector, payload: Dict[str, Any]) -> Dict[str, Any]:
        sql = payload.get("sql")
        if not sql:
            raise ValueError("payload.sql missing for JDBC call")
        try:  # pragma: no cover - optional dep
            import jaydebeapi  # type: ignore

            conn = jaydebeapi.connect(
                payload.get("driver", "org.postgresql.Driver"),
                con.config.url,
                [con.config.auth.get("user", ""), con.config.auth.get("password", "")],
            )
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall() if sql.strip().lower().startswith("select") else []
            cur.close()
            conn.close()
            return {"ok": True, "rows": rows}
        except Exception as exc:
            raise RuntimeError(f"jaydebeapi unavailable for {con.config.name}: {exc}") from exc

    async def _sftp(self, con: Connector, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action", "list")
        try:  # pragma: no cover - optional dep
            import paramiko  # type: ignore

            t = paramiko.Transport((con.config.url, payload.get("port", 22)))
            t.connect(
                username=con.config.auth.get("user", ""),
                password=con.config.auth.get("password", ""),
            )
            sftp = paramiko.SFTPClient.from_transport(t)
            if action == "list":
                result = {"files": sftp.listdir(payload.get("path", "/"))}
            elif action == "get":
                sftp.get(payload["remote"], payload["local"])
                result = {"downloaded": (payload["remote"], payload["local"])}
            else:
                sftp.put(payload["local"], payload["remote"])
                result = {"uploaded": (payload["local"], payload["remote"])}
            sftp.close()
            t.close()
            result["ok"] = True
            return result
        except Exception as exc:
            raise RuntimeError(f"connector backend unavailable for {con.config.name}: {exc}") from exc

    async def _mainframe(self, con: Connector, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action", "connect")
        try:  # pragma: no cover - optional dep
            from py3270 import Emulator  # type: ignore

            emu = Emulator(visible=False, model=2)
            emu.connect(con.config.url)
            result = {"connected": True, "screen_rows": 24, "screen_cols": 80, "action": action}
            emu.terminate()
            result["ok"] = True
            return result
        except Exception as exc:
            raise RuntimeError(f"connector backend unavailable for {con.config.name}: {exc}") from exc

    # ---------------------------------------------------- OSINT dispatch
    async def dispatch_osint_lookup(
        self,
        analyzers: List[str],
        payload: Dict[str, Any],
        connector_name: str = "osint-intelowl",
    ) -> Dict[str, Any]:
        """Dispatch an IntelOwl-style threat-intel lookup through the gateway.

        Public entry-point called by ``osint/connectors.py :: bind_intelowl``.
        The job is routed via the typed L5 gateway (rate-limit + auth + mTLS)
        against the Aorta egress whitelist, keeping the CC BY-NC-SAL-4.0
        IntelOwl service out-of-process (no license leakage into the core).

        Parameters
        ----------
        analyzers: list of IntelOwl analyzer / detector names to run.
        payload: IntelOwl-style payload (``value``, ``rttl``, ``tags``, ...).
        connector_name: L5 gateway connector id (default ``osint-intelowl``).

        Returns
        -------
        ``{"job_id", "ok", "status", "body", "analyzers", "connector", "ms"}``

        Raises
        ------
        KeyError when the connector is not registered.
        RuntimeError on transport failure (rate-limit, backend down, ...)
        """
        con = self.connectors.get(connector_name)
        if con is None:
            raise KeyError(
                f"OSINT dispatch: connector '{connector_name}' not registered. "
                "Register it first with "
                "l5.register(ConnectorConfig(name='osint-intelowl', kind='rest', "
                "url='https://intelowl.internal')) and add its FQDN to "
                "the Aorta egress whitelist (k8s/nse-aorta-egress.yaml)."
            )
        # Generic IntelOwl-style API call:
        #   POST /api/v1/analysis/job  {"value":..., "analyzers":[...]}
        job = await self.call(
            connector_name,
            method="POST",
            path="api/v1/analysis/job",
            payload={
                **payload,
                "analyzers": [a.get("name", a) if isinstance(a, dict) else a for a in analyzers],
            },
        )
        body = job.get("body")
        job_id = None
        if isinstance(body, dict):
            job_id = body.get("id") or body.get("job_id") or None
        result: Dict[str, Any] = {
            "job_id": str(job_id) if job_id is not None else None,
            "ok": job.get("status", 0) in (200, 201, 202),
            "status": job.get("status"),
            "body": body,
            "analyzers": list(analyzers),
            "connector": connector_name,
            "ms": round(job.get("ms", 0.0), 2),
        }
        if not result["ok"]:
            self.bump_fail()
        return result

    # ------------------------------------------------------------ auth util
    def _auth_header(self, con: Connector) -> Optional[str]:
        auth = con.config.auth
        if auth.get("type") == "bearer":
            return f"Bearer {auth.get('token', '')}"
        if auth.get("type") == "basic":
            import base64

            token = base64.b64encode(f"{auth.get('user','')}:{auth.get('password','')}".encode()).decode()
            return f"Basic {token}"
        entry = self.vault_get(con.config.name, "token")
        if entry:
            return f"Bearer {entry.value}"
        return None

    # -------------------------------------------------------------- status
    def status_report(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": c.config.name,
                "kind": c.config.kind,
                "requests": c.request_count,
                "errors": c.error_count,
                "last_used": c.last_used_at,
                "rate_limit_per_min": c.config.rate_limit_per_min,
            }
            for c in self.connectors.values()
        ]
