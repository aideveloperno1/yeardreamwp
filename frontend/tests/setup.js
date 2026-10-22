import "@testing-library/jest-dom/vitest";
import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";
const media = new Map();
window.matchMedia = (query) => {
  if (!media.has(query))
    media.set(query, {
      matches: false,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    });
  return media.get(query);
};
Element.prototype.scrollIntoView = vi.fn();
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  localStorage.clear();
  sessionStorage.clear();
  document.body.className = "";
});
