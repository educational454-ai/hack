"""FastAPI backend application for Evidence-First Misinformation Analyzer (AI-03)."""

import base64
import logging
import os
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.config import config
from core.pipeline import analyze_claim
from core.image_pipeline import analyze_image
from core.schemas import AnalysisResult

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Evidence-First AI Misinformation Analyzer",
    description="Multi-stage evidence-grounded verification API powered by Hugging Face models and BGE-M3.",
    version="1.0.0",
)

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
    claim: Optional[str] = Field(None, min_length=3, description="The textual statement, URL, or claim to verify.")
    image_base64: Optional[str] = Field(None, description="Base64-encoded image string or data URI.")
    image_filename: Optional[str] = Field(None, description="Filename for the uploaded image.")
    question: Optional[str] = Field(None, description="Optional question about the image or claim.")


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
    if req.image_base64:
        try:
            raw_b64 = req.image_base64.strip()
            if "," in raw_b64:
                raw_b64 = raw_b64.split(",", 1)[1]
            image_bytes = base64.b64decode(raw_b64)
            result = analyze_image(
                image_bytes=image_bytes,
                filename=req.image_filename or "uploaded_image.png",
                user_question=req.question or req.claim,
            )
            return result
        except Exception as exc:
            logger.error(f"Image analysis error: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to process image payload.")

    claim_text = (req.claim or "").strip()
    if not claim_text:
        raise HTTPException(status_code=400, detail="Claim text or image payload cannot be empty.")

    try:
        result = analyze_claim(claim_text)
        return result
    except Exception as exc:
        logger.error(f"Pipeline execution error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while processing the verification pipeline.")


@app.post("/api/analyze-image", response_model=AnalysisResult)
async def analyze_image_endpoint(
    file: UploadFile = File(...),
    question: Optional[str] = Form(None),
):
    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        result = analyze_image(
            image_bytes=image_bytes,
            filename=file.filename or "uploaded_image.png",
            user_question=question,
        )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Image upload analysis error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to analyze uploaded image.")
