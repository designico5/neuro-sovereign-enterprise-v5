import { useRef, useMemo, useState, useCallback } from "react";
import { useFrame } from "@react-three/fiber";
import { OrbitControls, Stars } from "@react-three/drei";
import * as THREE from "three";
import { LAYERS, GENIE } from "../lib/data";

const RING_DEFS = [
  { id: 0, r: 4.0, tilt: 0.15, op: 0.85 },
  { id: 1, r: 6.5, tilt: 0.35, op: 0.55 },
  { id: 2, r: 9.0, tilt: 0.55, op: 0.45 },
  { id: 3, r: 11.5, tilt: 0.75, op: 0.35 },
  { id: 4, r: 14.0, tilt: 0.95, op: 0.3 },
  { id: 5, r: 16.5, tilt: 1.15, op: 0.2 },
];

/* ── One layer ring: torus + additive glow shell ── */
function LayerRing({
  def,
  focused,
  onPick,
}: {
  def: (typeof RING_DEFS)[number];
  focused: boolean;
  onPick: (id: number) => void;
}) {
  const g = useRef<THREE.Group>(null);
  const ringRef = useRef<THREE.Mesh>(null);
  const glowRef = useRef<THREE.Mesh>(null);
  const layer = LAYERS[def.id];
  const [hovered, setHovered] = useState(false);

  useFrame((state, delta) => {
    if (g.current) g.current.rotation.y += delta * 0.06;
    if (ringRef.current) {
      const target = focused ? def.op + 0.4 : def.op;
      const m = ringRef.current.material as THREE.MeshBasicMaterial;
      m.opacity += (target - m.opacity) * 0.12;
    }
    if (glowRef.current) {
      const target = focused ? 0.55 : hovered ? 0.3 : 0;
      const m = glowRef.current.material as THREE.MeshBasicMaterial;
      m.opacity += (target - m.opacity) * 0.08;
    }
    if (g.current) {
      const s = 1 + Math.sin(state.clock.elapsedTime * 1.5 + def.id) * 0.006;
      g.current.scale.setScalar(s);
    }
  });

  return (
    <group rotation={[def.tilt, 0, 0]} position={[0, 0, 0]}>
      <group ref={g}>
        <mesh
          ref={ringRef}
          rotation={[Math.PI / 2 + def.tilt * 0.4, 0, 0]}
          onClick={(e) => {
            e.stopPropagation();
            onPick(def.id);
          }}
          onPointerOver={(e) => {
            e.stopPropagation();
            setHovered(true);
            document.body.style.cursor = "pointer";
          }}
          onPointerOut={() => {
            setHovered(false);
            document.body.style.cursor = "grab";
          }}
        >
          <torusGeometry args={[def.r, 0.06, 20, 220]} />
          <meshBasicMaterial color={layer.css} transparent opacity={def.op} />
        </mesh>
        <mesh
          ref={glowRef}
          rotation={[Math.PI / 2 + def.tilt * 0.4, 0, 0]}
        >
          <torusGeometry args={[def.r, 0.28, 16, 180]} />
          <meshBasicMaterial
            color={layer.css}
            transparent
            opacity={0}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </mesh>
      </group>
    </group>
  );
}

/* ── 17-layer golden-angle core ── */
function Core() {
  const sp = useRef<THREE.Mesh>(null);
  const shell = useRef<THREE.Mesh>(null);
  const stack = useRef<THREE.Group>(null);
  const light = useRef<THREE.PointLight>(null);

  const spheres = useMemo(() => {
    const arr: { x: number; y: number; z: number; color: string; baseY: number }[] = [];
    for (let i = 0; i < 17; i++) {
      const ang = i * 2.399;
      const rr = 1.55 + (i % 3) * 0.12;
      arr.push({
        x: Math.cos(ang) * rr,
        y: (i - 8) * 0.16,
        z: Math.sin(ang) * rr,
        color: `hsl(${(8 + i * 1.2) % 360}, 90%, 62%)`,
        baseY: (i - 8) * 0.16,
      });
    }
    return arr;
  }, []);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    const pulse = 1 + Math.sin(t * 2.2) * 0.06;
    if (sp.current) sp.current.scale.setScalar(pulse);
    if (shell.current) shell.current.scale.setScalar(pulse * 1.1);
    if (light.current) light.current.intensity = 1.3 + Math.sin(t * 2.2) * 0.4;
    if (stack.current) {
      stack.current.children.forEach((child, i) => {
        const def = spheres[i];
        if (!def) return;
        const m = child as THREE.Mesh;
        m.scale.setScalar(1 + Math.sin(t * 2.2 + i * 0.35) * 0.35);
        m.position.y = def.baseY * (1 + Math.sin(t * 1.1) * 0.08);
      });
    }
  });

  return (
    <group>
      <pointLight ref={light} color="#ffd08a" intensity={1.4} distance={40} />
      <mesh ref={sp}>
        <sphereGeometry args={[1.1, 40, 40]} />
        <meshStandardMaterial
          color="#ffd08a"
          emissive="#ffb347"
          emissiveIntensity={0.9}
          roughness={0.3}
          metalness={0.4}
        />
      </mesh>
      <mesh ref={shell}>
        <sphereGeometry args={[1.7, 32, 32]} />
        <meshBasicMaterial
          color="#ffd08a"
          transparent
          opacity={0.18}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </mesh>
      <group ref={stack}>
        {spheres.map((s, i) => (
          <mesh key={i} position={[s.x, s.y, s.z]}>
            <sphereGeometry args={[0.085, 12, 12]} />
            <meshBasicMaterial color={s.color} transparent opacity={0.95} />
          </mesh>
        ))}
      </group>
    </group>
  );
}

/* ── Metabolismus particle flow ── */
function Metabolism() {
  const ref = useRef<THREE.Points>(null);
  const COUNT = 520;

  const { geo, positions } = useMemo(() => {
    const g = new THREE.BufferGeometry();
    const pos = new Float32Array(COUNT * 3);
    const col = new Float32Array(COUNT * 3);
    const cA = new THREE.Color("#4dd8ff");
    const cB = new THREE.Color("#ff5ad0");
    const cC = new THREE.Color("#ffd08a");
    for (let i = 0; i < COUNT; i++) {
      const t = i / COUNT;
      const c =
        t < 0.5
          ? cA.clone().lerp(cB, t * 2)
          : cB.clone().lerp(cC, (t - 0.5) * 2);
      col[i * 3] = c.r;
      col[i * 3 + 1] = c.g;
      col[i * 3 + 2] = c.b;
    }
    g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    g.setAttribute("color", new THREE.BufferAttribute(col, 3));
    return { geo: g, positions: pos };
  }, []);

  useFrame((state) => {
    if (!ref.current) return;
    const t = state.clock.elapsedTime;
    for (let i = 0; i < COUNT; i++) {
      const a = t * 0.25 + i * 0.02;
      const rr = 5 + Math.sin(t * 0.5 + i * 0.35) * 2.6;
      positions[i * 3] = Math.cos(a) * rr;
      positions[i * 3 + 1] = Math.sin(a * 0.7 + i * 0.13) * 1.1;
      positions[i * 3 + 2] = Math.sin(a) * rr;
    }
    ref.current.geometry.attributes.position.needsUpdate = true;
  });

  return (
    <points ref={ref} geometry={geo}>
      <pointsMaterial
        size={0.16}
        vertexColors
        transparent
        opacity={0.9}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </points>
  );
}

/* ── Hexad ring: 6 octahedra ── */
function Hexad() {
  const g = useRef<THREE.Group>(null);
  useFrame((_, d) => {
    if (g.current) g.current.rotation.y -= d * 0.3;
  });
  return (
    <group ref={g}>
      {Array.from({ length: 6 }).map((_, i) => {
        const a = (i / 6) * Math.PI * 2;
        return (
          <mesh key={i} position={[Math.cos(a) * 2.6, 0, Math.sin(a) * 2.6]}>
            <octahedronGeometry args={[0.28, 0]} />
            <meshStandardMaterial
              color="#9fe0ff"
              emissive="#2a6f9f"
              emissiveIntensity={0.6}
              roughness={0.2}
              metalness={0.5}
            />
          </mesh>
        );
      })}
    </group>
  );
}

/* ── Genie nodes: 5 icosahedra ── */
function Genies() {
  const g = useRef<THREE.Group>(null);
  useFrame((_, d) => {
    if (g.current) g.current.rotation.y += d * 0.18;
  });
  return (
    <group ref={g}>
      {GENIE.map((gen, i) => {
        const a = (i / GENIE.length) * Math.PI * 2 - Math.PI / 2;
        return (
          <mesh key={gen.n} position={[Math.cos(a) * 3.4, 1.2, Math.sin(a) * 3.4]}>
            <icosahedronGeometry args={[0.3, 1]} />
            <meshStandardMaterial
              color={gen.c}
              emissive={gen.c}
              emissiveIntensity={0.55}
              roughness={0.3}
              metalness={0.5}
            />
          </mesh>
        );
      })}
    </group>
  );
}

/* ── Full scene composition ── */
export default function TorusScene({
  focusId,
  onPick,
}: {
  focusId: number;
  onPick: (id: number) => void;
}) {
  const world = useRef<THREE.Group>(null);
  const stars = useRef<THREE.Points>(null);
  const controls = useRef<any>(null);

  const clear = useCallback(() => onPick(-1), [onPick]);

  useFrame((state, delta) => {
    if (world.current) world.current.rotation.y += delta * 0.06;
    if (stars.current) stars.current.rotation.y += delta * 0.008;
  });

  return (
    <>
      <ambientLight color="#223355" intensity={0.6} />
      <pointLight color="#88aaff" intensity={1.1} distance={120} position={[10, 18, 14]} />
      <Stars radius={300} depth={120} count={1500} factor={5} saturation={0} fade speed={0.4} />

      <group ref={world} onPointerMissed={clear}>
        {RING_DEFS.map((def) => (
          <LayerRing key={def.id} def={def} focused={focusId === def.id} onPick={onPick} />
        ))}
        <Core />
        <Metabolism />
        <Hexad />
        <Genies />
      </group>

      <OrbitControls
        ref={controls}
        enablePan={false}
        minDistance={6}
        maxDistance={60}
        dampingFactor={0.08}
      />
    </>
  );
}
