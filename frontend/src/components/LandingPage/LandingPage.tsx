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
  ChevronLeft,
  ChevronRight,
  Quote,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Database,
  Search,
} from "lucide-react";
import "./landing.css";

interface LandingPageProps {
  onNavigateToAnalyzer: () => void;
}

const quotesData = [
  {
    id: 1,
    source: "WHO",
    quote: "“Misinformation online has the potential to travel further, faster and sometimes deeper than the truth.”",
  },
  {
    id: 2,
    source: "ANTÓNIO GUTERRES · UN",
    quote: "“The spread of hatred and lies online is causing grave harm to our world.”",
  },
  {
    id: 3,
    source: "ANTÓNIO GUTERRES · UN",
    quote: "“When information integrity is targeted, so is democracy — which depends on a shared, fact-based perception of reality.”",
  },
];

export const LandingPage: React.FC<LandingPageProps> = ({ onNavigateToAnalyzer }) => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [activeSection, setActiveSection] = useState("hero");
  const [activeQuoteIndex, setActiveQuoteIndex] = useState(0);
  const [isQuotePaused, setIsQuotePaused] = useState(false);

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

  // Quote carousel autoplay (every 5 seconds, paused on hover/interaction)
  useEffect(() => {
    if (isQuotePaused) return;
    const interval = setInterval(() => {
      setActiveQuoteIndex((prev) => (prev + 1) % quotesData.length);
    }, 5000);
    return () => clearInterval(interval);
  }, [isQuotePaused]);

  // IntersectionObserver for scroll-active progress dot indicator across 5 core sections
  useEffect(() => {
    const sectionIds = ["hero", "evidence", "analyzer", "multimodal", "final-cta"];

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

  const handlePrevQuote = () => {
    setIsQuotePaused(true);
    setActiveQuoteIndex((prev) => (prev - 1 + quotesData.length) % quotesData.length);
  };

  const handleNextQuote = () => {
    setIsQuotePaused(true);
    setActiveQuoteIndex((prev) => (prev + 1) % quotesData.length);
  };

  const handleDotClick = (index: number) => {
    setIsQuotePaused(true);
    setActiveQuoteIndex(index);
  };

  return (
    <div className="landing-root">
      {/* Cinematic Ambient Glow & Noise Overlay */}
      <div className="landing-ambient-glow" />
      <div className="landing-noise-overlay" />

      {/* Minimal Unobtrusive Navbar */}
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
              className={`landing-nav-link ${activeSection === "evidence" ? "active" : ""}`}
              onClick={() => scrollToSection("evidence")}
            >
              Evidence
            </span>
          </li>
          <li>
            <span
              className={`landing-nav-link ${activeSection === "analyzer" ? "active" : ""}`}
              onClick={() => scrollToSection("analyzer")}
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

      {/* Sidebar Progress Indicator (5 Core Sections) */}
      <aside className="landing-scroll-indicator" aria-label="Section navigation">
        {[
          { id: "hero", label: "01 Hero" },
          { id: "evidence", label: "02 Evidence" },
          { id: "analyzer", label: "03 Analyzer" },
          { id: "multimodal", label: "04 Multimodal" },
          { id: "final-cta", label: "05 Verify" },
        ].map((item) => (
          <div
            key={item.id}
            className={`scroll-indicator-dot ${activeSection === item.id ? "active" : ""}`}
            onClick={() => scrollToSection(item.id)}
            title={item.label}
          />
        ))}
      </aside>

      {/* ==================================================
          SECTION 01 — HERO / WHY (EDITORIAL COLLAGE COMPOSITION)
          ================================================== */}
      <section id="hero" className="hero-editorial-section">
        <div className="hero-grid-container">
          {/* Left / Center Oversized Editorial Typography */}
          <div className="hero-masthead-col">
            <div className="hero-editorial-badge">
              <Sparkles size={14} />
              <span>EVIDENCE-GROUNDED VERIFICATION ENGINE</span>
            </div>

            <h1 className="hero-masthead-title">
              VERIFY <br />
              <span className="hero-masthead-accent">WHAT YOU SEE.</span>
            </h1>

            <p className="hero-editorial-sub">
              Information moves faster than verification. Claims spread across feeds and media
              before fact-checking can respond. TruthGuard AI provides transparent,
              evidence-grounded claim verification.
            </p>

            <div className="hero-action-row">
              <button className="editorial-primary-btn" onClick={onNavigateToAnalyzer}>
                <span>ANALYZE A CLAIM</span>
                <ArrowRight size={18} />
              </button>

              <button
                className="editorial-secondary-btn"
                onClick={() => scrollToSection("evidence")}
              >
                <span>EXPLORE EVIDENCE ENGINE</span>
                <ArrowDown size={16} />
              </button>
            </div>
          </div>

          {/* Right / Background Overlapping Editorial Visual Collage */}
          <div className="hero-collage-col">
            <div className="hero-collage-stage">
              {/* Layer 1: Background Source Surface */}
              <div className="collage-surface surface-source">
                <div className="surface-header">
                  <Globe size={14} color="#38bdf8" />
                  <span className="surface-tag">AUTHORITATIVE SOURCE</span>
                </div>
                <div className="surface-body">
                  <span className="source-domain">reuters.com</span>
                  <p className="source-snippet">
                    “Peer-reviewed satellite data confirms historical baseline variance across arctic observations...”
                  </p>
                </div>
              </div>

              {/* Layer 2: Central Dominant Evidence Surface */}
              <div className="collage-surface surface-evidence">
                <div className="surface-header">
                  <Database size={15} color="#f97316" />
                  <span className="surface-tag text-orange">RETRIEVED PASSAGE</span>
                  <span className="score-pill">SIMILARITY 0.94</span>
                </div>
                <div className="surface-body">
                  <p className="evidence-quote-text">
                    “Direct observational telemetry from NASA Climate Monitoring confirms carbon measurement protocols remain uncompromised.”
                  </p>
                  <div className="evidence-meta-bar">
                    <span>BGE-M3 DENSE RETRIEVAL</span>
                    <span className="tier-tag">TIER 1 PRIMARY</span>
                  </div>
                </div>
              </div>

              {/* Layer 3: Narrow Input Claim Strip Crossing Composition */}
              <div className="collage-surface surface-claim-strip">
                <FileText size={15} color="#f97316" />
                <span className="claim-strip-label">CLAIM:</span>
                <span className="claim-strip-text">“NASA secret climate telemetry leaked online”</span>
              </div>

              {/* Layer 4: Verification Badge Extending & Cropped */}
              <div className="collage-surface surface-verdict">
                <div className="verdict-icon-glow">
                  <ShieldAlert size={20} />
                </div>
                <div className="verdict-text-block">
                  <span className="verdict-title">FALSE / MISLEADING</span>
                  <span className="verdict-confidence">CONFIDENCE SCORE 96%</span>
                </div>
              </div>

              {/* Decorative Flow Connectors */}
              <div className="collage-line line-1" />
              <div className="collage-line line-2" />
            </div>
          </div>
        </div>
      </section>

      <div className="editorial-divider" />

      {/* ==================================================
          SECTION 02 — EVIDENCE ENGINE (GIANT LAYERED BOARD)
          ================================================== */}
      <section id="evidence" className="evidence-editorial-section">
        <div className="section-header-block">
          <span className="editorial-kicker">02 / EVIDENCE ENGINE</span>
          <h2 className="giant-title">
            EVIDENCE <br />
            <span className="hero-masthead-accent">BEFORE CONCLUSIONS.</span>
          </h2>
          <p className="editorial-lead">
            We don't rely on black-box assertions. Every verification output is anchored in traceable, primary-source passages scored for semantic relevance.
          </p>
        </div>

        {/* Giant Asymmetric Layered Evidence Board */}
        <div className="evidence-board-stage">
          {/* Underlay Layer: Source Classification */}
          <div className="board-layer layer-source-tier">
            <div className="board-card-header">
              <Sparkles size={15} color="#38bdf8" />
              <span>SOURCE QUALITY TIERING</span>
            </div>
            <div className="tier-pill-row">
              <div className="tier-pill primary">TIER 1 · GOV & ACADEMIC (1.0x)</div>
              <div className="tier-pill secondary">TIER 2 · MAJOR NEWS (0.85x)</div>
              <div className="tier-pill low">TIER 3 · UNVERIFIED (0.5x)</div>
            </div>
          </div>

          {/* Central Highlighted Layer: Retrieved Snippet */}
          <div className="board-layer layer-central-evidence">
            <div className="board-card-header">
              <Search size={16} color="#f97316" />
              <span className="text-orange">PRIMARY RETRIEVED EVIDENCE</span>
              <span className="meta-badge">BGE RANK #1</span>
            </div>
            <blockquote className="board-passage">
              “The official atmospheric measurements published by WHO and NASA confirm zero unverified anomalies in the published quarterly dataset.”
            </blockquote>
            <div className="board-footer">
              <span>PROVENANCE: NASA.GOV / ATMOSPHERIC-REPORTS-2026</span>
              <span className="check-text">
                <CheckCircle2 size={13} color="#22c55e" /> VERIFIED MATCH
              </span>
            </div>
          </div>

          {/* Overlapping Foreground Layer: Semantic Relevance Gate */}
          <div className="board-layer layer-gate-verdict">
            <div className="gate-icon-wrap">
              <AlertTriangle size={18} color="#ef4444" />
            </div>
            <div className="gate-info">
              <span className="gate-title">SEMANTIC RELEVANCE ≠ TRUTH</span>
              <p className="gate-desc">
                High lexical match passages are passed through HuggingFace NLI cross-encoders to ensure true factual entailment rather than topical overlap.
              </p>
            </div>
          </div>
        </div>
      </section>

      <div className="editorial-divider" />

      {/* ==================================================
          SECTION 03 — QUOTE CAROUSEL (CINEMATIC MAGAZINE STAGE)
          ================================================== */}
      <section
        className="quote-magazine-section"
        onMouseEnter={() => setIsQuotePaused(true)}
        onMouseLeave={() => setIsQuotePaused(false)}
      >
        <span className="editorial-kicker text-center">WHY THIS MATTERS</span>

        <div className="magazine-carousel-stage">
          <div className="magazine-ambient-light" />

          {quotesData.map((item, index) => {
            let positionClass = "card-hidden";
            if (index === activeQuoteIndex) {
              positionClass = "card-active";
            } else if (
              index === (activeQuoteIndex - 1 + quotesData.length) % quotesData.length
            ) {
              positionClass = "card-prev";
            } else if (index === (activeQuoteIndex + 1) % quotesData.length) {
              positionClass = "card-next";
            }

            return (
              <div
                key={item.id}
                className={`magazine-quote-card ${positionClass}`}
                onClick={() => handleDotClick(index)}
              >
                <Quote size={48} className="quote-mark-icon" />
                <blockquote className="magazine-quote-body">{item.quote}</blockquote>
                <div className="magazine-quote-source">{item.source}</div>
              </div>
            );
          })}
        </div>

        {/* Carousel Controls */}
        <div className="magazine-carousel-controls">
          <button
            className="magazine-nav-btn"
            onClick={handlePrevQuote}
            aria-label="Previous quote"
          >
            <ChevronLeft size={20} />
          </button>

          <div className="magazine-dots">
            {quotesData.map((item, index) => (
              <span
                key={item.id}
                className={`magazine-dot ${index === activeQuoteIndex ? "active" : ""}`}
                onClick={() => handleDotClick(index)}
              />
            ))}
          </div>

          <button
            className="magazine-nav-btn"
            onClick={handleNextQuote}
            aria-label="Next quote"
          >
            <ChevronRight size={20} />
          </button>
        </div>
      </section>

      <div className="editorial-divider" />

      {/* ==================================================
          SECTION 03 / PRODUCT — ANALYZER SHOWCASE (HERO PRODUCT VISUAL)
          ================================================== */}
      <section id="analyzer" className="analyzer-showcase-section">
        <div className="section-header-block">
          <span className="editorial-kicker">03 / PRODUCT SHOWCASE</span>
          <h2 className="giant-title">
            TRANSPARENT <br />
            <span className="hero-masthead-accent">VERIFICATION INTERFACE.</span>
          </h2>
          <p className="editorial-lead">
            Experience the actual product engine in action — real-time retrieval, source quality analysis, and step-by-step evidence provenance.
          </p>
        </div>

        {/* Hero Product Frame (Occupying ~80% Viewport Width with 3D Perspective) */}
        <div className="hero-analyzer-viewport">
          <div className="analyzer-glow-backdrop" />
          <div className="analyzer-frame-container">
            {/* Top Browser Bar */}
            <div className="analyzer-topbar">
              <div className="topbar-dots">
                <span className="dot dot-red" />
                <span className="dot dot-yellow" />
                <span className="dot dot-green" />
              </div>
              <div className="topbar-url">https://truthguard.ai/analyzer</div>
              <div className="topbar-tag">LIVE ENGINE PREVIEW</div>
            </div>

            {/* Inner Analyzer Preview Body */}
            <div className="analyzer-inner-body">
              {/* Claim Header */}
              <div className="preview-claim-box">
                <span className="preview-label">INPUT PROPOSITION</span>
                <h3 className="preview-claim-heading">
                  “Scientists at WHO confirmed a new airborne pathogen outbreak in North America in 2026.”
                </h3>
              </div>

              {/* Verdict Summary Box */}
              <div className="preview-verdict-box">
                <div className="verdict-row-top">
                  <div className="verdict-badge-red">
                    <ShieldAlert size={18} />
                    <span>FALSE / UNFOUNDED</span>
                  </div>
                  <div className="verdict-score-tag">
                    CONFIDENCE <strong>94%</strong>
                  </div>
                </div>
                <p className="verdict-summary">
                  Official statements from the World Health Organization and CDC confirm no such pathogen outbreak was declared. Primary news agencies report normal seasonal metrics.
                </p>
              </div>

              {/* Evidence Snippets Grid */}
              <div className="preview-evidence-grid">
                <div className="preview-evidence-card">
                  <div className="ev-card-top">
                    <span className="ev-domain">WHO.INT</span>
                    <span className="ev-tier">TIER 1 OFFICIAL</span>
                  </div>
                  <p className="ev-text">
                    “Official WHO Press Release: Statements claiming a new airborne outbreak in 2026 are entirely false...”
                  </p>
                  <div className="ev-meta">SIMILARITY: 0.96 • ENTAILMENT: REFUTES</div>
                </div>

                <div className="preview-evidence-card">
                  <div className="ev-domain-bar">
                    <span className="ev-domain">REUTERS.COM</span>
                    <span className="ev-tier">TIER 2 NEWS</span>
                  </div>
                  <p className="ev-text">
                    “Fact Check: Viral claims of North American pathogen outbreak lack any empirical backing from health authorities.”
                  </p>
                  <div className="ev-meta">SIMILARITY: 0.91 • ENTAILMENT: REFUTES</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="editorial-divider" />

      {/* ==================================================
          SECTION 04 — MULTIMODAL + TRACEABILITY (MEDIA COLLAGE)
          ================================================== */}
      <section id="multimodal" className="multimodal-editorial-section">
        <div className="multimodal-editorial-grid">
          {/* Left / Top Oversized Title Overlapping Visual */}
          <div className="multimodal-title-block">
            <span className="editorial-kicker">04 / MULTIMODAL VERIFICATION</span>
            <h2 className="giant-title">
              VERIFY <br />
              MORE THAN <br />
              <span className="hero-masthead-accent">TEXT.</span>
            </h2>
            <p className="editorial-lead">
              Extract and analyze claim propositions across text articles, screenshots, document flyers, and web URLs with identical evidence rigor.
            </p>

            <button className="editorial-primary-btn mt-6" onClick={onNavigateToAnalyzer}>
              <span>TRY MULTIMODAL ANALYZER</span>
              <ArrowRight size={18} />
            </button>
          </div>

          {/* Right / Overlapping Media Surfaces Collage */}
          <div className="multimodal-collage-stage">
            {/* Layer 1: Image OCR Surface */}
            <div className="media-surface surface-image-ocr">
              <div className="media-surface-header">
                <ImageIcon size={16} className="text-orange" />
                <span>RAPID OCR ENGINE</span>
              </div>
              <div className="ocr-preview-box">
                <span className="ocr-tag">EXTRACTED TEXT FROM IMAGE</span>
                <p className="ocr-text">“Breaking: Government announces emergency curfew starting midnight...”</p>
              </div>
            </div>

            {/* Layer 2: Document Flyer Surface */}
            <div className="media-surface surface-document">
              <div className="media-surface-header">
                <Layers size={16} color="#38bdf8" />
                <span>DOCUMENT / FLYER ANALYSIS</span>
              </div>
              <div className="doc-preview-content">
                <div className="doc-line" />
                <div className="doc-line short" />
                <span className="doc-badge">PDF / FLYER PROVENANCE</span>
              </div>
            </div>

            {/* Layer 3: Web Article URL Surface */}
            <div className="media-surface surface-url-article">
              <div className="media-surface-header">
                <LinkIcon size={16} color="#4ade80" />
                <span>ARTICLE URL RETRIEVAL</span>
              </div>
              <div className="url-preview-bar">
                <span>https://news-archive.org/article/94028</span>
              </div>
            </div>

            {/* Layer 4: Traceability Provenance Chain Overlay */}
            <div className="media-surface surface-provenance-chain">
              <span className="chain-label">TRACEABLE PROVENANCE</span>
              <div className="chain-steps">
                <span className="c-step">INPUT</span>
                <span className="c-arr">→</span>
                <span className="c-step">OCR / PARSE</span>
                <span className="c-arr">→</span>
                <span className="c-step">BGE RETRIEVAL</span>
                <span className="c-arr">→</span>
                <span className="c-step text-orange">EVIDENCE VERDICT</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="editorial-divider" />

      {/* ==================================================
          SECTION 05 — FINAL CTA (POSTER-LIKE CLOSING FRAME)
          ================================================== */}
      <section id="final-cta" className="final-poster-section">
        <div className="poster-ambient-glow" />

        <div className="poster-content">
          <h2 className="poster-title">
            DON'T JUST BELIEVE IT. <br />
            <span className="hero-masthead-accent">VERIFY IT.</span>
          </h2>

          <p className="poster-sub">
            Evidence before conclusions. Fact-checking grounded in transparent primary sources.
          </p>

          <div className="poster-action-group">
            <button className="editorial-primary-btn poster-btn" onClick={onNavigateToAnalyzer}>
              <span>ANALYZE A CLAIM NOW</span>
              <ArrowRight size={20} />
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
