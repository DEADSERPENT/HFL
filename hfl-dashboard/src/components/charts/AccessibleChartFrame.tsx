"use client";

import { useId, useState, type ReactNode } from "react";
import { Table2 } from "lucide-react";

export type TableColumn = { key: string; label: string; numeric?: boolean };

/**
 * Wraps every chart with a title, a text summary, a persistent caveat and an
 * accessible data-table alternative.
 */
export function AccessibleChartFrame({
  title,
  summary,
  caveat,
  disclosure,
  columns,
  rows,
  children,
  headingLevel = 3,
  persistentLabel,
}: {
  title: string;
  summary: ReactNode;
  caveat?: ReactNode;
  disclosure?: string;
  columns: TableColumn[];
  rows: Record<string, ReactNode>[];
  children: ReactNode;
  headingLevel?: 2 | 3;
  persistentLabel?: string;
}) {
  const [showTable, setShowTable] = useState(false);
  const id = useId();
  const H = headingLevel === 2 ? "h2" : "h3";
  return (
    <figure aria-labelledby={`${id}-t`} aria-describedby={`${id}-s`} className="card p-5 md:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <H id={`${id}-t`} className="text-lg font-medium text-ink">
            {title}
          </H>
          {persistentLabel && (
            <p className="mt-1 inline-flex items-center gap-1.5 rounded-full border border-dashed border-model/60 px-2.5 py-0.5 text-xs font-medium text-model">
              {persistentLabel}
            </p>
          )}
        </div>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          aria-expanded={showTable}
          aria-controls={`${id}-table`}
          onClick={() => setShowTable((s) => !s)}
        >
          <Table2 size={14} aria-hidden /> {showTable ? "Hide data table" : "Show data table"}
        </button>
      </div>
      <figcaption id={`${id}-s`} className="mt-2 text-sm leading-relaxed text-muted">
        {summary}
        {disclosure && <span className="mt-1 block text-xs text-subtle">Axis note: {disclosure}</span>}
      </figcaption>

      <div className="mt-5">{children}</div>

      {caveat && (
        <p className="mt-4 rounded-md border border-caution/30 bg-caution/5 px-3 py-2 text-sm text-caution">
          <span className="font-semibold">Caveat: </span>
          {caveat}
        </p>
      )}

      <div id={`${id}-table`} hidden={!showTable} className="mt-5 overflow-x-auto">
        <table className="data-table">
          <caption className="sr-only">{title}: data table</caption>
          <thead>
            <tr>
              {columns.map((c) => (
                <th key={c.key} scope="col" className={c.numeric ? "num" : undefined}>
                  {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                {columns.map((c, j) =>
                  j === 0 ? (
                    <th key={c.key} scope="row" className="font-medium text-ink normal-case tracking-normal text-[0.92rem]">
                      {r[c.key]}
                    </th>
                  ) : (
                    <td key={c.key} className={c.numeric ? "num tnum text-ink" : "text-muted"}>
                      {r[c.key]}
                    </td>
                  ),
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </figure>
  );
}
