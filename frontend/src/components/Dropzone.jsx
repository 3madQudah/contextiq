import { UploadCloud } from "lucide-react";
import { useState } from "react";

import { ACCEPTED_EXTENSIONS } from "../lib/fileTypes.js";

export default function Dropzone({ inputRef, onFiles, disabled }) {
  const [isDragging, setIsDragging] = useState(false);

  function handleFiles(fileList) {
    if (disabled || !fileList?.length) return;
    onFiles(Array.from(fileList));
  }

  return (
    <div
      role="button"
      tabIndex={0}
      aria-disabled={disabled}
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);
        handleFiles(e.dataTransfer.files);
      }}
      onClick={() => !disabled && inputRef.current?.click()}
      onKeyDown={(e) => {
        if ((e.key === "Enter" || e.key === " ") && !disabled) {
          e.preventDefault();
          inputRef.current?.click();
        }
      }}
      className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border border-dashed px-6 py-10 text-center transition-colors ${
        disabled
          ? "cursor-not-allowed border-border opacity-60"
          : isDragging
            ? "border-accent bg-accent/5"
            : "border-border hover:bg-surface-hover"
      }`}
    >
      <UploadCloud
        size={20}
        strokeWidth={1.5}
        className={isDragging ? "text-accent" : "text-muted"}
      />
      <p className="text-sm text-foreground">
        {isDragging ? "Drop to upload" : "Drag and drop a file, or click to browse"}
      </p>
      <p className="text-xs text-muted">{ACCEPTED_EXTENSIONS.join(", ")}</p>
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        accept={ACCEPTED_EXTENSIONS.join(",")}
        onChange={(e) => {
          handleFiles(e.target.files);
          e.target.value = "";
        }}
      />
    </div>
  );
}
