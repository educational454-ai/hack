import React, { useState, useEffect, useCallback } from "react";
import { Scene3D } from "./Scene3D";
import { Shield, ArrowRight, CheckCircle2 } from "lucide-react";
import "./intro.css";

interface IntroSceneProps {
  onComplete: () => void;
}

const TOTAL_STAGES = 7;

const PIPELINE_STEPS = [
  { id: "claim", label: "CLAIM" },
  { id: "web", label: "WEB EVIDENCE" },
  { id: "source", label: "SOURCE QUALITY" },
  { id: "compare", label: "COMPARISON" },
  { id: "verify", label: "VERIFICATION" },
];

export const IntroScene: React.FC<IntroSceneProps> = ({ onComplete }) => {
  const [stage, setStage] = useState<number>(1);
  const [isExiting, setIsExiting] = useState<boolean>(false);
  const [hasWebGLError, setHasWebGLError] = useState<boolean>(false);
  const [reducedMotion, setReducedMotion] = useState<boolean>(false);
  const [activePipelineIdx, setActivePipelineIdx] = useState<number>(0);

  // Check prefers-reduced-motion
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducedMotion(mediaQuery.matches);

    const handleChange = (e: MediaQueryListEvent) => {
      setReducedMotion(e.matches);
    };
    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  // Discrete Stage Timers (Zero per-frame React state re-renders!)
  useEffect(() => {
    if (isExiting) return;

    // Stage duration timeline schedule (in milliseconds)
    const stageDurations: { [key: number]: number } = {
      1: 4000, // 0-4s: Information Discovery
      2: 5000, // 4-9s: Propagation
      3: 4000, // 9-13s: Signal & Noise
      4: 3000, // 13-16s: Hard Pause ("WHAT SHOULD YOU BELIEVE?")
      5: 6000, // 16-22s: Evidence Transformation
      6: 3000, // 22-25s: Verification Pulse
    };

    const duration = stageDurations[stage];
    if (!duration) return; // Stage 7 is final hold stage

    const timer = setTimeout(() => {
      setStage((prev) => Math.min(prev + 1, TOTAL_STAGES));
    }, duration);

    return () => clearTimeout(timer);
  }, [stage, isExiting]);

  // Stage 5 & 6 Pipeline Step Illumination
  useEffect(() => {
    if (stage === 5 || stage === 6) {
      setActivePipelineIdx(0);
      const interval = setInterval(() => {
        setActivePipelineIdx((prev) => (prev < PIPELINE_STEPS.length - 1 ? prev + 1 : prev));
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [stage]);

  const handleComplete = useCallback(() => {
    if (isExiting) return;
    setIsExiting(true);
    // Smooth transition zoom forward into analyzer
    setTimeout(() => {
      onComplete();
    }, 600);
  }, [isExiting, onComplete]);

  const handleStageSelect = (stageNum: number) => {
    setStage(stageNum);
  };

  // Progress percentage computed directly from discrete stage index
  const progressPercentage = Math.min((stage / TOTAL_STAGES) * 100, 100);

  return (
    <div className={`intro-overlay ${isExiting ? "exiting" : ""}`}>
      {/* 3D WebGL Background Scene */}
      {!hasWebGLError ? (
        <Scene3D
          stage={stage}
          isExiting={isExiting}
          reducedMotion={reducedMotion}
          onWebGLError={() => setHasWebGLError(true)}
        />
      ) : (
        /* CSS Gradient & Wireframe Fallback if WebGL fails */
        <div className="intro-css-fallback">
          <div className="fallback-globe-grid" />
        </div>
      )}

      {/* UI Content Layer */}
      <div className="intro-ui-layer">
        {/* Top Header Bar */}
        <header className="intro-header-bar">
          <div className="intro-brand-badge">
            <Shield size={15} />
            <span>AI Misinformation Analyzer</span>
          </div>

          <button className="intro-skip-btn" onClick={handleComplete}>
            <span>{stage === TOTAL_STAGES ? "Get Started" : "Skip Intro"}</span>
            <ArrowRight size={14} />
          </button>
        </header>

        {/* Central Stage Content Container */}
        <div className="intro-stage-container">
          {/* Scene 01: Information Discovery (0-4s) */}
          {stage === 1 && (
            <div className="intro-text-wrapper stage-fade-in">
              <h2 className="intro-stage-title">INFORMATION SURROUNDS US</h2>
              <p className="intro-stage-subtitle">
                Signals, statements, and sources move through connected global networks.
              </p>
            </div>
          )}

          {/* Scene 02: Propagation (4-9s) */}
          {stage === 2 && (
            <div className="intro-text-wrapper stage-fade-in">
              <h2 className="intro-stage-title">Propagation Across Networks</h2>
              <p className="intro-stage-subtitle">
                A single claim rapidly spreads, branches out, and amplifies across connected nodes.
              </p>
            </div>
          )}

          {/* Scene 03: Signal & Noise (9-13s) */}
          {stage === 3 && (
            <div className="intro-text-wrapper stage-fade-in">
              <h2 className="intro-stage-title">Signal & Noise Converge</h2>
              <p className="intro-stage-subtitle">
                Unverified headlines, emotional context, and noise obscure original facts.
              </p>
              <div className="intro-noise-fragments">
                <div className="intro-noise-tag">BREAKING...</div>
                <div className="intro-noise-tag">VIRAL...</div>
                <div className="intro-noise-tag">JUST IN...</div>
                <div className="intro-noise-tag">SHOCKING...</div>
                <div className="intro-noise-tag">100% TRUE...</div>
              </div>
            </div>
          )}

          {/* Scene 04: Hard Pause / Freeze (13-16s) */}
          {stage === 4 && (
            <div className="intro-text-wrapper freeze-fade-in">
              <h2 className="intro-freeze-title">WHAT SHOULD YOU BELIEVE?</h2>
              <p className="intro-freeze-subtitle">
                Without objective evidence and source analysis, truth becomes impossible to discern.
              </p>
            </div>
          )}

          {/* Scene 05 & 06: Evidence Transformation & Verification (16-25s) */}
          {(stage === 5 || stage === 6) && (
            <div className="intro-text-wrapper stage-fade-in">
              <h2 className="intro-stage-title">Evidence-First Verification</h2>
              <p className="intro-stage-subtitle">
                Transforming unverified claims into grounded, multi-source evidence analysis.
              </p>
              <div className="intro-pipeline-preview">
                {PIPELINE_STEPS.map((step, idx) => (
                  <React.Fragment key={step.id}>
                    <div className={`intro-pipeline-step ${idx <= activePipelineIdx ? "active" : ""}`}>
                      {idx <= activePipelineIdx && <CheckCircle2 size={14} />}
                      <span>{step.label}</span>
                    </div>
                    {idx < PIPELINE_STEPS.length - 1 && <span className="intro-pipeline-arrow">→</span>}
                  </React.Fragment>
                ))}
              </div>
            </div>
          )}

          {/* Scene 07: Product Reveal (25s+) */}
          {stage === 7 && (
            <div className="intro-reveal-card card-fade-in">
              <h1 className="intro-reveal-title">AI MISINFORMATION ANALYZER</h1>
              <p className="intro-reveal-sub">"Evidence before conclusions."</p>

              <button className="intro-get-started-btn" onClick={handleComplete}>
                <span>GET STARTED</span>
                <ArrowRight size={20} className="arrow-icon" />
              </button>
            </div>
          )}
        </div>

        {/* Bottom Footer Progress Bar & Stage Dots */}
        <footer className="intro-footer-bar">
          <div className="intro-stages-nav">
            {Array.from({ length: TOTAL_STAGES }).map((_, idx) => {
              const stageNum = idx + 1;
              return (
                <button
                  key={stageNum}
                  className={`intro-stage-dot ${stage === stageNum ? "active" : ""}`}
                  onClick={() => handleStageSelect(stageNum)}
                  title={`Stage ${stageNum}`}
                />
              );
            })}
          </div>

          <div className="intro-progress-track">
            <div
              className="intro-progress-bar"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </footer>
      </div>
    </div>
  );
};

export default IntroScene;
