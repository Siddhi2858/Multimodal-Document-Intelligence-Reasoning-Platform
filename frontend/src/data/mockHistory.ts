
export interface PastQuery {
  question: string;
  asked_at: string;
  pages: number[];
}

export const MOCK_PAST_QUERIES: PastQuery[] = [
  {
    question:
      "How does the cross-attention kernel isolate multi-column tabular delimiters?",
    asked_at: "Today · 10:14",
    pages: [4, 8],
  },
  {
    question:
      "What were the empirical results on low-contrast scanned documents?",
    asked_at: "Today · 10:18",
    pages: [18, 19],
  },
  {
    question:
      "What loss formulation weights multi-scale reading order?",
    asked_at: "Yesterday",
    pages: [6, 12],
  },
  {
    question:
      "Does the architecture support RTL or vertical CJK typography?",
    asked_at: "12 Oct",
    pages: [2],
  },
];
