import  SmallCaps  from "../components/ui/SmallCaps";
import StatusBadge from "../components/ui/StatusBadge";
import type { DocumentRecord } from "../types/document";

interface LibraryPageProps {
  documents: DocumentRecord[];
  documentsStatus: "loading" | "ready" | "error";
  documentsError: string;
  onSelectDocument: (document: DocumentRecord) => void;
  onBackDesk: () => void;
}

export function LibraryPage({
  documents,
  documentsStatus,
  documentsError,
  onSelectDocument,
  onBackDesk,
}: LibraryPageProps) {
  return (
    <main className="mx-auto max-w-5xl space-y-8 px-4 py-8 sm:px-6 sm:py-10">
      <header className="flex flex-col justify-between gap-4 border-b border-rule pb-4 sm:flex-row sm:items-baseline">
        <div>
          <SmallCaps>Repository</SmallCaps>
          <h1 className="mt-1 font-serif text-3xl font-medium text-parchment sm:text-4xl">
            Document Library
          </h1>
          <p className="mt-1 text-xs text-muted">
            Browse and open indexed documents to ask questions and inspect citations.
          </p>
        </div>

        <button
          onClick={onBackDesk}
          className="self-start text-xs text-brass hover:underline cursor-pointer font-medium"
        >
          ← Back to Dashboard
        </button>
      </header>

      {documents.length === 0 ? (
        <div className="rounded-lg border border-rule bg-surface p-8 text-center text-sm text-muted">
          {documentsStatus === "loading" && "Loading documents…"}
          {documentsStatus === "error" && (
            <span className="text-ember">{documentsError}</span>
          )}
          {documentsStatus === "ready" &&
            "No documents yet. Upload a PDF from the Dashboard to get started."}
        </div>
      ) : (
      <div className="divide-y divide-rule rounded-lg border border-rule bg-surface overflow-hidden">
        {documents.map((document, index) => (
          <button
            key={document.document_id}
            onClick={() => onSelectDocument(document)}
            className="group flex w-full flex-col justify-between gap-4 p-5 text-left transition-colors hover:bg-raised/70 md:flex-row md:items-center cursor-pointer"
          >
            <div className="min-w-0 space-y-1">
              <div className="flex items-start gap-3">
                <span className="shrink-0 font-mono text-xs font-bold text-brass rounded border border-brass/40 bg-brass/10 px-1.5 py-0.5">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h2 className="font-sans text-base font-semibold text-parchment group-hover:text-brass transition-colors">
                  {document.title}
                </h2>
              </div>

              <p className="pl-9 font-sans text-xs text-muted">
                {document.filename} · <span className="text-muted/80">{document.classification}</span>
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-4 pl-9 text-xs font-sans md:pl-0">
              <span className="font-mono text-muted">{document.page_count} pages</span>
              <span className="text-muted/70">{document.created_at}</span>
              <StatusBadge status={document.processing_status} />
              <span className="text-brass font-medium group-hover:underline">
                Open Document →
              </span>
            </div>
          </button>
        ))}
      </div>
      )}

      <p className="font-sans text-xs text-muted/70 text-center">
        Documents you upload appear here.
      </p>
    </main>
  );
}
