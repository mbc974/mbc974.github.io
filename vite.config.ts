import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";
import { cpSync, existsSync, mkdirSync } from "node:fs";

function copyStaticFiles() {
  const files = ["CNAME", "robots.txt", "sitemap.xml", "site.webmanifest", "script.js"];

  return {
    name: "copy-static-files",
    closeBundle() {
      const distDir = resolve(__dirname, "dist");

      files.forEach((file) => {
        const from = resolve(__dirname, file);
        if (existsSync(from)) {
          cpSync(from, resolve(distDir, file));
        }
      });

      const assetsFrom = resolve(__dirname, "assets");
      const assetsTo = resolve(distDir, "assets");
      if (existsSync(assetsFrom)) {
        mkdirSync(assetsTo, { recursive: true });
        cpSync(assetsFrom, assetsTo, { recursive: true });
      }
    }
  };
}

export default defineConfig({
  plugins: [react(), copyStaticFiles()],
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, "index.html"),
        adhesion: resolve(__dirname, "adhesion.html"),
        notFound: resolve(__dirname, "404.html")
      }
    }
  }
});
