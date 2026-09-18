"""FastAPI backend application for Evidence-First Misinformation Analyzer (AI-03)."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any

from core.config import config
from core.pipeline import analyze_claim
from core.schemas import AnalysisResult

import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Evidence-First AI Misinformation Analyzer",
    description="Multi-stage evidence-grounded verification API powered by Hugging Face models and BGE-M3.",
    version="1.0.0",
)

import os

# Configure CORS origins for production Vercel frontend and local development
cors_origins_env = os.getenv("ALLOWED_ORIGINS", "").strip()
if cors_origins_env:
    allowed_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
else:
    allowed_origins = [
        "https://hack-xi-red.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    claim: str = Field(..., min_length=3, description="The textual statement or claim to verify.")


class HealthResponse(BaseModel):
    status: str
    hf_token_configured: bool
    llm_model: str
    embedding_model: str


@app.get("/", response_model=Dict[str, str])
def root():
    return {
        "message": "AI-03 Evidence-First Misinformation Analyzer API is running.",
        "docs_url": "/docs",
    }


@app.get("/api/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="healthy",
        hf_token_configured=config.has_hf_token,
        llm_model=config.hf_llm_model,
        embedding_model=config.hf_embedding_model,
    )


@app.post("/api/analyze", response_model=AnalysisResult)
def analyze(req: AnalyzeRequest):
    claim_text = req.claim.strip()
    if not claim_text:
        raise HTTPException(status_code=400, detail="Claim text cannot be empty.")

    try:
        result = analyze_claim(claim_text)
        return result
    except Exception as exc:
        logger.error(f"Pipeline execution error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while processing the verification pipeline.")
