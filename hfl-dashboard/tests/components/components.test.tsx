import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { ResearchMetricCard } from "@/components/metrics/ResearchMetricCard";
import { ResultDetailDrawer } from "@/components/metrics/ResultDetailDrawer";
import { Tabs } from "@/components/content/Tabs";
import { MotionPreferenceProvider, useMotion } from "@/components/motion/MotionPreference";
import { ResultsExplorer } from "@/components/content/ResultsExplorer";
import { metricById } from "@/content/metrics";
import type { MetricRecord } from "@/lib/types";

vi.mock("@/components/three/ArchitectureScene", () => ({ ArchitectureScene: () => <div data-testid="three-scene" /> }));

describe("ResearchMetricCard", () => {
  it("renders value, unit, dataset, status, target and caveat", () => {
    render(<ResearchMetricCard record={metricById("update-delivery-eicu")!} />);
    expect(screen.getByText("97.83%")).toBeInTheDocument();
    expect(screen.getByText("eICU")).toBeInTheDocument();
    expect(screen.getByText("Target not met")).toBeInTheDocument();
    expect(screen.getByText("> 99%")).toBeInTheDocument();
    expect(screen.getByText(/Simulated at packet level in ns-3/)).toBeInTheDocument();
  });
  it("shows the CloudSim caveat on energy", () => {
    render(<ResearchMetricCard record={metricById("energy-wear")!} />);
    expect(screen.getByText(/CloudSim Plus simulation; not a physical hardware energy measurement/)).toBeInTheDocument();
    expect(screen.getByText("Modelled")).toBeInTheDocument();
  });
});

function DrawerHarness() {
  const [r, setR] = useState<MetricRecord | null>(null);
  return (
    <MotionPreferenceProvider>
      <button onClick={() => setR(metricById("utility-eicu-headline")!)}>open</button>
      <ResultDetailDrawer record={r} onClose={() => setR(null)} />
    </MotionPreferenceProvider>
  );
}

describe("ResultDetailDrawer", () => {
  it("opens, closes on Escape and restores focus", async () => {
    const user = userEvent.setup();
    render(<DrawerHarness />);
    const trigger = screen.getByText("open");
    await user.click(trigger);
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText("Inconclusive")).toBeInTheDocument();
    expect(within(dialog).getByText(/prespecified interval rule/)).toBeInTheDocument();
    await user.keyboard("{Escape}");
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(trigger).toHaveFocus();
  });
});

describe("Tabs", () => {
  function T() {
    const [v, setV] = useState<"a" | "b" | "c">("a");
    return (
      <Tabs items={[{ id: "a", label: "A" }, { id: "b", label: "B" }, { id: "c", label: "C" }]} value={v} onChange={setV} label="t">
        panel {v}
      </Tabs>
    );
  }
  it("moves with arrow keys, Home and End", async () => {
    const user = userEvent.setup();
    render(<T />);
    screen.getByRole("tab", { name: "A" }).focus();
    await user.keyboard("{ArrowRight}");
    expect(screen.getByRole("tab", { name: "B" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tab", { name: "B" })).toHaveFocus();
    await user.keyboard("{End}");
    expect(screen.getByText("panel c")).toBeInTheDocument();
    await user.keyboard("{Home}");
    expect(screen.getByRole("tab", { name: "A" })).toHaveAttribute("aria-selected", "true");
  });
});

describe("Results explorer filters", () => {
  it("updates chart summary and announcement together", async () => {
    const user = userEvent.setup();
    render(
      <MotionPreferenceProvider>
        <ResultsExplorer />
      </MotionPreferenceProvider>,
    );
    await user.selectOptions(screen.getByLabelText("Metric"), "update-delivery");
    await user.click(screen.getByRole("radio", { name: "eICU" }));
    expect(screen.getByText("Showing 1 result for Update delivery, eICU.")).toBeInTheDocument();
    expect(screen.getByText(/eICU \(two-edge configuration\) 97.83%.*target not met/)).toBeInTheDocument();
  });
});

describe("Architecture fallback and reduced motion", () => {
  beforeEach(() => vi.resetModules());

  it("shows the 2D diagram when WebGL is unavailable", async () => {
    vi.doMock("@/lib/webgl", () => ({ hasWebGL: () => false, isSmallScreen: () => false }));
    const { ArchitectureExplorer } = await import("@/components/architecture/ArchitectureExplorer");
    const { MotionPreferenceProvider: P } = await import("@/components/motion/MotionPreference");
    render(
      <P>
        <ArchitectureExplorer />
      </P>,
    );
    expect(await screen.findByText(/3D is unavailable on this device/)).toBeInTheDocument();
    expect(screen.getByRole("group", { name: /Two-dimensional diagram/ })).toBeInTheDocument();
  });

  it("honours prefers-reduced-motion and does not autoplay", async () => {
    const mm = window.matchMedia as unknown as ReturnType<typeof vi.fn>;
    mm.mockImplementation((q: string) => ({ matches: q.includes("reduce"), media: q, addEventListener: vi.fn(), removeEventListener: vi.fn() }));
    function Probe() {
      return <span>{useMotion().reduced ? "reduced" : "full"}</span>;
    }
    render(
      <MotionPreferenceProvider>
        <Probe />
      </MotionPreferenceProvider>,
    );
    await waitFor(() => expect(screen.getByText("reduced")).toBeInTheDocument());
    vi.doMock("@/lib/webgl", () => ({ hasWebGL: () => true, isSmallScreen: () => false }));
    const { ArchitectureExplorer } = await import("@/components/architecture/ArchitectureExplorer");
    const { MotionPreferenceProvider: P } = await import("@/components/motion/MotionPreference");
    render(
      <P>
        <ArchitectureExplorer />
      </P>,
    );
    await waitFor(() => expect(screen.getByRole("button", { name: "Play flow" })).toBeInTheDocument());
    mm.mockImplementation((q: string) => ({ matches: false, media: q, addEventListener: vi.fn(), removeEventListener: vi.fn() }));
  });
});
