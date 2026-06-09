import { describe, expect, it } from "vitest";

import { MAX_UPLOAD_MB, validateUpload } from "@/lib/upload";

describe("validateUpload", () => {
  it("accepts supported document types", () => {
    expect(validateUpload({ name: "trial.txt", size: 1000 })).toBeNull();
    expect(validateUpload({ name: "drug.pdf", size: 1000 })).toBeNull();
    expect(validateUpload({ name: "guideline.md", size: 1000 })).toBeNull();
  });

  it("rejects unsupported extensions", () => {
    expect(validateUpload({ name: "malware.exe", size: 10 })).toMatch(/unsupported/i);
    expect(validateUpload({ name: "sheet.csv", size: 10 })).toMatch(/unsupported/i);
  });

  it("rejects oversized files", () => {
    expect(validateUpload({ name: "big.pdf", size: (MAX_UPLOAD_MB + 1) * 1024 * 1024 })).toMatch(
      /too large/i,
    );
  });
});
