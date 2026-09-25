import React from "react";
import { Globe, ExternalLink, Lightbulb, CheckCircle2 } from "lucide-react";
import { AnalysisResult, SourceMetadata, EvidenceItem } from "../types";

interface RightSidebarProps {
  result: AnalysisResult | null;
}

function normalizeUrlString(url: string): string {
  if (!url) return "";
  let clean = url.trim();
  clean = clean.replace(/#.*$/, "");
  clean = clean.replace(/\/$/, "");
  return clean.toLowerCase();
}

function deduplicateSourcesByUrl(sources: SourceMetadata[]): SourceMetadata[] {
  const seen = new Set<string>();
  const unique: SourceMetadata[] = [];
  for (const src of sources) {
    const key = src.url ? normalizeUrlString(src.url) : src.domain;
    if (key && !seen.has(key)) {
      seen.add(key);
      unique.push(src);
    }
  }
  return unique;
}

export const RightSidebar: React.FC<RightSidebarProps> = ({ result }) => {
  if (!result) {
    return (
      <aside className="right-sidebar">
        <div className="sidebar-card empty-sidebar-card">
          <div className="sidebar-card-header">
            <Globe size={18} className="sidebar-header-icon" />
            <h4 className="sidebar-card-title">Relevant Resources</h4>
          </div>
          <p className="sidebar-empty-text">
            Submit a claim to view authoritative resources and evidence citations.
          </p>
        </div>
      </aside>
    );
  }

  const sourcesToDisplay = deduplicateSourcesByUrl(result.all_sources || []);

  // Combine supporting and contradicting evidence to look up similarity scores by URL or domain
  const allEvidence: EvidenceItem[] = [
    ...(result.supporting_evidence || []),
    ...(result.contradicting_evidence || []),
  ];

  const getSourceRelevanceScore = (source: SourceMetadata): number | null => {
    const matchedEv = allEvidence.find(
      (ev) => ev.url === source.url || (ev.domain && ev.domain === source.domain)
    );
    return matchedEv ? Math.min(100, Math.round(matchedEv.similarity_score * 100)) : null;
  };

  // Derive Takeaway Bullet Points strictly from backend result explanation & limitations
  const deriveTakeaways = (): string[] => {
    if (!result) return [];

    const bulletPoints: string[] = [];

    // Split backend explanation into distinct sentences
    const sentences = (result.explanation || "")
      .split(/(?<=[.!?])\s+/)
      .map((s) => s.trim())
      .filter((s) => s.length > 10);

    if (sentences.length > 0) {
      bulletPoints.push(sentences[0]);
    }
    if (sentences.length > 1) {
      bulletPoints.push(sentences[1]);
    }

    // Add limitation or third sentence if available
    if (result.evidence_limitations && result.evidence_limitations.length > 0) {
      bulletPoints.push(result.evidence_limitations[0]);
    } else if (sentences.length > 2) {
      bulletPoints.push(sentences[2]);
    }

    return bulletPoints.slice(0, 3);
  };

  const takeaways = deriveTakeaways();

  return (
    <aside className="right-sidebar">
      {/* 1. Relevant Resources Card */}
      <div className="sidebar-card resources-sidebar-card">
        <div className="sidebar-card-header">
          <div className="header-title-group">
            <Globe size={18} className="sidebar-header-icon" />
            <h4 className="sidebar-card-title">
              Relevant Resources ({sourcesToDisplay.length})
            </h4>
          </div>
        </div>

        {sourcesToDisplay.length > 0 ? (
          <div className="sidebar-sources-list">
            {sourcesToDisplay.map((src, idx) => {
              const relevanceScore = getSourceRelevanceScore(src);
              return (
                <SidebarResourceCard
                  key={idx}
                  source={src}
                  relevanceScore={relevanceScore}
                />
              );
            })}
          </div>
        ) : (
          <p className="sidebar-empty-text">No relevant resources were retrieved.</p>
        )}
      </div>

      {/* 2. Key Takeaways Card (derived purely from backend response) */}
      {takeaways.length > 0 && (
        <div className="sidebar-card takeaways-sidebar-card">
          <div className="sidebar-card-header">
            <Lightbulb size={18} className="sidebar-header-icon takeaways-icon" />
            <h4 className="sidebar-card-title">Key Takeaways</h4>
          </div>
          <ul className="takeaways-list">
            {takeaways.map((point, idx) => (
              <li key={idx} className="takeaway-item">
                <CheckCircle2 size={16} className="takeaway-bullet-icon" />
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </aside>
  );
};

/* --- Sidebar Resource Card Sub-component --- */
interface SidebarResourceCardProps {
  source: SourceMetadata;
  relevanceScore: number | null;
}

const SidebarResourceCard: React.FC<SidebarResourceCardProps> = ({
  source,
  relevanceScore,
}) => {
  const tierLabelMap: Record<string, string> = {
    primary: "PRIMARY SOURCE",
    secondary: "SECONDARY SOURCE",
    low_confidence: "LOW CONFIDENCE SOURCE",
  };
  const tierDisplay = tierLabelMap[source.tier] || source.tier.toUpperCase();

  const cardContent = (
    <>
      <div className="sidebar-resource-top">
        <span className={`sidebar-tier-badge ${source.tier}`}>
          {tierDisplay}
        </span>
        {relevanceScore !== null && (
          <span
            className="sidebar-relevance-pill"
            title="BGE-M3 semantic retrieval relevance score"
          >
            {relevanceScore}%
          </span>
        )}
      </div>
      <h5 className="sidebar-resource-title">
        {source.title || source.domain}
      </h5>
      <div className="sidebar-resource-domain-row">
        <span className="sidebar-resource-domain">{source.domain}</span>
        {source.url && <ExternalLink size={12} className="sidebar-link-icon" />}
      </div>
    </>
  );

  if (source.url) {
    return (
      <a
        href={source.url}
        target="_blank"
        rel="noopener noreferrer"
        className="sidebar-resource-item"
      >
        {cardContent}
      </a>
    );
  }

  return <div className="sidebar-resource-item no-link">{cardContent}</div>;
};
