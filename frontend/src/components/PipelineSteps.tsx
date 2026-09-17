import React, { useEffect, useState } from "react";
import { CheckCircle2, Clock } from "lucide-react";

interface PipelineStepsProps {
  isLoading: boolean;
}

const STEPS = [
  { id: 1, label: "Claim Classifier" },
  { id: 2, label: "Web Retrieval" },
  { id: 3, label: "Source Tiering" },
  { id: 4, label: "BGE-M3 Semantic Ranker" },
  { id: 5, label: "Hugging Face LLM Reasoning" },
];

export const PipelineSteps: React.FC<PipelineStepsProps> = ({ isLoading }) => {
  const [currentStep, setCurrentStep] = useState(1);

  useEffect(() => {
    if (!isLoading) {
      setCurrentStep(1);
      return;
    }

    // Step through the visual stages while waiting for backend
    const intervals = [
      setTimeout(() => setCurrentStep(2), 1200),
      setTimeout(() => setCurrentStep(3), 3500),
      setTimeout(() => setCurrentStep(4), 6500),
      setTimeout(() => setCurrentStep(5), 9500),
    ];

    return () => intervals.forEach(clearTimeout);
  }, [isLoading]);

  if (!isLoading) return null;

  return (
    <div className="pipeline-stepper">
      {STEPS.map((step) => {
        const isCompleted = currentStep > step.id;
        const isActive = currentStep === step.id;

        return (
          <div
            key={step.id}
            className={`step-item ${isCompleted ? "completed" : ""} ${
              isActive ? "active" : ""
            }`}
          >
            <div className="step-circle">
              {isCompleted ? (
                <CheckCircle2 size={16} />
              ) : isActive ? (
                <Clock size={16} />
              ) : (
                step.id
              )}
            </div>
            <span>{step.label}</span>
          </div>
        );
      })}
    </div>
  );
};
