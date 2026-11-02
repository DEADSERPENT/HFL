import Link from "next/link";

export default function NotFound() {
  return (
    <div className="container-site flex min-h-[60vh] flex-col items-start justify-center py-24">
      <p className="eyebrow">404</p>
      <h1 className="font-display mt-4 text-5xl text-ink">This page is not part of the Observatory</h1>
      <p className="mt-4 max-w-xl text-lg text-muted">The address may be mistyped, or the page may have moved.</p>
      <div className="mt-8 flex flex-wrap gap-3">
        <Link href="/" className="btn btn-primary">Back to the overview</Link>
        <Link href="/results/" className="btn btn-ghost">Results</Link>
        <Link href="/limitations/" className="btn btn-ghost">Limitations</Link>
      </div>
    </div>
  );
}
