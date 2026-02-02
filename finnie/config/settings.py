"""Configuration management for FinnIE application."""

import os
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class OpenAIConfig(BaseModel):
    """OpenAI API configuration."""
    api_key: str
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 1000


class MarketDataConfig(BaseModel):
    """Market data API configuration."""
    alpha_vantage_key: Optional[str] = None
    yfinance_enabled: bool = True


class RAGConfig(BaseModel):
    """RAG configuration."""
    faiss_index_path: str = "/app/faiss_data"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    top_k_results: int = 5
    chunk_size: int = 512
    chunk_overlap: int = 50


class ObservabilityConfig(BaseModel):
    """Observability configuration."""
    phoenix_host: str = "phoenix"
    phoenix_port: int = 6006
    otel_endpoint: str = "http://phoenix:4317"
    enable_tracing: bool = True


class CacheConfig(BaseModel):
    """Cache configuration."""
    ttl: int = 3600
    rate_limit_calls: int = 60
    rate_limit_period: int = 60


class AppConfig(BaseModel):
    """Main application configuration."""
    app_name: str = "FinnIE"
    app_version: str = "1.0.0"
    log_level: str = "INFO"
    
    openai: OpenAIConfig
    market_data: MarketDataConfig
    rag: RAGConfig
    observability: ObservabilityConfig
    cache: CacheConfig


def load_config() -> AppConfig:
    """Load application configuration from environment variables."""
    return AppConfig(
        app_name=os.getenv("APP_NAME", "FinnIE"),
        app_version=os.getenv("APP_VERSION", "1.0.0"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        openai=OpenAIConfig(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "1000")),
        ),
        market_data=MarketDataConfig(
            alpha_vantage_key=os.getenv("ALPHA_VANTAGE_API_KEY"),
            yfinance_enabled=os.getenv("YFINANCE_ENABLED", "true").lower() == "true",
        ),
        rag=RAGConfig(
            faiss_index_path=os.getenv("FAISS_INDEX_PATH", "/app/faiss_data"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
            top_k_results=int(os.getenv("TOP_K_RESULTS", "5")),
        ),
        observability=ObservabilityConfig(
            phoenix_host=os.getenv("PHOENIX_HOST", "phoenix"),
            phoenix_port=int(os.getenv("PHOENIX_PORT", "6006")),
            otel_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://phoenix:4317"),
        ),
        cache=CacheConfig(
            ttl=int(os.getenv("CACHE_TTL", "3600")),
            rate_limit_calls=int(os.getenv("RATE_LIMIT_CALLS", "60")),
            rate_limit_period=int(os.getenv("RATE_LIMIT_PERIOD", "60")),
        ),
    )


# Global config instance
config = load_config()
