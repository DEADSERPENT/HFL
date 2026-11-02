"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { Pause, Play } from "lucide-react";

const STORAGE_KEY = "pphfm-motion";

type MotionState = {
  /** OS-level prefers-reduced-motion. */
  systemReduced: boolean;
  /** The visitor pressed "Pause motion". */
  paused: boolean;
  /** True when decorative motion must not run. */
  reduced: boolean;
  setPaused: (p: boolean) => void;
};

const MotionContext = createContext<MotionState>({
  systemReduced: false,
  paused: false,
  reduced: true, // safest default before hydration
  setPaused: () => {},
});

export function MotionPreferenceProvider({ children }: { children: ReactNode }) {
  const [systemReduced, setSystemReduced] = useState(false);
  const [paused, setPausedState] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setSystemReduced(mq.matches);
    const onChange = (e: MediaQueryListEvent) => setSystemReduced(e.matches);
    mq.addEventListener?.("change", onChange);
    try {
      setPausedState(window.localStorage.getItem(STORAGE_KEY) === "paused");
    } catch {
      /* storage unavailable */
    }
    setReady(true);
    return () => mq.removeEventListener?.("change", onChange);
  }, []);

  const setPaused = useCallback((p: boolean) => {
    setPausedState(p);
    try {
      window.localStorage.setItem(STORAGE_KEY, p ? "paused" : "running");
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    document.documentElement.dataset.motion = paused ? "paused" : "running";
  }, [paused]);

  const value = useMemo(
    () => ({ systemReduced, paused, reduced: !ready || systemReduced || paused, setPaused }),
    [systemReduced, paused, ready, setPaused],
  );
  return <MotionContext.Provider value={value}>{children}</MotionContext.Provider>;
}

export function useMotion(): MotionState {
  return useContext(MotionContext);
}

/** Visible toggle for decorative motion. Honours, and never overrides, the OS preference. */
export function MotionPreferenceControl({ compact = false }: { compact?: boolean }) {
  const { paused, setPaused, systemReduced } = useMotion();
  const label = paused ? "Resume motion" : "Pause motion";
  return (
    <button
      type="button"
      className={compact ? "btn btn-ghost btn-sm !px-2.5" : "btn btn-ghost"}
      aria-pressed={paused}
      onClick={() => setPaused(!paused)}
      aria-label={compact ? label : undefined}
      title={systemReduced ? "Your system requests reduced motion; decorative motion stays off." : compact ? label : undefined}
    >
      {paused ? <Play size={15} aria-hidden /> : <Pause size={15} aria-hidden />}
      {!compact && <span>{label}</span>}
    </button>
  );
}

/** Inline script that applies the stored preference before first paint. */
export const MOTION_BOOT_SCRIPT = `try{if(localStorage.getItem("${STORAGE_KEY}")==="paused")document.documentElement.dataset.motion="paused"}catch(e){}`;
