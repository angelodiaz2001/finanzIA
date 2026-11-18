import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";

const SRC_DIR = join(process.cwd(), "src");
const HEX_COLOR_RE = /#[0-9a-fA-F]{3,8}\b/g;

function walk(dir) {
  const out = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      if (entry === "__tests__") continue;
      out.push(...walk(full));
    } else if (/\.(js|jsx)$/.test(entry)) {
      out.push(full);
    }
  }
  return out;
}

const errors = [];
for (const file of walk(SRC_DIR)) {
  const rel = relative(SRC_DIR, file).replaceAll("\\", "/");
  const content = readFileSync(file, "utf8");

  if (rel !== "api.js" && /\bfetch\s*\(/.test(content)) {
    errors.push(`${rel}: llamada directa a fetch() fuera de src/api.js`);
  }

  if (rel.startsWith("components/") && rel.endsWith(".jsx")) {
    const matches = content.match(HEX_COLOR_RE);
    if (matches) {
      errors.push(`${rel}: color hexadecimal fijo (${matches.join(", ")}); usa variables de styles.css`);
    }
  }
}

if (errors.length > 0) {
  console.error("Fallo en reglas estáticas del frontend:\n - " + errors.join("\n - "));
  process.exit(1);
}
console.log("Guardias estáticas del frontend OK (cliente HTTP único y cero hexadecimales en JSX).");
