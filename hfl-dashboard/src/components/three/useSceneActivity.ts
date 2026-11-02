"use client";

import { useEffect, useState, type RefObject } from "react";

/** True while the element is on screen and the document is visible. Used to pause rendering. */
export function useSceneActivity(ref: RefObject<HTMLElement | null>): { onScreen: boolean; active: boolean } {
  const [onScreen, setOnScreen] = useState(false);
  const [docVisible, setDocVisible] = useState(true);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (!("IntersectionObserver" in window)) {
      setOnScreen(true);
      return;
    }
    const obs = new IntersectionObserver(([e]) => setOnScreen(!!e?.isIntersecting), { rootMargin: "120px" });
    obs.observe(el);
    return () => obs.disconnect();
  }, [ref]);

  useEffect(() => {
    const on = () => setDocVisible(document.visibilityState !== "hidden");
    on();
    document.addEventListener("visibilitychange", on);
    return () => document.removeEventListener("visibilitychange", on);
  }, []);

  return { onScreen, active: onScreen && docVisible };
}
