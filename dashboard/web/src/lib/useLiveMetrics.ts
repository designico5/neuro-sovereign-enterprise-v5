import { useEffect, useRef, useState } from "react";
import { METRICS } from "../lib/data";

export interface LiveMetrics {
  values: Record<string, number>;
  phase: number;   // 0|1|2  → 3/6/9
  spark: number;   // 0|1|2  → L1/L2/L3
}

export function useLiveMetrics(intervalMs = 160): LiveMetrics {
  const t0 = useRef(performance.now());
  const [snap, setSnap] = useState<LiveMetrics>({ values: {}, phase: 0, spark: 0 });

  useEffect(() => {
    const id = setInterval(() => {
      const t = (performance.now() - t0.current) / 1000;
      const values: Record<string, number> = {};
      METRICS.forEach((m, i) => {
        values[m.key] = m.base + Math.sin(t * 0.6 + i * 0.7) * m.amp;
      });
      setSnap({
        values,
        phase: Math.floor(t / 3) % 3,
        spark: Math.floor(t / 2) % 3,
      });
    }, intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);

  return snap;
}
