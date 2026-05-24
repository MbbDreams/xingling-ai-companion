import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

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

    # CORS 中间件必须在最前面
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=600,  # 预检请求缓存 10 分钟
    )

    # 全局异常处理 - 捕获请求验证错误
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """捕获 Pydantic 验证错误，返回详细的错误信息"""
        errors = []
        for error in exc.errors():
            errors.append({
                "loc": error.get("loc", []),
                "msg": error.get("msg", ""),
                "type": error.get("type", "")
            })
        print(f"[Validation Error] {request.method} {request.url}: {errors}")
        return JSONResponse(
            status_code=400,
            content={
                "detail": "请求参数验证失败",
                "errors": errors
            }
        )

    # 全局异常处理 - 捕获 HTTP 异常
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        print(f"[HTTP Error] {request.method} {request.url}: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    # 请求日志中间件 - 跳过 OPTIONS 请求，不读取 body
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """记录所有请求（跳过 OPTIONS）"""
        # 跳过 OPTIONS 预检请求，让 CORS 中间件处理
        if request.method == "OPTIONS":
            return await call_next(request)
        
        print(f"[Request] {request.method} {request.url}")
        response = await call_next(request)
        print(f"[Response] {request.method} {request.url} - {response.status_code}")
        return response

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
