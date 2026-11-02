"use client";

import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { ContactShadows, OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import {
  Component,
  forwardRef,
  useEffect,
  useImperativeHandle,
  useLayoutEffect,
  useMemo,
  useRef,
  type ReactNode,
} from "react";
import { buildLayout, COMPRESSION_AT, lerp3, type SceneLayout } from "@/components/architecture/layout";
import type { LayerId } from "@/content/architecture";

/**
 * Three.js device-edge-cloud scene (conceptual model). All scientific text
 * lives in HTML outside the canvas; this component only draws geometry.
 */

export type SceneProps = {
  edges: number;
  highlightLayer: LayerId | null;
  showFlow: boolean;
  showPrivacy: boolean;
  showCompression: boolean;
  showEdgeAggregation: boolean;
  /** Animation running (already combined with motion preference and visibility). */
  playing: boolean;
  direction: "up" | "down";
  interactive: boolean;
  compact?: boolean;
  /** Hero only: tiers drop in once with a clay overshoot. Ignored when not playing. */
  assemble?: boolean;
  onError?: () => void;
};

export type CameraApi = {
  rotate: (radians: number) => void;
  tilt: (radians: number) => void;
  zoom: (factor: number) => void;
  reset: () => void;
};

const COLORS = {
  device: new THREE.Color("#ff7a5c"),
  edge: new THREE.Color("#93b78c"),
  cloud: new THREE.Color("#8fa6c2"),
  privacy: new THREE.Color("#6f9469"),
  link: new THREE.Color("#c9bca8"),
  particle: new THREE.Color("#3a2f25"),
};

const HOME = new THREE.Vector3(0, 4.2, 15);
const MIN_DIST = 6;
const MAX_DIST = 22;

class SceneErrorBoundary extends Component<{ onError?: () => void; children: ReactNode }, { failed: boolean }> {
  override state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  override componentDidCatch() {
    this.props.onError?.();
  }
  override render() {
    return this.state.failed ? null : this.props.children;
  }
}

function layerOpacity(layer: LayerId, highlight: LayerId | null): number {
  return highlight === null || highlight === layer ? 1 : 0.28;
}

function Devices({ layout, highlight }: { layout: SceneLayout; highlight: LayerId | null }) {
  const ref = useRef<THREE.InstancedMesh>(null);
  useLayoutEffect(() => {
    const mesh = ref.current;
    if (!mesh) return;
    const m = new THREE.Matrix4();
    const sc = new THREE.Matrix4().makeScale(1, 0.72, 1);
    layout.devices.forEach((d, i) => mesh.setMatrixAt(i, m.makeTranslation(d.x, d.y, d.z).multiply(sc)));
    mesh.instanceMatrix.needsUpdate = true;
  }, [layout]);
  const op = layerOpacity("device", highlight);
  return (
    <instancedMesh key={layout.devices.length} ref={ref} args={[undefined, undefined, layout.devices.length]}>
      <sphereGeometry args={[0.2, 24, 16]} />
      <meshStandardMaterial
        color={COLORS.device}
        emissive={COLORS.device}
        emissiveIntensity={highlight === "device" ? 0.35 : 0.06}
        roughness={0.85}
        metalness={0}
        transparent
        opacity={op}
      />
    </instancedMesh>
  );
}

function Edges({ layout, highlight, aggregation, playing }: { layout: SceneLayout; highlight: LayerId | null; aggregation: boolean; playing: boolean }) {
  const rings = useRef<THREE.Group>(null);
  useFrame((_, dt) => {
    if (playing && rings.current) rings.current.children.forEach((c) => (c.rotation.z += dt * 0.6));
  });
  const op = layerOpacity("edge", highlight);
  return (
    <group>
      {layout.edges.map((e, i) => (
        <mesh key={i} position={[e.x, e.y, e.z]}>
          <cylinderGeometry args={layout.edges.length > 2 ? [0.32, 0.36, 0.18, 36] : [0.5, 0.56, 0.24, 48]} />
          <meshStandardMaterial
            color={COLORS.edge}
            emissive={COLORS.edge}
            emissiveIntensity={highlight === "edge" ? 0.35 : 0.05}
            roughness={0.8}
            metalness={0}
            transparent
            opacity={op}
          />
        </mesh>
      ))}
      <group ref={rings} visible={aggregation}>
        {layout.edges.map((e, i) => (
          <mesh key={i} position={[e.x, e.y, e.z]} rotation={[Math.PI / 2, 0, 0]}>
            <torusGeometry args={[layout.edges.length > 2 ? 0.55 : 0.8, 0.03, 10, 56, Math.PI * 1.6]} />
            <meshStandardMaterial color={COLORS.edge} roughness={0.8} transparent opacity={0.9 * op} />
          </mesh>
        ))}
      </group>
    </group>
  );
}

function Cloud({ layout, highlight }: { layout: SceneLayout; highlight: LayerId | null }) {
  const op = layerOpacity("cloud", highlight);
  const c = layout.cloud;
  return (
    <group position={[c.x, c.y, c.z]}>
      <mesh>
        <sphereGeometry args={[0.5, 40, 28]} />
        <meshStandardMaterial color={COLORS.cloud} emissive={COLORS.cloud} emissiveIntensity={highlight === "cloud" ? 0.35 : 0.05} roughness={0.75} metalness={0} transparent opacity={op} />
      </mesh>
      {[0.85, 1.2].map((r, i) => (
        <mesh key={r} rotation={[Math.PI / 2, 0, i * 0.4]}>
          <torusGeometry args={[r, 0.028, 12, 96]} />
          <meshStandardMaterial color={COLORS.cloud} roughness={0.8} transparent opacity={(0.85 - i * 0.3) * op} />
        </mesh>
      ))}
    </group>
  );
}

function Links({ layout, highlight }: { layout: SceneLayout; highlight: LayerId | null }) {
  const geom = useMemo(() => {
    const pts: number[] = [];
    const seen = new Set<string>();
    for (const p of layout.paths) {
      const k = `${p.from.x},${p.from.z},${p.to.x},${p.to.z},${p.kind}`;
      if (seen.has(k)) continue;
      seen.add(k);
      pts.push(p.from.x, p.from.y, p.from.z, p.to.x, p.to.y, p.to.z);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pts, 3));
    return g;
  }, [layout]);
  useEffect(() => () => geom.dispose(), [geom]);
  return (
    <lineSegments geometry={geom}>
      <lineBasicMaterial color={COLORS.link} transparent opacity={highlight ? 0.14 : 0.24} />
    </lineSegments>
  );
}

function Particles({
  layout,
  playing,
  direction,
  compression,
  visible,
}: {
  layout: SceneLayout;
  playing: boolean;
  direction: "up" | "down";
  compression: boolean;
  visible: boolean;
}) {
  const ref = useRef<THREE.InstancedMesh>(null);
  const t = useRef(0);
  const dummy = useMemo(() => new THREE.Object3D(), []);
  const place = () => {
    const mesh = ref.current;
    if (!mesh) return;
    layout.paths.forEach((p, i) => {
      let f = (t.current + p.phase) % 1;
      if (direction === "down") f = 1 - f;
      const pos = lerp3(p.from, p.to, f);
      let s = 1;
      if (compression && direction === "up" && p.kind === "device-edge") s = f > COMPRESSION_AT ? 0.48 : 1;
      if (p.kind === "edge-cloud") s *= 1.25;
      dummy.position.set(pos.x, pos.y, pos.z);
      dummy.scale.setScalar(s);
      dummy.updateMatrix();
      mesh.setMatrixAt(i, dummy.matrix);
    });
    mesh.instanceMatrix.needsUpdate = true;
  };
  useLayoutEffect(place);
  useFrame((_, dt) => {
    if (!playing) return;
    t.current += Math.min(dt, 0.05) * 0.16;
    place();
  });
  return (
    <instancedMesh key={layout.paths.length} ref={ref} args={[undefined, undefined, layout.paths.length]} visible={visible}>
      <sphereGeometry args={[0.06, 12, 8]} />
      <meshStandardMaterial color={COLORS.particle} roughness={0.6} />
    </instancedMesh>
  );
}

function CompressionRings({ layout, visible }: { layout: SceneLayout; visible: boolean }) {
  const ref = useRef<THREE.InstancedMesh>(null);
  useLayoutEffect(() => {
    const mesh = ref.current;
    if (!mesh) return;
    const dummy = new THREE.Object3D();
    layout.devices.forEach((d, i) => {
      const e = layout.edges[d.edge]!;
      const p = lerp3(d, e, COMPRESSION_AT);
      dummy.position.set(p.x, p.y, p.z);
      dummy.lookAt(e.x, e.y, e.z);
      dummy.updateMatrix();
      mesh.setMatrixAt(i, dummy.matrix);
    });
    mesh.instanceMatrix.needsUpdate = true;
  }, [layout]);
  return (
    <instancedMesh key={layout.devices.length} ref={ref} args={[undefined, undefined, layout.devices.length]} visible={visible}>
      <torusGeometry args={[0.13, 0.014, 6, 24]} />
      <meshBasicMaterial color={COLORS.device} transparent opacity={0.9} />
    </instancedMesh>
  );
}

function PrivacyBoundary({ layout, visible }: { layout: SceneLayout; visible: boolean }) {
  const r = layout.deviceRadius;
  const ringGeom = useMemo(() => {
    const pts: THREE.Vector3[] = [];
    for (let i = 0; i <= 96; i++) {
      const a = (i / 96) * Math.PI * 2;
      pts.push(new THREE.Vector3(Math.cos(a), 0, Math.sin(a)));
    }
    return new THREE.BufferGeometry().setFromPoints(pts);
  }, []);
  useEffect(() => () => ringGeom.dispose(), [ringGeom]);
  return (
    <group position={[0, layout.tierY.device, 0]} visible={visible}>
      <mesh>
        <cylinderGeometry args={[r + 0.55, r + 0.55, 1.15, 72, 1, true]} />
        <meshBasicMaterial color={COLORS.privacy} transparent opacity={0.07} side={THREE.DoubleSide} depthWrite={false} />
      </mesh>
      <mesh>
        <cylinderGeometry args={[r - 0.55, r - 0.55, 1.15, 72, 1, true]} />
        <meshBasicMaterial color={COLORS.privacy} transparent opacity={0.04} side={THREE.DoubleSide} depthWrite={false} />
      </mesh>
      {[0.575, -0.575].map((y) => (
        <group key={y} position={[0, y, 0]}>
          <lineLoop geometry={ringGeom} scale={[r + 0.55, 1, r + 0.55]}>
            <lineBasicMaterial color={COLORS.privacy} transparent opacity={0.7} />
          </lineLoop>
          <lineLoop geometry={ringGeom} scale={[r - 0.55, 1, r - 0.55]}>
            <lineBasicMaterial color={COLORS.privacy} transparent opacity={0.4} />
          </lineLoop>
        </group>
      ))}
    </group>
  );
}

const CameraRig = forwardRef<CameraApi, { interactive: boolean }>(function CameraRig({ interactive }, ref) {
  const { camera, invalidate, controls } = useThree();
  useImperativeHandle(
    ref,
    () => {
      const target = () => ((controls as unknown as { target?: THREE.Vector3 })?.target ?? new THREE.Vector3());
      const apply = (fn: (s: THREE.Spherical) => void) => {
        const tg = target();
        const s = new THREE.Spherical().setFromVector3(camera.position.clone().sub(tg));
        fn(s);
        s.phi = THREE.MathUtils.clamp(s.phi, 0.35, 1.5);
        s.radius = THREE.MathUtils.clamp(s.radius, MIN_DIST, MAX_DIST);
        camera.position.copy(tg).add(new THREE.Vector3().setFromSpherical(s));
        camera.lookAt(tg);
        (controls as unknown as { update?: () => void })?.update?.();
        invalidate();
      };
      return {
        rotate: (d) => apply((s) => (s.theta += d)),
        tilt: (d) => apply((s) => (s.phi += d)),
        zoom: (f) => apply((s) => (s.radius *= f)),
        reset: () => {
          (controls as unknown as { target?: THREE.Vector3 })?.target?.set(0, 0, 0);
          camera.position.copy(HOME);
          camera.lookAt(0, 0, 0);
          (controls as unknown as { update?: () => void })?.update?.();
          invalidate();
        },
      };
    },
    [camera, controls, invalidate],
  );
  return interactive ? (
    <OrbitControls makeDefault enablePan={false} enableDamping dampingFactor={0.08} minDistance={MIN_DIST} maxDistance={MAX_DIST} minPolarAngle={0.35} maxPolarAngle={1.5} />
  ) : null;
});

const easeOutBack = (t: number) => {
  const c1 = 1.70158;
  const c3 = c1 + 1;
  return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
};

/** Drops a tier into place once, with an overshoot like pressed clay. */
function TierDrop({ index, enabled, children }: { index: number; enabled: boolean; children: ReactNode }) {
  const g = useRef<THREE.Group>(null);
  const t = useRef(1);
  const done = useRef(false);
  useLayoutEffect(() => {
    const grp = g.current;
    if (!grp) return;
    if (enabled && !done.current) {
      t.current = 0;
      grp.position.y = 2.2;
      grp.scale.setScalar(0.001);
    } else if (!enabled) {
      // Interrupted or never started: rest in place, and never replay.
      t.current = 1;
      done.current = true;
      grp.position.y = 0;
      grp.scale.setScalar(1);
    }
  }, [enabled]);
  useFrame((_, dt) => {
    if (!g.current || t.current >= 1) return;
    t.current = Math.min(1, t.current + dt / 1.1);
    const local = Math.max(0, Math.min(1, (t.current - index * 0.18) / 0.64));
    const e = easeOutBack(local);
    g.current.position.y = (1 - e) * 2.2;
    g.current.scale.setScalar(Math.max(0.001, e));
    if (t.current >= 1) {
      done.current = true;
      g.current.position.y = 0;
      g.current.scale.setScalar(1);
    }
  });
  return <group ref={g}>{children}</group>;
}

function IdleSpin({ playing }: { playing: boolean }) {
  const { scene } = useThree();
  useFrame((_, dt) => {
    if (playing) scene.rotation.y += dt * 0.04;
  });
  return null;
}

export function ArchitectureScene(props: SceneProps & { active: boolean; dpr: [number, number]; apiRef?: React.Ref<CameraApi> }) {
  const layout = useMemo(() => buildLayout(props.edges, { compact: props.compact }), [props.edges, props.compact]);
  const running = props.playing && props.active;
  return (
    <SceneErrorBoundary onError={props.onError}>
      <Canvas
        frameloop={running ? "always" : "demand"}
        dpr={props.dpr}
        camera={{ position: HOME.toArray(), fov: 42, near: 0.1, far: 100 }}
        gl={{ antialias: true, alpha: true, powerPreference: "low-power", failIfMajorPerformanceCaveat: false }}
        onCreated={({ gl }) => {
          gl.setClearColor(0x000000, 0);
          gl.domElement.addEventListener("webglcontextlost", (e) => {
            e.preventDefault();
            props.onError?.();
          });
        }}
        aria-hidden
      >
        <hemisphereLight args={["#fffdfa", "#e0c98d", 1.15]} />
        <directionalLight position={[-5, 9, 6]} intensity={1.6} color="#fff6ea" />
        <directionalLight position={[6, 3, -4]} intensity={0.35} color="#ffe2d6" />
        <group>
          <Links layout={layout} highlight={props.highlightLayer} />
          <TierDrop index={0} enabled={!!props.assemble && running}>
            <Devices layout={layout} highlight={props.highlightLayer} />
            <CompressionRings layout={layout} visible={props.showCompression} />
            <PrivacyBoundary layout={layout} visible={props.showPrivacy} />
          </TierDrop>
          <TierDrop index={1} enabled={!!props.assemble && running}>
            <Edges layout={layout} highlight={props.highlightLayer} aggregation={props.showEdgeAggregation} playing={running} />
          </TierDrop>
          <TierDrop index={2} enabled={!!props.assemble && running}>
            <Cloud layout={layout} highlight={props.highlightLayer} />
          </TierDrop>
          <Particles layout={layout} playing={running} direction={props.direction} compression={props.showCompression} visible={props.showFlow} />
        </group>
        <ContactShadows key={props.edges} frames={160} position={[0, layout.tierY.device - 0.45, 0]} scale={14} opacity={0.32} blur={2.6} far={6} resolution={512} color="#8a6a3a" />
        {!props.interactive && <IdleSpin playing={running} />}
        <CameraRig ref={props.apiRef} interactive={props.interactive} />
      </Canvas>
    </SceneErrorBoundary>
  );
}

export default ArchitectureScene;
