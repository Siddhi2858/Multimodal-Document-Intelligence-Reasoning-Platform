
interface RunningMarginRailProps {
  currentFolio?: string | number;
  activeRoute?: string;
}

export default function RunningMarginRail({
  currentFolio = "1",
  activeRoute = "/",
}: RunningMarginRailProps) {
  const displayFolio = typeof currentFolio === "number" ? `Page ${currentFolio}` : currentFolio;

  const routeLabel =
    activeRoute === "/"
      ? "Home"
      : activeRoute === "/app"
        ? "Dashboard"
        : activeRoute.includes("/processing")
          ? "Processing"
          : "Viewer";

  return (
    <aside
      aria-label="Page navigation rail"
      className="hidden xl:flex w-12 shrink-0 flex-col justify-between items-center py-6 border-r border-rule bg-night text-muted select-none z-30"
    >
      <div className="flex flex-col items-center space-y-4">
        <span className="font-sans text-[10px] text-brass uppercase font-semibold">
          Folio
        </span>

        <div className="w-px h-6 bg-rule" />

        <span className="font-mono text-xs text-parchment font-medium">
          {displayFolio}
        </span>
      </div>

      <div className="flex flex-col items-center space-y-3 font-sans text-[10px] text-muted/70">
        <span className="font-medium">
          {routeLabel}
        </span>
      </div>
    </aside>
  );
}
