import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.api.routes import router
from app.monitoring.cost_tracker import init_db
from app.monitoring.metrics import HTTP_REQUEST_DURATION, HTTP_REQUESTS_TOTAL


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
        ).inc()
        HTTP_REQUEST_DURATION.labels(endpoint=request.url.path).observe(duration)
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Agent IA Autonome", version="1.0.0", lifespan=lifespan)
app.add_middleware(MetricsMiddleware)
app.include_router(router)
