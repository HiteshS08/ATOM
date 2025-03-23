from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.exceptions import HTTPException

# from .faststream import init_fastream_router
from app.api import router
from .config import settings
from .exception_handler import exception_exception_handler
from .middleware import CorrelationIdMiddleware, LoggingMiddleware


def add_middlewares(app_: FastAPI) -> None:
    app_.add_middleware(LoggingMiddleware)
    app_.add_middleware(CorrelationIdMiddleware)


def create_app() -> FastAPI:
    app_ = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        # lifespan=lifespan,
        docs_url=None if settings.ENVIRONMENT == "production" else "/docs",
        redoc_url=None if settings.ENVIRONMENT == "production" else "/redoc",
    )

    # Add Exception handler
    app_.add_exception_handler(Exception, exception_exception_handler)
    app_.add_exception_handler(HTTPException, exception_exception_handler)

    app_.add_middleware(LoggingMiddleware)
    app_.add_middleware(CorrelationIdMiddleware)
    # init_routers(app_=app_)

    app_.include_router(router)
    if settings.FASTSTREAM_ENABLE:
        from app.worker.faststream import faststream_router
        app_.include_router(faststream_router)

    return app_


app = create_app()
Instrumentator().instrument(app).expose(app)
