import  Button  from "../components/ui/Button";
import  SmallCaps  from "../components/ui/SmallCaps";

const COLORS = [
  { name: "night", hex: "#0E1512", className: "bg-night text-parchment" },
  { name: "surface", hex: "#151F1A", className: "bg-surface text-parchment" },
  { name: "raised", hex: "#1C2822", className: "bg-raised text-parchment" },
  { name: "parchment", hex: "#ECE5D3", className: "bg-[#ECE5D3] text-[#1E1A16]" },
  { name: "brass", hex: "#C8A25B", className: "bg-brass text-night" },
  { name: "verdigris", hex: "#4F8A78", className: "bg-verdigris text-night" },
  { name: "ember", hex: "#C65D3B", className: "bg-ember text-parchment" },
  { name: "rule", hex: "#2B3A33", className: "bg-rule text-parchment" },
];

export function StyleguidePage() {
  const handleRetry = () => {
    window.alert("Simulation notice: In a production setup, this sends a retry request to the retrieval backend.");
  };

  return (
    <main className="mx-auto max-w-5xl space-y-10 px-4 py-8 sm:px-6 sm:py-10">
      <header className="space-y-2 border-b border-rule pb-4">
        <SmallCaps>Design System &amp; Components</SmallCaps>
        <h1 className="mt-1 font-serif text-3xl font-medium text-parchment sm:text-4xl">
          Style Guide &amp; Response States
        </h1>
        <p className="text-xs sm:text-sm text-muted">
          Design tokens, button components, and clear AI response feedback states.
        </p>
      </header>

      <section className="space-y-3">
        <SmallCaps>01 · Color Palette Tokens</SmallCaps>
        <div className="grid grid-cols-2 gap-3 font-mono text-[11px] sm:grid-cols-4 md:grid-cols-8">
          {COLORS.map((color) => (
            <div
              key={color.name}
              className={`rounded border border-rule p-3 ${color.className}`}
            >
              <div className="font-bold">{color.hex}</div>
              <div className="mt-1 text-[10px] opacity-80 capitalize">{color.name}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <SmallCaps>02 · Button Variants</SmallCaps>
        <div className="flex flex-wrap items-center gap-3 rounded-lg border border-rule bg-surface p-5">
          <Button variant="primary">Primary Action</Button>
          <Button variant="secondary">Secondary Action</Button>
          <Button variant="raised">Raised Surface</Button>
          <Button variant="ghost">Ghost Button</Button>
          <Button variant="primary" disabled>
            Disabled State
          </Button>
        </div>
      </section>

      <section className="space-y-6">
        <SmallCaps>03 · Three Explicit AI Response States</SmallCaps>

        <article className="space-y-2">
          <div className="font-sans text-xs font-semibold text-brass">
            State 1: No Direct Answer Found (found = false)
          </div>
          <div className="space-y-2 rounded-lg border border-rule bg-surface p-5">
            <h2 className="font-sans text-base font-semibold text-parchment">
              No direct answer found in this document.
            </h2>
            <p className="text-xs text-muted">
              Try rephrasing your question, or inspect the closest passages identified in the document:
            </p>
            <div className="rounded border border-rule bg-night p-3 font-serif text-xs italic text-muted">
              “Preliminary assumptions regarding environmental constraints were omitted from Section 2.” (Page 3 · Match 0.24)
            </div>
          </div>
        </article>

        <article className="space-y-2">
          <div className="font-sans text-xs font-semibold text-brass">
            State 2: Low Confidence Warning
          </div>
          <div className="space-y-2 rounded-lg border-y border-r border-rule border-l-4 border-l-brass bg-surface p-5">
            <div className="flex items-center gap-2 text-xs font-medium text-brass">
              <span className="font-bold text-sm">⚠</span>
              <span>Low confidence match. Please verify against cited sources.</span>
            </div>
            <p className="font-sans text-sm leading-relaxed text-parchment/90">
              The text references approximate compute requirements across cluster nodes, noting roughly 340 TPU-v4 days, though exact electricity metrics and host billings were omitted from the primary appendices.
            </p>
          </div>
        </article>

        <article className="space-y-2">
          <div className="font-sans text-xs font-semibold text-ember">
            State 3: Retrieval or Connection Error
          </div>
          <div className="flex flex-col justify-between gap-4 rounded-lg border border-ember/60 bg-surface p-4 sm:flex-row sm:items-center">
            <div>
              <h2 className="font-sans text-sm font-semibold text-ember">
                Unable to complete search request.
              </h2>
              <p className="mt-1 text-xs text-muted">
                Connection timed out while querying document chunk 18-04.
              </p>
            </div>
            <Button variant="secondary" size="sm" onClick={handleRetry}>
              Retry Query
            </Button>
          </div>
        </article>
      </section>
    </main>
  );
}
