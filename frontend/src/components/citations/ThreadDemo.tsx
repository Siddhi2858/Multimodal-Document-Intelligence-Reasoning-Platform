
import { useState } from "react";
import SmallCaps from "../ui/SmallCaps";

interface CitationSpecimen {
  id: number;
  label: string;
  sourceText: string;
  page: number;
  chunk: string;
  score: number;
  plateExcerpt: string;
}

const citations: CitationSpecimen[] = [
  {
    id: 1,
    label: "Spatial Layout Analysis",
    sourceText:
      "Spatial projection matrices restrict token receptive fields along the reading axis.",
    page: 4,
    chunk: "chunk-4-02",
    score: 0.88,
    plateExcerpt:
      "“...horizontal projection matrices compress token affinity along reading axis, forcing the attention distribution to saturate when crossing vertical boundary margins.”",
  },
  {
    id: 2,
    label: "Tabular Boundary Detection",
    sourceText:
      "Cross-attention heads suppress cross-column bleed by 34.2% over standard vision models.",
    page: 8,
    chunk: "chunk-8-01",
    score: 0.81,
    plateExcerpt:
      "“In tabular regimes (Table 2), cross-attention heads suppress cross-column bleed by 34.2% over isotropic ViT configurations.”",
  },
];

export default function ThreadDemo() {
  const [activeCitationIdx, setActiveCitationIdx] = useState(0);
  const activeCit = citations[activeCitationIdx];

  return (
    <div className="relative bg-surface rounded-lg border border-rule p-5 sm:p-6 overflow-hidden space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-rule gap-2">
        <div>
          <SmallCaps>Interactive Citation Demo</SmallCaps>
          <h3 className="font-serif text-xl text-parchment font-medium mt-1">
            Source Citations: Linking Answers Directly to Pages
          </h3>
        </div>

        <div className="font-mono text-xs text-brass border border-brass/40 bg-brass/10 px-3 py-1 rounded self-start sm:self-auto font-medium">
          Page {activeCit.page} · {activeCit.chunk} · Match {(activeCit.score * 100).toFixed(0)}%
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
        <div className="md:col-span-6 space-y-3.5 leading-relaxed">
          <p className="text-sm text-parchment/90 border-l-2 border-brass/60 pl-3.5 py-0.5">
            Hover or select an excerpt to see how each sentence links to its exact passage on the source document page:
          </p>

          <div
            onMouseEnter={() => setActiveCitationIdx(0)}
            onClick={() => setActiveCitationIdx(0)}
            className={`p-3.5 rounded border cursor-pointer transition-all ${
              activeCitationIdx === 0
                ? "border-brass bg-raised text-parchment shadow-sm"
                : "border-rule bg-night/60 text-muted hover:text-parchment hover:border-rule/80"
            }`}
          >
            <div className="flex items-center justify-between mb-1 font-mono text-xs text-brass">
              <span className="font-sans font-medium">{citations[0].label}</span>
              <span className="font-bold">[1]</span>
            </div>

            <p className="text-sm font-sans italic text-parchment/90">
              "{citations[0].sourceText}"
            </p>
          </div>

          <div
            onMouseEnter={() => setActiveCitationIdx(1)}
            onClick={() => setActiveCitationIdx(1)}
            className={`p-3.5 rounded border cursor-pointer transition-all ${
              activeCitationIdx === 1
                ? "border-brass bg-raised text-parchment shadow-sm"
                : "border-rule bg-night/60 text-muted hover:text-parchment hover:border-rule/80"
            }`}
          >
            <div className="flex items-center justify-between mb-1 font-mono text-xs text-brass">
              <span className="font-sans font-medium">{citations[1].label}</span>
              <span className="font-bold">[2]</span>
            </div>

            <p className="text-sm font-sans italic text-parchment/90">
              "{citations[1].sourceText}"
            </p>
          </div>

          <p className="text-xs text-muted/80 pt-1">
            Tip: Citations provide instant traceability so users can verify factual claims without manual searching.
          </p>
        </div>

        <div className="md:col-span-6">
          <div className="w-full bg-[#ECE5D3] text-[#1E1A16] rounded border border-brass/60 p-5 font-serif text-xs leading-normal shadow-sm">
            <div className="flex justify-between items-center border-b border-[#1E1A16]/20 pb-2 mb-3 font-mono text-[10px] text-[#1E1A16]/70">
              <span className="font-sans font-semibold">DOCUMENT PREVIEW</span>
              <span className="font-bold">PAGE {String(activeCit.page).padStart(2, "0")}</span>
            </div>

            <div className="space-y-1.5 opacity-60">
              <div className="w-full h-1.5 bg-[#1E1A16]/25 rounded-xs" />
              <div className="w-5/6 h-1.5 bg-[#1E1A16]/25 rounded-xs" />
              <div className="w-full h-1.5 bg-[#1E1A16]/25 rounded-xs" />
            </div>

            <div className="my-3 p-3 bg-[#C8A25B]/20 border-l-2 border-[#C8A25B] text-[#1E1A16] rounded-xs">
              <div className="font-mono text-[10px] font-bold text-[#8E3B2F] tracking-wider uppercase mb-1">
                CITED PASSAGE [{activeCit.chunk}]
              </div>

              <p className="font-serif italic text-xs leading-relaxed font-medium">
                {activeCit.plateExcerpt}
              </p>
            </div>

            <div className="space-y-1.5 opacity-60">
              <div className="w-4/5 h-1.5 bg-[#1E1A16]/25 rounded-xs" />
              <div className="w-full h-1.5 bg-[#1E1A16]/25 rounded-xs" />
              <div className="w-3/4 h-1.5 bg-[#1E1A16]/25 rounded-xs" />
            </div>

            <div className="mt-4 pt-2 border-t border-[#1E1A16]/20 flex justify-between font-mono text-[10px] text-[#1E1A16]/60">
              <span>SOURCE CHUNK: {activeCit.chunk}</span>
              <span className="font-semibold text-[#8E3B2F]">
                CONFIDENCE: {(activeCit.score * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          <div className="mt-2 text-xs text-muted flex items-center justify-between px-1">
            <span>Direct Page Citation</span>
            <span className="text-brass font-mono font-medium">
              Score: {activeCit.score.toFixed(2)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
