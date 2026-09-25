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

  const uniqueDomains = Array.from(
    new Set(summaryEvidence.map((ev) => ev.domain).filter(Boolean))
  );
  const hasMultipleDomains = uniqueDomains.length > 1;
  const isSinglePublisher = summaryEvidence.length > 1 && uniqueDomains.length === 1;

  return (
    <div className="result-container">
      {/* Webpage Header for URL modes */}
      {result.webpage && (
        <div className="webpage-header-card">
          <div className="webpage-header-top">
            <span className="webpage-badge">Analyzed Webpage</span>
            <span className="webpage-domain">{result.webpage.domain}</span>
          </div>
          {result.webpage.title && (
            <h3 className="webpage-title">{result.webpage.title}</h3>
          )}
          <div className="webpage-meta-row">
            {result.webpage.url && (
              <a
                href={result.webpage.url}
                target="_blank"
                rel="noopener noreferrer"
                className="details-toggle-btn"
                aria-label="Open original webpage in new tab"
              >
                Visit Webpage <ExternalLink size={12} />
              </a>
            )}
            {result.webpage.publication_date && (
              <span className="webpage-date">Published: {result.webpage.publication_date}</span>
            )}
            {result.webpage.author && (
              <span className="webpage-author">Author: {result.webpage.author}</span>
            )}
          </div>
        </div>
      )}

      {/* User Question Banner for URL+Question mode */}
      {result.mode === "url_question" && result.user_question && (
        <div className="user-question-box">
          <span className="question-label">User Query:</span>
          <p className="question-text">"{result.user_question}"</p>
        </div>
      )}

      {/* 1. Verdict Banner */}
      <div className={`verdict-banner ${result.verdict}`}>
        <div className="verdict-left">
          <span className="verdict-emoji">{result.verdict_symbol}</span>
          <div>
            <span className="verdict-label">
              {result.mode === "url" ? "Article Assessment" : "Assessment"}
            </span>
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

      {/* 2. Targeted Answer for URL+Question mode */}
      {result.mode === "url_question" && result.targeted_answer && (
        <div className="card-section targeted-answer-card">
          <h3 className="card-heading">
            <HelpCircle size={19} className="heading-icon" />
            Targeted Answer
          </h3>
          <p className="targeted-answer-text">{result.targeted_answer}</p>
        </div>
      )}

      {/* 3. Why? Evidence Synthesis */}
      <div className="explanation-card">
        <h3 className="card-heading">
          <BookOpen size={19} className="heading-icon" />
          Why? Evidence Synthesis
        </h3>
        <p className="explanation-text">{result.explanation}</p>
      </div>

      {/* 4. Relevant Page Context (URL+Question mode) */}
      {result.relevant_page_context && result.relevant_page_context.length > 0 && (
        <div className="card-section page-context-section">
          <h3 className="card-heading">
            <BookOpen size={19} className="heading-icon" />
            Relevant Page Context (From Provided Webpage)
          </h3>
          <p className="visual-evidence-disclaimer">
            Extracted directly from the provided URL — the webpage is the subject being analyzed, not independent proof.
          </p>
          <div className="page-context-list">
            {result.relevant_page_context.map((ctx, idx) => (
              <div key={idx} className="page-context-item">
                "{ctx}"
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 5. Claims Analyzed Grid (URL-Only mode) */}
      {result.mode === "url" && result.claims_analyzed && result.claims_analyzed.length > 0 && (
        <div className="card-section">
          <h3 className="card-heading">
            <CheckCircle2 size={19} className="heading-icon" />
            Key Claims Analyzed ({result.claims_analyzed.length})
          </h3>
          <div className="claims-analyzed-grid">
            {result.claims_analyzed.map((c, idx) => (
              <div key={idx} className="claim-analyzed-card">
                <div className="claim-analyzed-header">
                  <span className={`stance-tag ${c.verdict}`}>
                    {c.verdict_symbol} {c.verdict_title}
                  </span>
                  <span className="relevance-tag">
                    Confidence: {Math.round(c.confidence_score * 100)}%
                  </span>
                </div>
                <p className="claim-analyzed-text">"{c.claim}"</p>
                <p className="claim-analyzed-expl">{c.explanation}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 6. Visual Evidence Section (Conditional) */}
      <VisualEvidenceSection images={images} />

      {/* 7. Summary Evidence Cards */}
      {!isSubjective && summaryEvidence.length > 0 && (
        <div className="card-section">
          <div className="card-section-header">
            <h3 className="card-heading" style={{ marginBottom: 0 }}>
              <CheckCircle2 size={19} className="heading-icon" />
              Retrieved Evidence Summary ({summaryEvidence.length} {summaryEvidence.length === 1 ? "item" : "items"})
            </h3>
            {hasMultipleDomains ? (
              <span
                className="source-diversity-badge multi-domain"
                title="Evidence spans multiple independent publisher domains"
              >
                {uniqueDomains.length} Independent Source Domains
              </span>
            ) : isSinglePublisher ? (
              <span
                className="source-diversity-badge single-domain"
                title="Multiple evidence passages extracted from a single source domain"
              >
                Single Source Domain ({uniqueDomains[0]})
              </span>
            ) : null}
          </div>
          <div className="evidence-summary-grid">
            {summaryEvidence.map((ev, idx) => (
              <SummaryEvidenceCard key={idx} item={ev} />
            ))}
          </div>
        </div>
      )}

      {/* 8. Evidence Limitations */}
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
          {Math.min(100, Math.round(item.similarity_score * 100))}% Relevance
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



