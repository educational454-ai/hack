import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  ArrowRight,
  ArrowDown,
  Globe,
  FileText,
  Search,
  CheckCircle2,
  AlertTriangle,
  Zap,
  Layers,
  Sparkles,
  Link,
  Image as ImageIcon,
  ExternalLink,
} from "lucide-react";
import "./landing.css";

interface LandingPageProps {
  onNavigateToAnalyzer: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onNavigateToAnalyzer }) => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [activeSection, setActiveSection] = useState("hero");

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

  return (
    <div className="landing-root">
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
              className="landing-nav-link"
              onClick={() => scrollToSection("how-it-works")}
            >
              How It Works
            </span>
          </li>
          <li>
            <span
              className="landing-nav-link"
              onClick={() => scrollToSection("sources")}
            >
              Source Quality
            </span>
          </li>
          <li>
            <span
              className="landing-nav-link"
              onClick={() => scrollToSection("multimodal")}
            >
              Multimodal
            </span>
          </li>
          <li>
            <span className="landing-nav-link" onClick={onNavigateToAnalyzer}>
              Analyzer
            </span>
          </li>
        </ul>

        <button className="landing-nav-cta" onClick={onNavigateToAnalyzer}>
          <span>ANALYZE A CLAIM</span>
          <ArrowRight size={15} />
        </button>
      </nav>

      {/* Sidebar Progress Dots */}
      <aside className="landing-scroll-indicator">
        {[
          "hero",
          "speed",
          "how-it-works",
          "sources",
          "evidence",
          "preview",
          "multimodal",
          "final-cta",
        ].map((id) => (
          <div
            key={id}
            className={`scroll-indicator-dot ${
              activeSection === id ? "active" : ""
            }`}
            onClick={() => scrollToSection(id)}
            title={id}
          />
        ))}
      </aside>

      {/* Hero Section */}
      <section id="hero" className="landing-section hero-section">
        <div className="hero-glow-bg" />

        <div className="hero-badge">
          <Sparkles size={14} />
          <span>Evidence-First Misinformation Analyzer</span>
        </div>

        <h1 className="hero-title">
          VERIFY <span className="hero-title-highlight">WHAT YOU SEE.</span>
        </h1>

        <p className="hero-subtitle">
          AI-powered misinformation analysis built around evidence, source quality,
          semantic relevance, and transparent verification.
        </p>

        <div className="hero-cta-group">
          <button className="primary-btn" onClick={onNavigateToAnalyzer}>
            <span>ANALYZE A CLAIM</span>
            <ArrowRight size={18} />
          </button>

          <button
            className="secondary-btn"
            onClick={() => scrollToSection("speed")}
          >
            <span>EXPLORE HOW IT WORKS</span>
            <ArrowDown size={16} />
          </button>
        </div>

        {/* Hero Abstract Evidence Composition */}
        <div className="hero-composition">
          <div className="composition-node-center">
            <ShieldAlert size={36} />
          </div>

          <div className="composition-card left">
            <FileText size={16} color="#f97316" />
            <span>Extracted Claim Proposition</span>
          </div>

          <div className="composition-card right">
            <Globe size={16} color="#38bdf8" />
            <span>Real-time Web Evidence</span>
          </div>

          <div className="composition-card bottom">
            <CheckCircle2 size={16} color="#22c55e" />
            <span>Truthful Provenance Validation</span>
          </div>
        </div>
      </section>

      {/* Section 1: Information Moves Fast */}
      <section id="speed" className="landing-section speed-section">
        <h2 className="huge-heading">
          INFORMATION MOVES <br />
          <span style={{ color: "#f97316" }}>FASTER THAN VERIFICATION.</span>
        </h2>

        <p className="hero-subtitle" style={{ margin: "0 auto" }}>
          Claims spread across articles, social posts, images, and webpages.
          The challenge is not finding information—it is determining what evidence
          actually supports it.
        </p>

        <div className="speed-grid">
          <div className="speed-card">
            <div className="speed-card-icon">
              <Zap size={22} />
            </div>
            <h3 className="speed-card-title">Unfiltered Velocity</h3>
            <p className="speed-card-desc">
              Millions of unverified statements propagate across digital networks
              every minute before fact-checking occurs.
            </p>
          </div>

          <div className="speed-card">
            <div className="speed-card-icon">
              <AlertTriangle size={22} />
            </div>
            <h3 className="speed-card-title">Contextual Noise</h3>
            <p className="speed-card-desc">
              Manipulated headlines, viral memes, and out-of-context quotes easily
              obscure original factual context.
            </p>
          </div>

          <div className="speed-card">
            <div className="speed-card-icon">
              <Search size={22} />
            </div>
            <h3 className="speed-card-title">Evidence Disconnect</h3>
            <p className="speed-card-desc">
              Traditional search engines surface matching text keywords without
              verifying underlying factual truth probability.
            </p>
          </div>
        </div>
      </section>

      {/* Section 2: Evidence Before Conclusions (Architecture Pipeline) */}
      <section id="how-it-works" className="landing-section pipeline-section">
        <div className="hero-badge">
          <Layers size={14} />
          <span>System Architecture</span>
        </div>

        <h2 className="huge-heading">
          EVIDENCE BEFORE <br />
          <span style={{ color: "#f97316" }}>CONCLUSIONS.</span>
        </h2>

        <p className="hero-subtitle" style={{ margin: "0 auto" }}>
          Every claim passes through a structured 8-stage verification pipeline
          before generating a grounded assessment.
        </p>

        <div className="pipeline-flow">
          {[
            { step: "01", title: "CLAIM INPUT", desc: "Statement, article URL, or uploaded document image" },
            { step: "02", title: "WEB RETRIEVAL", desc: "Multi-engine web search gathering raw web evidence" },
            { step: "03", title: "SOURCE QUALITY", desc: "Domain reputation classification & tier filtering" },
            { step: "04", title: "SEMANTIC RELEVANCE", desc: "BGE-M3 dense vector passage re-ranking" },
            { step: "05", title: "EVIDENCE GATE", desc: "Strict quality threshold filtering weak or noise snippets" },
            { step: "06", title: "AI VERIFICATION", desc: "Hugging Face cross-encoder NLI model inference" },
            { step: "07", title: "PROVENANCE VALIDATION", desc: "Canonical URL normalization & quote link mapping" },
            { step: "08", title: "TRUTHFUL VERDICT", desc: "Score, neutral explanation, and transparent evidence list" },
          ].map((item, idx) => (
            <div
              key={item.step}
              className={`pipeline-item ${idx === 2 || idx === 5 ? "active" : ""}`}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                <span className="pipeline-step-num">{item.step}</span>
                <span className="pipeline-step-title">{item.title}</span>
              </div>
              <span className="pipeline-step-desc">{item.desc}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Section 3: Source Quality */}
      <section id="sources" className="landing-section source-section">
        <h2 className="huge-heading">
          NOT ALL SOURCES <br />
          <span style={{ color: "#38bdf8" }}>CARRY THE SAME WEIGHT.</span>
        </h2>

        <p className="hero-subtitle" style={{ margin: "0 auto" }}>
          Source domain authority is evaluated before evidence passages contribute
          to final verification scores.
        </p>

        <div className="source-layers-grid">
          <div className="source-layer-card primary">
            <span className="source-layer-badge">TIER 1</span>
            <h3 className="source-layer-title">PRIMARY SOURCES</h3>
            <p className="source-layer-desc">
              Official government records, academic archives, peer-reviewed studies,
              and direct primary documentation.
            </p>
          </div>

          <div className="source-layer-card secondary">
            <span className="source-layer-badge">TIER 2</span>
            <h3 className="source-layer-title">SECONDARY REPORTING</h3>
            <p className="source-layer-desc">
              Established news organizations, verified investigative reporting,
              and credible reference publications.
            </p>
          </div>

          <div className="source-layer-card low">
            <span className="source-layer-badge">TIER 3</span>
            <h3 className="source-layer-title">LOW CONFIDENCE</h3>
            <p className="source-layer-desc">
              Unverified personal blogs, automated content feeds, or unknown
              domain reputations filtered by evidence gates.
            </p>
          </div>
        </div>
      </section>

      {/* Section 4: Semantic Relevance vs Truth */}
      <section id="evidence" className="landing-section semantic-section">
        <h2 className="huge-heading">
          RELEVANCE IS <span style={{ color: "#f97316" }}>NOT TRUTH.</span>
        </h2>

        <div className="semantic-box">
          <div className="semantic-quote">
            "Semantic similarity helps identify relevant passages across the web.
            It does not itself determine whether a claim is factual."
          </div>

          <p className="hero-subtitle" style={{ margin: 0 }}>
            Dense vector models (like BGE-M3) locate passages discussing the same topic.
            Cross-encoder inference models then evaluate logical entailment versus
            contradiction to determine factual truth.
          </p>
        </div>
      </section>

      {/* Section 5: Real Analyzer Preview */}
      <section id="preview" className="landing-section showcase-section">
        <div className="hero-badge">
          <Sparkles size={14} />
          <span>Product Showcase</span>
        </div>

        <h2 className="huge-heading">THE ANALYZER IN ACTION</h2>

        <div className="showcase-preview-card">
          <div className="showcase-header">
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <ShieldAlert size={20} color="#f97316" />
              <span style={{ fontWeight: 700, color: "#ffffff" }}>
                Claim Analysis: "India banned UPI in 2025"
              </span>
            </div>
            <span className="showcase-preview-tag">EXAMPLE ANALYSIS</span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
            <div style={{ background: "rgba(30, 41, 59, 0.5)", padding: "1.25rem", borderRadius: "12px" }}>
              <div style={{ fontSize: "0.8rem", color: "#94a3b8", fontWeight: 600, marginBottom: "0.5rem" }}>
                VERDICT
              </div>
              <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "#ef4444" }}>
                🔴 CONTRADICTED
              </div>
              <div style={{ fontSize: "0.85rem", color: "#cbd5e1", marginTop: "0.5rem" }}>
                Verification Confidence: 95.0%
              </div>
            </div>

            <div style={{ background: "rgba(30, 41, 59, 0.5)", padding: "1.25rem", borderRadius: "12px" }}>
              <div style={{ fontSize: "0.8rem", color: "#94a3b8", fontWeight: 600, marginBottom: "0.5rem" }}>
                INDEPENDENT EVIDENCE
              </div>
              <div style={{ fontSize: "0.9rem", color: "#ffffff", fontWeight: 600 }}>
                3 Independent Source Domains
              </div>
              <div style={{ fontSize: "0.8rem", color: "#94a3b8", marginTop: "0.25rem" }}>
                npci.org.in, rbi.org.in, pressinformationbureau.gov.in
              </div>
            </div>
          </div>

          <div style={{ marginTop: "1.5rem", textAlign: "center" }}>
            <button className="primary-btn" onClick={onNavigateToAnalyzer}>
              <span>TRY THE ANALYZER</span>
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
      </section>

      {/* Section 6: Multimodal Inputs */}
      <section id="multimodal" className="landing-section">
        <div style={{ textAlign: "center" }}>
          <h2 className="huge-heading">
            VERIFY MORE <span style={{ color: "#38bdf8" }}>THAN TEXT.</span>
          </h2>
          <p className="hero-subtitle" style={{ margin: "0 auto" }}>
            Native multi-modal input processing for images, documents, URLs, and queries.
          </p>
        </div>

        <div className="multimodal-grid">
          <div className="multimodal-card">
            <h3 className="multimodal-card-title">
              <ImageIcon size={20} color="#f97316" />
              <span>IMAGE ANALYSIS</span>
            </h3>
            <p className="hero-subtitle" style={{ fontSize: "0.9rem", margin: 0 }}>
              RapidOCR extracts claims from news clips, flyers, and memes.
            </p>
            <div className="multimodal-steps">
              <div className="multimodal-step-pill">1. Upload Image / Screenshot</div>
              <div className="multimodal-step-pill">2. RapidOCR Text Extraction</div>
              <div className="multimodal-step-pill">3. Proposition Normalization</div>
              <div className="multimodal-step-pill">4. Web Evidence Verification</div>
            </div>
          </div>

          <div className="multimodal-card">
            <h3 className="multimodal-card-title">
              <Link size={20} color="#38bdf8" />
              <span>URL VERIFICATION</span>
            </h3>
            <p className="hero-subtitle" style={{ fontSize: "0.9rem", margin: 0 }}>
              Extracts context directly from article links and web documents.
            </p>
            <div className="multimodal-steps">
              <div className="multimodal-step-pill">1. Paste Web Article URL</div>
              <div className="multimodal-step-pill">2. Scraping & Context Parsing</div>
              <div className="multimodal-step-pill">3. Independent Web Retrieval</div>
              <div className="multimodal-step-pill">4. Cross-Domain Assessment</div>
            </div>
          </div>
        </div>
      </section>

      {/* Section 7: Transparent Results */}
      <section id="transparent" className="landing-section transparent-section">
        <h2 className="huge-heading">
          A VERDICT YOU CAN <span style={{ color: "#f97316" }}>TRACE.</span>
        </h2>

        <p className="hero-subtitle" style={{ margin: "0 auto" }}>
          Every verdict links directly to its source URL, extracted snippet, and provenance details.
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

      {/* Section 8: Final CTA */}
      <section id="final-cta" className="landing-section final-cta-section">
        <h2 className="final-cta-title">
          DON'T JUST BELIEVE IT. <br />
          <span style={{ color: "#f97316" }}>VERIFY IT.</span>
        </h2>

        <p className="hero-subtitle" style={{ margin: "0 auto 3rem auto" }}>
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
