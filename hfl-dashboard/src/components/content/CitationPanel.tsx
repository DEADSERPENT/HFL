import { PUBLICATION } from "@/content/publication";

/** Shows approved bibliographic metadata only. Unconfirmed fields are never rendered or invented. */
export function CitationPanel() {
  const p = PUBLICATION;
  return (
    <section aria-label="Citation" className="card p-6">
      <p className="text-[0.8125rem] font-semibold text-subtle">Status</p>
      <p className="mt-1 text-ink">{p.status}</p>
      <p className="mt-5 text-[0.8125rem] font-semibold text-subtle">Title</p>
      <p className="font-display mt-1 text-2xl text-ink">{p.title}</p>
      {p.confirmed && p.authors ? (
        <>
          <p className="mt-5 text-[0.8125rem] font-semibold text-subtle">Authors</p>
          <ul className="mt-1 text-muted">
            {p.authors.map((a) => (
              <li key={a.name}>
                {a.name}, {a.affiliation}
              </li>
            ))}
          </ul>
          {p.venue && <p className="mt-3 text-muted">{p.venue}</p>}
          {p.doi && <p className="mt-1 text-muted">DOI: {p.doi}</p>}
        </>
      ) : (
        <p className="mt-5 rounded-md border border-line bg-surface/60 px-3 py-2 text-sm text-muted">
          Author list, venue, DOI and publication date will appear here only after the final metadata and publication status are confirmed. No
          citation metadata is shown until then.
        </p>
      )}
    </section>
  );
}
