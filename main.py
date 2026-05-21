from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.logging import setup_logging
from app.core.exceptions import (
    SiagaAIException, siagaai_exception_handler,
    validation_exception_handler, generic_exception_handler,
)
from app.api.routes import chat, location, escalate, health, models, knowledge
from app.api.routes import ml as ml_route


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await init_db()

    # Auto-load knowledge base
    import os
    if os.path.exists("app/data/disaster_knowledge.json"):
        from app.services.ai.knowledge_base import knowledge_base
        count = knowledge_base.load_from_json("app/data/disaster_knowledge.json")
        print(f"[SiagaAI] Knowledge base: {count} dokumen")

    # Pre-warm ML Model
    try:
        from app.services.ml.flood_predictor import flood_predictor
        flood_predictor.ensure_loaded()
        meta = flood_predictor._metadata
        print(f"[SiagaAI] ML Model loaded — Accuracy: {meta.get('accuracy',0)*100:.1f}%  F1: {meta.get('f1_score_weighted',0):.4f}  v{meta.get('model_version','?')}")
    except Exception as e:
        print(f"[SiagaAI] ML Model warning: {e}")

    yield
    await close_db()


app = FastAPI(
    title="SiagaAI API",
    description=(
        "Backend SiagaAI — AI Chatbot Prediksi Bencana Alam Indonesia.\n\n"
        "**AI Engines:**\n"
        "- Custom ML Model (Random Forest, 99.1% accuracy) untuk prediksi risiko banjir\n"
        "- LLM Multi-model (Groq/Llama 3.3, OpenAI, Gemini) untuk chatbot NLP\n"
        "- RAG (ChromaDB) dengan 42 dokumen knowledge base kebencanaan Indonesia\n\n"
        "**Data Real-time:** BMKG (gempa) + OpenWeatherMap (cuaca)"
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(SiagaAIException, siagaai_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ─── Routes ───────────────────────────────────────────────────
app.include_router(health.router,    prefix="/api/health",    tags=["Health"])
app.include_router(models.router,    prefix="/api/models",    tags=["LLM Models"])
app.include_router(ml_route.router,  prefix="/api/ml",        tags=["ML Model"])
app.include_router(chat.router,      prefix="/api/chat",      tags=["Chat"])
app.include_router(location.router,  prefix="/api/location",  tags=["Location"])
app.include_router(escalate.router,  prefix="/api/escalate",  tags=["Escalation"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge Base"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "app":           settings.APP_NAME,
        "version":       settings.APP_VERSION,
        "status":        "running",
        "docs":          "/docs",
        "default_model": settings.DEFAULT_MODEL,
        "endpoints": {
            "health":    "/api/health",
            "ml_model":  "/api/ml/predict",
            "chat":      "/api/chat/send",
            "location":  "/api/location/status",
            "escalate":  "/api/escalate",
            "knowledge": "/api/knowledge/stats",
        }
    }
