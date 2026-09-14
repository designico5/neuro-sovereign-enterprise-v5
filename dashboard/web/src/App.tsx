import { AnimatePresence } from "framer-motion";
import { useState } from "react";
import { Canvas } from "@react-three/fiber";
import TorusScene from "./components/TorusScene";
import {
  Header,
  LayerList,
  MetricsPanel,
  PhasePanel,
  GeniePanel,
  FocusPanel,
  StatusStrip,
} from "./components/Hud";
import { useLiveMetrics } from "./lib/useLiveMetrics";

export default function App() {
  const [sel, setSel] = useState(-1);
  const live = useLiveMetrics();

  return (
    <div className="relative h-full w-full overflow-hidden">
      {/* ── 3D canvas (fixed background) ── */}
      <div className="fixed inset-0">
        <Canvas
          camera={{ position: [0, 4, 18.5], fov: 55, near: 0.1, far: 2000 }}
          gl={{ antialias: true, alpha: true }}
          dpr={[1, 2]}
        >
          <color attach="background" args={["#04060d"]} />
          <fogExp2 attach="fog" args={["#04060d", 0.016]} />
          <TorusScene focusId={sel} onPick={setSel} />
        </Canvas>
      </div>

      {/* ── HUD overlay ── */}
      <div className="pointer-events-none fixed inset-0">
        <StatusStrip live={live} />
        <Header />
        <LayerList sel={sel} onSel={(id) => setSel(id === sel ? -1 : id)} />
        <MetricsPanel live={live} />
        <PhasePanel live={live} />
        <GeniePanel />
        <AnimatePresence>
          <FocusPanel sel={sel} onClear={() => setSel(-1)} />
        </AnimatePresence>
      </div>
    </div>
  );
}
