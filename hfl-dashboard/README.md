# PP-HFM Research Observatory

A standalone, static, public website presenting *Patient-Level Differential Privacy in Hierarchical Federated Learning for Multimodal Medical IoT*.

It is **not** a frontend for the research repository: every number is a hand-authored, curated record. Nothing is read from research files at build or run time, and the browser makes no requests outside the site.

The previous dashboard is preserved in `../hfl-dashboard-old/` (run `npm install` there to use it).

## Commands

| Command | What it does |
|---|---|
| `npm run dev` | Development server at http://localhost:3000 |
| `npm run build` | Static export to `out/`, then the public-bundle check |
| `npm run serve` | Serves `out/` at http://127.0.0.1:4173 |
| `npm run typecheck` | Strict TypeScript check |
| `npm test` | Unit, content-validation and component tests (Vitest) |
| `npm run test:e2e` | End-to-end tests on desktop and mobile (Playwright; needs `npm run build` first) |
| `npm run verify` | All of the above |

Set `NEXT_PUBLIC_SITE_URL` at build time to the public origin, for Open Graph URLs and the sitemap.

## Stack

Next.js (App Router, static export) · TypeScript (strict) · Tailwind CSS 4 · Three.js via React Three Fiber and Drei (loaded only when a 3D view mounts) · Framer Motion · Zod · Vitest + Testing Library · Playwright. Fonts (Sora, Fraunces) are self-hosted.

The visual design is adapted from the PaySphere reference: claymorphism on white, a coral/sage/sand palette, Fraunces (with its `SOFT` axis turned up) for display and Sora for text. Text colours are darkened to meet WCAG AA.

Design rules worth keeping:
- **The material carries meaning:**
  - raised `.clay` = something you can press or operate;
  - inset `.readout` / `.inset-well` = a measured value;
  - flat paper or the quiet `.card` tint = prose.
- **Colour has one meaning each:**
  - coral = action and the patient side;
  - sage = measured;
  - slate = modelled;
  - sand = inconclusive;
  - mulberry = target not met.
- **One orchestrated motion only:** the hero diorama assembles once. Nothing else animates unless the visitor acts.
- **No generic tells:** no caps-tracked labels, no arrows appended to links, no middle-dot meta strings, and no numbered markers unless the content is a sequence.

## Where things live

- `src/content/` is the curated public content layer: `metrics.ts` (every result), `datasets.ts`, `privacy.ts`, `experiments.ts`, `limitations.ts`, `publication.ts`, `architecture.ts`, `research.ts`.
- `src/lib/validation.ts` holds the content rules. They run in the tests **and** during `next build`, so a violation fails the build.
- `src/lib/metric-status.ts` holds the target-classification rule (the prespecified interval rule).
- `src/components/three/` holds the 3D scene. `src/components/architecture/` holds the explorer, the 2D fallback diagram and the guided story.
- `scripts/check-public-bundle.mjs` is the release gate: it scans `out/` for restricted file types, internal paths, repository endpoints and secrets.

## Content review (before changing any value)

1. Check the value, interval and wording against the final manuscript.
2. Set `basis` (measured / modelled). The `evidenceStatus` must equal what the data imply: the build fails if an inconclusive or missed result is labelled as a success.
3. Keep the unit, evaluation context, interpretation and caveat beside the value. Modelled results must say so, and energy must name CloudSim Plus.
4. Publish no records, samples, per-hospital counts or small cohort cells.
5. Leave author, venue, DOI and date empty in `publication.ts` until they are confirmed; validation enforces this.
6. Update `REVIEWED_AT` in `metrics.ts`, then run `npm run verify`.
