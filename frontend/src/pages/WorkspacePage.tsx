import { useMemo, useState, type FormEvent } from "react";
import { askQuestion, ApiError } from "../api/client";
import Button from "../components/ui/Button";
import SmallCaps from "../components/ui/SmallCaps";
import type { QuestionResponse, QuestionSource } from "../types/qa";

interface WorkspacePageProps {
  onNavigate: (route: string) => void;
  documentId: string;
  documentTitle: string;
  pageCount: number;
  initialQuestion?: string;
}

interface QaItem {
  id: string;
  question: string;
  response: QuestionResponse | null;
  error: string | null;
}

/** The model sometimes adds **bold** markers; show plain text instead. */
function cleanAnswer(text: string): string {
  return text.replace(/\*\*/g, "").trim();
}

/** Page numbers the answer itself mentions, e.g. "[page 4]". */
function pagesMentioned(answer: string): Set<number> {
  const pages = new Set<number>();
  for (const match of answer.matchAll(/page\s+(\d+)/gi)) {
    pages.add(Number(match[1]));
  }
  return pages;
}

export function WorkspacePage({
  onNavigate,
  documentId,
  documentTitle,
  pageCount,
  initialQuestion = "",
}: WorkspacePageProps) {
  const [workspaceTab, setWorkspaceTab] = useState<"chat" | "overview">("chat");
  const [qaList, setQaList] = useState<QaItem[]>([]);
  const [queryInput, setQueryInput] = useState(initialQuestion);
  const [appliedInitial, setAppliedInitial] = useState(initialQuestion);
  const [isQuerying, setIsQuerying] = useState(false);
  const [activeFolio, setActiveFolio] = useState(1);
  const [activeChunkId, setActiveChunkId] = useState<string | null>(null);
  const [expandedChunks, setExpandedChunks] = useState<Set<string>>(new Set());

  // A question chosen from the history drawer fills the input box.
  if (initialQuestion !== appliedInitial) {
    setAppliedInitial(initialQuestion);
    if (initialQuestion) setQueryInput(initialQuestion);
  }

  const pageNumbers = useMemo(
    () => Array.from({ length: pageCount }, (_, index) => index + 1),
    [pageCount],
  );

  // How many answered questions cite each page.
  const citationCount = useMemo(() => {
    const counts = new Map<number, number>();
    for (const item of qaList) {
      if (!item.response?.found) continue;
      for (const page of new Set(item.response.sources.map((s) => s.page_number))) {
        counts.set(page, (counts.get(page) ?? 0) + 1);
      }
    }
    return counts;
  }, [qaList]);

  // Passages retrieved for the page being viewed (newest question first, no repeats).
  const passagesForActivePage = useMemo(() => {
    const seen = new Set<string>();
    const passages: QuestionSource[] = [];
    for (const item of [...qaList].reverse()) {
      for (const source of item.response?.sources ?? []) {
        if (source.page_number === activeFolio && !seen.has(source.chunk_id)) {
          seen.add(source.chunk_id);
          passages.push(source);
        }
      }
    }
    return passages;
  }, [qaList, activeFolio]);

  const showSource = (source: QuestionSource) => {
    setActiveFolio(source.page_number);
    setActiveChunkId(source.chunk_id);
  };

  // Clicking a passage in the answer shows or hides its full text.
  const toggleSource = (source: QuestionSource) => {
    showSource(source);
    setExpandedChunks((previous) => {
      const next = new Set(previous);
      if (next.has(source.chunk_id)) next.delete(source.chunk_id);
      else next.add(source.chunk_id);
      return next;
    });
  };

  const selectPage = (pageNumber: number) => {
    setActiveFolio(pageNumber);
    setActiveChunkId(null);
  };

  const handleAsk = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const questionText = queryInput.trim();
    if (!questionText || isQuerying) return;

    setQueryInput("");
    setIsQuerying(true);

    const id = `qa-${Date.now()}`;

    try {
      const response = await askQuestion(documentId, questionText);
      setQaList((previous) => [
        ...previous,
        { id, question: questionText, response, error: null },
      ]);

      const first = response.found ? response.sources[0] : undefined;
      if (first) showSource(first);
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : "Something went wrong. Please try again.";
      setQaList((previous) => [
        ...previous,
        { id, question: questionText, response: null, error: message },
      ]);
    } finally {
      setIsQuerying(false);
    }
  };

  return (
    <section className="flex min-h-[calc(100vh-62px)] flex-1 flex-col overflow-hidden bg-night">
      <header className="flex shrink-0 flex-col justify-between gap-3 border-b border-rule bg-surface px-4 py-3 sm:flex-row sm:items-center sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <span className="shrink-0 text-xs font-semibold text-brass uppercase font-sans">
            Document:
          </span>
          <span className="truncate font-sans text-sm font-semibold text-parchment">
            {documentTitle}
          </span>
          <span className="hidden font-mono text-xs text-muted sm:inline">
            ({pageCount} pages)
          </span>
        </div>

        <div className="flex shrink-0 gap-1 border border-rule bg-night p-1 rounded-md">
          <button
            onClick={() => setWorkspaceTab("chat")}
            className={`px-3 py-1 text-xs font-medium rounded transition-colors cursor-pointer ${
              workspaceTab === "chat"
                ? "bg-brass font-semibold text-night"
                : "text-muted hover:text-parchment"
            }`}
          >
            Questions &amp; Answers
          </button>
          <button
            onClick={() => setWorkspaceTab("overview")}
            className={`px-3 py-1 text-xs font-medium rounded transition-colors cursor-pointer ${
              workspaceTab === "overview"
                ? "bg-brass font-semibold text-night"
                : "text-muted hover:text-parchment"
            }`}
          >
            Document Overview
          </button>
        </div>
      </header>

      {workspaceTab === "chat" ? (
        <div className="flex min-h-0 flex-1 overflow-hidden">
          <aside className="flex w-16 shrink-0 flex-col justify-between overflow-y-auto border-r border-rule bg-surface/80 py-3 sm:w-[92px]">
            <div className="flex flex-col items-center gap-1.5 px-2">
              <span className="font-sans text-[11px] uppercase tracking-wider font-semibold text-muted mb-1">
                Pages
              </span>

              {pageNumbers.map((pageNumber) => {
                const selected = pageNumber === activeFolio;
                const hasCitation = citationCount.has(pageNumber);

                return (
                  <button
                    key={pageNumber}
                    onClick={() => selectPage(pageNumber)}
                    title={
                      hasCitation
                        ? `Page ${pageNumber} (cited by ${citationCount.get(pageNumber)} question${
                            citationCount.get(pageNumber) === 1 ? "" : "s"
                          })`
                        : `Page ${pageNumber}`
                    }
                    className={`flex h-8 w-full items-center justify-between rounded-xs border px-1.5 text-left font-mono text-[10px] transition-all cursor-pointer ${
                      selected
                        ? "border-brass bg-raised text-brass font-bold shadow-xs"
                        : hasCitation
                          ? "border-brass/40 bg-surface text-parchment hover:border-brass/70"
                          : "border-rule/60 bg-night/70 text-muted hover:border-muted"
                    }`}
                  >
                    <span>p.{String(pageNumber).padStart(2, "0")}</span>
                    {hasCitation && <span className="h-1.5 w-1.5 rounded-full bg-brass" />}
                  </button>
                );
              })}
            </div>

            <div className="border-t border-rule pt-2 text-center font-mono text-[10px] text-muted">
              {pageCount} pages
            </div>
          </aside>

          <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
            <div className="flex-1 space-y-8 overflow-y-auto px-4 py-6 sm:px-8 lg:px-10">
              <div className="mx-auto max-w-reading space-y-8">
                {qaList.length === 0 && !isQuerying && (
                  <div className="space-y-2 rounded-lg border border-rule bg-surface/80 p-6 text-center">
                    <h2 className="font-serif text-lg text-parchment">
                      Ask your first question
                    </h2>
                    <p className="text-xs text-muted">
                      Type a question below. The answer is written from passages found in
                      this document, with the pages they came from.
                    </p>
                  </div>
                )}

                {qaList.map((qa, questionIndex) => {
                  const mentioned = qa.response ? pagesMentioned(qa.response.answer) : new Set<number>();

                  return (
                    <article
                      key={qa.id}
                      className="space-y-3.5 border-b border-rule pb-7 last:border-0"
                    >
                      <div className="flex items-baseline gap-2.5">
                        <span className="rounded border border-brass/50 bg-brass/10 px-2 py-0.5 font-mono text-xs font-semibold text-brass">
                          Q{questionIndex + 1}
                        </span>
                        <h2 className="font-sans text-lg font-semibold leading-snug text-parchment sm:text-xl">
                          {qa.question}
                        </h2>
                      </div>

                      <div className="space-y-3.5 sm:pl-7">
                        {qa.error ? (
                          <div className="rounded-lg border border-ember/40 bg-ember/10 p-4 text-sm text-ember">
                            {qa.error}
                          </div>
                        ) : qa.response && !qa.response.found ? (
                          <div className="space-y-2 rounded-lg border border-rule bg-surface/80 p-4">
                            <h3 className="font-sans text-sm font-semibold text-parchment">
                              No direct answer found in this document.
                            </h3>
                            <p className="text-xs text-muted">
                              Try rephrasing your question or using words that appear in the
                              document.
                            </p>
                          </div>
                        ) : qa.response ? (
                          <>
                            <div className="whitespace-pre-wrap text-sm font-sans leading-relaxed text-parchment/95 sm:text-[15px]">
                              {cleanAnswer(qa.response.answer)}
                            </div>

                            <div className="space-y-2 border-t border-rule/70 pt-3">
                              <SmallCaps>Source Pages &amp; Passages</SmallCaps>
                              {qa.response.sources.map((source, sourceIndex) => {
                                const expanded = expandedChunks.has(source.chunk_id);

                                return (
                                <button
                                  key={source.chunk_id}
                                  onClick={() => toggleSource(source)}
                                  aria-expanded={expanded}
                                  className="flex w-full flex-col justify-between gap-2 rounded border border-rule bg-surface p-3 text-left transition-all hover:border-brass/70 hover:bg-raised/70 sm:flex-row sm:items-center cursor-pointer"
                                >
                                  <span className="font-serif text-xs italic text-parchment/90">
                                    <span className="mr-2 font-mono not-italic text-brass font-bold">
                                      [{sourceIndex + 1}]
                                    </span>
                                    {expanded ? source.text || source.snippet : source.snippet}
                                    <span className="mt-1.5 block font-sans text-[11px] not-italic text-muted">
                                      {expanded ? "Show less ▲" : "Show full passage ▼"}
                                    </span>
                                  </span>
                                  <span className="shrink-0 font-mono text-xs text-brass font-medium">
                                    Page {source.page_number} · Match {(source.score * 100).toFixed(0)}%
                                    {mentioned.has(source.page_number) && (
                                      <span className="ml-2 rounded border border-verdigris/40 bg-verdigris/10 px-1.5 py-0.5 text-[10px] text-verdigris">
                                        cited
                                      </span>
                                    )}
                                  </span>
                                </button>
                                );
                              })}
                            </div>
                          </>
                        ) : null}
                      </div>
                    </article>
                  );
                })}

                {isQuerying && (
                  <div className="space-y-2.5 py-3 sm:pl-7">
                    <p className="font-sans text-sm italic text-brass">
                      Searching the document and writing an answer…
                    </p>
                    <div className="h-1 max-w-md overflow-hidden rounded bg-night border border-rule">
                      <div className="animate-brass-sweep h-full w-1/3 bg-brass" />
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="shrink-0 border-t border-rule bg-surface p-4 sm:px-8">
              <form
                onSubmit={handleAsk}
                className="mx-auto flex max-w-reading items-center gap-3"
              >
                <input
                  value={queryInput}
                  onChange={(event) => setQueryInput(event.target.value)}
                  placeholder="Ask a question about this document…"
                  disabled={isQuerying}
                  className="min-w-0 flex-1 rounded border border-rule bg-night px-3 py-2 text-sm text-parchment placeholder:text-muted/60 focus:border-brass focus:outline-none"
                />
                <Button
                  type="submit"
                  variant="primary"
                  disabled={isQuerying || !queryInput.trim()}
                >
                  Ask Question
                </Button>
              </form>
              <p className="mx-auto mt-2 max-w-reading text-center font-sans text-xs text-muted/70">
                Answers are generated from the retrieved passages. Check the cited pages
                before relying on them.
              </p>
            </div>
          </div>

          <aside className="hidden w-[330px] shrink-0 space-y-4 overflow-y-auto border-l border-rule bg-surface p-5 xl:block">
            <div className="flex items-center justify-between gap-2 border-b border-rule pb-2.5">
              <span className="font-mono text-xs font-bold text-brass">
                PAGE {String(activeFolio).padStart(2, "0")}
              </span>
              <span className="font-sans text-xs text-muted/80">Cited Passages</span>
            </div>

            {passagesForActivePage.length === 0 ? (
              <p className="rounded border border-rule bg-night p-3 text-xs text-muted">
                No question has retrieved a passage from this page yet. Ask a question, or
                pick a page marked with a dot.
              </p>
            ) : (
              <div className="space-y-3">
                {passagesForActivePage.map((source) => (
                  <div
                    key={source.chunk_id}
                    className={`rounded border p-3 ${
                      source.chunk_id === activeChunkId
                        ? "border-brass bg-brass/10"
                        : "border-rule bg-night"
                    }`}
                  >
                    <div className="font-mono text-[10px] font-bold uppercase tracking-wider text-brass">
                      {source.chunk_id} · Match {(source.score * 100).toFixed(0)}%
                    </div>
                    <p className="mt-1.5 font-serif text-xs italic leading-relaxed text-parchment/90">
                      {source.text || source.snippet}
                    </p>
                  </div>
                ))}
              </div>
            )}

            <p className="border-t border-rule pt-3 font-sans text-[11px] leading-snug text-muted/70">
              Page images and exact on-page highlights come later, with page rendering and
              layout analysis.
            </p>
          </aside>
        </div>
      ) : (
        <div className="flex-1 space-y-6 overflow-y-auto px-4 py-6 sm:px-8">
          <div className="mx-auto max-w-6xl space-y-6">
            <header className="space-y-3 border-b border-rule pb-4">
              <h2 className="font-serif text-2xl font-medium text-parchment sm:text-3xl">
                Document Overview: {documentTitle}
              </h2>
              <div className="flex flex-wrap gap-4 border-t border-rule pt-3 text-xs text-muted">
                <span className="rounded bg-surface px-2.5 py-1 border border-rule">
                  Total Pages: <strong className="text-parchment font-mono">{pageCount}</strong>
                </span>
                <span className="rounded bg-surface px-2.5 py-1 border border-rule">
                  Questions asked:{" "}
                  <strong className="text-parchment font-mono">{qaList.length}</strong>
                </span>
                <span className="rounded bg-surface px-2.5 py-1 border border-rule">
                  Pages cited:{" "}
                  <strong className="text-verdigris font-mono">{citationCount.size}</strong>
                </span>
              </div>
            </header>

            <section className="space-y-4 rounded-lg border border-rule bg-surface p-5 sm:p-6">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <SmallCaps>Page Grid — Click Any Page to View</SmallCaps>
                <span className="text-xs text-muted">
                  Pages with a dot were cited by at least one answer
                </span>
              </div>

              <div className="grid grid-cols-5 gap-2.5 sm:grid-cols-10">
                {pageNumbers.map((pageNumber) => (
                  <button
                    key={pageNumber}
                    onClick={() => {
                      selectPage(pageNumber);
                      setWorkspaceTab("chat");
                    }}
                    className="group flex h-14 flex-col items-center justify-center gap-1 rounded border border-rule bg-night p-1.5 hover:border-brass/80 transition-colors cursor-pointer"
                  >
                    <span className="font-mono text-[11px] font-medium text-muted group-hover:text-parchment">
                      p.{pageNumber}
                    </span>
                    <span
                      className={`h-1.5 w-1.5 rounded-full ${
                        citationCount.has(pageNumber) ? "bg-brass" : "bg-transparent"
                      }`}
                    />
                  </button>
                ))}
              </div>
            </section>

            <section className="space-y-4 rounded-lg border border-rule bg-surface p-5 sm:p-6">
              <SmallCaps>Pages Cited So Far</SmallCaps>

              {citationCount.size === 0 ? (
                <p className="text-xs text-muted">
                  Nothing cited yet. Ask a question in the Questions &amp; Answers tab.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[420px] border-collapse text-left text-xs font-sans">
                    <thead>
                      <tr className="border-b border-rule uppercase text-muted text-[11px] font-semibold">
                        <th className="px-3.5 py-2.5">Page</th>
                        <th className="px-3.5 py-2.5">Cited by</th>
                        <th className="px-3.5 py-2.5 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-rule">
                      {[...citationCount.entries()]
                        .sort((a, b) => a[0] - b[0])
                        .map(([pageNumber, count]) => (
                          <tr
                            key={pageNumber}
                            className="cursor-pointer hover:bg-raised transition-colors"
                            onClick={() => {
                              selectPage(pageNumber);
                              setWorkspaceTab("chat");
                            }}
                          >
                            <td className="px-3.5 py-3 font-mono font-semibold text-brass">
                              Page {String(pageNumber).padStart(2, "0")}
                            </td>
                            <td className="px-3.5 py-3 text-parchment">
                              {count} question{count === 1 ? "" : "s"}
                            </td>
                            <td className="px-3.5 py-3 text-right text-xs text-brass font-medium hover:underline">
                              View passages →
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>

            <div className="flex flex-wrap gap-3 pt-2">
              <Button variant="secondary" onClick={() => onNavigate("/app")}>
                ← Back to Dashboard
              </Button>
              <Button variant="secondary" onClick={() => onNavigate("/library")}>
                View All Documents
              </Button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
