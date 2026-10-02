import React, { useState, useEffect } from "react";
import { Header } from "./components/Header";
import { ClaimInput } from "./components/ClaimInput";
import { PipelineSteps } from "./components/PipelineSteps";
import { ResultCard } from "./components/ResultCard";
import { LeftSidebar } from "./components/LeftSidebar";
import { RightSidebar } from "./components/RightSidebar";
import { analyzeClaimAPI, analyzeImageAPI } from "./api";
import { AnalysisResult, HistoryItem } from "./types";
import { AlertCircle } from "lucide-react";

const HISTORY_STORAGE_KEY = "misinfo_chat_history";

const LandingPageLazy = React.lazy(() => import("./components/LandingPage/LandingPage"));

export const App: React.FC = () => {
  const [currentPath, setCurrentPath] = useState<string>(() => {
    return window.location.pathname;
  });

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname);
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const navigateTo = (path: string) => {
    window.history.pushState({}, "", path);
    setCurrentPath(path);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const [claim, setClaim] = useState("");
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Initialize last 5 chats from localStorage
  const [history, setHistory] = useState<HistoryItem[]>(() => {
    try {
      const saved = localStorage.getItem(HISTORY_STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          return parsed.slice(0, 5);
        }
      }
    } catch (e) {
      console.error("Failed to read chat history from localStorage", e);
    }
    return [];
  });
  const [activeHistoryId, setActiveHistoryId] = useState<string | null>(null);

  const handleAnalyze = async (claimToAnalyze: string, imageFile?: File | null) => {
    const fileToUse = imageFile !== undefined ? imageFile : selectedImage;
    if (!claimToAnalyze.trim() && !fileToUse) return;

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      let data: AnalysisResult;
      if (fileToUse) {
        data = await analyzeImageAPI(fileToUse, claimToAnalyze);
      } else {
        data = await analyzeClaimAPI(claimToAnalyze);
      }
      setResult(data);

      // Save to chat history (up to last 5 chats)
      const claimTitle =
        claimToAnalyze.trim() ||
        (data.extracted_image_text
          ? `Image: ${data.extracted_image_text.slice(0, 60)}`
          : fileToUse
          ? `Image: ${fileToUse.name}`
          : "Untitled Inquiry");

      const newItem: HistoryItem = {
        id: `${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
        claim: claimTitle,
        timestamp: Date.now(),
        result: data,
      };

      setHistory((prev) => {
        const filtered = prev.filter(
          (item) => item.claim.toLowerCase() !== claimTitle.toLowerCase()
        );
        const updated = [newItem, ...filtered].slice(0, 5);
        try {
          localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(updated));
        } catch (storageErr) {
          console.error("Failed to save history", storageErr);
        }
        return updated;
      });
      setActiveHistoryId(newItem.id);
    } catch (err: any) {
      setError(
        err.message ||
          "Failed to verify claim. Make sure the backend server is running on http://127.0.0.1:8000."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectHistory = (item: HistoryItem) => {
    setActiveHistoryId(item.id);
    setClaim(item.claim);
    setSelectedImage(null);
    setResult(item.result);
    setError(null);
  };

  const handleNewChat = () => {
    setActiveHistoryId(null);
    setClaim("");
    setSelectedImage(null);
    setResult(null);
    setError(null);
    const textarea = document.querySelector(".claim-textarea") as HTMLTextAreaElement;
    textarea?.focus();
  };

  const handleDeleteHistory = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setHistory((prev) => {
      const updated = prev.filter((item) => item.id !== id);
      try {
        localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(updated));
      } catch {}
      return updated;
    });
    if (activeHistoryId === id) {
      setActiveHistoryId(null);
    }
  };

  const handleClearHistory = () => {
    setHistory([]);
    try {
      localStorage.removeItem(HISTORY_STORAGE_KEY);
    } catch {}
    setActiveHistoryId(null);
  };

  // Render Landing Page on '/' (or any non-analyzer route)
  if (currentPath !== "/analyzer") {
    return (
      <React.Suspense fallback={<div style={{ backgroundColor: "#030712", minHeight: "100vh" }} />}>
        <LandingPageLazy onNavigateToAnalyzer={() => navigateTo("/analyzer")} />
      </React.Suspense>
    );
  }

  // Render Analyzer Application on '/analyzer'
  return (
    <div className="app-container">
      <Header onNavigateHome={() => navigateTo("/")} />

      <div className="app-layout">
        <LeftSidebar
          history={history}
          activeHistoryId={activeHistoryId}
          onSelectHistory={handleSelectHistory}
          onNewChat={handleNewChat}
          onDeleteHistory={handleDeleteHistory}
          onClearHistory={handleClearHistory}
        />

        <main className="main-content">
          <ClaimInput
            claim={claim}
            setClaim={setClaim}
            selectedImage={selectedImage}
            setSelectedImage={setSelectedImage}
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
    </div>
  );
};

export default App;
