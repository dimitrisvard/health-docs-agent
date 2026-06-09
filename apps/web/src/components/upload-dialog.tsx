"use client";

import { FileText, UploadCloud } from "lucide-react";
import { type DragEvent, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { ingestDocument } from "@/lib/api";
import { ACCEPTED_EXT, MAX_UPLOAD_MB, validateUpload } from "@/lib/upload";
import { cn } from "@/lib/utils";

export function UploadDialog({
  open,
  onClose,
  onUploaded,
}: {
  open: boolean;
  onClose: () => void;
  onUploaded: () => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const choose = (f: File | undefined) => {
    if (!f) return;
    const err = validateUpload(f);
    setError(err);
    setFile(err ? null : f);
  };

  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragging(false);
    choose(e.dataTransfer.files[0]);
  };

  const reset = () => {
    setFile(null);
    setError(null);
    setDragging(false);
  };

  const close = () => {
    reset();
    onClose();
  };

  const upload = async () => {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      await ingestDocument(file);
      onUploaded();
      reset();
      onClose();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={close}
      title="Upload a document"
      description="Add a public, non-PII health document to the corpus."
    >
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "flex cursor-pointer flex-col items-center gap-2 rounded-lg border-2 border-dashed px-4 py-8 text-center transition-colors",
          dragging ? "border-primary bg-accent" : "border-border hover:border-primary/40",
        )}
      >
        {file ? (
          <FileText className="size-6 text-primary" />
        ) : (
          <UploadCloud className="size-6 text-muted-foreground" />
        )}
        <p className="text-sm">{file ? file.name : "Drag a file here, or click to browse"}</p>
        <p className="text-xs text-muted-foreground">
          {ACCEPTED_EXT.join(", ")} · up to {MAX_UPLOAD_MB} MB
        </p>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXT.join(",")}
          className="hidden"
          onChange={(e) => choose(e.target.files?.[0])}
        />
      </div>

      {error && <p className="mt-3 text-sm text-destructive">{error}</p>}

      <div className="mt-5 flex justify-end gap-2">
        <Button variant="ghost" onClick={close} disabled={busy}>
          Cancel
        </Button>
        <Button onClick={upload} disabled={!file || busy}>
          {busy ? "Ingesting…" : "Upload & ingest"}
        </Button>
      </div>
    </Dialog>
  );
}
