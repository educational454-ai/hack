import React, { useState, useEffect, useCallback } from "react";
import { Scene3D } from "./Scene3D";
import { Shield, ArrowRight, CheckCircle2 } from "lucide-react";
import "./intro.css";

interface IntroSceneProps {
  onComplete: () => void;
}

const STAGE_DURATION_MS = 5000; // 5 seconds per stage
const TOTAL_STAGES = 6;

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

  // Stage timer loop
  useEffect(() => {
    if (stage >= TOTAL_STAGES || isExiting) return;

    const timer = setTimeout(() => {
      setStage((prev) => Math.min(prev + 1, TOTAL_STAGES));
    }, STAGE_DURATION_MS);

    return () => clearTimeout(timer);
  }, [stage, isExiting]);

  // Sequentially illuminate pipeline steps during Stage 5
  useEffect(() => {
    if (stage === 5) {
      setActivePipelineIdx(0);
      const interval = setInterval(() => {
        setActivePipelineIdx((prev) => (prev < PIPELINE_STEPS.length - 1 ? prev + 1 : prev));
      }, 900);
      return () => clearInterval(interval);
    }
  }, [stage]);

  const handleComplete = useCallback(() => {
    if (isExiting) return;
    setIsExiting(true);
    // Smooth exit zoom/fade transition before calling parent callback
    setTimeout(() => {
      onComplete();
    }, 700);
  }, [isExiting, onComplete]);

  const handleStageSelect = (stageNum: number) => {
    setStage(stageNum);
  };

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
        {/* Top Header */}
        <header className="intro-header-bar">
          <div className="intro-brand-badge">
            <Shield size={16} />
            <span>AI Misinformation Analyzer</span>
          </div>

          <button className="intro-skip-btn" onClick={handleComplete}>
            <span>{stage === TOTAL_STAGES ? "Get Started" : "Skip Intro"}</span>
            <ArrowRight size={14} />
          </button>
        </header>

        {/* Central Stage Content */}
        <div className="intro-stage-container">
          {stage === 1 && (
            <>
              <h2 className="intro-stage-title">Information Surrounds Us</h2>
              <p className="intro-stage-subtitle">
                Millions of signals, statements, and sources flow across global networks every second.
              </p>
            </>
          )}

          {stage === 2 && (
            <>
              <h2 className="intro-stage-title">Propagation Across Networks</h2>
              <p className="intro-stage-subtitle">
                A single claim rapidly spreads, branches out, and amplifies across connected nodes.
              </p>
            </>
          )}

          {stage === 3 && (
            <>
              <h2 className="intro-stage-title">Signal & Noise Converge</h2>
              <p className="intro-stage-subtitle">
                Unverified headlines, emotional context, and noise obscure original facts.
              </p>
              <div className="intro-noise-fragments">
                <div className="intro-noise-tag">"BREAKING..."</div>
                <div className="intro-noise-tag">"SCIENTISTS CONFIRM..."</div>
                <div className="intro-noise-tag">"SHOCKING NEWS..."</div>
                <div className="intro-noise-tag">"100% TRUE..."</div>
              </div>
            </>
          )}

          {stage === 4 && (
            <>
              <h2 className="intro-stage-title">WHAT SHOULD YOU BELIEVE?</h2>
              <p className="intro-stage-subtitle">
                Without objective evidence and source analysis, truth becomes impossible to discern.
              </p>
            </>
          )}

          {stage === 5 && (
            <>
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
            </>
          )}

          {stage === 6 && (
            <div className="intro-reveal-card">
              <h1 className="intro-reveal-title">AI MISINFORMATION ANALYZER</h1>
              <p className="intro-reveal-sub">"Evidence before conclusions."</p>

              <button className="intro-get-started-btn" onClick={handleComplete}>
                <span>GET STARTED</span>
                <ArrowRight size={20} />
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
