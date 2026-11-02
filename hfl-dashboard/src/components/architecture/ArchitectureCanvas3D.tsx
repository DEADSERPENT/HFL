"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
import type { CameraApi, SceneProps } from "@/components/three/ArchitectureScene";
import { useSceneActivity } from "@/components/three/useSceneActivity";
import { hasWebGL, isSmallScreen } from "@/lib/webgl";

/** Three.js is only downloaded when this component mounts in the browser. */
const ArchitectureScene = dynamic(() => import("@/components/three/ArchitectureScene").then((m) => m.ArchitectureScene), {
  ssr: false,
  loading: () => <SceneLoading />,
});

function SceneLoading() {
  return (
    <div className="flex h-full items-center justify-center text-sm text-subtle" role="status">
      Loading 3D view…
    </div>
  );
}

/**
 * Lazy 3D canvas that only mounts once its container nears the viewport,
 * pauses when off screen or when the tab is hidden, caps pixel ratio, and
 * reports failure so the caller can switch to the 2D diagram.
 */
export function ArchitectureCanvas3D({
  apiRef,
  onUnavailable,
  className = "",
  label,
  ...scene
}: SceneProps & {
  apiRef?: React.Ref<CameraApi>;
  onUnavailable: () => void;
  className?: string;
  label: string;
}) {
  const wrap = useRef<HTMLDivElement>(null);
  const { onScreen, active } = useSceneActivity(wrap);
  const [mounted, setMounted] = useState(false);
  const [dpr, setDpr] = useState<[number, number]>([1, 1.5]);

  useEffect(() => {
    if (!hasWebGL()) {
      onUnavailable();
      return;
    }
    setDpr(isSmallScreen() ? [1, 1.25] : [1, Math.min(1.75, window.devicePixelRatio || 1)]);
  }, [onUnavailable]);

  useEffect(() => {
    if (onScreen) setMounted(true);
  }, [onScreen]);

  return (
    <div ref={wrap} className={className || "relative h-full w-full"} aria-label={label} role="img">
      {mounted && <ArchitectureScene {...scene} apiRef={apiRef} active={active} dpr={dpr} onError={onUnavailable} />}
    </div>
  );
}
