/** One cited passage returned by POST /api/documents/{id}/ask */
export interface QuestionSource {
  page_number: number;
  chunk_id: string;
  snippet: string;
  /** The complete retrieved passage (the snippet is a short preview of it). */
  text: string;
  score: number;
  top_offset: number;
}

/** Response of POST /api/documents/{id}/ask */
export interface QuestionResponse {
  found: boolean;
  answer: string;
  sources: QuestionSource[];
}