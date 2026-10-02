import React from "react";
import { ShieldAlert, ArrowLeft } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";

interface HeaderProps {
  onNavigateHome?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onNavigateHome }) => {
  return (
    <header className="app-header">
      <div className="logo-group" onClick={onNavigateHome} style={{ cursor: onNavigateHome ? "pointer" : "default" }}>
        <div className="logo-icon">
          <ShieldAlert size={22} />
        </div>
        <div>
          <h1 className="brand-title">AI Misinfo Analyzer</h1>
        </div>
      </div>

      <div className="header-actions">
        {onNavigateHome && (
          <button
            className="replay-intro-btn"
            onClick={onNavigateHome}
            title="Return to Landing Page"
          >
            <ArrowLeft size={14} />
            <span>Landing Page</span>
          </button>
        )}
        <ThemeToggle />
      </div>
    </header>
  );
};
