import React from "react";
import { Lightbulb, Layers, Search, FileText, ShieldCheck } from "lucide-react";

export const LeftSidebar: React.FC = () => {
  return (
    <aside className="left-sidebar">
      {/* 1. Quick Overview Card */}
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

      {/* 2. Our Promise Card */}
      <div className="sidebar-card promise-card">
        <div className="sidebar-card-header">
          <ShieldCheck size={18} className="sidebar-header-icon promise-icon" />
          <h4 className="sidebar-card-title">Our Promise</h4>
        </div>
        <p className="promise-text">
          No hardcoded data. No fake evidence.
          <br />
          Only real sources and verified information.
        </p>
      </div>
    </aside>
  );
};
