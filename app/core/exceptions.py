from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog

logger = structlog.get_logger()


class SiagaAIException(Exception):
    def __init__(self, message: str, status_code: int = 500, detail: str = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail or message
        super().__init__(self.message)


class ModelNotFoundError(SiagaAIException):
    def __init__(self, model_name: str):
        super().__init__(
            message=f"Model '{model_name}' tidak tersedia atau belum dikonfigurasi",
            status_code=404,
        )


class ModelProviderError(SiagaAIException):
    def __init__(self, provider: str, msg: str):
        super().__init__(
            message=f"Provider '{provider}' error: {msg}",
            status_code=503,
        )


class WeatherServiceError(SiagaAIException):
    def __init__(self, message: str = "Gagal mengambil data cuaca"):
        super().__init__(message=message, status_code=503)


class BMKGServiceError(SiagaAIException):
    def __init__(self, message: str = "Gagal mengambil data BMKG"):
        super().__init__(message=message, status_code=503)


class AIServiceError(SiagaAIException):
    def __init__(self, message: str = "Layanan AI sedang tidak tersedia"):
        super().__init__(message=message, status_code=503)


class SessionNotFoundError(SiagaAIException):
    def __init__(self, session_id: str):
        super().__init__(
            message=f"Sesi '{session_id}' tidak ditemukan",
            status_code=404,
        )


async def siagaai_exception_handler(request: Request, exc: SiagaAIException):
    logger.error("SiagaAI error", path=request.url.path, error=exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.message, "detail": exc.detail},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [{"field": "->".join(str(x) for x in e["loc"]), "message": e["msg"]} for e in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={"success": False, "error": "Validasi request gagal", "detail": errors},
    )


async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error", "detail": str(exc)},
    )
