import React from "react";
import {
  ExternalLink,
  BookOpen,
  AlertTriangle,
  XCircle,
  CheckCircle2,
  HelpCircle,
} from "lucide-react";
import {
  AnalysisResult,
  EvidenceItem,
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

      {/* 3. Summary Evidence Cards */}
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



