
export interface MockSource {
  page_number: number;
  chunk_id: string;
  snippet: string;
  score: number;
  topOffset: number;
}

export interface MockQuestion {
  id: string;
  question: string;
  response: {
    found: boolean;
    answer: string;
    sources: MockSource[];
  };
}

export const MOCK_QUESTIONS: MockQuestion[] = [
  {
    id: "qa-1",
    question:
      "How does the cross-attention kernel isolate multi-column tabular delimiters?",
    response: {
      found: true,
      answer:
        "The model enforces an anisotropic spatial bias matrix aligned directly with detected white-space channels. Rather than treating visual layout as an isotropic patch grid, the horizontal projection matrices compress token affinity along the horizontal reading axis, forcing the attention distribution to saturate when crossing vertical boundary margins.",
      sources: [
        {
          page_number: 4,
          chunk_id: "chk-4-02",
          snippet:
            "“...horizontal projection matrices restrict spatial receptive fields, producing high boundary gradients at structural gutters.”",
          score: 0.88,
          topOffset: 120,
        },
        {
          page_number: 8,
          chunk_id: "chk-8-01",
          snippet:
            "“In tabular regimes (Table 2), cross-attention heads suppress cross-column bleed by 34.2% over isotropic ViT configurations.”",
          score: 0.81,
          topOffset: 240,
        },
      ],
    },
  },
  {
    id: "qa-2",
    question:
      "What were the empirical results on low-contrast scanned documents?",
    response: {
      found: true,
      answer:
        "When evaluated on scanned document test sets where pages 18 through 20 underwent optical character recognition (OCR), character error rates fell from 14.2% to 3.8% after applying layout-aware correction. Tabular structures preserved multi-column cells accurately.",
      sources: [
        {
          page_number: 18,
          chunk_id: "chk-18-04",
          snippet:
            "“OCR degradation benchmarks: table extraction F1 score increased to 0.912 when OCR bounding boxes were fused prior to attention projection.”",
          score: 0.79,
          topOffset: 160,
        },
        {
          page_number: 19,
          chunk_id: "chk-19-02",
          snippet:
            "“Appendix B: OCR confusion matrix and synthetic degradation parameters for scanned ledger facsimiles.”",
          score: 0.74,
          topOffset: 210,
        },
      ],
    },
  },
];
