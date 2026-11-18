"""Composition root: dependencies are assembled here and replaceable in tests."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .agent import AgentService, BasicContextSource, EmptyKnowledgeRetriever, MockModelProvider
from .api import create_router
from .config import Settings
from .domain import AppError, ModelProvider
from .repository import ChatRepository
from .service import ChatService


def create_app(settings: Settings | None = None, model: ModelProvider | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    repository = ChatRepository(settings.database_path)
    agent = AgentService(model or MockModelProvider(), BasicContextSource(), EmptyKnowledgeRetriever())
    service = ChatService(repository, agent, settings.history_limit)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        repository.initialize()
        yield

    app = FastAPI(title="Luna Heart Local Development API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.allowed_origins),
                       allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

    @app.exception_handler(AppError)
    async def application_error(request: Request, exc: AppError):
        return JSONResponse(status_code=exc.status,
                            content={"error": {"code": exc.code, "message": exc.message}})

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"error": {
            "code": "invalid_request", "message": "请检查输入格式，消息须为 1 至 4000 字"}})

    app.include_router(create_router(repository, service))
    return app


app = create_app()
