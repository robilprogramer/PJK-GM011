from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.ai.chatbot import ChatbotService
from app.services.ai.knowledge_base import KnowledgeBaseService, knowledge_base
from app.services.ai.llm_factory import LLMFactory, llm_factory
from app.services.weather.bmkg import BMKGService
from app.services.weather.openweather import OpenWeatherService
from app.services.location.geocoder import GeocoderService
from app.services.disaster.risk_analyzer import RiskAnalyzer
from functools import lru_cache


@lru_cache()
def get_chatbot_service() -> ChatbotService:
    return ChatbotService()


@lru_cache()
def get_bmkg_service() -> BMKGService:
    return BMKGService()


@lru_cache()
def get_owm_service() -> OpenWeatherService:
    return OpenWeatherService()


@lru_cache()
def get_geocoder_service() -> GeocoderService:
    return GeocoderService()


@lru_cache()
def get_risk_analyzer() -> RiskAnalyzer:
    return RiskAnalyzer()


def get_knowledge_base() -> KnowledgeBaseService:
    return knowledge_base


def get_llm_factory() -> LLMFactory:
    return llm_factory
