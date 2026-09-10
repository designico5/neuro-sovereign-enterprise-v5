import { motion } from "framer-motion";
import { LAYERS, GENIE, PHASES, SPARK, METRICS, LayerDef } from "../lib/data";
import { LiveMetrics } from "../lib/useLiveMetrics";

const fadeUp = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -12 },
};

export function Header() {
  return (
    <motion.div
      {...fadeUp}
      className="nx-panel absolute left-1/2 top-4 -translate-x-1/2 flex items-center gap-4 max-w-[700px] px-6 py-2.5"
    >
      <span
        className="text-[28px]"
        style={{ filter: "drop-shadow(0 0 12px rgba(120,180,255,.7))" }}
      >
        ⟁
      </span>
      <div>
        <h1 className="text-[15px] font-semibold tracking-[0.14em] text-[#eaf1ff]">
          NEXUS TORUS · NSE-v5
        </h1>
        <div className="text-[10.5px] text-[var(--nexus-dim)] tracking-[0.08em]">
          LEBENDIGE 3D-RAUMSTRUKTUR · 17→5-SCHICHT-KOMPRIERUNG · 369/SPARK²
        </div>
      </div>
      <div className="ml-3 flex items-center gap-1.5 border-l border-[var(--nexus-line)] pl-3 text-[10px] text-[var(--nexus-good)] tracking-[0.1em]">
        <span className="nx-dot" /> LIVE
      </div>
    </motion.div>
  );
}

export function LayerList({
  sel,
  onSel,
}: {
  sel: number;
  onSel: (id: number) => void;
}) {
  return (
    <motion.div
      {...fadeUp}
      className="nx-panel absolute left-4 top-24 w-[252px] p-3.5 nx-sidebar"
    >
      <h2 className="mb-2.5 text-[11px] font-semibold tracking-[0.16em] text-[var(--nexus-dim)]">
        SCHICHTEN (5 + ARCHIV)
      </h2>
      {LAYERS.map((l) => (
        <LayerRow key={l.id} l={l} on={sel === l.id} onSel={() => onSel(l.id)} />
      ))}
    </motion.div>
  );
}

function LayerRow({ l, on, onSel }: { l: LayerDef; on: boolean; onSel: () => void }) {
  return (
    <div
      className={"nx-layer" + (on ? " nx-on" : "")}
      onClick={onSel}
    >
      <span className="w-[22px] text-center text-[18px]" style={{ color: l.css }}>
        {l.glyph}
      </span>
      <span className="flex-1 text-[13px] font-semibold">{l.name}</span>
      <span className="text-[10px] text-[var(--nexus-dim)]">{l.role}</span>
      <span
        className="h-2.5 w-2.5 rounded-[3px]"
        style={{ background: l.css, boxShadow: `0 0 8px ${l.css}` }}
      />
    </div>
  );
}

export function MetricsPanel({ live }: { live: LiveMetrics }) {
  return (
    <motion.div
      {...fadeUp}
      className="nx-panel absolute right-4 top-24 w-[264px] p-3.5 nx-sidebar"
    >
      <h2 className="mb-2.5 text-[11px] font-semibold tracking-[0.16em] text-[var(--nexus-dim)]">
        LIVE-METRIKEN
      </h2>
      {METRICS.map((m) => {
        const v = live.values[m.key] ?? m.base;
        return (
          <div key={m.key} className="mb-[11px]">
            <div className="mb-1 flex justify-between text-[11.5px]">
              <span className="text-[var(--nexus-dim)]">{m.label}</span>
              <span className="font-semibold text-[#eaf1ff] tabular-nums">
                {v.toFixed(2)}
              </span>
            </div>
            <div className="nx-bar">
              <div
                style={{
                  width: Math.min(100, v * 100) + "%",
                  background: m.color,
                  boxShadow: `0 0 8px ${m.color}`,
                }}
              />
            </div>
            {m.target != null && (
              <div className="mt-[3px] text-[9.5px] text-[var(--nexus-dim)]">
                Ziel ≥ {m.target}
              </div>
            )}
          </div>
        );
      })}
    </motion.div>
  );
}

export function PhasePanel({ live }: { live: LiveMetrics }) {
  return (
    <motion.div
      {...fadeUp}
      className="nx-panel absolute bottom-[132px] left-4 w-[252px] p-3 nx-sidebar"
    >
      <h2 className="mb-2.5 text-[11px] font-semibold tracking-[0.16em] text-[var(--nexus-dim)]">
        369 / SPARK²
      </h2>
      <div className="flex gap-2">
        {PHASES.map((p, i) => (
          <div
            key={p.n}
            className={"nx-chip" + (live.phase === i ? " nx-on" : "")}
          >
            <div className="text-[20px] font-bold">{p.n}</div>
            <div className="text-[9px] tracking-[0.1em] text-[var(--nexus-dim)]">
              {p.hz}
            </div>
          </div>
        ))}
      </div>
      <div className="mt-2.5 flex gap-2">
        {SPARK.map((s, i) => (
          <div key={s.l} className={"nx-spark" + (live.spark === i ? " nx-on" : "")}>
            <b className="block text-[13px] text-[var(--nexus-core)]">
              {s.v.toFixed(2)}
            </b>
            {s.l}
          </div>
        ))}
      </div>
    </motion.div>
  );
}

export function GeniePanel() {
  return (
    <motion.div
      {...fadeUp}
      className="nx-panel absolute bottom-[132px] right-4 w-[264px] p-3 nx-sidebar"
    >
      <h2 className="mb-2.5 text-[11px] font-semibold tracking-[0.16em] text-[var(--nexus-dim)]">
        GENIE-MODULE (SPARK-BONUS)
      </h2>
      {GENIE.map((g) => (
        <div
          key={g.n}
          className="mb-[7px] flex items-center gap-2 text-[11.5px]"
        >
          <span
            className="nx-gdot"
            style={{ background: g.c, boxShadow: `0 0 8px ${g.c}` }}
          />
          <span className="flex-1">{g.n}</span>
          <span className="font-semibold text-[var(--nexus-core)] tabular-nums">
            ×{g.m.toFixed(1)}
          </span>
        </div>
      ))}
    </motion.div>
  );
}

export function FocusPanel({ sel, onClear }: { sel: number; onClear: () => void }) {
  if (sel < 0) return null;
  const l = LAYERS[sel];
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 16 }}
      className="nx-panel absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-4 px-5 py-3"
    >
      <span
        className="mt-0.5 text-[30px]"
        style={{ color: l.css, textShadow: `0 0 16px ${l.css}` }}
      >
        {l.glyph}
      </span>
      <div className="flex-1">
        <div
          className="mb-1 flex items-center gap-3 text-[14px] font-semibold"
          style={{ color: l.css }}
        >
          {l.name}
          <button
            onClick={onClear}
            className="ml-auto rounded-[8px] border border-[var(--nexus-line)] px-2 py-0.5 text-[9px] text-[var(--nexus-dim)]"
          >
            ✕
          </button>
        </div>
        <div className="mb-2 text-[11px] text-[var(--nexus-dim)]">
          {l.role} · {l.note}
        </div>
        <div className="flex flex-wrap gap-1.5">
          {l.contains.map((c) => (
            <span
              key={c}
              className="nx-tag"
              style={{ borderColor: l.css + "55" }}
            >
              {c}
            </span>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

export function StatusStrip({ live }: { live: LiveMetrics }) {
  return (
    <div className="pointer-events-none absolute left-4 top-4 z-10 text-[10px] tracking-[0.06em] text-[var(--nexus-dim)]">
      STATUS: <span style={{ color: "#6bff8f" }}>3D: AKTIV</span> ·{" "}
      <span style={{ color: "#6bff8f" }}>LIVE: AKTIV</span> · Phase {PHASES[live.phase].n} ·
      Spark {SPARK[live.spark].l}
    </div>
  );
}
