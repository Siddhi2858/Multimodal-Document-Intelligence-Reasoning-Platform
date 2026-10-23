
import type { DocumentRecord } from "../types/document";

export const MOCK_CATALOGUE: DocumentRecord[] = [
  {
    document_id: "doc-1",
    filename: "Attention_in_Convolutional_Layout_Models.pdf",
    title: "Attention in Convolutional Layout Models",
    page_count: 20,
    processing_status: "ready",
    created_at: "14 Oct 2024 · 09:22",
    classification: "Research Paper · Computer Vision",
  },
  {
    document_id: "doc-2",
    filename: "Manuale_Tipografico_Bodoni_1788.pdf",
    title: "Manuale Tipografico: Typography Sample Pages",
    page_count: 48,
    processing_status: "ready",
    created_at: "03 Oct 2024 · 16:40",
    classification: "Historical Book · Typography",
  },
  {
    document_id: "doc-3",
    filename: "Demographic_Indices_Stratified_Census_1940.pdf",
    title: "Demographic Indices & Stratified Census Report",
    page_count: 92,
    processing_status: "ready",
    created_at: "28 Sep 2024 · 11:15",
    classification: "Statistical Report & Census",
  },
  {
    document_id: "doc-4",
    filename: "Aldine_Press_Venetiis_1494.pdf",
    title: "Aldine Press Historical Printing Ledger",
    page_count: 14,
    processing_status: "processing",
    created_at: "Just now",
    classification: "Scanned Manuscript Archive",
  },
];
