import { useCallback, useEffect, useState } from "react";

import  TopBar  from "./components/layout/TopBar";
import { HistoryDrawer } from "./components/history/HistoryDrawer";

import { LandingPage } from "./pages/LandingPage";
import { DeskPage } from "./pages/DeskPage";
import { ProcessingPage } from "./pages/ProcessingPage";
import { WorkspacePage } from "./pages/WorkspacePage";
import { LibraryPage } from "./pages/LibraryPage";
import { StyleguidePage } from "./pages/StyleguidePage";

import { ApiError, getDocument, getDocuments, uploadPdf } from "./api/client";

import type { DocumentRecord } from "./types/document";
import type { PastQuery } from "././types/history";

function getDocumentRoute(documentId: string) {
  return `/doc/${documentId}`;
}

function getDocumentIdFromRoute(route: string): string | null {
  const match = route.match(/^\/doc\/([^/]+)/);
  return match?.[1] ?? null;
}

function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Something went wrong.";
}

function App() {
  const [route, setRoute] = useState(
    () => window.location.pathname || "/",
  );

  const [historyOpen, setHistoryOpen] = useState(false);
  const [pendingQuestion, setPendingQuestion] = useState("");

  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [documentsStatus, setDocumentsStatus] = useState<
    "loading" | "ready" | "error"
  >("loading");
  const [documentsError, setDocumentsError] = useState("");

  const [selectedDocument, setSelectedDocument] =
    useState<DocumentRecord | null>(null);
  const [documentError, setDocumentError] = useState("");

  const needsDocuments = route === "/app" || route === "/library";

  const isLanding = route === "/";
  const isDesk = route === "/app";
  const isLibrary = route === "/library";
  const isStyleguide = route === "/styleguide";
  const isProcessing = route.endsWith("/processing");
  const isWorkspace = route.startsWith("/doc/") && !isProcessing;

  const routeDocumentId = getDocumentIdFromRoute(route);

  // The document shown for the current URL: from the loaded list, or the one we opened.
  const activeDocument: DocumentRecord | null = routeDocumentId
    ? (documents.find((document) => document.document_id === routeDocumentId) ??
      (selectedDocument?.document_id === routeDocumentId ? selectedDocument : null))
    : selectedDocument;

  const documentTitles = Object.fromEntries(
    documents.map((document) => [document.document_id, document.title]),
  );

  const needsDocumentFetch = routeDocumentId !== null && activeDocument === null;

  const navigate = useCallback((nextRoute: string) => {
    window.history.pushState({}, "", nextRoute);
    setRoute(nextRoute);
    window.scrollTo({ top: 0, behavior: "auto" });
  }, []);

  useEffect(() => {
    const handlePopState = () => {
      setRoute(window.location.pathname || "/");
    };

    window.addEventListener("popstate", handlePopState);

    return () => {
      window.removeEventListener("popstate", handlePopState);
    };
  }, []);

  // Load the document list on start, and again whenever Dashboard/Library opens.
  useEffect(() => {
    let cancelled = false;

    getDocuments()
      .then((loaded) => {
        if (cancelled) return;
        setDocuments(loaded);
        setDocumentsStatus("ready");
        setDocumentsError("");
      })
      .catch((error) => {
        if (cancelled) return;
        setDocumentsStatus("error");
        setDocumentsError(errorMessage(error));
      });

    return () => {
      cancelled = true;
    };
  }, [needsDocuments]);

  // A /doc/:id URL that is not in the list yet (e.g. after a page reload): fetch it.
  useEffect(() => {
    if (!needsDocumentFetch || !routeDocumentId) return;

    let cancelled = false;

    getDocument(routeDocumentId)
      .then((document) => {
        if (cancelled) return;
        setDocumentError("");
        setSelectedDocument(document);
      })
      .catch((error) => {
        if (!cancelled) setDocumentError(errorMessage(error));
      });

    return () => {
      cancelled = true;
    };
  }, [needsDocumentFetch, routeDocumentId]);

  // While the backend is processing the document, ask for its status every 1.5 s.
  const activeId = activeDocument?.document_id;
  const isActiveProcessing = activeDocument?.processing_status === "processing";

  useEffect(() => {
    if (!isProcessing || !isActiveProcessing || !activeId) return;

    let cancelled = false;

    const timer = window.setInterval(() => {
      getDocument(activeId)
        .then((updated) => {
          if (cancelled) return;
          setSelectedDocument(updated);
          setDocuments((previous) =>
            previous.map((item) =>
              item.document_id === updated.document_id ? updated : item,
            ),
          );
        })
        .catch(() => {
          // Temporary network problem: keep polling.
        });
    }, 1500);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [isProcessing, isActiveProcessing, activeId]);

  const openDocument = useCallback(
    (document: DocumentRecord) => {
      setSelectedDocument(document);
      setPendingQuestion("");
      navigate(
        document.processing_status === "ready"
          ? getDocumentRoute(document.document_id)
          : `${getDocumentRoute(document.document_id)}/processing`,
      );
    },
    [navigate],
  );

  const openSpecimen = useCallback(() => {
    const firstReady = documents.find(
      (document) => document.processing_status === "ready",
    );

    if (!firstReady) {
      navigate("/app");
      return;
    }

    setSelectedDocument(firstReady);
    setPendingQuestion("");
    navigate(getDocumentRoute(firstReady.document_id));
  }, [documents, navigate]);

  // Upload a PDF to the backend, then follow its processing on the next page.
  const uploadDocument = useCallback(
    async (file: File) => {
      const uploaded = await uploadPdf(file);

      setDocuments((previous) => [
        ...previous.filter((item) => item.document_id !== uploaded.document_id),
        uploaded,
      ]);
      setSelectedDocument(uploaded);
      setPendingQuestion("");
      navigate(`${getDocumentRoute(uploaded.document_id)}/processing`);
    },
    [navigate],
  );

  const openProcessedDocument = useCallback(() => {
    if (!activeDocument) return;

    setPendingQuestion("");
    navigate(getDocumentRoute(activeDocument.document_id));
  }, [navigate, activeDocument]);

  const handleHistorySelection = useCallback(
    (pastQuery: PastQuery) => {
      // Open the document the question was asked about; very old entries
      // without a document fall back to the one currently open.
      const documentId = pastQuery.document_id || activeDocument?.document_id;

      if (!documentId) {
        navigate("/library");
        return;
      }

      setPendingQuestion(pastQuery.question);
      navigate(getDocumentRoute(documentId));
    },
    [navigate, activeDocument],
  );

  const activeRoute = isLanding
    ? "/"
    : isDesk
      ? "/app"
      : isLibrary
        ? "/library"
        : isStyleguide
          ? "/styleguide"
          : isProcessing
            ? "processing"
            : "viewer";

  return (
    <div className="min-h-screen bg-night text-parchment">
      <TopBar
        activeRoute={activeRoute}
        onNavigate={navigate}
        onToggleHistory={() => setHistoryOpen((open) => !open)}
        currentDocTitle={activeDocument?.title}
        viewerRoute={activeDocument ? getDocumentRoute(activeDocument.document_id) : null}
        processingRoute={
          activeDocument && (isProcessing || isActiveProcessing)
            ? `${getDocumentRoute(activeDocument.document_id)}/processing`
            : null
        }
      />

      <div className="relative">
        {isLanding && (
          <LandingPage
            onOpenSpecimen={openSpecimen}
            onNavigateDesk={() => navigate("/app")}
          />
        )}

        {isDesk && (
          <DeskPage
            documents={documents}
            documentsStatus={documentsStatus}
            documentsError={documentsError}
            onOpenDocument={(documentId) => {
              const document = documents.find(
                (item) => item.document_id === documentId,
              );

              if (document) {
                openDocument(document);
              }
            }}
            onUpload={uploadDocument}
          />
        )}

        {isProcessing && (
          <ProcessingPage
            document={activeDocument}
            onOpenDocument={openProcessedDocument}
            onBackDesk={() => navigate("/app")}
          />
        )}

        {isWorkspace && !activeDocument && (
          <main className="mx-auto max-w-3xl px-4 py-16 text-center text-sm text-muted">
            {documentError ? (
              <div className="space-y-3">
                <p className="text-ember">{documentError}</p>
                <button
                  onClick={() => navigate("/app")}
                  className="text-xs text-brass hover:underline cursor-pointer font-medium"
                >
                  ← Back to Dashboard
                </button>
              </div>
            ) : (
              "Loading document…"
            )}
          </main>
        )}

        {isWorkspace &&
          activeDocument &&
          activeDocument.processing_status !== "ready" && (
            <main className="mx-auto max-w-3xl space-y-3 px-4 py-16 text-center text-sm text-muted">
              <p>
                This document is not ready for questions yet (status:{" "}
                {activeDocument.processing_status}).
              </p>
              <button
                onClick={() =>
                  navigate(`${getDocumentRoute(activeDocument.document_id)}/processing`)
                }
                className="text-xs text-brass hover:underline cursor-pointer font-medium"
              >
                View processing status →
              </button>
            </main>
          )}

        {isWorkspace &&
          activeDocument &&
          activeDocument.processing_status === "ready" && (
            <WorkspacePage
              key={activeDocument.document_id}
              onNavigate={navigate}
              documentId={activeDocument.document_id}
              documentTitle={activeDocument.title}
              pageCount={activeDocument.page_count}
              initialQuestion={pendingQuestion}
            />
          )}

        {isLibrary && (
          <LibraryPage
            documents={documents}
            documentsStatus={documentsStatus}
            documentsError={documentsError}
            onSelectDocument={openDocument}
            onBackDesk={() => navigate("/app")}
          />
        )}

        {isStyleguide && <StyleguidePage />}
      </div>

      <HistoryDrawer
        isOpen={historyOpen}
        onClose={() => setHistoryOpen(false)}
        onSelectQuery={handleHistorySelection}
        documentTitles={documentTitles}
      />
    </div>
  );
}

export default App;
