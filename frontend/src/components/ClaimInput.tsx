import React, { useRef, useState, useMemo } from "react";
import { ArrowRight, Loader2, X, Plus } from "lucide-react";

interface ClaimInputProps {
  claim: string;
  setClaim: (claim: string) => void;
  selectedImage: File | null;
  setSelectedImage: (file: File | null) => void;
  onAnalyze: (claimText: string, imageFile?: File | null) => void;
  isLoading: boolean;
}

const PRESET_CLAIMS = [
  "India banned UPI in 2025",
  "RBI banned 500 rupee notes in 2025",
  "ISRO landed Chandrayaan-3 near lunar south pole",
  "This herbal medicine cures cancer",
];

export const ClaimInput: React.FC<ClaimInputProps> = ({
  claim,
  setClaim,
  selectedImage,
  setSelectedImage,
  onAnalyze,
  isLoading,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  // Generate temporary object URL for preview
  const imagePreviewUrl = useMemo(() => {
    if (!selectedImage) return null;
    return URL.createObjectURL(selectedImage);
  }, [selectedImage]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.type.startsWith("image/")) {
        setSelectedImage(file);
      }
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type.startsWith("image/")) {
        setSelectedImage(file);
      }
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  // Support pasting screenshots directly from clipboard (Ctrl+V)
  const handlePaste = (e: React.ClipboardEvent) => {
    if (e.clipboardData && e.clipboardData.items) {
      for (let i = 0; i < e.clipboardData.items.length; i++) {
        const item = e.clipboardData.items[i];
        if (item.type.indexOf("image") !== -1) {
          const file = item.getAsFile();
          if (file) {
            e.preventDefault();
            setSelectedImage(file);
            return;
          }
        }
      }
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoading) return;
    if (selectedImage || claim.trim()) {
      onAnalyze(claim.trim(), selectedImage);
    } else {
      const textarea = document.querySelector(".claim-textarea") as HTMLTextAreaElement;
      textarea?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (isLoading) return;
      if (selectedImage || claim.trim()) {
        onAnalyze(claim.trim(), selectedImage);
      }
    }
  };

  const selectPreset = (preset: string) => {
    setSelectedImage(null);
    setClaim(preset);
    onAnalyze(preset, null);
  };

  const removeImage = () => {
    setSelectedImage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div
      className={`claim-card ${isDragging ? "drag-active" : ""}`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onPaste={handlePaste}
    >
      <form onSubmit={handleSubmit}>
        {/* Hidden file input */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept="image/*"
          style={{ display: "none" }}
        />

        {/* Selected Image Preview Chip */}
        {selectedImage && imagePreviewUrl && (
          <div className="image-upload-preview">
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", minWidth: 0 }}>
              <img
                src={imagePreviewUrl}
                alt="Selected claim"
                className="image-preview-thumb"
              />
              <div className="image-preview-info">
                <span className="image-preview-name">{selectedImage.name}</span>
                <span className="image-preview-size">
                  {formatFileSize(selectedImage.size)} • Screenshot / Image
                </span>
              </div>
            </div>
            <button
              type="button"
              className="image-remove-btn"
              onClick={removeImage}
              title="Remove image"
            >
              <X size={16} />
            </button>
          </div>
        )}

        <div className="input-container">
          <button
            type="button"
            className="input-plus-btn"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            title="Upload image from system (+)"
            aria-label="Upload image from system"
          >
            <Plus size={20} strokeWidth={2.4} />
          </button>
          <textarea
            className="claim-textarea"
            rows={3}
            placeholder={
              selectedImage
                ? "Optional: Ask a specific question about this image, or leave blank to verify its text..."
                : "Paste a claim, URL, or image (drag & drop / Ctrl+V screenshot)..."
            }
            value={claim}
            onChange={(e) => setClaim(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
          />
        </div>

        <div className="action-row">
          <div className="quick-claims">
            <span className="quick-label">Try an example:</span>
            {PRESET_CLAIMS.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                className="chip-btn"
                onClick={() => selectPreset(preset)}
                disabled={isLoading}
              >
                "{preset}"
              </button>
            ))}
          </div>

          <button
            type="submit"
            className="submit-btn"
            disabled={isLoading || (!claim.trim() && !selectedImage)}
          >
            {isLoading ? (
              <>
                <Loader2 size={18} className="spin" />
                Analyzing Evidence...
              </>
            ) : (
              <>
                <ArrowRight size={18} strokeWidth={2.5} />
                {selectedImage ? "Analyze Image" : "Analyze Claim"}
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
