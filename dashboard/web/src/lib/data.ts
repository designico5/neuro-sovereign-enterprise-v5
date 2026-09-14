export interface LayerDef {
  id: number;
  glyph: string;
  name: string;
  css: string;
  role: string;
  contains: string[];
  note: string;
}

export const LAYERS: LayerDef[] = [
  {
    id: 0, glyph: "⟁", name: "01_CORE", css: "#ffd08a",
    role: "invarianter Kernel",
    contains: ["neurosovereign/ (17 Layer)", "neuro_stack_final.toml"],
    note: "Unveränderlich, aber strahlend. Endosymbiotic-Source.",
  },
  {
    id: 1, glyph: "⟂", name: "02_MEMBRANE", css: "#4dd8ff",
    role: "semi-permeable Grenze",
    contains: ["k8s/", "terraform/", "Dockerfile", "docker-compose.yml"],
    note: "IaC + Container — Grenze zwischen Kernel und Außenwelt.",
  },
  {
    id: 2, glyph: "◬", name: "03_SYNAPSE", css: "#ff5ad0",
    role: "autokatalytisches Netzwerk",
    contains: ["config/ (Layer-Configs)", "ai_providers_*"],
    note: "Layer-Config + AI-Präparate — Konnektome des Systems.",
  },
  {
    id: 3, glyph: "◉", name: "04_OBSERVER", css: "#6bff8f",
    role: "Meta-Ebene",
    contains: [".github/", "security/", "signing/", "state/"],
    note: "CI/CD + Security + Signing + State — das Auge des Organismus.",
  },
  {
    id: 4, glyph: "⏣", name: "05_OUTPUT", css: "#ff9a4d",
    role: "manifestierte Realität",
    contains: ["deployment/", "voice/", "desktop/", "setup/"],
    note: "Alles Sichtbare: Deployment, Voice, Desktop, Setup.",
  },
  {
    id: 5, glyph: "ⓐ", name: "99_ARCHIVE", css: "#8b97ad",
    role: "Verdauungstrakt",
    contains: ["science-codeevolve/", "self_improving/", "verus/", "_manifest.json"],
    note: "Stasierte Orphans — gelagert, nie gelöscht.",
  },
];

export const GENIE = [
  { n: "Tesla", m: 2.0, c: "#ffd08a" },
  { n: "Ramanujan", m: 2.5, c: "#4dd8ff" },
  { n: "Gödel", m: 2.2, c: "#ff5ad0" },
  { n: "Feynman", m: 1.9, c: "#6bff8f" },
  { n: "Jung", m: 1.7, c: "#ff9a4d" },
];

export const PHASES = [
  { n: "3", hz: "528 Hz" },
  { n: "6", hz: "639 Hz" },
  { n: "9", hz: "963 Hz" },
];

export const SPARK = [
  { l: "L1", v: 0.95 },
  { l: "L2", v: 1.425 },
  { l: "L3", v: 2.1375 },
];

export const METRICS = [
  { key: "genius", label: "Genialitäts-Index", base: 0.78, amp: 0.02, color: "#6bff8f", target: 0.75 },
  { key: "auto", label: "Autokatalyse (G4)", base: 0.53, amp: 0.03, color: "#ffd08a", target: 0.50 },
  { key: "iso", label: "Isomorphie (G2)", base: 0.62, amp: 0.04, color: "#4dd8ff" },
  { key: "tunnel", label: "Quanten-Tunnel (G3)", base: 0.41, amp: 0.05, color: "#ff5ad0" },
  { key: "irre", label: "Irreduzibilität (G5)", base: 0.88, amp: 0.03, color: "#ff9a4d" },
  { key: "fractal", label: "Fraktale Komp. (G1)", base: 0.47, amp: 0.04, color: "#8b97ad" },
  { key: "symb", label: "Symbiose-Score", base: 0.95, amp: 0.01, color: "#cfe0ff" },
];
