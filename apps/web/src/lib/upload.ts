export const ACCEPTED_EXT = [".txt", ".md", ".markdown", ".pdf"];
export const MAX_UPLOAD_MB = 10;

/** Validate a candidate upload; returns an error message, or null if acceptable. */
export function validateUpload(file: { name: string; size: number }): string | null {
  const ext = `.${(file.name.split(".").pop() ?? "").toLowerCase()}`;
  if (!ACCEPTED_EXT.includes(ext)) {
    return `Unsupported file type. Use ${ACCEPTED_EXT.join(", ")}.`;
  }
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
    return `File is too large (max ${MAX_UPLOAD_MB} MB).`;
  }
  return null;
}
