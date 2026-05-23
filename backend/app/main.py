import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response

# Allow `python backend/app/main.py` or PyCharm "Run main.py" to resolve
# imports from the backend package root without extra terminal parameters.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# 在任何配置读取之前，加载 .env 文件到环境变量
_env_file = BACKEND_DIR / ".env"
if _env_file.exists():
    load_dotenv(_env_file)
    print(f"[config] 已加载 .env: {_env_file}")
else:
    print(f"[config] 警告: 未找到 .env 文件 ({_env_file})")

from app.api.router import api_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Xingling AI Companion API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse(url="/docs", status_code=307)

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon() -> Response:
        return Response(status_code=204)

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "xingling-backend"}

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    os.environ["PYTHONPATH"] = os.pathsep.join(
        [str(BACKEND_DIR), os.environ.get("PYTHONPATH", "")]
    ).strip(os.pathsep)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
