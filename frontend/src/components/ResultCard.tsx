import React, { useState } from "react";
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

function extractDomain(url: string): string {
  if (!url) return "Web Source";
  try {
    const parsed = new URL(url.startsWith("http") ? url : `http://${url}`);
    let host = parsed.hostname.toLowerCase();
    if (host.startsWith("www.")) host = host.slice(4);
    return host;
  } catch {
    return "Web Source";
  }
}

export const ResultCard: React.FC<ResultCardProps> = ({ result }) => {
  const isSubjective = result.claim_type === "subjective_opinion";

  // Combine top evidence: 3 cards per row, maximum 2 rows = max 6 cards
  const summaryEvidence: EvidenceItem[] = [
    ...result.contradicting_evidence,
    ...result.supporting_evidence,
  ].slice(0, 6);

  const images = result.relevant_images || [];

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

      {/* 3. Visual Evidence Section (Conditional) */}
      <VisualEvidenceSection images={images} />

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

/* --- Visual Evidence Section Component --- */
const VisualEvidenceSection: React.FC<{ images: RelevantImage[] }> = ({ images }) => {
  const [failedUrls, setFailedUrls] = useState<Record<string, boolean>>({});

  const handleImageError = (url: string) => {
    setFailedUrls((prev) => ({ ...prev, [url]: true }));
  };

  // Filter out invalid or failed images, limit to max 2
  const validImages = (images || [])
    .filter(
      (img) =>
        img &&
        (img.image_url || img.thumbnail_url) &&
        !failedUrls[img.image_url] &&
        !(img.thumbnail_url && failedUrls[img.thumbnail_url])
    )
    .slice(0, 2);

  if (validImages.length === 0) return null;

  return (
    <div className="card-section visual-evidence-section">
      <div className="visual-evidence-header">
        <h3 className="card-heading" style={{ marginBottom: "0.2rem" }}>
          <ImageIcon size={19} className="heading-icon" />
          Visual Evidence
        </h3>
        <p className="visual-evidence-disclaimer">
          Visual context from retrieved web sources — images are not used as standalone proof.
        </p>
      </div>

      <div className="visual-evidence-grid">
        {validImages.map((img, idx) => {
          const displayUrl = img.thumbnail_url || img.image_url;
          const targetUrl = img.source_url && img.source_url.trim() ? img.source_url.trim() : undefined;
          const domain = targetUrl ? extractDomain(targetUrl) : "";
          const altText = img.title || "Retrieved visual evidence";

          return (
            <div key={idx} className="visual-evidence-card">
              <div className="visual-img-wrapper">
                <img
                  src={displayUrl}
                  alt={altText}
                  onError={() => handleImageError(displayUrl)}
                  loading="lazy"
                />
              </div>
              <div className="visual-card-body">
                {img.title ? (
                  <h4 className="visual-card-title" title={img.title}>
                    {img.title}
                  </h4>
                ) : null}
                <div className="visual-card-footer">
                  {domain ? <span className="visual-domain">{domain}</span> : null}
                  {img.relevance_score != null ? (
                    <span className="visual-relevance">
                      Image relevance: {Math.round(img.relevance_score <= 1 ? img.relevance_score * 100 : img.relevance_score)}%
                    </span>
                  ) : null}
                  {targetUrl ? (
                    <a
                      href={targetUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="details-toggle-btn"
                      title="View original article source"
                      aria-label={domain ? `Open source article on ${domain}` : "Open source article"}
                    >
                      Source <ExternalLink size={12} />
                    </a>
                  ) : null}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

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



