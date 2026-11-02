import type { Metadata, Viewport } from "next";
import "@fontsource-variable/sora";
import "@fontsource-variable/fraunces/full.css";
import "./globals.css";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { ReadingProgress } from "@/components/layout/ReadingProgress";
import { MotionPreferenceProvider, MOTION_BOOT_SCRIPT } from "@/components/motion/MotionPreference";
import { SITE } from "@/content/site";
import { assertContentValid } from "@/content/assert";

assertContentValid();

/** Public origin for absolute Open Graph URLs; set NEXT_PUBLIC_SITE_URL at deploy time. */
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: SITE.name, template: `%s | ${SITE.wordmark}` },
  description: SITE.tagline,
  applicationName: SITE.name,
  robots: { index: true, follow: true },
  openGraph: {
    type: "website",
    siteName: SITE.name,
    title: SITE.name,
    description: SITE.tagline,
    images: [{ url: "/social-preview/og.svg", width: 1200, height: 630, alt: SITE.name }],
  },
  icons: { icon: "/brand/favicon.svg" },
};

export const viewport: Viewport = { themeColor: "#ffffff", colorScheme: "light" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en-GB" data-motion="running" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: MOTION_BOOT_SCRIPT }} />
      </head>
      <body>
        <div aria-hidden className="blob blob--coral" />
        <div aria-hidden className="blob blob--sage" />
        <div aria-hidden className="blob blob--sand" />
        <div aria-hidden className="grain" />
        <MotionPreferenceProvider>
          <ReadingProgress />
          <SiteHeader />
          <main id="main" tabIndex={-1} className="outline-none">
            {children}
          </main>
          <SiteFooter />
        </MotionPreferenceProvider>
      </body>
    </html>
  );
}
