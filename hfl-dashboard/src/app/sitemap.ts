import type { MetadataRoute } from "next";
import { PAGES } from "@/content/site";

export const dynamic = "force-static";

const BASE = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export default function sitemap(): MetadataRoute.Sitemap {
  return PAGES.map((p) => ({ url: new URL(p.href, BASE).toString(), changeFrequency: "monthly", priority: p.href === "/" ? 1 : 0.7 }));
}
