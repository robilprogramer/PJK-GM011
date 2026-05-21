"""
Core Chatbot Service — SiagaAI
Menggunakan LLMFactory untuk multi-model support.
Primary model: Groq + Llama 3.3 70B
"""

import uuid
import asyncio
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.core.config import settings
from app.core.exceptions import AIServiceError
from app.schemas.chat import ChatRequest, ChatResponse, MessageIntent
from app.schemas.location import WeatherData, EarthquakeData, DisasterRisk

from app.services.ai.llm_factory import llm_factory
from app.services.ai.prompts import (
    SYSTEM_BASE, SYSTEM_EMERGENCY,
    build_realtime_context, build_rag_context,
)
from app.services.ai.intent import detect_intent, check_escalation, get_suggested_actions
from app.services.ai.knowledge_base import knowledge_base
from app.services.weather.bmkg import BMKGService
from app.services.weather.openweather import OpenWeatherService
from app.services.disaster.risk_analyzer import RiskAnalyzer

import structlog

logger = structlog.get_logger()


class ChatbotService:
    """
    Core service chatbot SiagaAI.

    Pipeline per request:
    1. Deteksi intent + cek eskalasi
    2. Fetch data real-time (cuaca + gempa) secara paralel
    3. Analisis risiko bencana
    4. Cari dokumen relevan (RAG)
    5. Build prompt (system + context + history + user message)
    6. Invoke LLM (via factory — model bisa diganti per request)
    7. Return respons + metadata
    """

    def __init__(self):
        self._bmkg = BMKGService()
        self._owm = OpenWeatherService()
        self._risk = RiskAnalyzer()

    async def process(self, request: ChatRequest) -> ChatResponse:
        """Entry point utama chatbot."""
        try:
            # 1. Deteksi intent
            intent = detect_intent(request.message)
            requires_escalation = check_escalation(request.message)

            # 2. Ambil data real-time (paralel jika ada lokasi)
            weather: WeatherData | None = None
            earthquake: EarthquakeData | None = None
            risks: list[DisasterRisk] = []
            overall_risk: str | None = None

            if request.location:
                weather, earthquake, risks, overall_risk = await self._fetch_realtime(
                    request.location.lat, request.location.lng
                )

            # 3. RAG — cari dokumen relevan
            rag_docs = await knowledge_base.search(request.message, n_results=3)

            # 4. Pilih model
            model_name = request.model_name or settings.DEFAULT_MODEL
            llm = llm_factory.get_llm(model_name)

            # 5. Build messages
            messages = self._build_messages(
                request, intent, weather, earthquake,
                risks, overall_risk, rag_docs
            )

            # 6. Invoke LLM
            logger.info(
                "Invoking LLM",
                model=model_name,
                intent=intent,
                session=request.session_id,
            )
            response = await llm.ainvoke(messages)
            reply = response.content

            # 7. Return
            return ChatResponse(
                success=True,
                reply=reply,
                intent=intent,
                session_id=request.session_id,
                model_used=model_name,
                requires_escalation=requires_escalation,
                suggested_actions=get_suggested_actions(intent, overall_risk),
                message_id=str(uuid.uuid4()),
            )

        except AIServiceError:
            raise
        except Exception as e:
            logger.error("Chatbot error", error=str(e))
            raise AIServiceError(f"Gagal memproses pesan: {str(e)}")

    # ─── Private Methods ──────────────────────────────────────────────────────

    async def _fetch_realtime(
        self, lat: float, lng: float
    ) -> tuple[WeatherData | None, EarthquakeData | None, list[DisasterRisk], str | None]:
        """Fetch cuaca + gempa secara paralel, lalu analisis risiko."""
        weather_result, eq_result = await asyncio.gather(
            self._owm.get_current_weather(lat, lng),
            self._bmkg.get_latest_earthquake(),
            return_exceptions=True,
        )

        weather = None if isinstance(weather_result, Exception) else weather_result
        earthquake = None if isinstance(eq_result, Exception) else eq_result

        if isinstance(weather_result, Exception):
            logger.warning("Weather fetch failed", error=str(weather_result))
        if isinstance(eq_result, Exception):
            logger.warning("BMKG fetch failed", error=str(eq_result))

        risks, overall_risk = [], None
        if weather or earthquake:
            w = weather or WeatherData(
                temperature=0, humidity=0, condition="tidak tersedia",
                wind_speed=0, rainfall_1h=0
            )
            e = earthquake or EarthquakeData()
            risks, overall_risk = self._risk.analyze(w, e)

        return weather, earthquake, risks, overall_risk

    def _build_messages(
        self,
        request: ChatRequest,
        intent: MessageIntent,
        weather: WeatherData | None,
        earthquake: EarthquakeData | None,
        risks: list[DisasterRisk],
        overall_risk: str | None,
        rag_docs: list[str],
    ) -> list:
        # Pilih system prompt
        system_text = (
            SYSTEM_EMERGENCY if intent == MessageIntent.emergency else SYSTEM_BASE
        )

        # Injeksikan data real-time
        system_text += build_realtime_context(
            request.location, weather, earthquake, risks, overall_risk
        )

        # Injeksikan RAG
        system_text += build_rag_context(rag_docs)

        messages = [SystemMessage(content=system_text)]

        # History (batasi sesuai config)
        for h in request.history[-settings.LLM_HISTORY_LIMIT:]:
            if h.role == "user":
                messages.append(HumanMessage(content=h.content))
            elif h.role == "assistant":
                messages.append(AIMessage(content=h.content))

        messages.append(HumanMessage(content=request.message))
        return messages
