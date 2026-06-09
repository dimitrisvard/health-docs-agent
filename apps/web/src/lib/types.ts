export type SourceKind = "trial" | "drug_label" | "guideline";

export interface Source {
  id: number;
  kind: SourceKind;
  title: string;
  source_uri: string | null;
}

/** A retrieved chunk surfaced as a citation / inspector row. */
export interface Citation {
  id: number;
  document_id: number | null;
  title: string | null;
  section: string | null;
  score: number | null;
  text: string | null;
}

export type ChatRole = "user" | "assistant";
export type MessageStatus = "streaming" | "done" | "error";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  citations?: Citation[];
  status?: MessageStatus;
}

export interface IngestResult {
  document_id: number;
  title: string;
  chunks: number;
}

export const KIND_LABEL: Record<SourceKind, string> = {
  trial: "Trial",
  drug_label: "Drug label",
  guideline: "Guideline",
};
