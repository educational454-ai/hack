import React from "react";
import {
  ExternalLink,
  BookOpen,
  AlertTriangle,
  XCircle,
  CheckCircle2,
  HelpCircle,
  Image as ImageIcon,
} from "lucide-react";
import {
  AnalysisResult,
  EvidenceItem,
  RelevantImage,
} from "../types";

interface ResultCardProps {
  result: AnalysisResult;
}

export const ResultCard: React.FC<ResultCardProps> = ({ result }) => {
  const isSubjective = result.claim_type === "subjective_opinion";

  // Combine top evidence: 3 cards per row, maximum 2 rows = max 6 cards
  const summaryEvidence: EvidenceItem[] = [
    ...result.contradicting_evidence,
    ...result.supporting_evidence,
  ].slice(0, 6);

  return (
    <div className="result-container">
      {/* 1. Verdict Banner */}
      <div className={`verdict-banner ${result.verdict}`}>
        <div className="verdict-left">
          <span className="verdict-emoji">{result.verdict_symbol}</span>
          <div>
            <span className="verdict-label">Assessment</span>
            <h2 className="verdict-title">{result.verdict_title}</h2>
          </div>
        </div>

        <div className="verdict-meta">
          <span
            className="meta-pill"
            title="Internal model verification confidence score (not a probability of truth)"
          >
            Verification Confidence: {Math.round(result.confidence_score * 100)}%
          </span>
          {result.latency_seconds && (
            <span className="meta-pill">{result.latency_seconds}s</span>
          )}
        </div>
      </div>

      {/* 2. Why? Evidence Synthesis */}
      <div className="explanation-card">
        <h3 className="card-heading">
          <BookOpen size={19} className="heading-icon" />
          Why? Evidence Synthesis
        </h3>
        <p className="explanation-text">{result.explanation}</p>
      </div>

      {/* 3. Visual Evidence Section */}
      <VisualEvidenceSection images={result.relevant_images || []} />

      {/* 4. Summary Evidence Cards */}
      {!isSubjective && summaryEvidence.length > 0 && (
        <div className="card-section">
          <h3 className="card-heading">
            <CheckCircle2 size={19} className="heading-icon" />
            Evidence Summary ({summaryEvidence.length} items)
          </h3>
          <div className="evidence-summary-grid">
            {summaryEvidence.map((ev, idx) => (
              <SummaryEvidenceCard key={idx} item={ev} />
            ))}
          </div>
        </div>
      )}

      {/* 5. Evidence Limitations */}
      {result.evidence_limitations && result.evidence_limitations.length > 0 && (
        <div className="card-section">
          <h3 className="card-heading">
            <AlertTriangle size={18} className="warning-icon" />
            Evidence Limitations & Caveats
          </h3>
          <ul className="limitations-list">
            {result.evidence_limitations.map((lim, idx) => (
              <li key={idx}>{lim}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

/* --- Visual Evidence Section --- */
export const VisualEvidenceSection: React.FC<{ images: RelevantImage[] }> = ({ images }) => {
  const [failedIndices, setFailedIndices] = React.useState<Record<number, boolean>>({});

  if (!images || images.length === 0) return null;

  // Filter valid candidate images (have thumbnail/image URL and haven't failed loading)
  const candidateImages = images.filter(
    (img, idx) => !failedIndices[idx] && img && (img.image_url || img.thumbnail_url)
  );

  if (candidateImages.length === 0) return null;

  // Render max 2 images
  const displayImages = candidateImages.slice(0, 2);

  return (
    <div className="card-section visual-evidence-section">
      <div className="visual-evidence-header">
        <h3 className="card-heading">
          <ImageIcon size={19} className="heading-icon" />
          Visual Evidence
        </h3>
        <p className="visual-evidence-disclaimer">
          Visual context from retrieved web sources — images are not used as standalone proof.
        </p>
      </div>

      <div className="visual-evidence-grid">
        {displayImages.map((img, displayIdx) => {
          const originalIdx = images.indexOf(img);
          const sourceDomain = img.domain || extractDomainSimple(img.source_url);
          const hasRelevance =
            typeof img.relevance_score === "number" &&
            !isNaN(img.relevance_score) &&
            img.relevance_score > 0;

          return (
            <div key={displayIdx} className="visual-evidence-card">
              <div className="visual-evidence-thumb-container">
                <img
                  src={img.thumbnail_url || img.image_url}
                  alt={img.title || "Retrieved visual evidence"}
                  className="visual-evidence-img"
                  onError={() => {
                    const idxToMark = originalIdx >= 0 ? originalIdx : displayIdx;
                    setFailedIndices((prev) => ({ ...prev, [idxToMark]: true }));
                  }}
                />
              </div>

              <div className="visual-evidence-body">
                <h4 className="visual-evidence-title" title={img.title}>
                  {img.title || "Retrieved Visual Evidence"}
                </h4>

                <div className="visual-evidence-meta">
                  {sourceDomain && (
                    <span className="visual-evidence-domain" title={sourceDomain}>
                      {sourceDomain}
                    </span>
                  )}
                  {hasRelevance && (
                    <span className="visual-evidence-relevance">
                      Image relevance: {Math.round((img.relevance_score as number) * 100)}%
                    </span>
                  )}
                </div>

                {img.source_url ? (
                  <a
                    href={img.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="visual-evidence-link"
                    title="Open official web source page"
                  >
                    View source <ExternalLink size={12} />
                  </a>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

function extractDomainSimple(url: string): string {
  if (!url) return "";
  try {
    const urlStr = url.startsWith("http") ? url : `http://${url}`;
    const parsed = new URL(urlStr);
    let host = parsed.hostname.toLowerCase();
    if (host.startsWith("www.")) host = host.slice(4);
    return host;
  } catch {
    return "";
  }
}

/* --- Summary Evidence Card --- */
const SummaryEvidenceCard: React.FC<{ item: EvidenceItem }> = ({ item }) => {
  const stance = item.stance || "neutral";
  const isContradicting = stance === "contradicts";
  const isSupporting = stance === "supports";

  const tierLabelMap: Record<string, string> = {
    primary: "Primary Source",
    secondary: "Secondary Source",
    low_confidence: "Lower Confidence Source",
  };
  const tierDisplay = tierLabelMap[item.source_tier] || item.source_tier;

  return (
    <div className="summary-ev-card">
      <div className="summary-ev-header">
        <span
          className={`stance-tag ${
            isContradicting ? "contradicts" : isSupporting ? "supports" : "neutral"
          }`}
        >
          {isContradicting ? (
            <>
              <XCircle size={12} /> Contradicts
            </>
          ) : isSupporting ? (
            <>
              <CheckCircle2 size={12} /> Supports
            </>
          ) : (
            <>
              <HelpCircle size={12} /> Neutral Context
            </>
          )}
        </span>
        <span
          className="relevance-tag"
          title="BGE-M3 semantic relevance similarity match against claim text"
        >
          {Math.round(item.similarity_score * 100)}% Relevance
        </span>
      </div>

      <p className="summary-ev-snippet">
        "{item.passage.slice(0, 115).trim()}..."
      </p>

      <div className="summary-ev-footer">
        <span className="summary-domain" title={tierDisplay}>
          {item.domain}
        </span>
        {item.url ? (
          <a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="details-toggle-btn"
            title="Open official source article"
          >
            View details <ExternalLink size={12} />
          </a>
        ) : (
          <span className="details-toggle-btn disabled">
            No URL
          </span>
        )}
      </div>
    </div>
  );
};
