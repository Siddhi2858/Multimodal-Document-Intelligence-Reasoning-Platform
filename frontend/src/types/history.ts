/** One saved question, as returned by GET /api/history */
export interface PastQuery {
  question: string;
  asked_at: string;
  pages: number[];
  /** The document the question was asked about ("" for very old entries). */
  document_id: string;
}