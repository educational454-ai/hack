import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  ArrowRight,
  ArrowDown,
  Globe,
  FileText,
  Sparkles,
  Link as LinkIcon,
  Image as ImageIcon,
  ExternalLink,
  Lock,
  Cpu,
  ShieldCheck,
  ChevronRight,
} from "lucide-react";
import "./landing.css";

interface LandingPageProps {
  onNavigateToAnalyzer: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onNavigateToAnalyzer }) => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [activeSection, setActiveSection] = useState("hero");
  const [activePipelineStep, setActivePipelineStep] = useState(3); // 0-indexed active step

  // Track navbar glass blur state on scroll
  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 40) {
        setIsScrolled(true);
      } else {
        setIsScrolled(false);
      }
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // IntersectionObserver for scroll-active progress dot indicator across 5 core sections
  useEffect(() => {
    const sectionIds = [
      "hero",
      "evidence-engine",
      "analyzer-showcase",
      "multimodal",
      "final-cta",
    ];

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      { threshold: 0.3 }
    );

    sectionIds.forEach((id) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  const pipelineSteps = [
    { step: "01", title: "CLAIM INPUT", desc: "Statement, article URL, or uploaded document image" },
    { step: "02", title: "WEB RETRIEVAL", desc: "Multi-engine search gathering independent web evidence" },
    { step: "03", title: "SOURCE QUALITY", desc: "Domain reputation classification & tier filtering" },
    { step: "04", title: "SEMANTIC RELEVANCE", desc: "BGE-M3 dense vector passage re-ranking" },
    { step: "05", title: "EVIDENCE GATE", desc: "Strict quality threshold filtering weak or noisy snippets" },
    { step: "06", title: "AI VERIFICATION", desc: "Grounded AI verification using LLM inference" },
    { step: "07", title: "PROVENANCE", desc: "Canonical URL normalization & exact quote link mapping" },
    { step: "08", title: "TRUTHFUL VERDICT", desc: "Score, neutral explanation, and transparent evidence list" },
  ];

  return (
    <div className="landing-root">
      {/* Background Ambient Gradients */}
      <div className="landing-ambient-bg" />

      {/* Navbar (4 concise section links + CTA) */}
      <nav className={`landing-nav ${isScrolled ? "scrolled" : ""}`}>
        <div className="landing-brand" onClick={() => scrollToSection("hero")}>
          <div className="landing-brand-icon">
            <ShieldAlert size={18} />
          </div>
          <span>TRUTHGUARD AI</span>
        </div>

        <ul className="landing-nav-links">
          <li>
            <span
              className={`landing-nav-link ${activeSection === "hero" ? "active" : ""}`}
              onClick={() => scrollToSection("hero")}
            >
              Home
            </span>
          </li>
          <li>
            <span
              className={`landing-nav-link ${activeSection === "evidence-engine" ? "active" : ""}`}
              onClick={() => scrollToSection("evidence-engine")}
            >
              Evidence
            </span>
          </li>
          <li>
            <span
              className={`landing-nav-link ${activeSection === "analyzer-showcase" ? "active" : ""}`}
              onClick={() => scrollToSection("analyzer-showcase")}
            >
              Analyzer
            </span>
          </li>
          <li>
            <span
              className={`landing-nav-link ${activeSection === "multimodal" ? "active" : ""}`}
              onClick={() => scrollToSection("multimodal")}
            >
              Multimodal
            </span>
          </li>
        </ul>

        <button className="landing-nav-cta" onClick={onNavigateToAnalyzer}>
          <span>ANALYZE A CLAIM</span>
          <ArrowRight size={15} />
        </button>
      </nav>

      {/* Sidebar Progress Dots (EXACTLY 5 core sections) */}
      <aside className="landing-scroll-indicator" aria-label="Section navigation">
        {[
          { id: "hero", label: "Home" },
          { id: "evidence-engine", label: "Evidence Engine" },
          { id: "analyzer-showcase", label: "Analyzer" },
          { id: "multimodal", label: "Multimodal" },
          { id: "final-cta", label: "Verify" },
        ].map((item) => (
          <div
            key={item.id}
            className={`scroll-indicator-dot ${activeSection === item.id ? "active" : ""}`}
            onClick={() => scrollToSection(item.id)}
            title={item.label}
          />
        ))}
      </aside>

      {/* SECTION 01 — HERO / WHY */}
      <section id="hero" className="landing-section hero-section">
        <div className="hero-glow-bg" />

        <div className="hero-badge">
          <Sparkles size={14} />
          <span>EVIDENCE-FIRST MISINFORMATION ANALYZER</span>
        </div>

        <h1 className="hero-title">
          VERIFY <br />
          <span className="hero-title-highlight">WHAT YOU SEE.</span>
        </h1>

        <p className="hero-subtitle">
          Information moves faster than verification. Claims spread across articles, feeds,
          and images before fact-checking can respond. TruthGuard AI provides transparent,
          evidence-grounded claim verification.
        </p>

        <div className="hero-cta-group">
          <button className="primary-btn" onClick={onNavigateToAnalyzer}>
            <span>ANALYZE A CLAIM</span>
            <ArrowRight size={18} />
          </button>

          <button
            className="secondary-btn"
            onClick={() => scrollToSection("evidence-engine")}
          >
            <span>EXPLORE THE ENGINE</span>
            <ArrowDown size={16} />
          </button>
        </div>

        {/* Hero Abstract Product Visual: CLAIM -> EVIDENCE -> VERIFICATION */}
        <div className="hero-product-visualization">
          <div className="vis-connector-line" />

          <div className="vis-node vis-claim-node">
            <div className="vis-node-badge">INPUT CLAIM</div>
            <div className="vis-node-content">
              <FileText size={16} className="vis-icon-orange" />
              <span>Input Claim Proposition</span>
            </div>
            <div className="vis-node-meta">Text • Web Article URL • Image OCR</div>
          </div>

          <div className="vis-center-engine">
            <div className="vis-engine-core">
              <ShieldAlert size={28} />
            </div>
            <span className="vis-engine-label">TRUTHGUARD VERIFICATION ENGINE</span>
          </div>

          <div className="vis-node vis-verdict-node">
            <div className="vis-node-badge badge-green">VERIFICATION</div>
            <div className="vis-node-content">
              <ShieldCheck size={16} className="vis-icon-green" />
              <span className="vis-verdict-title">VERIFIED RESULT</span>
            </div>
            <div className="vis-node-meta">Traceable Evidence • Source Provenance</div>
          </div>

          {/* Compact floating indicators */}
          <div className="vis-float-card float-1">
            <Globe size={13} color="#38bdf8" />
            <span>Web Evidence Retrieval</span>
          </div>

          <div className="vis-float-card float-2">
            <Cpu size={13} color="#f97316" />
            <span>Source Quality Tiering</span>
          </div>
        </div>
      </section>

      {/* Section Divider */}
      <div className="section-divider-line" />

      {/* SECTION 02 — THE EVIDENCE ENGINE */}
      <section id="evidence-engine" className="landing-section engine-section">
        <span className="section-kicker">SYSTEM ARCHITECTURE & INTEGRITY</span>
        <h2 className="huge-heading">
          EVIDENCE BEFORE <br />
          <span className="text-orange">CONCLUSIONS.</span>
        </h2>

        <p className="hero-subtitle">
          Every claim passes through a structured 8-stage verification pipeline to ensure rigorous,
          reproducible assessment grounded in source domain quality.
        </p>

        {/* 8-Stage Compact Pipeline Visual */}
        <div className="pipeline-flow">
          {pipelineSteps.map((item, idx) => {
            const isActive = idx === activePipelineStep;
            return (
              <div
                key={item.step}
                className={`pipeline-item ${isActive ? "active" : ""}`}
                onMouseEnter={() => setActivePipelineStep(idx)}
                onClick={() => setActivePipelineStep(idx)}
              >
                <div className="pipeline-item-left">
                  <span className="pipeline-step-num">{item.step}</span>
                  <span className="pipeline-step-title">{item.title}</span>
                </div>
                <span className="pipeline-step-desc">{item.desc}</span>
                {isActive && <div className="pipeline-active-indicator" />}
              </div>
            );
          })}
        </div>

        {/* Compact Source Quality & Technical Distinction */}
        <div className="engine-sub-grid">
          {/* Source Quality Breakdown */}
          <div className="engine-sub-card">
            <h3 className="engine-sub-title">Source Quality Classification</h3>
            <div className="source-tier-mini-list">
              <div className="tier-mini-item primary">
                <span className="tier-badge badge-primary">TIER 1</span>
                <div>
                  <strong>PRIMARY SOURCES</strong>
                  <p>Official government archives (.gov), academic publications, and central bank records.</p>
                </div>
              </div>

              <div className="tier-mini-item secondary">
                <span className="tier-badge badge-secondary">TIER 2</span>
                <div>
                  <strong>SECONDARY REPORTING</strong>
                  <p>Established news organizations and verified investigative reporting outlets.</p>
                </div>
              </div>

              <div className="tier-mini-item low">
                <span className="tier-badge badge-low">TIER 3</span>
                <div>
                  <strong>LOW CONFIDENCE</strong>
                  <p>Unverified blogs and automated content feeds filtered out by strict evidence gates.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Relevance vs Truth Concept */}
          <div className="engine-sub-card">
            <h3 className="engine-sub-title">Relevance Is Not Truth</h3>
            <blockquote className="semantic-editorial-quote-compact">
              "Semantic relevance finds passages discussing the same topic.
              Verification determines whether those passages support or contradict the claim."
            </blockquote>
            <div className="semantic-flow-line-compact">
              <span>01 CLAIM</span>
              <ChevronRight size={14} className="sem-arrow" />
              <span>02 RELEVANT PASSAGE</span>
              <ChevronRight size={14} className="sem-arrow" />
              <span>03 SOURCE TIER</span>
              <ChevronRight size={14} className="sem-arrow" />
              <span className="text-orange">04 VERIFICATION</span>
            </div>
          </div>
        </div>
      </section>

      {/* Section Divider */}
      <div className="section-divider-line" />

      {/* SECTION 03 — THE ANALYZER (Hero Product Visual) */}
      <section id="analyzer-showcase" className="landing-section showcase-section">
        <div className="hero-badge">
          <Sparkles size={14} />
          <span>ACTUAL PRODUCT INTERFACE</span>
        </div>

        <h2 className="huge-heading">THE ANALYZER IN ACTION</h2>

        <p className="hero-subtitle">
          Interactive claim analysis studio showcasing real-time proposition extraction, source tiering, and traceable evidence.
        </p>

        {/* UI Structural Preview (No fabricated real-world data) */}
        <div className="showcase-frame">
          <div className="showcase-topbar">
            <div className="showcase-window-dots">
              <span className="dot dot-red" />
              <span className="dot dot-yellow" />
              <span className="dot dot-green" />
            </div>
            <div className="showcase-url-bar">
              <Lock size={12} color="#f97316" />
              <span>truthguard.ai/analyzer</span>
            </div>
            <span className="showcase-preview-tag">PRODUCT PREVIEW / EXAMPLE ANALYSIS</span>
          </div>

          <div className="showcase-body">
            <div className="showcase-claim-header">
              <div className="showcase-claim-label">INPUT CLAIM PROPOSITION</div>
              <div className="showcase-claim-text">
                "[Sample claim proposition submitted for verification]"
              </div>
            </div>

            <div className="showcase-verdict-banner">
              <div className="showcase-verdict-main">
                <div className="verdict-pill-red">
                  <ShieldAlert size={18} />
                  <span>CONTRADICTED</span>
                </div>
                <div className="verdict-confidence">
                  <span>Verification Confidence:</span>
                  <strong>High Confidence</strong>
                </div>
              </div>
              <p className="verdict-summary-text">
                Structural preview demonstrating how retrieved web evidence passages and source domain reputations form a grounded verdict.
              </p>
            </div>

            <div className="showcase-evidence-grid">
              <div className="showcase-evidence-card">
                <div className="evidence-card-header">
                  <span className="evidence-source-domain">domain.example.gov</span>
                  <span className="evidence-tier-tag">TIER 1 PRIMARY</span>
                </div>
                <p className="evidence-snippet">
                  "Retrieved factual evidence passage snippet extracted from canonical primary source URL."
                </p>
                <div className="evidence-meta-row">
                  <span>Relevance: High</span>
                  <span>NLI: Contradiction</span>
                </div>
              </div>

              <div className="showcase-evidence-card">
                <div className="evidence-card-header">
                  <span className="evidence-source-domain">news-outlet.example</span>
                  <span className="evidence-tier-tag">TIER 2 SECONDARY</span>
                </div>
                <p className="evidence-snippet">
                  "Corroborating reporting passage supporting the independent verifier assessment."
                </p>
                <div className="evidence-meta-row">
                  <span>Relevance: Relevant</span>
                  <span>NLI: Supporting</span>
                </div>
              </div>
            </div>

            <div className="showcase-action-bar">
              <button className="primary-btn" onClick={onNavigateToAnalyzer}>
                <span>TRY THE ANALYZER</span>
                <ArrowRight size={18} />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Section Divider */}
      <div className="section-divider-line" />

      {/* SECTION 04 — MULTIMODAL + TRACEABILITY */}
      <section id="multimodal" className="landing-section multimodal-section">
        <span className="section-kicker">MULTIMODAL & TRACEABILITY</span>
        <h2 className="huge-heading">
          VERIFY MORE <span className="text-orange">THAN TEXT.</span>
        </h2>
        <p className="hero-subtitle">
          Process claim propositions from images, documents, web article URLs, or direct statements with full provenance transparency.
        </p>

        <div className="multimodal-combined-box">
          {/* 2 Clean Input Paths */}
          <div className="multimodal-paths-compact">
            <div className="multimodal-path-card">
              <div className="path-icon-wrapper">
                <ImageIcon size={20} className="text-orange" />
              </div>
              <h3 className="path-title">IMAGE / DOCUMENT ANALYSIS</h3>
              <p className="path-desc">
                RapidOCR extracts text claims from screenshots, news clips, and document flyers.
              </p>
              <div className="path-flow-line">
                <span className="flow-step">IMAGE</span>
                <span className="flow-arr">→</span>
                <span className="flow-step">OCR</span>
                <span className="flow-arr">→</span>
                <span className="flow-step">CLAIM</span>
                <span className="flow-arr">→</span>
                <span className="flow-step">EVIDENCE</span>
                <span className="flow-arr">→</span>
                <span className="flow-step">VERDICT</span>
              </div>
            </div>

            <div className="multimodal-path-card">
              <div className="path-icon-wrapper">
                <LinkIcon size={20} color="#38bdf8" />
              </div>
              <h3 className="path-title">URL & WEB ARTICLE VERIFICATION</h3>
              <p className="path-desc">
                Extract context directly from article links and independent web documents.
              </p>
              <div className="path-flow-line">
                <span className="flow-step">URL</span>
                <span className="flow-arr">→</span>
                <span className="flow-step">CONTEXT</span>
                <span className="flow-arr">→</span>
                <span className="flow-step">RETRIEVAL</span>
                <span className="flow-arr">→</span>
                <span className="flow-step">EVIDENCE</span>
                <span className="flow-arr">→</span>
                <span className="flow-step">VERDICT</span>
              </div>
            </div>
          </div>

          {/* Compact Traceability Banner */}
          <div className="traceability-compact-banner">
            <span className="trace-title">A VERDICT YOU CAN TRACE</span>
            <div className="transparent-chain-compact">
              <div className="chain-pill">VERDICT</div>
              <span className="chain-arrow">→</span>
              <div className="chain-pill">EXPLANATION</div>
              <span className="chain-arrow">→</span>
              <div className="chain-pill">EVIDENCE SNIPPET</div>
              <span className="chain-arrow">→</span>
              <div className="chain-pill">AUTHORITATIVE SOURCE</div>
              <span className="chain-arrow">→</span>
              <div className="chain-pill">PROVENANCE</div>
            </div>
          </div>
        </div>
      </section>

      {/* Section Divider */}
      <div className="section-divider-line" />

      {/* SECTION 05 — FINAL CTA */}
      <section id="final-cta" className="landing-section final-cta-section">
        <h2 className="final-cta-title">
          DON'T JUST BELIEVE IT. <br />
          <span className="text-orange">VERIFY IT.</span>
        </h2>

        <p className="hero-subtitle" style={{ marginBottom: "3rem" }}>
          Evidence before conclusions.
        </p>

        <div className="hero-cta-group">
          <button className="primary-btn" onClick={onNavigateToAnalyzer}>
            <span>ANALYZE A CLAIM</span>
            <ArrowRight size={18} />
          </button>

          <button className="secondary-btn" onClick={onNavigateToAnalyzer}>
            <span>EXPLORE THE ANALYZER</span>
            <ExternalLink size={16} />
          </button>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;


