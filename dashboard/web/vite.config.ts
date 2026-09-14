import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  base: "./",
  plugins: [react(), tailwindcss()],
  server: { port: 8765, host: "127.0.0.1" },
  preview: { port: 8765, host: "127.0.0.1" },
  build: {
    outDir: "dist",
    sourcemap: false,
    chunkSizeWarningLimit: 2000,
  },
});
