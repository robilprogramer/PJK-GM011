"""
LLM Factory — SiagaAI Multi-Model Support
==========================================
Mendukung:
  - Groq Cloud  : llama-3.3-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b-32768
  - OpenAI      : gpt-4o-mini, gpt-3.5-turbo
  - Google Gemini: gemini-1.5-flash, gemini-2.0-flash

Cara pakai:
    from app.services.ai.llm_factory import llm_factory
    llm = llm_factory.get_llm("llama-3.3-70b-versatile")
"""

from dataclasses import dataclass, field
from typing import Any
from app.core.config import settings
from app.core.exceptions import ModelNotFoundError, ModelProviderError
import structlog

logger = structlog.get_logger()


# ─── Model Registry ───────────────────────────────────────────────────────────

@dataclass
class ModelInfo:
    model_id: str           # ID yang dikirim ke API provider
    display_name: str       # Nama tampilan untuk UI
    provider: str           # groq | openai | gemini
    context_window: int     # Konteks maksimal (token)
    is_free: bool           # Apakah tersedia gratis
    is_active: bool         # Apakah aktif (butuh API key)
    description: str        # Deskripsi singkat
    tags: list[str] = field(default_factory=list)


MODEL_REGISTRY: dict[str, ModelInfo] = {
    # ── Groq / Llama ────────────────────────────────────────────
    "llama-3.3-70b-versatile": ModelInfo(
        model_id="llama-3.3-70b-versatile",
        display_name="Llama 3.3 70B",
        provider="groq",
        context_window=128000,
        is_free=True,
        is_active=True,
        description="Model Llama terbaru dari Meta, akurasi tinggi & Bahasa Indonesia bagus. Direkomendasikan.",
        tags=["recommended", "groq", "llama", "free"],
    ),
    "llama-3.1-8b-instant": ModelInfo(
        model_id="llama-3.1-8b-instant",
        display_name="Llama 3.1 8B (Cepat)",
        provider="groq",
        context_window=131072,
        is_free=True,
        is_active=True,
        description="Model Llama kecil, respons sangat cepat. Cocok jika butuh latensi rendah.",
        tags=["fast", "groq", "llama", "free"],
    ),
    "mixtral-8x7b-32768": ModelInfo(
        model_id="mixtral-8x7b-32768",
        display_name="Mixtral 8x7B",
        provider="groq",
        context_window=32768,
        is_free=True,
        is_active=True,
        description="Model Mixtral MoE dari Mistral AI via Groq. Bagus untuk instruksi panjang.",
        tags=["groq", "mixtral", "free"],
    ),
    "llama-3.1-70b-versatile": ModelInfo(
        model_id="llama-3.1-70b-versatile",
        display_name="Llama 3.1 70B",
        provider="groq",
        context_window=128000,
        is_free=True,
        is_active=True,
        description="Llama 3.1 70B — versi sebelumnya, stabil dan handal.",
        tags=["groq", "llama", "free"],
    ),
    # ── OpenAI ──────────────────────────────────────────────────
    "gpt-4o-mini": ModelInfo(
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini",
        provider="openai",
        context_window=128000,
        is_free=False,
        is_active=bool(settings.OPENAI_API_KEY),
        description="GPT-4o Mini dari OpenAI. Akurasi sangat tinggi, berbayar per token.",
        tags=["openai", "paid"],
    ),
    "gpt-3.5-turbo": ModelInfo(
        model_id="gpt-3.5-turbo",
        display_name="GPT-3.5 Turbo",
        provider="openai",
        context_window=16385,
        is_free=False,
        is_active=bool(settings.OPENAI_API_KEY),
        description="GPT-3.5 Turbo — model OpenAI yang lebih murah.",
        tags=["openai", "paid"],
    ),
    # ── Google Gemini ────────────────────────────────────────────
    "gemini-1.5-flash": ModelInfo(
        model_id="gemini-1.5-flash",
        display_name="Gemini 1.5 Flash",
        provider="gemini",
        context_window=1000000,
        is_free=True,
        is_active=bool(settings.GEMINI_API_KEY),
        description="Gemini 1.5 Flash dari Google. Context window sangat besar, gratis.",
        tags=["gemini", "google", "free"],
    ),
    "gemini-2.0-flash": ModelInfo(
        model_id="gemini-2.0-flash",
        display_name="Gemini 2.0 Flash",
        provider="gemini",
        context_window=1000000,
        is_free=True,
        is_active=bool(settings.GEMINI_API_KEY),
        description="Gemini 2.0 Flash — versi terbaru Gemini, lebih cepat dan akurat.",
        tags=["gemini", "google", "free", "latest"],
    ),
}


# ─── Factory ──────────────────────────────────────────────────────────────────

class LLMFactory:
    """
    Factory untuk membuat instance LLM berdasarkan nama model.
    Mendukung Groq, OpenAI, dan Google Gemini.
    """

    def get_llm(
        self,
        model_name: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> Any:
        """
        Buat dan kembalikan instance LLM.

        Args:
            model_name: Nama model. Default: settings.DEFAULT_MODEL
            temperature: Override temperature. Default: settings.LLM_TEMPERATURE
            max_tokens: Override max tokens. Default: settings.LLM_MAX_TOKENS

        Returns:
            BaseChatModel instance (LangChain compatible)

        Raises:
            ModelNotFoundError: jika model tidak ada di registry
            ModelProviderError: jika API key tidak tersedia atau provider error
        """
        name = model_name or settings.DEFAULT_MODEL
        temp = temperature if temperature is not None else settings.LLM_TEMPERATURE
        tokens = max_tokens or settings.LLM_MAX_TOKENS

        if name not in MODEL_REGISTRY:
            raise ModelNotFoundError(name)

        info = MODEL_REGISTRY[name]

        logger.info("Creating LLM", model=name, provider=info.provider)

        if info.provider == "groq":
            return self._create_groq(name, info, temp, tokens)
        elif info.provider == "openai":
            return self._create_openai(name, info, temp, tokens)
        elif info.provider == "gemini":
            return self._create_gemini(name, info, temp, tokens)
        else:
            raise ModelNotFoundError(name)

    def _create_groq(self, name: str, info: ModelInfo, temp: float, tokens: int):
        if not settings.GROQ_API_KEY:
            raise ModelProviderError("groq", "GROQ_API_KEY belum diset di .env")
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                model=info.model_id,
                temperature=temp,
                max_tokens=tokens,
                api_key=settings.GROQ_API_KEY,
            )
        except ImportError:
            raise ModelProviderError("groq", "Install: pip install langchain-groq")
        except Exception as e:
            raise ModelProviderError("groq", str(e))

    def _create_openai(self, name: str, info: ModelInfo, temp: float, tokens: int):
        if not settings.OPENAI_API_KEY:
            raise ModelProviderError("openai", "OPENAI_API_KEY belum diset di .env")
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=info.model_id,
                temperature=temp,
                max_tokens=tokens,
                api_key=settings.OPENAI_API_KEY,
            )
        except ImportError:
            raise ModelProviderError("openai", "Install: pip install langchain-openai")
        except Exception as e:
            raise ModelProviderError("openai", str(e))

    def _create_gemini(self, name: str, info: ModelInfo, temp: float, tokens: int):
        if not settings.GEMINI_API_KEY:
            raise ModelProviderError("gemini", "GEMINI_API_KEY belum diset di .env")
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=info.model_id,
                temperature=temp,
                max_output_tokens=tokens,
                google_api_key=settings.GEMINI_API_KEY,
            )
        except ImportError:
            raise ModelProviderError("gemini", "Install: pip install langchain-google-genai")
        except Exception as e:
            raise ModelProviderError("gemini", str(e))

    def list_models(self, only_active: bool = False) -> list[ModelInfo]:
        """Daftar semua model yang tersedia."""
        models = list(MODEL_REGISTRY.values())
        if only_active:
            models = [m for m in models if m.is_active]
        return models

    def get_model_info(self, model_name: str) -> ModelInfo:
        if model_name not in MODEL_REGISTRY:
            raise ModelNotFoundError(model_name)
        return MODEL_REGISTRY[model_name]

    def is_available(self, model_name: str) -> bool:
        info = MODEL_REGISTRY.get(model_name)
        if not info:
            return False
        return info.is_active


# ─── Singleton ────────────────────────────────────────────────────────────────
llm_factory = LLMFactory()
