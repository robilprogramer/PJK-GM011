from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    # ─── App ──────────────────────────────────────────────────────
    APP_NAME: str = "SiagaAI"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    SECRET_KEY: str = Field(default="dev-secret-change-in-production")

    # ─── CORS ─────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000"])

    # ─── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/siagaai"
    )

    # ─── LLM - Groq (Primary) ─────────────────────────────────────
    GROQ_API_KEY: str = Field(default="")

    # ─── LLM - OpenAI (Opsional) ──────────────────────────────────
    OPENAI_API_KEY: str = Field(default="")

    # ─── LLM - Google Gemini (Opsional) ───────────────────────────
    GEMINI_API_KEY: str = Field(default="")

    # ─── LLM Default Config ───────────────────────────────────────
    DEFAULT_MODEL: str = Field(default="llama-3.3-70b-versatile")
    LLM_MAX_TOKENS: int = 1500
    LLM_TEMPERATURE: float = 0.3
    LLM_HISTORY_LIMIT: int = 10

    # ─── ChromaDB (RAG) ───────────────────────────────────────────
    CHROMA_DB_PATH: str = Field(default="./chroma_db")
    CHROMA_COLLECTION: str = "siagaai_knowledge"

    # ─── OpenWeatherMap ───────────────────────────────────────────
    OWM_API_KEY: str = Field(default="")
    OWM_BASE_URL: str = "https://api.openweathermap.org/data/2.5"

    # ─── BMKG ─────────────────────────────────────────────────────
    BMKG_GEMPA_URL: str = "https://data.bmkg.go.id/DataMKG/TEWS/autogempa.json"
    BMKG_GEMPA_LIST_URL: str = "https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json"
    BMKG_CUACA_URL: str = "https://api.bmkg.go.id/publik/prakiraan-cuaca"

    # ─── HTTP ─────────────────────────────────────────────────────
    HTTP_TIMEOUT: int = 15
    HTTP_RETRIES: int = 3

    # ─── Risk Thresholds ──────────────────────────────────────────
    RAIN_WASPADA_MM: float = 5.0
    RAIN_SIAGA_MM: float = 20.0
    RAIN_AWAS_MM: float = 50.0
    EQ_WASPADA_MAG: float = 4.0
    EQ_SIAGA_MAG: float = 5.5
    EQ_AWAS_MAG: float = 7.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
