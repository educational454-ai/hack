import React, { KeyboardEvent } from "react";
import { Search, Loader2 } from "lucide-react";

interface ClaimInputProps {
  claim: string;
  setClaim: (claim: string) => void;
  onAnalyze: (claimText: string) => void;
  isLoading: boolean;
}

const PRESET_CLAIMS = [
  "India banned UPI in 2025",
  "Modi is a protagonist",
  "Is India a state",
  "This herbal medicine cures cancer",
];

export const ClaimInput: React.FC<ClaimInputProps> = ({
  claim,
  setClaim,
  onAnalyze,
  isLoading,
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoading) return;
    if (claim.trim()) {
      onAnalyze(claim.trim());
    } else {
      const textarea = document.querySelector(".claim-textarea") as HTMLTextAreaElement;
      textarea?.focus();
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (isLoading) return;
      if (claim.trim()) {
        onAnalyze(claim.trim());
      }
    }
  };

  const selectPreset = (preset: string) => {
    setClaim(preset);
    onAnalyze(preset);
  };

  return (
    <div className="claim-card">
      <form onSubmit={handleSubmit}>
        <div className="input-container">
          <textarea
            className="claim-textarea"
            rows={3}
            placeholder="Enter information or URL..."
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
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 size={18} className="spin" />
                Analyzing Evidence...
              </>
            ) : (
              <>
                <Search size={18} />
                Analyze Claim
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
