import React from "react";
import { ShieldAlert } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";

export const Header: React.FC = () => {
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
        <ThemeToggle />
      </div>
    </header>
  );
};
