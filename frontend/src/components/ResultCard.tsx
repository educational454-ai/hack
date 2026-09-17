import React from "react";
import {
  ExternalLink,
  BookOpen,
  AlertTriangle,
  XCircle,
  CheckCircle2,
  Globe,
} from "lucide-react";
import {
  AnalysisResult,
  EvidenceItem,
  SourceMetadata,
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
      {/* 1. Verdict Banner (Removed factual tag as requested) */}
      <div className={`verdict-banner ${result.verdict}`}>
        <div className="verdict-left">
          <span className="verdict-emoji">{result.verdict_symbol}</span>
          <div>
            <span className="verdict-label">Assessment</span>
            <h2 className="verdict-title">{result.verdict_title}</h2>
          </div>
        </div>

        <div className="verdict-meta">
          <span className="meta-pill">
            Confidence: {Math.round(result.confidence_score * 100)}%
          </span>
          {result.latency_seconds && (
            <span className="meta-pill">{result.latency_seconds}s</span>
          )}
        </div>
      </div>

      {/* 2. Why? Evidence Synthesis (First as requested) */}
      <div className="explanation-card">
        <h3 className="card-heading">
          <BookOpen size={19} className="heading-icon" />
          Why? Evidence Synthesis
        </h3>
        <p className="explanation-text">{result.explanation}</p>
      </div>

      {/* 3. Summary Evidence Cards (3 cards per row, max 2 rows, expandable details) */}
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

      {/* 4. Relevant Resources Card with direct links to actual articles */}
      {result.all_sources && result.all_sources.length > 0 && (
        <div className="card-section">
          <h3 className="card-heading">
            <Globe size={19} className="heading-icon" />
            Relevant Resources ({result.all_sources.length})
          </h3>
          <div className="sources-grid">
            {result.all_sources.map((src, idx) => (
              <SourceResourceCard key={idx} source={src} />
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

/* --- Summary Evidence Card with Direct Link to Official Site --- */
const SummaryEvidenceCard: React.FC<{ item: EvidenceItem }> = ({ item }) => {
  const isContradicting = item.stance === "contradicts";

  return (
    <div className="summary-ev-card">
      <div className="summary-ev-header">
        <span
          className={`stance-tag ${isContradicting ? "contradicts" : "supports"}`}
        >
          {isContradicting ? (
            <>
              <XCircle size={12} /> Contradicts
            </>
          ) : (
            <>
              <CheckCircle2 size={12} /> Supports
            </>
          )}
        </span>
        <span className="relevance-tag">
          {Math.round(item.similarity_score * 100)}% Match
        </span>
      </div>

      <p className="summary-ev-snippet">
        "{item.passage.slice(0, 115).trim()}..."
      </p>

      <div className="summary-ev-footer">
        <span className="summary-domain">{item.domain}</span>
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="details-toggle-btn"
          title="Open official source article"
        >
          View details <ExternalLink size={12} />
        </a>
      </div>
    </div>
  );
};

/* --- Relevant Resource Card with Direct Article Link --- */
const SourceResourceCard: React.FC<{ source: SourceMetadata }> = ({
  source,
}) => {
  return (
    <a
      href={source.url}
      target="_blank"
      rel="noopener noreferrer"
      className="resource-card"
    >
      <div className="resource-header">
        <span className={`tier-badge ${source.tier}`}>{source.tier}</span>
        <ExternalLink size={13} className="resource-link-icon" />
      </div>
      <h5 className="resource-title">{source.title || source.domain}</h5>
      <span className="resource-domain">{source.domain}</span>
    </a>
  );
};

