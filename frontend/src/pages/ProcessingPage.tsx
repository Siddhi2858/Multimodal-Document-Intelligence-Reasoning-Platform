import Button from "../components/ui/Button";
import SmallCaps from "../components/ui/SmallCaps";
import StatusBadge from "../components/ui/StatusBadge";
import type { DocumentRecord } from "../types/document";

interface ProcessingPageProps {
  document: DocumentRecord | null;
  onOpenDocument: () => void;
  onBackDesk: () => void;
}

// What the backend does while a document is processing. The backend reports
// only "processing", "ready" or "failed", so these are shown as a checklist
// of what happens, not as live per-step progress.
const STEPS = [
  {
    title: "Reading the PDF",
    label: "Extracting the text of every page",
  },
  {
    title: "Splitting into passages",
    label: "Cutting each page into short, page-tagged chunks",
  },
  {
    title: "Building the search index",
    label: "Creating embeddings and storing them for retrieval",
  },
];

export function ProcessingPage({
  document,
  onOpenDocument,
  onBackDesk,
}: ProcessingPageProps) {
  if (!document) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16 text-center text-sm text-muted">
        Loading document…
      </main>
    );
  }

  const isReady = document.processing_status === "ready";
  const isFailed = document.processing_status === "failed";

  return (
    <main className="mx-auto max-w-3xl space-y-8 px-4 py-10 sm:px-6">
      <header className="space-y-2 text-center">
        <div className="flex items-center justify-center gap-2">
          <span
            className={`h-2 w-2 rounded-full ${
              isFailed ? "bg-ember" : isReady ? "bg-verdigris" : "bg-brass animate-pulse"
            }`}
          />
          <SmallCaps>Document Processing</SmallCaps>
        </div>

        <h1 className="font-serif text-3xl font-medium text-parchment sm:text-4xl">
          {isReady ? "Processed " : isFailed ? "Could not process " : "Processing "}
          <span className="italic text-brass">{document.filename}</span>
        </h1>

        <div className="flex flex-wrap items-center justify-center gap-3 pt-1 font-sans text-xs text-muted">
          <StatusBadge status={document.processing_status} />
          {isReady && (
            <>
              <span>·</span>
              <span>{document.page_count} pages indexed</span>
            </>
          )}
        </div>
      </header>

      <section className="space-y-4 rounded-lg border border-rule bg-surface p-5 sm:p-6">
        <div className="h-2 w-full overflow-hidden rounded-full border border-rule bg-night">
          {isReady && <div className="h-full w-full bg-verdigris" />}
          {isFailed && <div className="h-full w-full bg-ember" />}
          {!isReady && !isFailed && (
            <div className="animate-brass-sweep h-full w-1/3 rounded bg-brass" />
          )}
        </div>

        <SmallCaps>What happens during processing</SmallCaps>

        <div className="divide-y divide-rule text-xs">
          {STEPS.map((step) => (
            <div key={step.title} className="flex items-center gap-3.5 py-3">
              <div className="w-5 text-center font-mono">
                {isReady ? (
                  <span className="font-bold text-verdigris">✓</span>
                ) : (
                  <span className="text-muted/50">•</span>
                )}
              </div>
              <div
                className={isReady ? "text-parchment/80 font-medium" : "text-parchment/90"}
              >
                {step.title}:{" "}
                <span className="font-normal text-xs text-muted">{step.label}</span>
              </div>
            </div>
          ))}
        </div>

        {!isReady && !isFailed && (
          <p className="border-t border-rule pt-4 font-sans text-xs text-muted">
            This page updates by itself. Processing usually takes under a minute,
            and the first document after starting the server can take longer
            while the language model loads.
          </p>
        )}

        {isFailed && (
          <div className="space-y-3 border-t border-rule pt-4">
            <p className="font-sans text-xs text-ember">
              Processing failed. The file may be a scanned PDF (text recognition
              for scans is not supported yet) or may be damaged.
            </p>
            <Button variant="secondary" onClick={onBackDesk}>
              ← Back to Dashboard
            </Button>
          </div>
        )}

        {isReady && (
          <div className="flex flex-wrap items-center justify-between gap-4 border-t border-rule pt-4">
            <div>
              <h2 className="font-serif text-base font-semibold text-parchment">
                Processing Complete
              </h2>
              <p className="mt-0.5 font-sans text-xs text-muted">
                All pages are indexed and ready for questions.
              </p>
            </div>

            <Button variant="primary" onClick={onOpenDocument}>
              Open Document Viewer →
            </Button>
          </div>
        )}
      </section>

      {!isFailed && !isReady && (
        <div className="text-center">
          <button
            onClick={onBackDesk}
            className="cursor-pointer font-sans text-xs text-muted transition-colors hover:text-parchment"
          >
            Back to Dashboard (processing continues)
          </button>
        </div>
      )}
    </main>
  );
}
