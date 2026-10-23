
import { useState } from "react";
import type { MockPage } from "../../data/mockPages";
import { MOCK_PAGES } from "../../data/mockPages";
import SmallCaps from "../ui/SmallCaps";

interface ForeEdgeStackProps {
  pages?: MockPage[];
  activePageNumber?: number;
  onSelectPage?: (pageNumber: number) => void;
}

const colorMap: Record<MockPage["page_type"], string> = {
  text_heavy: "#9AA39A",
  table: "#C8A25B",
  figure: "#4F8A78",
  mixed: "#C65D3B",
};

export default function ForeEdgeStack({
  pages = MOCK_PAGES,
  activePageNumber,
  onSelectPage,
}: ForeEdgeStackProps) {
  const [hoveredPage, setHoveredPage] = useState<MockPage | null>(null);
  const activePage = hoveredPage ?? pages.find((p) => p.page_number === activePageNumber) ?? null;

  return (
    <div className="relative bg-surface rounded-lg border border-rule p-4 sm:p-5 space-y-4">
      <div className="flex items-center justify-between pb-2.5 border-b border-rule">
        <div>
          <SmallCaps>Page Preview &amp; Layout</SmallCaps>
          <div className="text-xs text-muted mt-0.5">Interactive document pages overview</div>
        </div>
        <span className="font-mono text-xs text-brass font-medium px-2 py-0.5 rounded bg-surface border border-rule">
          {pages.length} pages
        </span>
      </div>

      <div className="py-2 px-1.5 bg-night rounded border border-rule max-h-[300px] overflow-y-auto">
        <div className="flex flex-col space-y-1">
          {pages.map((p) => {
            const isHovered = hoveredPage?.page_number === p.page_number;
            const isSelected = activePageNumber === p.page_number;
            const tabColor = colorMap[p.page_type] || "#9AA39A";

            return (
              <button
                type="button"
                key={p.page_number}
                onMouseEnter={() => setHoveredPage(p)}
                onMouseLeave={() => setHoveredPage(null)}
                onClick={() => onSelectPage?.(p.page_number)}
                className={`group relative flex items-center h-7 rounded px-1.5 cursor-pointer transition-all duration-150 text-left w-full ${
                  isSelected
                    ? "bg-raised border border-brass/80 text-parchment"
                    : isHovered
                      ? "bg-raised/70 border border-rule/80 text-parchment"
                      : "bg-surface/60 border border-transparent hover:bg-raised/50 text-muted"
                }`}
              >
                <div
                  className="w-2.5 h-3.5 rounded-xs shrink-0 mr-2.5"
                  style={{ backgroundColor: tabColor }}
                  title={`${p.page_type}: page ${p.page_number}`}
                />

                <div className="flex-1 flex items-center justify-between font-sans text-xs">
                  <span className={`font-mono text-[11px] ${isSelected ? "text-brass font-bold" : "group-hover:text-parchment"}`}>
                    Page {String(p.page_number).padStart(2, "0")}
                  </span>

                  <div className="flex items-center gap-1.5 font-mono text-[10px]">
                    <span className="capitalize text-muted/80">
                      {p.page_type.replace("_", " ")}
                    </span>
                    {p.used_ocr && (
                      <span className="text-ember border border-ember/40 rounded px-1 text-[9px] font-semibold">
                        OCR
                      </span>
                    )}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      <div className="rounded p-3 bg-night border border-rule text-xs space-y-2">
        {activePage ? (
          <>
            <div className="flex justify-between items-center text-parchment border-b border-rule pb-1.5">
              <span className="font-medium">
                Page {activePage.page_number} Content Breakdown
              </span>

              <span className="text-brass uppercase font-mono text-[11px] font-semibold">
                {activePage.page_type.replace("_", " ")}
              </span>
            </div>

            <div className="grid grid-cols-4 gap-2 pt-1 font-mono text-[11px]">
              <div className="bg-surface/80 p-1.5 rounded border border-rule text-center">
                <span className="text-muted block text-[10px]">Text</span>
                <span className="text-parchment font-semibold">
                  {Math.round(activePage.probabilities.text_heavy * 100)}%
                </span>
              </div>

              <div className="bg-surface/80 p-1.5 rounded border border-rule text-center">
                <span className="text-muted block text-[10px]">Tables</span>
                <span className="text-brass font-semibold">
                  {Math.round(activePage.probabilities.table * 100)}%
                </span>
              </div>

              <div className="bg-surface/80 p-1.5 rounded border border-rule text-center">
                <span className="text-muted block text-[10px]">Figures</span>
                <span className="text-verdigris font-semibold">
                  {Math.round(activePage.probabilities.figure * 100)}%
                </span>
              </div>

              <div className="bg-surface/80 p-1.5 rounded border border-rule text-center">
                <span className="text-muted block text-[10px]">Mixed</span>
                <span className="text-ember font-semibold">
                  {Math.round(activePage.probabilities.mixed * 100)}%
                </span>
              </div>
            </div>
          </>
        ) : (
          <div className="text-muted text-center py-1">
            Hover or click any page above to inspect its layout breakdown.
          </div>
        )}
      </div>
    </div>
  );
}
