import React, { useState } from "react";
import { Analytics } from "@vercel/analytics/react";
import { Header } from "./components/Header";
import { ClaimInput } from "./components/ClaimInput";
import { PipelineSteps } from "./components/PipelineSteps";
import { ResultCard } from "./components/ResultCard";
import { LeftSidebar } from "./components/LeftSidebar";
import { RightSidebar } from "./components/RightSidebar";
import { analyzeClaimAPI } from "./api";
import { AnalysisResult } from "./types";
import { AlertCircle } from "lucide-react";

export const App: React.FC = () => {
  const [claim, setClaim] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (claimToAnalyze: string) => {
    if (!claimToAnalyze.trim()) return;

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await analyzeClaimAPI(claimToAnalyze);
      setResult(data);
    } catch (err: any) {
      setError(
        err.message ||
          "Failed to verify claim. Make sure the backend server is running on http://127.0.0.1:8000."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <Header />

      <div className="app-layout">
        <LeftSidebar />

        <main className="main-content">
          <ClaimInput
            claim={claim}
            setClaim={setClaim}
            onAnalyze={handleAnalyze}
            isLoading={isLoading}
          />

          {error && (
            <div className="error-banner">
              <AlertCircle size={20} />
              <span>{error}</span>
            </div>
          )}

          <PipelineSteps isLoading={isLoading} />

          {result && <ResultCard result={result} />}
        </main>

        <RightSidebar result={result} />
      </div>
      <Analytics />
    </div>
  );
};

export default App;
