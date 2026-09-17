"""Configuration management for the Evidence-First Misinformation Analyzer."""

import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


@dataclass
class Config:
    @property
    def hf_token(self) -> str:
        load_dotenv(BASE_DIR / ".env")
        return os.getenv("HF_TOKEN", "").strip()

    @property
    def hf_llm_model(self) -> str:
        load_dotenv(BASE_DIR / ".env")
        return os.getenv("HF_LLM_MODEL", "Qwen/Qwen2.5-72B-Instruct").strip()

    @property
    def hf_embedding_model(self) -> str:
        load_dotenv(BASE_DIR / ".env")
        return os.getenv("HF_EMBEDDING_MODEL", "BAAI/bge-m3").strip()

    @property
    def max_search_results(self) -> int:
        return int(os.getenv("MAX_SEARCH_RESULTS", "5"))

    @property
    def top_k_evidence(self) -> int:
        return int(os.getenv("TOP_K_EVIDENCE", "4"))

    @property
    def http_timeout(self) -> float:
        return float(os.getenv("HTTP_TIMEOUT", "6.0"))

    @property
    def allow_mock_fallback(self) -> bool:
        return os.getenv("ALLOW_MOCK_FALLBACK", "true").lower() in ("true", "1", "yes")

    @property
    def low_memory_mode(self) -> bool:
        return os.getenv("LOW_MEMORY_MODE", "true").lower() in ("true", "1", "yes")

    @property
    def has_hf_token(self) -> bool:
        return bool(self.hf_token and len(self.hf_token) > 5)


config = Config()


def reload_config() -> Config:
    global config
    load_dotenv(BASE_DIR / ".env", override=True)
    config = Config()
    return config

