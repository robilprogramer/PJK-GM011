"""
SiagaAI Backend — main.py
==========================
FastAPI app dengan ML model (Random Forest) yang diload saat startup.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog
import logging

# Setup logging minimal
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = structlog.get_logger()


# ─── Lifespan: load model saat server start ───────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──
    print("\n" + "="*55)
    print("  SiagaAI Backend — Starting up")
    print("="*55)

    # Load ML Model
    try:
        from app.services.ml.flood_predictor import flood_predictor
        flood_predictor.ensure_loaded()
        meta = flood_predictor._metadata
        print(f"  ✓ ML Model loaded")
        print(f"    Version  : {meta.get('model_version','?')}")
        print(f"    Accuracy : {meta.get('accuracy',0)*100:.1f}%")
        print(f"    F1-Score : {meta.get('f1_score_weighted',0):.4f}")
        print(f"    Features : {len(flood_predictor._model.feature_importances_)}")
    except Exception as e:
        print(f"  ✗ ML Model load failed: {e}")

    print("="*55 + "\n")

    yield  # ← server berjalan di sini

    # ── SHUTDOWN ──
    print("\n[SiagaAI] Shutting down...")


# ─── App ──────────────────────────────────────────────────────
app = FastAPI(
    title="SiagaAI ML Backend",
    description=(
        "Backend SiagaAI: Custom ML Model (Random Forest) prediksi risiko banjir "
        "dari data historis 47 kota Indonesia. Accuracy 99.1%, F1 0.9915."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # ganti ke domain spesifik di production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ───────────────────────────────────────────────────
from app.api.routes.ml import router as ml_router
app.include_router(ml_router, prefix="/api/ml")


# ─── Root ─────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {
        "app":     "SiagaAI ML Backend",
        "version": "1.0.0",
        "status":  "running",
        "docs":    "/docs",
        "endpoints": {
            "predict":      "POST /api/ml/predict",
            "predict_auto": "POST /api/ml/predict-auto",
            "batch":        "POST /api/ml/batch",
            "model_info":   "GET  /api/ml/model-info",
            "health":       "GET  /api/ml/health",
        },
    }
