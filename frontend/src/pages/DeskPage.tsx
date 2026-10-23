import { useRef, useState } from "react";
import  Button  from "../components/ui/Button";
import  SmallCaps  from "../components/ui/SmallCaps";
import  ForeEdgeStack  from "../components/document/ForeEdgeStack";
import StatusBadge from "../components/ui/StatusBadge";
import type { DocumentRecord } from "../types/document";

interface DeskPageProps {
  documents: DocumentRecord[];
  documentsStatus: "loading" | "ready" | "error";
  documentsError: string;
  onOpenDocument: (documentId: string) => void;
  onUpload: (file: File) => Promise<void>;
}

export function DeskPage({
  documents,
  documentsStatus,
  documentsError,
  onOpenDocument,
  onUpload,
}: DeskPageProps) {
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file?: File) => {
    if (!file || uploading) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setUploadError("Please select a PDF file.");
      return;
    }

    setUploadError("");
    setUploading(true);

    try {
      await onUpload(file);
    } catch (error) {
      setUploadError(
        error instanceof Error ? error.message : "Upload failed. Please try again.",
      );
      setUploading(false);
    }
    // On success the app navigates to the Processing page, so no reset is needed.
  };

  return (
    <main className="mx-auto max-w-6xl space-y-10 px-4 py-8 sm:px-6 sm:py-10">
      <header className="flex flex-col justify-between gap-2 border-b border-rule pb-4 sm:flex-row sm:items-baseline">
        <div>
          <SmallCaps>Document Management</SmallCaps>
          <h1 className="mt-1 font-serif text-3xl font-medium text-parchment sm:text-4xl">
            Dashboard
          </h1>
        </div>
        <span className="font-mono text-xs text-brass font-medium">
          Ready to process PDF documents
        </span>
      </header>

      <section className="grid grid-cols-1 items-start gap-8 lg:grid-cols-12">
        <div className="space-y-4 lg:col-span-5">
          <SmallCaps>Upload New Document</SmallCaps>

          <div
            onDragOver={(event) => {
              event.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(event) => {
              event.preventDefault();
              setDragOver(false);
              void handleFile(event.dataTransfer.files[0]);
            }}
            onClick={() => fileInputRef.current?.click()}
            className={`relative cursor-pointer rounded-lg border-2 border-dashed bg-surface p-7 text-center transition-all ${
              dragOver
                ? "border-brass bg-raised"
                : "border-rule hover:border-brass/60"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              className="hidden"
              onChange={(event) => void handleFile(event.target.files?.[0])}
              onClick={(event) => event.stopPropagation()}
            />

            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-raised border border-rule text-brass text-xl">
              📄
            </div>

            <p className="font-sans font-medium text-base text-parchment">
              Drag and drop your PDF here, or{" "}
              <span className="text-brass underline decoration-brass underline-offset-4 font-semibold">
                browse
              </span>
            </p>
            <p className="mt-1.5 font-sans text-xs text-muted">
              PDF format · Up to 50 MB · Text-based PDFs
            </p>

            <div className="mt-4">
              <Button
                variant="secondary"
                size="sm"
                onClick={(event) => {
                  event.stopPropagation();
                  fileInputRef.current?.click();
                }}
              >
                {uploading ? "Uploading…" : "Upload PDF"}
              </Button>
            </div>

            {uploadError && (
              <p className="mt-3 font-sans text-xs text-ember">{uploadError}</p>
            )}
          </div>

          <div className="grid grid-cols-3 gap-3 border-t border-rule pt-4 text-xs text-muted">
            <div className="space-y-1">
              <span className="font-mono font-bold text-brass text-xs">01</span>
              <div className="font-medium text-parchment">Upload</div>
              <div className="text-[11px] text-muted/80 leading-snug">Your PDF document</div>
            </div>
            <div className="space-y-1">
              <span className="font-mono font-bold text-verdigris text-xs">02</span>
              <div className="font-medium text-parchment">Process</div>
              <div className="text-[11px] text-muted/80 leading-snug">Extract &amp; index text</div>
            </div>
            <div className="space-y-1">
              <span className="font-mono font-bold text-ember text-xs">03</span>
              <div className="font-medium text-parchment">Ask Questions</div>
              <div className="text-[11px] text-muted/80 leading-snug">Get cited answers</div>
            </div>
          </div>
        </div>

        <div className="space-y-4 lg:col-span-7">
          <SmallCaps>Document Page Breakdown</SmallCaps>
          <ForeEdgeStack />
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex flex-col justify-between gap-2 border-b border-rule pb-2 sm:flex-row sm:items-center">
          <div>
            <SmallCaps>Library</SmallCaps>
            <h2 className="mt-1 font-serif text-2xl text-parchment font-medium">
              Available Documents
            </h2>
          </div>
          <span className="font-mono text-xs text-muted">
            {documents.length} documents
          </span>
        </div>

        {documents.length === 0 ? (
          <div className="rounded-lg border border-rule bg-surface p-8 text-center text-sm text-muted">
            {documentsStatus === "loading" && "Loading documents…"}
            {documentsStatus === "error" && (
              <span className="text-ember">{documentsError}</span>
            )}
            {documentsStatus === "ready" &&
              "No documents yet. Upload a PDF above to get started."}
          </div>
        ) : (
        <div className="overflow-x-auto rounded-lg border border-rule bg-surface">
          <table className="w-full min-w-[680px] border-collapse text-left">
            <thead className="bg-raised/60 font-sans text-xs uppercase tracking-wider text-muted border-b border-rule">
              <tr>
                <th className="p-3.5 font-semibold">Document Name</th>
                <th className="p-3.5 font-semibold">Document Type</th>
                <th className="p-3.5 font-semibold">Pages</th>
                <th className="p-3.5 font-semibold">Status</th>
                <th className="p-3.5 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-rule font-sans text-sm">
              {documents.map((document) => (
                <tr
                  key={document.document_id}
                  className="bg-night/80 hover:bg-raised/50 transition-colors"
                >
                  <td className="p-3.5">
                    <div className="font-medium text-parchment">
                      {document.title}
                    </div>
                    <div className="mt-0.5 font-mono text-[11px] text-muted/80">
                      {document.filename}
                    </div>
                  </td>
                  <td className="p-3.5 text-xs text-muted">
                    {document.classification}
                  </td>
                  <td className="p-3.5 font-mono text-xs text-parchment">
                    {document.page_count} pages
                  </td>
                  <td className="p-3.5">
                    <StatusBadge status={document.processing_status} />
                  </td>
                  <td className="p-3.5 text-right">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => onOpenDocument(document.document_id)}
                    >
                      Open Document →
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        )}
      </section>
    </main>
  );
}
