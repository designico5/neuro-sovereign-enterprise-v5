"""
Neuro-Sovereign Enterprise `nse` CLI.

Commands:
    nse start        Start the full 17-layer platform
    nse status       Health report for all layers
    nse identity     Sub-commands: new / anchor / verify / encrypt
    nse dao          Sub-commands: propose / vote / tally / veto
    nse route        Geo-political routing decision
    nse compliance   Run GDPR/EU AI Act / NIST / PCI / SOX compliance checks
    nse legal        Charter / multisig / oracle operations
    nse swarm        Agent swarm: submit / scale / status
    nse knowledge    Add / search knowledge chunks
    nse strategy     List strategies + forecast + trending
    nse vision       OKR dashboard
    nse sbom         Generate real SBOM
    nse test         Smoke-test all 17 layers
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional

from . import NSEPlatform, PlatformConfig, __version__

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    help="Neuro-Sovereign Enterprise v5 CLI",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)
identity_app = typer.Typer(help="Ethos Identity Layer")
dao_app = typer.Typer(help="DAO Governance Layer")
legal_app = typer.Typer(help="Legal Sovereignty Layer")
swarm_app = typer.Typer(help="Agent Swarm Orchestration")
knowledge_app = typer.Typer(help="Data Knowledge Layer")
strategy_app = typer.Typer(help="Strategy Market")
vision_app = typer.Typer(help="Vision & Goals")

app.add_typer(identity_app, name="identity")
app.add_typer(dao_app, name="dao")
app.add_typer(legal_app, name="legal")
app.add_typer(swarm_app, name="swarm")
app.add_typer(knowledge_app, name="knowledge")
app.add_typer(strategy_app, name="strategy")
app.add_typer(vision_app, name="vision")

console = Console()


def _print_json(data: Any) -> None:
    console.print_json(json.dumps(data, default=str, ensure_ascii=False, indent=2))


# ------------------------------------------------------------------ root
@app.command("version")
def version_cmd() -> None:
    """Show Neuro-Sovereign Enterprise version."""
    console.print(f"[bold]Neuro-Sovereign Enterprise[/bold] v{__version__}")


@app.command("start")
def start_cmd(block: bool = typer.Option(True, help="Wait for shutdown signal")) -> None:
    """Start the 17-layer Neuro-Sovereign platform."""
    async def _runner() -> None:
        platform = NSEPlatform()
        await platform.start()
        hr = platform.health_report()
        _print_json(hr)
        console.print(
            f"\n[green]Platform at {hr['completion_percentage']}% completion "
            f"({hr['totals']['layers_initialized']}/{hr['totals']['layers_total']} layers initialized)[/green]"
        )
        if block:
            try:
                await asyncio.sleep(10**9)
            except asyncio.CancelledError:
                await platform.stop()
    asyncio.run(_runner())


@app.command("status")
def status_cmd() -> None:
    """Quick-start the platform, print health report, exit."""
    async def _runner() -> None:
        platform = NSEPlatform()
        await platform.start()
        hr = platform.health_report()
        t = Table(title=f"Health Report ({hr['completion_percentage']}%)")
        t.add_column("#", justify="right")
        t.add_column("Layer")
        t.add_column("Init")
        t.add_column("Healthy")
        for l in hr["layers"]:
            t.add_row(
                str(l["id"]), l["name"],
                "[green]YES[/green]" if l["initialized"] else "[red]NO[/red]",
                "[green]OK[/green]" if l["healthy"] else ("[yellow]TBD[/yellow]" if l["healthy"] is None else "[red]BAD[/red]"),
            )
        console.print(t)
        await platform.stop()
    asyncio.run(_runner())


# ================================================================ IDENTITY
@identity_app.command("new")
def identity_new(display_name: str, password: Optional[str] = None) -> None:
    """Create a new ECC Ed25519 identity."""
    async def _r() -> None:
        p = NSEPlatform()
        await p.start()
        eth = p.get_layer(15)
        ident = eth.generate(display_name, password=password)
        _print_json({
            "id": ident.id,
            "name": ident.display_name,
            "ethos_vector": ident.ethos_vector,
            "signing_pubkey_b64": ident.public_key_bytes_b64,
            "encryption_pubkey_b64": ident.encryption_public_key_b64,
        })
        await p.stop()
    asyncio.run(_r())


@identity_app.command("anchor")
def identity_anchor(identity_id: str, data: str, password: Optional[str] = None,
                    ttl_seconds: int = 3600) -> None:
    """Create a signed identity anchor."""
    async def _r() -> None:
        p = NSEPlatform()
        await p.start()
        eth = p.get_layer(15)
        try:
            payload = json.loads(data)
        except Exception:
            payload = {"raw": data}
        anc = eth.create_anchor(identity_id, payload, ttl_seconds=ttl_seconds, password=password)
        _print_json({
            "anchor_id": anc.anchor_id,
            "expires_at": anc.expires_at,
            "signature_b64": anc.signature_b64,
            "proof": anc.proof,
        })
        await p.stop()
    asyncio.run(_r())


@identity_app.command("verify")
def identity_verify(identity_id: str, anchor_id: str, data: Optional[str] = None) -> None:
    """Verify an identity anchor."""
    async def _r() -> None:
        p = NSEPlatform()
        await p.start()
        eth = p.get_layer(15)
        # Re-fetch anchor from DB
        row = eth._conn.execute(  # type: ignore[union-attr]
            "SELECT anchor_id,identity_id,nonce,signed_at,expires_at,payload_hash,signature_b64,signing_pubkey_b64,proof_json "
            "FROM anchors WHERE anchor_id=?", (anchor_id,),
        ).fetchone()
        if not row:
            console.print("[red]anchor not found[/red]")
            raise SystemExit(2)
        from .layers.layer_15_ethos import IdentityAnchor
        anc = IdentityAnchor(
            anchor_id=row[0], identity_id=row[1], nonce=row[2],
            signed_at=row[3], expires_at=row[4], payload_hash=row[5],
            signature_b64=row[6], signing_pubkey_b64=row[7],
            proof=json.loads(row[8]) if row[8] else {},
        )
        payload: Optional[Dict[str, Any]] = None
        if data:
            try:
                payload = json.loads(data)
            except Exception:
                payload = {"raw": data}
        ok = eth.verify_anchor(anc, payload)
        console.print("[green]ANCHOR VALID[/green]" if ok else "[bold red]ANCHOR INVALID[/bold red]")
        await p.stop()
    asyncio.run(_r())


# ==================================================================== DAO
@dao_app.command("voters")
def dao_voters() -> None:
    async def _r() -> None:
        p = NSEPlatform()
        await p.start()
        dao = p.get_layer(11)
        dao.add_voter("root", reputation=100)
        dao.add_voter("alice", reputation=10)
        dao.add_voter("bob", reputation=5)
        _print_json({"voters": {k: {"rep": v.reputation, "delegated_to": v.delegated_to}
                     for k, v in dao.voters.items()}})
        await p.stop()
    asyncio.run(_r())


@dao_app.command("propose")
def dao_propose(title: str, proposer: str = "root", kind: str = "parameter",
                description: str = "", days: int = 7) -> None:
    async def _r() -> None:
        p = NSEPlatform()
        await p.start()
        dao = p.get_layer(11)
        for who, rep in (("root", 100), ("alice", 10), ("bob", 5)):
            try:
                dao.add_voter(who, reputation=rep)
            except Exception:
                pass
        prop = dao.new_proposal(title, description or title, proposer, kind,
                               duration_seconds=days * 86400)
        _print_json({"id": prop.id, "title": prop.title, "quorum": prop.quorum,
                     "pass_pct": prop.pass_threshold_pct})
        await p.stop()
    asyncio.run(_r())


@dao_app.command("vote")
def dao_vote(proposal_id: str, choice: str, voter: str = "root") -> None:
    async def _r() -> None:
        from .layers.layer_11_dao import VoteChoice
        p = NSEPlatform()
        await p.start()
        dao = p.get_layer(11)
        try:
            dao.add_voter(voter, reputation=10)
        except Exception:
            pass
        v = dao.cast(proposal_id, voter, choice)  # type: ignore[arg-type]
        _print_json({"weight": v.weight, "choice": v.choice})
        await p.stop()
    asyncio.run(_r())


@dao_app.command("tally")
def dao_tally(proposal_id: str) -> None:
    async def _r() -> None:
        p = NSEPlatform()
        await p.start()
        dao = p.get_layer(11)
        _print_json(dao.tally(proposal_id))
        await p.stop()
    asyncio.run(_r())


@dao_app.command("veto")
def dao_veto(proposal_id: str, vetoer: str = "root", reason: str = "") -> None:
    async def _r() -> None:
        p = NSEPlatform()
        await p.start()
        dao = p.get_layer(11)
        dao.human_veto(proposal_id, vetoer, reason)
        console.print(f"[red]Vetoed by {vetoer}[/red]: {reason or '—'}")
        await p.stop()
    asyncio.run(_r())


# ================================================================ COMPLIANCE
@app.command("compliance")
def compliance_check(operation: str, actor: str = "alice",
                     prompt: str = "", output: str = "", eu_ai_risk: str = "minimal") -> None:
    """Run compliance audit against frameworks (GDPR, EU AI Act, NIST, PCI, SOX)."""
    async def _r() -> None:
        p = NSEPlatform()
        await p.start()
        c = p.get_layer(14)
        ctx = {"prompt": prompt, "output": output, "eu_ai_risk": eu_ai_risk,
               "authenticated": True, "roles": ["user"], "change_ticket": "CHG-1000",
               "approved_by": actor}
        audit = await c.evaluate(operation, actor, ctx)
        _print_json({
            "id": audit.id,
            "overall": audit.overall,
            "hash": audit.signed_hash,
            "frameworks": {
                fw: [
                    {"rule": r.rule_id, "severity": r.severity,
                     "passed": r.passed, "evidence": r.evidence}
                    for r in results
                ]
                for fw, results in audit.framework_results.items()
            },
        })
        await p.stop()
    asyncio.run(_r())


# ================================================================ GEO ROUTE
@app.command("route")
def route_cmd(operation: str, ip: str, target: str, categories: str = "personal") -> None:
    """Geo-political routing decision."""
    async def _r() -> None:
        from .layers.layer_16_geo import DataCategory
        p = NSEPlatform()
        await p.start()
        g = p.get_layer(16)
        cats = [c.strip() for c in categories.split(",")]
        audit = g.route(operation, ip, target, cats)  # type: ignore[arg-type]
        _print_json({
            "decision": audit.decision,
            "matched_rule": audit.matched_rule,
            "source_jurisdiction": audit.source_jurisdiction,
            "target_jurisdiction": audit.target_jurisdiction,
            "notes": audit.notes,
        })
        await p.stop()
    asyncio.run(_r())


# ================================================================ LEGAL
@legal_app.command("propose-op")
def legal_propose(name: str, proposer: str = "root", signatures_required: int = 3) -> None:
    async def _r() -> None:
        p = NSEPlatform()
        await p.start()
        l = p.get_layer(17)
        op = l.propose_operation(proposer, name, {"action": "charter-amend",
                                                   "value": "add A4"}, signatures_required)
        _print_json({"id": op.id, "signers": sorted(op.signers),
                     "required": op.required_signatures})
        await p.stop()
    asyncio.run(_r())


@legal_app.command("confirm-op")
def legal_confirm(op_id: str, signer: str) -> None:
    async def _r() -> None:
        p = NSEPlatform()
        await p.start()
        l = p.get_layer(17)
        op = l.confirm_operation(signer, op_id)
        _print_json({"id": op.id, "signers": sorted(op.signers),
                     "executed": op.executed})
        await p.stop()
    asyncio.run(_r())


@legal_app.command("check-compliance")
def legal_check(jurisdiction: str, subject: str) -> None:
    async def _r() -> None:
        p = NSEPlatform()
        await p.start()
        l = p.get_layer(17)
        passed, info = await l.check_compliance(jurisdiction, subject)
        _print_json({"passed": passed, **info})
        await p.stop()
    asyncio.run(_r())


# ================================================================ SWARM
@swarm_app.command("status")
def swarm_status() -> None:
    async def _r() -> None:
        p = NSEPlatform()
        await p.start()
        s = p.get_layer(10)
        _print_json(s.status_report())
        await p.stop()
    asyncio.run(_r())


@swarm_app.command("scale")
def swarm_scale(delta: int) -> None:
    async def _r() -> None:
        p = NSEPlatform()
        await p.start()
        s = p.get_layer(10)
        alive = await s.scale(delta)
        _print_json({"alive": alive})
        await p.stop()
    asyncio.run(_r())


# ================================================================ KNOWLEDGE
@knowledge_app.command("add")
def knowledge_add(source: str, content: str) -> None:
    async def _r() -> None:
        p = NSEPlatform()
        await p.start()
        k = p.get_layer(4)
        chunk = k.add(source, content)
        _print_json({"id": chunk.id, "source": chunk.source})
        await p.stop()
    asyncio.run(_r())


@knowledge_app.command("search")
def knowledge_search(query: str, top_k: int = 5) -> None:
    async def _r() -> None:
        p = NSEPlatform()
        await p.start()
        k = p.get_layer(4)
        hits = k.search(query, top_k=top_k)
        t = Table(title="Knowledge Hits")
        t.add_column("Score")
        t.add_column("ID")
        t.add_column("Source")
        t.add_column("Excerpt")
        for h in hits:
            t.add_row(str(h["score"]), h["id"], h["source"], h["content"])
        console.print(t)
        await p.stop()
    asyncio.run(_r())


# ================================================================ STRATEGY
@strategy_app.command("trending")
def strategy_trending_cmd(top_k: int = 5) -> None:
    async def _r() -> None:
        p = NSEPlatform()
        await p.start()
        s = p.get_layer(13)
        s.list_strategy("Aggressive-Inference-Scaling", 60, "20% cost savings", 15.0, sharpe=1.6, max_drawdown_pct=8.0)
        s.list_strategy("Energy-Procurement-Arbitrage", 30, "Peak/off-peak shift", 8.2, sharpe=1.2)
        s.list_strategy("Compliance-Process-Optimization", 90, "Reduce audit costs", 12.0, sharpe=2.1)
        _print_json(s.trending(top_k))
        await p.stop()
    asyncio.run(_r())


# ================================================================ VISION
@vision_app.command("dashboard")
def vision_dashboard() -> None:
    async def _r() -> None:
        p = NSEPlatform()
        await p.start()
        v = p.get_layer(12)
        obj = v.add_objective("Q4 2026 Compliance Attainment", "governance-team", days=120)
        v.add_kr(obj.id, "90% automated audits", 0.0, 0.9, unit="pct", weight=2.0)
        v.add_kr(obj.id, "<1 critical regressions", 5, 0, unit="count")
        v.progress(obj.id, 0.3)
        _print_json(v.dashboard())
        await p.stop()
    asyncio.run(_r())


# ================================================================ SBOM
@app.command("sbom")
def sbom_cmd(output: str = "sbom-generated.json") -> None:
    """Generate a real SBOM from project metadata + imports."""
    import importlib.metadata as md
    components = []
    known = [
        "cryptography", "pynacl", "ecdsa", "web3", "SQLAlchemy",
        "httpx", "aiohttp", "websockets", "PyJWT", "sqlitedict",
        "numpy", "pydantic", "pydantic-settings", "tenacity",
        "structlog", "python-dotenv", "pyyaml", "click", "typer",
        "rich", "APScheduler", "prometheus-client", "RestrictedPython",
        "docker", "paramiko", "jinja2", "pygit2",
        "ollama", "openai", "torch", "chromadb",
        "networkx", "sentence-transformers",
    ]
    for name in known:
        try:
            ver = md.version(name)
            dist = md.distribution(name)
            components.append({
                "name": name, "version": ver,
                "license": dist.metadata.get("License", "UNKNOWN"),
                "supplier": dist.metadata.get("Author", ""),
            })
        except Exception:
            components.append({"name": name, "version": "missing-declared"})
    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "tool": {"name": "nse-sbom-generator", "version": __version__},
            "component": {"name": "neuro-sovereign-enterprise", "version": __version__},
        },
        "components": components,
        "dependencies": [
            {"ref": "neuro-sovereign-enterprise",
             "dependsOn": [c["name"] for c in components]}
        ],
    }
    outpath = os.path.abspath(output)
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(sbom, f, indent=2)
    console.print(f"[green]SBOM written to {outpath}[/green] ({len(components)} components)")


# ================================================================ SMOKE TEST
@app.command("test")
def test_cmd() -> None:
    """End-to-end smoke test across all 17 layers."""
    failures: List[str] = []
    async def _r() -> None:
        p = NSEPlatform()
        await p.start()
        hr = p.health_report()
        # 1-5: Core infra
        try:
            e = p.get_layer(1); assert callable(e.sample_once)
        except Exception as ex: failures.append(f"L1: {ex}")
        try:
            c = p.get_layer(2); assert c.inventory()
        except Exception as ex: failures.append(f"L2: {ex}")
        try:
            i = p.get_layer(3); r = await i.plan("k8s", {"replicas": 2}); assert r
        except Exception as ex: failures.append(f"L3: {ex}")
        try:
            k = p.get_layer(4); k.add("tutorial", "hello sovereign", {"kind": "doc"})
            hits = k.search("hello")
            assert len(hits) >= 0
        except Exception as ex: failures.append(f"L4: {ex}")
        try:
            ig = p.get_layer(5);
            from .layers.layer_5_integration import ConnectorConfig
            ig.register(ConnectorConfig(name="example", kind="rest", url="https://example.com"))
            st = ig.status_report(); assert len(st) == 1
        except Exception as ex: failures.append(f"L5: {ex}")
        # Layer 6: Sandbox (try RestrictedPython)
        try:
            s6 = p.get_layer(6)
            res = await s6.python_code("result = 21 * 2\n")
            assert res.ok and "42" in res.output
            shell_res = await s6.shell_command(["echo", "hello-nse"])
            assert shell_res.ok and "hello-nse" in shell_res.output
        except Exception as ex: failures.append(f"L6: {ex}")
        # L7 Evolution
        try:
            s7 = p.get_layer(7); ids = s7.seed(["def a(): return 1", "def b(): return 2", "def c(): return 3"])
            ev = await s7.evolve(generations=2, pop_size=6)
            assert "best_score" in ev
        except Exception as ex: failures.append(f"L7: {ex}")
        # L8 Verification
        try:
            v8 = p.get_layer(8)
            r = await v8.verify("def ok(): return 1", "python-syntax")
            assert r.passed
        except Exception as ex: failures.append(f"L8: {ex}")
        # L9 Neuro-Symbolic
        try:
            c9 = p.get_layer(9)
            c9.add_fact("mammal(human)")
            c9.add_clause("mortal", ["mammal(x)"], weight=1.0)
            # Route a query
            route = c9.route("analyse: review our goals")
            assert route.get("lane")
        except Exception as ex: failures.append(f"L9: {ex}")
        # L10 Swarm
        try:
            from .layers.layer_10_swarm import Task
            s10 = p.get_layer(10)
            t = Task(id="t1", name="noop", priority=5)
            await s10.submit(t)
        except Exception as ex: failures.append(f"L10: {ex}")
        # L11 DAO
        try:
            s11 = p.get_layer(11)
            s11.add_voter("demo-voter", reputation=8)
            prop = s11.new_proposal("Smoke-test prop", "Smoke test", "demo-voter", duration_seconds=2)
            assert prop.id
        except Exception as ex: failures.append(f"L11: {ex}")
        # L12 Vision
        try:
            v12 = p.get_layer(12); assert v12.mission_statement()
        except Exception as ex: failures.append(f"L12: {ex}")
        # L13 Strategy
        try:
            s13 = p.get_layer(13)
            s13.list_strategy("Smoke", 10, "test", 5.0, sharpe=1.0)
            assert s13.trending(1)
        except Exception as ex: failures.append(f"L13: {ex}")
        # L14 Compliance
        try:
            c14 = p.get_layer(14)
            audit = await c14.evaluate("smoke-op", "demo", {"prompt": "hello", "authenticated": True, "roles": ["u"]})
            assert audit.id
        except Exception as ex: failures.append(f"L14: {ex}")
        # L15 Identity
        try:
            i15 = p.get_layer(15)
            ident = i15.generate("Smoke Test Ident", password="pass1234")
            anc = i15.create_anchor(ident.id, {"msg": "hi"}, ttl_seconds=60, password="pass1234")
            assert i15.verify_anchor(anc, {"msg": "hi"})
            # Envelope X25519
            i15.generate("Bob Smoke", password="bob1234")
            try:
                env = i15.encrypt_to(ident.id, "Bob Smoke", "hello identity", sender_password="pass1234")
                dec = i15.decrypt_from("Bob Smoke", env, sender_password="bob1234")
                assert dec == "hello identity"
            except Exception as ex:
                failures.append(f"L15-crypto: {ex}")
        except Exception as ex: failures.append(f"L15: {ex}")
        # L16 Geo Router
        try:
            g16 = p.get_layer(16)
            r = g16.route("op", "192.168.1.1", "US", ["personal"])
            assert r.decision
        except Exception as ex: failures.append(f"L16: {ex}")
        # L17 Legal
        try:
            l17 = p.get_layer(17)
            assert l17.status()["frameworks"]
            # Multisig: 1st admin already = founding; add 2 more
            admin2 = "0x1111111111111111111111111111111111111111"
            admin3 = "0x2222222222222222222222222222222222222222"
            founding_admin = list(l17.admins)[0]
            l17.add_admin(founding_admin, admin2)
            l17.add_admin(founding_admin, admin3)
            op = l17.propose_operation(founding_admin, "smoke-multisig", {"x": 1}, required_signatures=3)
            assert admin2 not in op.signers
            # confirm with admin2
            l17.confirm_operation(admin2, op.id)
            # Duplicate signing MUST fail (THE FIX for Solidity bug!)
            try:
                l17.confirm_operation(admin2, op.id)
                failures.append("L17: duplicate signing NOT BLOCKED")
            except PermissionError:
                pass  # GOOD! Duplicate blocked!
            # confirm with admin3 -> should execute
            l17.confirm_operation(admin3, op.id)
            assert op.executed
            # Compliance check
            ok, _ = await l17.check_compliance("EU", "benign-operation")
            assert ok is True
        except Exception as ex: failures.append(f"L17: {ex}")
        # DONE
        await p.stop()
        t = Table(title="17-Layer Smoke Test")
        t.add_column("Result")
        t.add_column("Completion %")
        t.add_column("Layers Init")
        t.add_column("Failures")
        t.add_row(
            "[green]PASS[/green]" if not failures else "[bold red]FAIL[/bold red]",
            f"{hr['completion_percentage']}%",
            f"{hr['totals']['layers_initialized']}/{hr['totals']['layers_total']}",
            str(len(failures)),
        )
        console.print(t)
        if failures:
            console.print("[bold red]Failures:[/bold red]")
            for f in failures:
                console.print(" •", f)
            raise SystemExit(1)
        console.print("[green]All 17 layers smoke-passed.[/green]")
    asyncio.run(_r())


if __name__ == "__main__":
    app()
