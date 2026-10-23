import { useEffect, useState } from "react";
import { ApiError, getHistory } from "../../api/client";
import type { PastQuery } from "../../types/history";

interface HistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectQuery: (query: PastQuery) => void;
  /** document_id -> title, so each question can show which document it belongs to. */
  documentTitles: Record<string, string>;
}

export function HistoryDrawer({
  isOpen,
  onClose,
  onSelectQuery,
  documentTitles,
}: HistoryDrawerProps) {
  const [entries, setEntries] = useState<PastQuery[] | null>(null);
  const [error, setError] = useState("");

  // Load the saved questions every time the drawer opens.
  useEffect(() => {
    if (!isOpen) return;

    let cancelled = false;

    getHistory()
      .then((list) => {
        if (cancelled) return;
        setEntries(list);
        setError("");
      })
      .catch((failure) => {
        if (cancelled) return;
        setError(failure instanceof ApiError ? failure.message : "Could not load history.");
      });

    return () => {
      cancelled = true;
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-night/60 backdrop-blur-[2px]"
      onClick={onClose}
    >
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Question history"
        className="flex h-full w-full max-w-md flex-col justify-between border-l border-rule bg-surface shadow-xl"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="flex items-center justify-between gap-3 border-b border-rule px-6 py-4">
          <div className="flex items-center gap-2">
            <span className="text-brass">⏱</span>
            <h2 className="font-sans text-sm font-semibold text-parchment">
              Question History
            </h2>
          </div>
          <button
            onClick={onClose}
            className="shrink-0 text-xs text-muted hover:text-parchment px-2 py-1 rounded hover:bg-raised transition-colors cursor-pointer"
          >
            ✕ Close
          </button>
        </header>

        <div className="flex-1 space-y-3 overflow-y-auto p-5">
          <p className="text-xs text-muted mb-2">
            Click any previous question to open its document with the question filled in:
          </p>

          {entries === null && !error && (
            <p className="rounded border border-rule bg-night p-3 text-xs text-muted">
              Loading history…
            </p>
          )}

          {entries === null && error && (
            <p className="rounded border border-ember/40 bg-ember/10 p-3 text-xs text-ember">
              {error}
            </p>
          )}

          {entries !== null && entries.length === 0 && (
            <p className="rounded border border-rule bg-night p-3 text-xs text-muted">
              No questions yet. Questions you ask will be saved here.
            </p>
          )}

          {(entries ?? []).map((query, index) => (
            <button
              key={`${query.question}-${index}`}
              onClick={() => {
                onSelectQuery(query);
                onClose();
              }}
              className="group w-full space-y-2.5 rounded-md border border-rule bg-night p-3.5 text-left transition-all hover:border-brass/70 hover:bg-raised/60 cursor-pointer"
            >
              <p className="text-sm font-medium leading-snug text-parchment group-hover:text-brass transition-colors">
                "{query.question}"
              </p>

              {query.document_id && (
                <p className="truncate font-sans text-[11px] text-muted">
                  {documentTitles[query.document_id] ?? query.document_id}
                </p>
              )}

              <div className="flex flex-wrap items-center justify-between gap-2 border-t border-rule/50 pt-2 text-xs text-muted">
                <span className="font-sans">{query.asked_at}</span>
                <div className="flex flex-wrap items-center gap-1.5">
                  {query.pages.length === 0 ? (
                    <span className="text-[11px] text-muted/70">No answer found</span>
                  ) : (
                    <>
                      <span className="text-[11px] text-muted/70">Sources:</span>
                      {query.pages.map((page) => (
                        <span
                          key={page}
                          className="rounded border border-brass/40 bg-brass/10 px-1.5 py-0.5 font-mono text-[11px] text-brass font-medium"
                        >
                          Page {page}
                        </span>
                      ))}
                    </>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>

        <footer className="border-t border-rule px-6 py-3.5 text-center font-sans text-xs text-muted/80">
          Saved questions from all your documents
        </footer>
      </aside>
    </div>
  );
}
