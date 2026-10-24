from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .container import Container, build_container
from .infrastructure.config import Settings
from .presentation.api.error_handlers import register_error_handlers
from .presentation.api.routes import router


def create_app(container: Container | None = None) -> FastAPI:
    app = FastAPI(title="Lab 2FA - Step-Up Auth + Prefect")
    app.state.container = container or build_container(Settings.from_env())
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    register_error_handlers(app)
    app.include_router(router)
    return app


app = create_app()
