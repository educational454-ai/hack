import React, { useRef, useState, useMemo, useEffect } from "react";
import { ArrowRight, Loader2, X, Plus, Mic } from "lucide-react";

// SpeechRecognition type declarations for browsers (WebKit & standard)
interface IWindow extends Window {
  SpeechRecognition?: any;
  webkitSpeechRecognition?: any;
}

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
  const [isListening, setIsListening] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(true);
  const recognitionRef = useRef<any>(null);
  const claimRef = useRef(claim);
  claimRef.current = claim;

  // Initialize Web Speech Recognition
  useEffect(() => {
    const win = window as unknown as IWindow;
    const SpeechRecognition = win.SpeechRecognition || win.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setVoiceSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-IN"; // Default to Indian English / English

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event: any) => {
      let finalTranscript = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        }
      }

      if (finalTranscript) {
        const current = claimRef.current;
        setClaim(current ? `${current.trim()} ${finalTranscript.trim()}` : finalTranscript.trim());
      }
    };

    recognition.onerror = (event: any) => {
      console.warn("Speech recognition error:", event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      try {
        recognition.abort();
      } catch {
        // cleanup safe
      }
    };
  }, [setClaim]);

  const toggleVoiceInput = () => {
    if (!voiceSupported) {
      alert("Voice search is not supported on this browser. Try Chrome, Edge, or Safari.");
      return;
    }

    if (isListening) {
      try {
        recognitionRef.current?.stop();
      } catch {
        setIsListening(false);
      }
    } else {
      try {
        recognitionRef.current?.start();
      } catch (err) {
        console.warn("Error starting speech recognition:", err);
      }
    }
  };

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

          <div className="input-textarea-wrapper">
            <textarea
              className={`claim-textarea ${isListening ? "listening-active" : ""}`}
              rows={3}
              placeholder={
                isListening
                  ? "🎙️ Listening... Speak your claim or query now..."
                  : selectedImage
                  ? "Optional: Ask a specific question about this image, or leave blank to verify its text..."
                  : "Paste a claim, URL, image, or speak your query..."
              }
              value={claim}
              onChange={(e) => setClaim(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
            />

            {/* Voice Search Mic Button inside textarea right-corner */}
            <button
              type="button"
              className={`voice-search-btn ${isListening ? "active" : ""}`}
              onClick={toggleVoiceInput}
              disabled={isLoading}
              title={isListening ? "Stop listening" : "Speak your claim (Voice Search)"}
              aria-label={isListening ? "Stop listening" : "Speak your claim"}
            >
              {isListening ? (
                <div className="voice-mic-pulsing">
                  <Mic size={19} className="pulse-icon" />
                </div>
              ) : (
                <Mic size={19} />
              )}
            </button>
          </div>
        </div>

        {isListening && (
          <div className="voice-listening-banner">
            <span className="voice-wave-dot dot1"></span>
            <span className="voice-wave-dot dot2"></span>
            <span className="voice-wave-dot dot3"></span>
            <span className="voice-status-text">Listening to your voice in English / Hindi... (Click mic to stop)</span>
          </div>
        )}

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
