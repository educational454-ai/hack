import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  ArrowRight,
  ArrowDown,
  Globe,
  FileText,
  Search,
  AlertTriangle,
  Zap,
  Layers,
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

  // Cycle active pipeline stage automatically every 4s unless hovered
  useEffect(() => {
    const interval = setInterval(() => {
      setActivePipelineStep((prev) => (prev + 1) % 8);
    }, 4500);
    return () => clearInterval(interval);
  }, []);

  // IntersectionObserver for scroll-active progress dot indicator
  useEffect(() => {
    const sectionIds = [
      "hero",
      "speed",
      "how-it-works",
      "sources",
      "evidence",
      "preview",
      "multimodal",
      "transparent",
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
      { threshold: 0.25 }
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
    { step: "05", title: "EVIDENCE GATE", desc: "Strict quality threshold filtering weak or noise snippets" },
    { step: "06", title: "AI VERIFICATION", desc: "Hugging Face cross-encoder NLI model inference" },
    { step: "07", title: "PROVENANCE", desc: "Canonical URL normalization & exact quote link mapping" },
    { step: "08", title: "TRUTHFUL VERDICT", desc: "Score, neutral explanation, and transparent evidence list" },
  ];

  return (
    <div className="landing-root">
      {/* Background Ambient Gradients */}
      <div className="landing-ambient-bg" />

      {/* Navbar */}
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
              className={`landing-nav-link ${activeSection === "how-it-works" ? "active" : ""}`}
              onClick={() => scrollToSection("how-it-works")}
            >
              Architecture
            </span>
          </li>
          <li>
            <span
              className={`landing-nav-link ${activeSection === "sources" ? "active" : ""}`}
              onClick={() => scrollToSection("sources")}
            >
              Source Quality
            </span>
          </li>
          <li>
            <span
              className={`landing-nav-link ${activeSection === "preview" ? "active" : ""}`}
              onClick={() => scrollToSection("preview")}
            >
              Product Preview
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

      {/* Sidebar Progress Dots */}
      <aside className="landing-scroll-indicator" aria-label="Section navigation">
        {[
          "hero",
          "speed",
          "how-it-works",
          "sources",
          "evidence",
          "preview",
          "multimodal",
          "transparent",
          "final-cta",
        ].map((id) => (
          <div
            key={id}
            className={`scroll-indicator-dot ${activeSection === id ? "active" : ""}`}
            onClick={() => scrollToSection(id)}
            title={id.replace("-", " ").toUpperCase()}
          />
        ))}
      </aside>

      {/* Hero Section */}
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
          AI-powered claim analysis built around real web evidence, source quality tiers,
          dense vector relevance, and fully transparent, traceable verdicts.
        </p>

        <div className="hero-cta-group">
          <button className="primary-btn" onClick={onNavigateToAnalyzer}>
            <span>ANALYZE A CLAIM</span>
            <ArrowRight size={18} />
          </button>

          <button
            className="secondary-btn"
            onClick={() => scrollToSection("how-it-works")}
          >
            <span>EXPLORE HOW IT WORKS</span>
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
              <span>"India banned UPI transactions in 2025"</span>
            </div>
            <div className="vis-node-meta">Text • URL • Image OCR</div>
          </div>

          <div className="vis-center-engine">
            <div className="vis-engine-core">
              <ShieldAlert size={28} />
            </div>
            <span className="vis-engine-label">TRUTHGUARD VERIFICATION ENGINE</span>
            <div className="vis-pulse-ring" />
          </div>

          <div className="vis-node vis-verdict-node">
            <div className="vis-node-badge badge-red">VERDICT</div>
            <div className="vis-node-content">
              <ShieldCheck size={16} className="vis-icon-green" />
              <span className="vis-verdict-title">CONTRADICTED</span>
            </div>
            <div className="vis-node-meta">Confidence: 95% • 3 Sources</div>
          </div>

          {/* Floating evidence indicators */}
          <div className="vis-float-card float-1">
            <Globe size={13} color="#38bdf8" />
            <span>Primary Domain: rbi.org.in</span>
          </div>

          <div className="vis-float-card float-2">
            <Cpu size={13} color="#f97316" />
            <span>NLI Entailment: Contradiction</span>
          </div>
        </div>
      </section>

      {/* Section Divider */}
      <div className="section-divider-line" />

      {/* Section 1: Information Moves Fast */}
      <section id="speed" className="landing-section speed-section">
        <span className="section-kicker">THE MISINFORMATION LANDSCAPE</span>
        <h2 className="huge-heading">
          INFORMATION MOVES <br />
          <span className="text-orange">FASTER THAN VERIFICATION.</span>
        </h2>

        <p className="hero-subtitle">
          Claims spread across articles, social feeds, images, and headlines.
          The challenge is not finding information—it is determining what evidence
          actually supports or contradicts it.
        </p>

        <div className="speed-grid">
          <div className="speed-card">
            <div className="speed-card-icon">
              <Zap size={20} />
            </div>
            <h3 className="speed-card-title">Unfiltered Velocity</h3>
            <p className="speed-card-desc">
              Unverified statements propagate across digital networks in seconds, long before manual fact-checking can respond.
            </p>
          </div>

          <div className="speed-card">
            <div className="speed-card-icon">
              <AlertTriangle size={20} />
            </div>
            <h3 className="speed-card-title">Contextual Noise</h3>
            <p className="speed-card-desc">
              Manipulated headlines, viral memes, and out-of-context quotes easily obscure original factual context.
            </p>
          </div>

          <div className="speed-card">
            <div className="speed-card-icon">
              <Search size={20} />
            </div>
            <h3 className="speed-card-title">Evidence Disconnect</h3>
            <p className="speed-card-desc">
              Traditional search engines return text keyword matches without evaluating factual truth probability.
            </p>
          </div>
        </div>
      </section>

      {/* Section Divider */}
      <div className="section-divider-line" />

      {/* Section 2: Evidence Architecture Pipeline (8 Stages) */}
      <section id="how-it-works" className="landing-section pipeline-section">
        <div className="hero-badge">
          <Layers size={14} />
          <span>VERIFICATION PIPELINE</span>
        </div>

        <h2 className="huge-heading">
          EVIDENCE BEFORE <br />
          <span className="text-orange">CONCLUSIONS.</span>
        </h2>

        <p className="hero-subtitle">
          Every claim passes through a structured 8-stage verification pipeline
          to ensure rigorous, reproducible assessment.
        </p>

        <div className="pipeline-flow">
          {pipelineSteps.map((item, idx) => {
            const isActive = idx === activePipelineStep;
            return (
              <div
                key={item.step}
                className={`pipeline-item ${isActive ? "active" : ""}`}
                onMouseEnter={() => setActivePipelineStep(idx)}
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
      </section>

      {/* Section Divider */}
      <div className="section-divider-line" />

      {/* Section 3: Source Quality */}
      <section id="sources" className="landing-section source-section">
        <span className="section-kicker">SOURCE EVALUATION</span>
        <h2 className="huge-heading">
          NOT ALL SOURCES <br />
          <span className="text-orange">CARRY THE SAME WEIGHT.</span>
        </h2>

        <p className="hero-subtitle">
          Source domain authority is classified before evidence passages contribute
          to final verification scores.
        </p>

        <div className="source-tier-structure">
          <div className="source-tier-card tier-primary">
            <div className="tier-header">
              <span className="tier-badge badge-primary">TIER 1 — DOMINANT</span>
              <span className="tier-weight-label">PRIMARY SOURCES</span>
            </div>
            <h3 className="tier-title">Official & Academic Records</h3>
            <p className="tier-desc">
              Government portals (.gov, .gov.in, .edu), official central bank publications, peer-reviewed scientific journals, and primary documentation.
            </p>
          </div>

          <div className="source-tier-card tier-secondary">
            <div className="tier-header">
              <span className="tier-badge badge-secondary">TIER 2 — SUPPORTING</span>
              <span className="tier-weight-label">SECONDARY REPORTING</span>
            </div>
            <h3 className="tier-title">Established News Outlets</h3>
            <p className="tier-desc">
              Recognized major news organizations, verified investigative reporting, and reputable reference publications.
            </p>
          </div>

          <div className="source-tier-card tier-low">
            <div className="tier-header">
              <span className="tier-badge badge-low">TIER 3 — QUIET</span>
              <span className="tier-weight-label">LOW CONFIDENCE</span>
            </div>
            <h3 className="tier-title">Unverified Web Content</h3>
            <p className="tier-desc">
              Personal blogs, unverified social posts, or automated content feeds filtered out by strict evidence gates.
            </p>
          </div>
        </div>
      </section>

      {/* Section Divider */}
      <div className="section-divider-line" />

      {/* Section 4: Semantic Relevance vs Truth */}
      <section id="evidence" className="landing-section semantic-section">
        <span className="section-kicker">TECHNICAL DISTINCTION</span>
        <h2 className="huge-heading">
          RELEVANCE IS <span className="text-orange">NOT TRUTH.</span>
        </h2>

        <div className="semantic-container">
          <blockquote className="semantic-editorial-quote">
            "Dense vector models locate passages discussing the same topic.
            Cross-encoder NLI inference then evaluates logical entailment versus contradiction to determine factual truth."
          </blockquote>

          <div className="semantic-flow-diagram">
            <div className="sem-step">
              <span className="sem-step-num">01</span>
              <span className="sem-step-label">CLAIM</span>
            </div>
            <ChevronRight size={18} className="sem-arrow" />
            <div className="sem-step">
              <span className="sem-step-num">02</span>
              <span className="sem-step-label">RELEVANT PASSAGE</span>
            </div>
            <ChevronRight size={18} className="sem-arrow" />
            <div className="sem-step">
              <span className="sem-step-num">03</span>
              <span className="sem-step-label">SOURCE TIER</span>
            </div>
            <ChevronRight size={18} className="sem-arrow" />
            <div className="sem-step sem-highlight">
              <span className="sem-step-num">04</span>
              <span className="sem-step-label">VERIFICATION</span>
            </div>
          </div>
        </div>
      </section>

      {/* Section Divider */}
      <div className="section-divider-line" />

      {/* Section 5: Analyzer Showcase (Hero Product Visual Anchor) */}
      <section id="preview" className="landing-section showcase-section">
        <div className="hero-badge">
          <Sparkles size={14} />
          <span>ACTUAL PRODUCT INTERFACE</span>
        </div>

        <h2 className="huge-heading">THE ANALYZER IN ACTION</h2>

        <p className="hero-subtitle">
          Interactive claim analysis view showcasing exact verdict scoring, passage retrieval, and source provenance.
        </p>

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
                "India has officially banned UPI digital payments starting from 2025."
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
                  <strong>95.0%</strong>
                </div>
              </div>
              <p className="verdict-summary-text">
                Official statements from NPCI and RBI confirm that UPI payments remain operational and fully supported across all banking networks.
              </p>
            </div>

            <div className="showcase-evidence-grid">
              <div className="showcase-evidence-card">
                <div className="evidence-card-header">
                  <span className="evidence-source-domain">npci.org.in</span>
                  <span className="evidence-tier-tag">TIER 1 PRIMARY</span>
                </div>
                <p className="evidence-snippet">
                  "NPCI confirms UPI operations continue standard processing across all participating member banks without disruption."
                </p>
                <div className="evidence-meta-row">
                  <span>Relevance: 0.94</span>
                  <span>NLI: Contradiction (96%)</span>
                </div>
              </div>

              <div className="showcase-evidence-card">
                <div className="evidence-card-header">
                  <span className="evidence-source-domain">rbi.org.in</span>
                  <span className="evidence-tier-tag">TIER 1 PRIMARY</span>
                </div>
                <p className="evidence-snippet">
                  "Reserve Bank of India reiterates digital payment infrastructure stability and ongoing expansion initiatives."
                </p>
                <div className="evidence-meta-row">
                  <span>Relevance: 0.91</span>
                  <span>NLI: Contradiction (94%)</span>
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

      {/* Section 6: Multimodal Inputs */}
      <section id="multimodal" className="landing-section multimodal-section">
        <span className="section-kicker">MULTIMODAL CAPABILITY</span>
        <h2 className="huge-heading">
          VERIFY MORE <span className="text-orange">THAN TEXT.</span>
        </h2>
        <p className="hero-subtitle">
          Process claim propositions from news clips, documents, web URLs, or direct statements.
        </p>

        <div className="multimodal-paths">
          {/* Path 1: Image */}
          <div className="multimodal-path-card">
            <div className="path-icon-wrapper">
              <ImageIcon size={22} className="text-orange" />
            </div>
            <h3 className="path-title">IMAGE / DOCUMENT ANALYSIS</h3>
            <p className="path-desc">
              RapidOCR extracts text claims from screenshots, news clips, and flyers.
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

          {/* Path 2: URL */}
          <div className="multimodal-path-card">
            <div className="path-icon-wrapper">
              <LinkIcon size={22} color="#38bdf8" />
            </div>
            <h3 className="path-title">URL & WEB ARTICLE VERIFICATION</h3>
            <p className="path-desc">
              Extract context directly from article links and web documents.
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
      </section>

      {/* Section Divider */}
      <div className="section-divider-line" />

      {/* Section 7: Transparent Traceable Verdicts */}
      <section id="transparent" className="landing-section transparent-section">
        <span className="section-kicker">PROVENANCE & INTEGRITY</span>
        <h2 className="huge-heading">
          A VERDICT YOU CAN <span className="text-orange">TRACE.</span>
        </h2>

        <p className="hero-subtitle">
          Every verdict links directly back to its source URL, extracted snippet, and provenance details.
        </p>

        <div className="transparent-chain">
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
      </section>

      {/* Final CTA */}
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

