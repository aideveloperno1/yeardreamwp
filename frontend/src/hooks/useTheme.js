import { useEffect, useState } from "react";
const normal = (v) => (["light", "dark", "system"].includes(v) ? v : "system");
export default function useTheme() {
  const [theme, setTheme] = useState(() => {
    try {
      return normal(localStorage.getItem("safety-chat.theme"));
    } catch {
      return "system";
    }
  });
  useEffect(() => {
    const media = matchMedia("(prefers-color-scheme: dark)");
    const apply = () => {
      document.documentElement.dataset.theme =
        theme === "system" ? (media.matches ? "dark" : "light") : theme;
    };
    const sync = (e) => {
      if (e.key === "safety-chat.theme" || e.key === null) {
        try {
          setTheme(normal(localStorage.getItem("safety-chat.theme")));
        } catch {
          /* Keep current preference. */
        }
      }
    };
    apply();
    media.addEventListener("change", apply);
    window.addEventListener("storage", sync);
    return () => {
      media.removeEventListener("change", apply);
      window.removeEventListener("storage", sync);
    };
  }, [theme]);
  return [
    theme,
    (value) => {
      setTheme(value);
      try {
        localStorage.setItem("safety-chat.theme", value);
      } catch {
        /* Choice still applies in memory. */
      }
    },
  ];
}
