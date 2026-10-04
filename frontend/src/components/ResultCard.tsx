import React, { useState, useMemo } from "react";
import {
  ExternalLink,
  BookOpen,
  AlertTriangle,
  AlertCircle,
  XCircle,
  CheckCircle2,
  HelpCircle,
  Image as ImageIcon,
  ShieldCheck,
  Languages,
} from "lucide-react";
import {
  AnalysisResult,
  EvidenceItem,
  RelevantImage,
  FactCheckItem,
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
  const isInsufficient =
    result.verdict === "insufficient_evidence" ||
    result.verdict_title?.toLowerCase().includes("insufficient");

  const displayVerdictTitle = isInsufficient
    ? "No Official Evidence"
    : result.verdict_title;

  // Combine top evidence: 3 cards per row, maximum 2 rows = max 6 cards
  let summaryEvidence: EvidenceItem[] = [
    ...result.contradicting_evidence,
    ...result.supporting_evidence,
  ];

  // If no direct supporting/contradicting items, include retrieved sources so user always has related articles
  if (summaryEvidence.length === 0 && result.all_sources && result.all_sources.length > 0) {
    summaryEvidence = result.all_sources.slice(0, 6).map((src, idx) => ({
      id: `ref_${idx + 1}`,
      url: src.url,
      title: src.title || src.domain,
      domain: src.domain,
      source_tier: src.tier,
      passage: src.tier_reason || `Related article reporting on this topic from ${src.domain}.`,
      similarity_score: 0.65,
      stance: "neutral",
    }));
  }
  summaryEvidence = summaryEvidence.slice(0, 6);

  // Distinct relevant resources for quick linking in insufficient evidence cases
  const relevantResources = useMemo(() => {
    const list: Array<{ url: string; domain: string; title?: string }> = [];
    const seenUrls = new Set<string>();

    const addSource = (url?: string, domain?: string, title?: string) => {
      if (!url || !url.startsWith("http")) return;
      const cleanUrl = url.trim();
      if (seenUrls.has(cleanUrl)) return;
      seenUrls.add(cleanUrl);
      list.push({
        url: cleanUrl,
        domain: domain || extractDomain(cleanUrl),
        title: title || domain || extractDomain(cleanUrl),
      });
    };

    if (result.all_sources && result.all_sources.length > 0) {
      result.all_sources.forEach((s) => addSource(s.url, s.domain, s.title));
    }
    if (summaryEvidence && summaryEvidence.length > 0) {
      summaryEvidence.forEach((ev) => addSource(ev.url, ev.domain, ev.title));
    }

    return list.slice(0, 6);
  }, [result.all_sources, summaryEvidence]);

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

      {/* Uploaded Image & OCR Extraction Banner */}
      {result.mode === "image" && (result.image_preview || result.extracted_image_text) && (
        <div className="image-result-section">
          {result.image_preview && (
            <div className="image-result-thumb-wrapper">
              <img
                src={result.image_preview}
                alt="Analyzed screenshot"
                className="image-result-thumb"
              />
            </div>
          )}
          <div className="image-result-details">
            {result.extracted_image_text && (
              <div className="ocr-extracted-box">
                <span className="ocr-badge">OCR Detected Claim</span>
                <p className="ocr-text">"{result.extracted_image_text}"</p>
              </div>
            )}
            {result.user_question && (
              <div className="user-question-box" style={{ padding: "0.6rem 0.85rem" }}>
                <span className="question-label">User Query:</span>
                <p className="question-text" style={{ fontSize: "0.92rem" }}>"{result.user_question}"</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 1. Verdict Banner */}
      <div className={`verdict-banner ${result.verdict}`}>
        <div className="verdict-left">
          <span className="verdict-emoji">{result.verdict_symbol}</span>
          <div>
            <span className="verdict-label">
              {result.mode === "url"
                ? "Article Assessment"
                : result.mode === "image"
                ? "Image Claim Assessment"
                : "Assessment"}
            </span>
            <h2 className="verdict-title">{displayVerdictTitle}</h2>
          </div>
        </div>

        <div className="verdict-meta">
          {result.detected_language_name && (
            <span
              className="meta-pill language-pill"
              title={`Input detected as ${result.detected_language_name} (${result.detected_language}) - processed with cross-lingual embeddings`}
            >
              <Languages size={13} style={{ marginRight: "0.25rem", verticalAlign: "middle" }} />
              {result.detected_language_name}
            </span>
          )}
          <span
            className="meta-pill"
            title="Strength and consensus of retrieved evidence supporting or refuting this claim"
          >
            {displayVerdictTitle === "TEXT EXTRACTED" || result.question_intent === "text_extraction"
              ? "Extraction Accuracy"
              : "Evidence Strength"}
            : {Math.round(result.confidence_score * 100)}%
          </span>
          {typeof result.latency_seconds === "number" && result.latency_seconds > 0 ? (
            <span className="meta-pill">{result.latency_seconds}s</span>
          ) : null}
        </div>
      </div>

      {/* 2. Answer Statement */}
      {(result.targeted_answer || isInsufficient) && (
        <div className={`card-section targeted-answer-card ${isInsufficient ? "insufficient-answer-card" : ""}`}>
          <h3 className="card-heading">
            {isInsufficient ? (
              <AlertCircle size={19} className="heading-icon text-amber-500" />
            ) : (
              <CheckCircle2 size={19} className="heading-icon" />
            )}
            Answer
          </h3>
          <p className="targeted-answer-text">
            {isInsufficient ? (
              <>
                <strong className="insufficient-heading-accent">No official evidence found.</strong> Here's what I found:
              </>
            ) : (
              result.targeted_answer
            )}
          </p>

          {isInsufficient && relevantResources.length > 0 && (
            <div className="insufficient-resources-wrapper">
              <span className="insufficient-resources-label">Relevant Resources:</span>
              <div className="insufficient-resources-chips">
                {relevantResources.map((res, idx) => (
                  <a
                    key={idx}
                    href={res.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="insufficient-resource-chip"
                    title={res.title || res.domain}
                  >
                    <ExternalLink size={12} className="res-icon" />
                    <span className="chip-domain">{res.domain}</span>
                    {res.title && res.title.toLowerCase() !== res.domain.toLowerCase() && (
                      <span className="chip-title">— {res.title.slice(0, 40)}...</span>
                    )}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 3. Google Fact-Checked By (if available) */}
      <FactCheckSection factChecks={result.fact_checks || []} />

      {/* 4. Why? Evidence Synthesis */}
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
                    Evidence Strength: {Math.round(c.confidence_score * 100)}%
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

      {/* 7. Summary / Available Evidence Cards */}
      {!isSubjective && summaryEvidence.length > 0 && (
        <div className="card-section">
          <div className="card-section-header">
            <h3 className="card-heading" style={{ marginBottom: 0 }}>
              {isInsufficient ? (
                <>
                  <BookOpen size={19} className="heading-icon" />
                  Available Evidences & Relevant Resources ({summaryEvidence.length} {summaryEvidence.length === 1 ? "item" : "items"})
                </>
              ) : (
                <>
                  <CheckCircle2 size={19} className="heading-icon" />
                  Retrieved Evidence Summary ({summaryEvidence.length} {summaryEvidence.length === 1 ? "item" : "items"})
                </>
              )}
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

          {isInsufficient && (
            <p className="visual-evidence-disclaimer" style={{ marginTop: "0.5rem", marginBottom: "0.75rem" }}>
              No official documentation confirms this assertion. Here is what related reporting and indexed resources found on this topic.
            </p>
          )}

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
    primary: "Official Source",
    secondary: "News Article",
    low_confidence: "Blogs & Articles",
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

/* --- Fact-Check Section Component --- */
const SIGNAL_STYLE: Record<string, { bg: string; text: string; label: string }> = {
  contradicted:          { bg: "#fde8e8", text: "#b91c1c", label: "False / Misleading" },
  supported:             { bg: "#d1fae5", text: "#065f46", label: "True / Verified" },
  conflicting:           { bg: "#fef3c7", text: "#92400e", label: "Mixed / Disputed" },
  insufficient_evidence: { bg: "#f3f4f6", text: "#374151", label: "Unverified" },
};

const FactCheckSection: React.FC<{ factChecks: FactCheckItem[] }> = ({ factChecks }) => {
  if (!factChecks || factChecks.length === 0) return null;

  return (
    <div className="card-section fact-check-section">
      <h3 className="card-heading">
        <ShieldCheck size={19} className="heading-icon" />
        Fact-Checked By ({factChecks.length} {factChecks.length === 1 ? "publisher" : "publishers"})
      </h3>
      <p className="visual-evidence-disclaimer">
        Results from Google Fact Check Tools — verified by independent fact-checking organisations.
      </p>
      <div className="fact-check-grid">
        {factChecks.map((fc, idx) => {
          const style = SIGNAL_STYLE[fc.verdict_signal] || SIGNAL_STYLE.insufficient_evidence;
          const dateStr = fc.claim_date
            ? new Date(fc.claim_date).toLocaleDateString("en-US", { year: "numeric", month: "short" })
            : null;

          return (
            <div key={idx} className="fact-check-card">
              <div className="fact-check-header">
                <span className="fact-check-publisher">{fc.publisher_name}</span>
                <span
                  className="fact-check-rating-badge"
                  style={{ backgroundColor: style.bg, color: style.text }}
                >
                  {fc.rating}
                </span>
              </div>
              <p className="fact-check-claim">"{fc.claim_text.slice(0, 120)}{fc.claim_text.length > 120 ? "…" : ""}"</p>
              <div className="fact-check-footer">
                {dateStr && <span className="fact-check-date">{dateStr}</span>}
                {fc.claimant && <span className="fact-check-claimant">via {fc.claimant}</span>}
                <a
                  href={fc.rating_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="details-toggle-btn"
                  title={`Read full fact-check by ${fc.publisher_name}`}
                >
                  Full fact-check <ExternalLink size={12} />
                </a>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
