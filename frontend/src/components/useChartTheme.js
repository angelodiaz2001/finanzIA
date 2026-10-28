import { useEffect, useState } from "react";

const VARS = ["--series-1", "--series-2", "--grid", "--axis", "--muted", "--surface", "--text"];

function readVars() {
  const style = getComputedStyle(document.documentElement);
  return Object.fromEntries(VARS.map((v) => [v, style.getPropertyValue(v).trim()]));
}

// Recharts necesita colores concretos; los leemos de las variables CSS para que
// el modo claro/oscuro y la paleta vivan en un solo lugar (styles.css).
export default function useChartTheme() {
  const [vars, setVars] = useState(readVars);
  useEffect(() => {
    const update = () => setVars(readVars());
    const media = window.matchMedia?.("(prefers-color-scheme: dark)");
    media?.addEventListener?.("change", update);
    const observer = new MutationObserver(update);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => {
      media?.removeEventListener?.("change", update);
      observer.disconnect();
    };
  }, []);
  return vars;
}
