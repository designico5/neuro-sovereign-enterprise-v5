# External Docking Points

These top-level directories are **not** one of the 17 internal NSE
molecules. They are reserved mount points for external toolchains that the
platform (built on the ECC agent harness) can plug in. The Nexus
(`NSEPlatform`) probes them via a small, uniform contract.

## The contract

Every docking point exposes the same three members so the registry treats
them uniformly:

| Member        | Meaning                                                                 |
|---------------|-------------------------------------------------------------------------|
| `NAME`        | Stable identifier used by the Nexus registry                           |
| `AVAILABLE`   | `False` while the directory only holds the stub, `True` once wired     |
| `dock()`      | Returns the callable the Swarm (L10) dispatches to; raises `NotImplementedError` while stubbed |

A docking point must **never be left empty**. An empty directory is a
silent failure mode; a declared stub (`AVAILABLE=False` + loud `dock()`)
is an explicit, registry-visible "present but not wired" state. That is
the whole point of this rule: the atlas stays consistent.

## The three points

| Directory                        | Role                          | Importable? |
|----------------------------------|-------------------------------|-------------|
| `self_improving_coding_agent/`   | ECC self-improving harness    | yes (valid module name) |
| `science-codeevolve/`            | external code-evolve engine   | **no** (hyphen = not a Python package; filesystem-only mount marker) |
| `verus/`                         | Verus proof / verification    | yes (valid module name) |

> `science-codeevolve` keeps the hyphen because it mirrors the upstream
> tool name. It is intentionally a **filesystem-only** mount marker, not an
> importable package; its `__init__.py` documents the contract but is not
> meant to be imported. The other two are ordinary importable packages.

## Wiring a point

1. Drop the real toolchain into the directory.
2. Set `AVAILABLE = True` in that directory's `__init__.py`.
3. Implement `dock()` so it returns a callable the Swarm/Nexus can invoke.
4. No other layer is allowed to reach into a docking point directly – it
   goes through the Nexus boundary, exactly like every other molecule.
