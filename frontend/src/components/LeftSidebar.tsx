import React from "react";
import {
  Lightbulb,
  Layers,
  Search,
  FileText,
  Clock,
  Trash2,
  PlusCircle,
  X,
  MessageSquare,
} from "lucide-react";
import { HistoryItem } from "../types";

interface LeftSidebarProps {
  history: HistoryItem[];
  activeHistoryId: string | null;
  onSelectHistory: (item: HistoryItem) => void;
  onNewChat: () => void;
  onDeleteHistory: (id: string, e: React.MouseEvent) => void;
  onClearHistory: () => void;
}

function formatRelativeTime(ts: number): string {
  const diffSec = Math.max(0, Math.floor((Date.now() - ts) / 1000));
  if (diffSec < 45) return "Just now";
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) return `${diffHour}h ago`;
  return new Date(ts).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

function getVerdictShortLabel(verdict?: string): string {
  switch (verdict) {
    case "supported":
      return "Supported";
    case "contradicted":
      return "Contradicted";
    case "insufficient_evidence":
      return "Unverified";
    case "conflicting_evidence":
      return "Conflicting";
    case "subjective_opinion":
      return "Opinion";
    default:
      return "Analyzed";
  }
}

export const LeftSidebar: React.FC<LeftSidebarProps> = ({
  history,
  activeHistoryId,
  onSelectHistory,
  onNewChat,
  onDeleteHistory,
  onClearHistory,
}) => {
  return (
    <aside className="left-sidebar">
      {/* 1. New Chat / New Analysis Button */}
      <button
        type="button"
        className="new-chat-btn"
        onClick={onNewChat}
        title="Start a new claim or query analysis"
      >
        <PlusCircle size={17} />
        <span>New Analysis</span>
      </button>

      {/* 2. Recent Chat History (Last 5) */}
      <div className="sidebar-card history-card">
        <div className="sidebar-card-header history-header">
          <div className="history-header-title-group">
            <Clock size={16} className="sidebar-header-icon" />
            <h4 className="sidebar-card-title">Recent Chats</h4>
          </div>

          {history.length > 0 && (
            <button
              type="button"
              className="history-clear-btn"
              onClick={onClearHistory}
              title="Clear last 5 chats"
              aria-label="Clear chat history"
            >
              <Trash2 size={14} />
            </button>
          )}
        </div>

        {history.length === 0 ? (
          <div className="history-empty">
            <MessageSquare size={20} className="history-empty-icon" />
            <p className="history-empty-text">
              No recent chats yet. Your last 5 analyses will be saved here automatically.
            </p>
          </div>
        ) : (
          <div className="history-list">
            {history.map((item) => {
              const isActive = activeHistoryId === item.id;
              const verdict = item.result?.verdict;
              const verdictLabel = getVerdictShortLabel(verdict);

              return (
                <div
                  key={item.id}
                  className={`history-item ${isActive ? "active" : ""}`}
                  onClick={() => onSelectHistory(item)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onSelectHistory(item);
                    }
                  }}
                  title={item.claim}
                >
                  <div className="history-item-top">
                    <span className={`history-verdict-pill ${verdict || "default"}`}>
                      {verdictLabel}
                    </span>
                    <span className="history-item-time">
                      {formatRelativeTime(item.timestamp)}
                    </span>
                    <button
                      type="button"
                      className="history-delete-item-btn"
                      onClick={(e) => onDeleteHistory(item.id, e)}
                      title="Remove from history"
                      aria-label="Delete this history item"
                    >
                      <X size={13} />
                    </button>
                  </div>

                  <p className="history-item-claim">{item.claim}</p>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 3. Quick Overview Card */}
      <div className="sidebar-card overview-card">
        <div className="sidebar-card-header">
          <Lightbulb size={18} className="sidebar-header-icon" />
          <h4 className="sidebar-card-title">Quick Overview</h4>
        </div>
        <p className="overview-intro">
          This tool analyzes claims using real web evidence and AI verification to help identify misinformation.
        </p>

        <div className="overview-features">
          <div className="feature-item">
            <div className="feature-icon-wrapper">
              <Layers size={15} />
            </div>
            <div>
              <div className="feature-title">Evidence-first approach</div>
              <div className="feature-subtext">Real sources, not assumptions</div>
            </div>
          </div>

          <div className="feature-item">
            <div className="feature-icon-wrapper">
              <Search size={15} />
            </div>
            <div>
              <div className="feature-title">Source quality filtering</div>
              <div className="feature-subtext">Prioritizes authoritative sources</div>
            </div>
          </div>

          <div className="feature-item">
            <div className="feature-icon-wrapper">
              <FileText size={15} />
            </div>
            <div>
              <div className="feature-title">Transparent reasoning</div>
              <div className="feature-subtext">See exactly what evidence was used</div>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};
