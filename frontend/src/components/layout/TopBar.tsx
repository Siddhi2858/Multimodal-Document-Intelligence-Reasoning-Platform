
interface TopBarProps {
  activeRoute: string;
  onNavigate: (route: string) => void;
  onToggleHistory: () => void;
  currentDocTitle?: string | null;
  viewerRoute?: string | null;
  processingRoute?: string | null;
}

export default function TopBar({
  activeRoute,
  onNavigate,
  onToggleHistory,
  currentDocTitle,
  viewerRoute,
  processingRoute,
}: TopBarProps) {
  return (
    <header className="sticky top-0 z-40 bg-night/95 backdrop-blur-sm border-b border-rule">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between gap-4">
        <div className="flex items-center space-x-4 min-w-0">
          <button
            onClick={() => onNavigate("/")}
            className="group flex items-center space-x-2.5 text-left focus:outline-none cursor-pointer"
            title="Go to Folio Overview"
          >
            <span className="font-serif text-2xl font-semibold tracking-tight text-parchment group-hover:text-brass transition-colors">
              Folio
            </span>

            <span className="hidden sm:inline-block font-sans text-xs text-muted/80 font-medium px-2 py-0.5 rounded bg-surface border border-rule">
              Document Intelligence
            </span>
          </button>

          {currentDocTitle && (
            <div className="hidden lg:flex items-center space-x-2 border-l border-rule pl-4 py-0.5 min-w-0">
              <span className="text-xs text-muted">Document:</span>
              <span className="text-xs text-parchment/90 font-medium truncate max-w-xs" title={currentDocTitle}>
                {currentDocTitle}
              </span>
            </div>
          )}
        </div>

        <nav className="flex items-center space-x-1 sm:space-x-2 text-xs font-sans">
          <button
            onClick={() => onNavigate("/")}
            className={`px-2.5 py-1.5 rounded font-medium transition-colors cursor-pointer ${
              activeRoute === "/"
                ? "bg-surface text-brass border border-brass/50 font-semibold"
                : "text-muted hover:text-parchment hover:bg-surface/50"
            }`}
          >
            Overview
          </button>

          <button
            onClick={() => onNavigate("/app")}
            className={`px-2.5 py-1.5 rounded font-medium transition-colors cursor-pointer ${
              activeRoute === "/app"
                ? "bg-surface text-brass border border-brass/50 font-semibold"
                : "text-muted hover:text-parchment hover:bg-surface/50"
            }`}
          >
            Dashboard
          </button>

          <button
            onClick={() => onNavigate(viewerRoute ?? "/library")}
            title={viewerRoute ? undefined : "Pick a document from the Library"}
            className={`px-2.5 py-1.5 rounded font-medium transition-colors cursor-pointer ${
              activeRoute === "viewer"
                ? "bg-surface text-brass border border-brass/50 font-semibold"
                : "text-muted hover:text-parchment hover:bg-surface/50"
            }`}
          >
            Document Viewer
          </button>

          {processingRoute && (
          <button
            onClick={() => onNavigate(processingRoute)}
            className={`px-2.5 py-1.5 rounded font-medium transition-colors cursor-pointer hidden md:inline-flex ${
              activeRoute === "processing"
                ? "bg-surface text-brass border border-brass/50 font-semibold"
                : "text-muted hover:text-parchment hover:bg-surface/50"
            }`}
          >
            Processing
          </button>
          )}

          <button
            onClick={() => onNavigate("/library")}
            className={`px-2.5 py-1.5 rounded font-medium transition-colors cursor-pointer ${
              activeRoute === "/library"
                ? "bg-surface text-brass border border-brass/50 font-semibold"
                : "text-muted hover:text-parchment hover:bg-surface/50"
            }`}
          >
            Library
          </button>

          <button
            onClick={() => onNavigate("/styleguide")}
            className={`px-2.5 py-1.5 rounded font-medium transition-colors cursor-pointer hidden sm:inline-flex ${
              activeRoute === "/styleguide"
                ? "bg-surface text-brass border border-brass/50 font-semibold"
                : "text-muted hover:text-parchment hover:bg-surface/50"
            }`}
          >
            Style Guide
          </button>

          <button
            onClick={onToggleHistory}
            title="Open question history"
            className="ml-1 text-xs text-brass hover:text-parchment bg-surface hover:bg-raised border border-rule hover:border-brass/70 px-2.5 py-1.5 rounded flex items-center space-x-1.5 cursor-pointer transition-colors"
          >
            <span className="text-brass font-bold">⏱</span>
            <span className="hidden md:inline font-sans font-medium">
              History
            </span>
          </button>
        </nav>
      </div>
    </header>
  );
}
