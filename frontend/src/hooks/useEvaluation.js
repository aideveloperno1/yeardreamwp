import { useEffect, useRef, useState } from "react";
import C from "../lib/evaluation.js";
import { session } from "../lib/storage.js";
export default function useEvaluation() {
  const [loaded] = useState(() => C.load(session));
  const [data, setData] = useState(loaded.data);
  const dataRef = useRef(loaded.data);
  const [warning, setWarning] = useState(loaded.warning);
  const active = useRef(null);
  const timer = useRef(null);
  const publish = (next) => {
    dataRef.current = next;
    setData(structuredClone(next));
    const w = loaded.warning || C.save(session, next);
    setWarning(w);
  };
  function interrupt() {
    if (!active.current) return;
    clearTimeout(timer.current);
    const next = structuredClone(dataRef.current);
    const b = Object.values(next.batches).find((b) => b.id === active.current);
    if (b) {
      b.state = "interrupted";
      b.items.forEach((i) => {
        if (i.state === "running") i.state = "pending";
      });
    }
    active.current = null;
    publish(next);
  }
  useEffect(() => {
    // Persist the interrupted state restored from a previous reload, without clearing damaged records.
    if (!loaded.warning) C.save(session, dataRef.current);
    window.addEventListener("pagehide", interrupt);
    return () => {
      window.removeEventListener("pagehide", interrupt);
      interrupt();
    };
  }, []);
  function start(fail) {
    if (active.current) return;
    const next = structuredClone(dataRef.current);
    const { type, variant } = next.selection;
    const batch = C.create(type, variant, fail);
    next.batches[type + ":" + variant] = batch;
    active.current = batch.id;
    const tick = () => {
      if (active.current !== batch.id) return;
      const state = structuredClone(dataRef.current);
      const b = state.batches[type + ":" + variant];
      const item = b.items.find((i) => i.state === "pending");
      if (!item) {
        b.state = b.items.some((i) => i.state === "failed")
          ? "partial"
          : "completed";
        active.current = null;
        publish(state);
        return;
      }
      item.state = "running";
      publish(state);
      timer.current = setTimeout(() => {
        if (active.current !== batch.id) return;
        const updated = structuredClone(dataRef.current);
        C.finishItem(updated.batches[type + ":" + variant], item.id);
        publish(updated);
        tick();
      }, 320);
    };
    publish(next);
    tick();
  }
  function select(changes) {
    if (active.current) return;
    const next = structuredClone(dataRef.current);
    next.selection = { ...next.selection, ...changes };
    publish(next);
  }
  return { data, warning, busy: !!active.current, start, select };
}
