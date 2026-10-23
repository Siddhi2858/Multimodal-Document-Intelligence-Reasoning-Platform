import  Button  from "../components/ui/Button";
import  SmallCaps  from "../components/ui/SmallCaps";
import  ThreadDemo  from "../components/citations/ThreadDemo";
import  ForeEdgeStack  from "../components/document/ForeEdgeStack";

interface LandingPageProps {
  onOpenSpecimen: () => void;
  onNavigateDesk: () => void;
}

export function LandingPage({
  onOpenSpecimen,
  onNavigateDesk,
}: LandingPageProps) {
  return (
    <main className="mx-auto max-w-6xl space-y-20 px-4 py-10 sm:px-8 sm:py-16">
      <section className="space-y-6">
        <div className="flex items-center gap-2.5">
          <span className="h-2 w-2 bg-brass" />
          <SmallCaps>
            Nocturnal Reading Room for Dense Documents
          </SmallCaps>
        </div>

        <h1 className="max-w-4xl font-serif text-4xl font-normal leading-tight tracking-tight text-parchment sm:text-6xl">
          Ask the document.
          <br />
          <span className="font-light italic text-brass">
            See the exact folios it came from.
          </span>
        </h1>

        <p className="max-w-2xl text-base leading-relaxed text-muted sm:text-lg">
          Upload a 100-page PDF, ask in your natural language, and every
          answer arrives with a physical brass thread drawn directly to
          numbered pages, tabular registers, and scanned plates.
        </p>

        <div className="flex flex-wrap items-center gap-4 pt-2">
          <Button variant="primary" size="lg" onClick={onOpenSpecimen}>
            Inspect Monograph Paper (20 pp.)
          </Button>
          <Button variant="secondary" size="lg" onClick={onNavigateDesk}>
            Enter Private Desk
          </Button>
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between gap-4 border-b border-rule pb-2">
          <SmallCaps>Primary Interaction Model</SmallCaps>
          <span className="font-mono text-xs text-muted">
            Direct Typographic Proof
          </span>
        </div>
        <ThreadDemo />
      </section>

      <section className="grid grid-cols-1 items-start gap-8 lg:grid-cols-12">
        <div className="space-y-4 lg:col-span-5">
          <div className="border-b border-rule pb-2">
            <SmallCaps>Physical Metaphor</SmallCaps>
            <h2 className="mt-1 font-serif text-2xl font-medium text-parchment">
              The Fore-Edge
            </h2>
          </div>

          <p className="text-sm leading-relaxed text-muted">
            Just as an archivist glances across the fore-edge of a bound
            codex to see coloured thumb-tabs and paper density, Folio maps
            pages into an interactive physical spine. Hover over a leaf to
            reveal its layout before asking a question.
          </p>

          <div className="space-y-2 border border-rule bg-surface p-4 font-mono text-xs">
            <div className="font-semibold text-parchment">
              Classification Color Palette
            </div>
            <div className="grid grid-cols-2 gap-3 pt-1 text-muted">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 bg-type-text" />
                Text Heavy
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 bg-type-table" />
                Tabular Data
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 bg-type-figure" />
                Figure Plate
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 bg-type-mixed" />
                Mixed Layout
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-7">
          <ForeEdgeStack />
        </div>
      </section>

      <section className="space-y-6">
        <div className="border-b border-rule pb-2">
          <SmallCaps>Epistemological Contrast</SmallCaps>
          <h2 className="mt-1 font-serif text-3xl font-normal text-parchment">
            Literal Keyword Search vs Folio Reading
          </h2>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <article className="space-y-3 border border-rule bg-surface p-6">
            <div className="flex items-center justify-between gap-3 font-mono text-xs text-ember">
              <span>TRADITIONAL PDF CMD+F</span>
              <span>0 MATCHES FOUND</span>
            </div>
            <h3 className="font-serif text-xl text-parchment">
              “Compute cost TPU cluster”
            </h3>
            <p className="text-xs leading-relaxed text-muted">
              A literal search may fail when the publication uses different
              wording, such as:
              <span className="font-mono text-muted/80">
                {" "}“Hardware configurations were calibrated against standard
                distributed ML benchmarks across 340 TPU-v4 node-days.”
              </span>
            </p>
            <div className="border-t border-rule pt-2 font-mono text-[11px] text-muted/60">
              Outcome: the reader may assume the information is missing.
            </div>
          </article>

          <article className="space-y-3 border border-brass/50 bg-raised p-6">
            <div className="flex items-center justify-between gap-3 font-mono text-xs text-brass">
              <span>FOLIO SYNTACTIC DESK</span>
              <span>CONFIDENCE 0.86</span>
            </div>
            <h3 className="font-serif text-xl text-parchment">
              Natural inquiry finds a semantic passage
            </h3>
            <p className="font-serif text-sm italic leading-relaxed text-parchment/90">
              “Hardware configurations were calibrated against standard
              distributed ML benchmarks over a three-week window (340
              TPU-v4 days) without published financial ledger figures.”
            </p>
            <div className="flex justify-between gap-3 border-t border-rule pt-2 font-mono text-[11px] text-brass">
              <span>Cited Folios: p. 2, p. 17</span>
              <span>Chunk tagged</span>
            </div>
          </article>
        </div>
      </section>

      <section className="space-y-6 border border-rule bg-surface p-6 sm:p-8">
        <div className="border-b border-rule pb-3">
          <SmallCaps>Editorial Integrity Charter</SmallCaps>
          <h2 className="mt-1 font-serif text-2xl font-medium text-parchment sm:text-3xl">
            What Folio Will Not Pretend to Do
          </h2>
        </div>

        <div className="grid grid-cols-1 gap-6 text-xs text-muted md:grid-cols-3">
          <article className="space-y-2 border-l border-rule pl-4">
            <h3 className="font-mono text-sm font-bold text-brass">
              § 01 · No Hallucinated Answers
            </h3>
            <p>
              If the document does not contain the answer, Folio explicitly
              states that the document does not seem to say. It should not
              invent evidence.
            </p>
          </article>

          <article className="space-y-2 border-l border-rule pl-4">
            <h3 className="font-mono text-sm font-bold text-verdigris">
              § 02 · No Chat Bubble Persona
            </h3>
            <p>
              Queries return typographical prose formatted as monograph
              marginalia rather than a conventional chatbot conversation.
            </p>
          </article>

          <article className="space-y-2 border-l border-rule pl-4">
            <h3 className="font-mono text-sm font-bold text-ember">
              § 03 · Scanned Plates Never Concealed
            </h3>
            <p>
              Pages requiring OCR remain visibly marked with OCR tags and
              processing information.
            </p>
          </article>
        </div>
      </section>

      <footer className="flex flex-col items-center justify-between gap-4 border-t border-rule pt-8 font-mono text-xs text-muted sm:flex-row">
        <span>FOLIO PRIVATA · SPECIFICATION EDITION N° 102</span>
        <div className="flex gap-6">
          <button onClick={onOpenSpecimen} className="hover:text-brass">
            Specimen Paper
          </button>
          <button onClick={onNavigateDesk} className="hover:text-brass">
            Private Desk
          </button>
        </div>
      </footer>
    </main>
  );
}
