"use client";

import Link from "next/link";
import { useEffect, useId, useMemo, useRef, useState } from "react";
import { Search } from "lucide-react";
import { searchContent } from "@/content/search-index";
import { Dialog } from "./Dialog";

/** Searches only the curated, bundled index of public site content. No network requests. */
export function PublicContentSearch() {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const input = useRef<HTMLInputElement>(null);
  const listId = useId();
  const results = useMemo(() => searchContent(q), [q]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen(true);
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  return (
    <>
      <button type="button" className="btn btn-ghost btn-sm !px-2.5 2xl:!px-3.5" onClick={() => setOpen(true)} aria-label="Search the Observatory">
        <Search size={15} aria-hidden />
        <span className="hidden 2xl:inline">Search</span>
      </button>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title="Search the Observatory"
        description="Searches this website's curated public content only."
        variant="center"
        initialFocus={input}
      >
        <label htmlFor={`${listId}-q`} className="sr-only">
          Search terms
        </label>
        <input
          ref={input}
          id={`${listId}-q`}
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="e.g. eICU delivery, epsilon, energy"
          className="field-input w-full px-4 py-3 text-base placeholder:text-subtle"
          autoComplete="off"
        />
        <p role="status" aria-live="polite" className="mt-3 text-xs text-subtle">
          {q.trim() ? `${results.length} result${results.length === 1 ? "" : "s"}` : "Type to search pages, results, datasets and limitations."}
        </p>
        <ul className="mt-3 space-y-2">
          {results.map((r) => (
            <li key={`${r.section}-${r.href}-${r.title}`}>
              <Link
                href={r.href}
                onClick={() => setOpen(false)}
                className="card card-interactive block p-3"
              >
                <span className="text-[0.8125rem] font-semibold text-subtle">{r.section}</span>
                <span className="block font-medium text-ink">{r.title}</span>
                <span className="mt-0.5 line-clamp-2 block text-sm text-muted">{r.text}</span>
              </Link>
            </li>
          ))}
        </ul>
      </Dialog>
    </>
  );
}
