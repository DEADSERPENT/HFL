import type { Metadata } from "next";
import { PageHeader, Section } from "@/components/layout/Page";
import { MotionPreferenceControl } from "@/components/motion/MotionPreference";
import { pageMeta } from "@/content/site";

const meta = pageMeta("/accessibility/");
export const metadata: Metadata = { title: meta.title, description: meta.description };

const ALTERNATIVES: [string, string][] = [
  ["3D architecture", "A full 2D SVG diagram with the same layers, flows, privacy boundary and labels; every camera action has a button; arrow keys rotate when the scene is focused."],
  ["Charts", "Every chart has a text summary, a persistent caveat and a data table. Each bar or point is a button that opens a details panel."],
  ["Evidence status", "Shown with text and a distinct icon and outline style, never by colour alone."],
  ["Animation", "Decorative motion follows your system's reduced-motion setting and can be paused at any time with the Pause motion control."],
  ["Search", "Searches this site's curated content only, with results announced to screen readers."],
];

export default function AccessibilityPage() {
  return (
    <>
      <PageHeader eyebrow="About" title="Accessibility" lead="This site aims to meet WCAG 2.2 AA. Every claim is available as text; motion, colour and 3D are never required to understand it." />
      <div className="container-site">
        <Section id="commitments" title="What we support">
          <ul className="grid gap-2 text-muted">
            {[
              "Semantic landmarks, a logical heading order and a skip link.",
              "Keyboard access to every control, with a visible focus indicator.",
              "Accessible names for icon-only buttons.",
              "Dialogs that trap focus, close with Escape and return focus.",
              "Tabs and radio groups operable with arrow keys.",
              "Text contrast tuned for a dark background, with a higher-contrast palette when your system requests it.",
              "Touch targets of at least 36–44 px.",
              "Polite screen-reader announcements when filters change.",
            ].map((x) => (
              <li key={x} className="flex gap-3">
                <span aria-hidden className="mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                {x}
              </li>
            ))}
          </ul>
        </Section>
        <Section id="alternatives" title="Interaction alternatives">
          <dl className="grid gap-3 md:grid-cols-2">
            {ALTERNATIVES.map(([k, v]) => (
              <div key={k} className="card p-5">
                <dt className="font-medium text-ink">{k}</dt>
                <dd className="mt-1 text-sm text-muted">{v}</dd>
              </div>
            ))}
          </dl>
        </Section>
        <Section id="motion" title="Motion">
          <p className="prose-site">Use this control to pause decorative motion across the site. Your choice is remembered on this device.</p>
          <div className="mt-4">
            <MotionPreferenceControl />
          </div>
        </Section>
        <Section id="limits" title="Known limitations" intro={<p>The 3D scene itself is not readable by screen readers; its content is provided in the adjacent text panels and the 2D diagram. Automated and manual checks are ongoing.</p>} />
      </div>
    </>
  );
}
