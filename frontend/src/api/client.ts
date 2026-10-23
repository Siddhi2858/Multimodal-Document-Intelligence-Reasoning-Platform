/**
 * api/client.ts
 * -------------
 * All calls to the FastAPI backend live here, so pages never use fetch directly.
 *
 * The backend address comes from VITE_API_URL (frontend/.env) and defaults to
 * http://localhost:8000/api for local development.
 */

import type { DocumentRecord } from "../types/document";
import type { PastQuery } from "./../types/history";
import type { QuestionResponse } from "../types/qa";

const API_BASE: string =
  (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000/api";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/** Fetch JSON from the backend and turn failures into readable ApiErrors. */
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE}${path}`, init);
  } catch {
    throw new ApiError(
      0,
      "Cannot reach the backend. Check that the server is running on port 8000.",
    );
  }

  if (!response.ok) {
    let message = response.statusText || "Request failed";

    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") {
        message = body.detail;
      }
    } catch {
      // The error response had no JSON body; keep the status text.
    }

    throw new ApiError(response.status, message);
  }

  return (await response.json()) as T;
}

/** GET /api/documents */
export function getDocuments(): Promise<DocumentRecord[]> {
  return request<DocumentRecord[]>("/documents");
}

/** GET /api/documents/{id} */
export function getDocument(documentId: string): Promise<DocumentRecord> {
  return request<DocumentRecord>(`/documents/${encodeURIComponent(documentId)}`);
}

/** POST /api/documents/upload — returns the new record with status "processing". */
export function uploadPdf(file: File): Promise<DocumentRecord> {
  const form = new FormData();
  form.append("file", file);

  // No Content-Type header: the browser adds the multipart boundary itself.
  return request<DocumentRecord>("/documents/upload", { method: "POST", body: form });
}

/** POST /api/documents/{id}/ask — retrieve passages and generate a cited answer. */
export function askQuestion(documentId: string, question: string): Promise<QuestionResponse> {
  return request<QuestionResponse>(`/documents/${encodeURIComponent(documentId)}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
}

/** GET /api/history — saved questions, newest first. */
export function getHistory(): Promise<PastQuery[]> {
  return request<PastQuery[]>("/history");
}