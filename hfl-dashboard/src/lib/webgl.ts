/** Browser-only capability checks. Safe to import from server components; never runs during prerender. */

let cached: boolean | null = null;

export function hasWebGL(): boolean {
  if (typeof window === "undefined") return false;
  if (cached !== null) return cached;
  try {
    const canvas = document.createElement("canvas");
    const gl =
      (canvas.getContext("webgl2") as WebGLRenderingContext | null) ??
      (canvas.getContext("webgl") as WebGLRenderingContext | null);
    cached = !!gl;
    gl?.getExtension("WEBGL_lose_context")?.loseContext();
  } catch {
    cached = false;
  }
  return cached;
}

/** For tests. */
export function __resetWebGLCache(): void {
  cached = null;
}

export function isSmallScreen(): boolean {
  return typeof window !== "undefined" && window.matchMedia("(max-width: 767px)").matches;
}
