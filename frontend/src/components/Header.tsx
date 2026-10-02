import React from "react";
import { ShieldAlert, Play } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";

interface HeaderProps {
  onReplayIntro?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onReplayIntro }) => {
  return (
    <header className="app-header">
      <div className="logo-group">
        <div className="logo-icon">
          <ShieldAlert size={22} />
        </div>
        <div>
          <h1 className="brand-title">AI Misinfo Analyzer</h1>
        </div>
      </div>

      <div className="header-actions">
        {onReplayIntro && (
          <button
            className="replay-intro-btn"
            onClick={onReplayIntro}
            title="Replay intro animation"
          >
            <Play size={14} />
            <span>Replay Intro</span>
          </button>
        )}
        <ThemeToggle />
      </div>
    </header>
  );
};
