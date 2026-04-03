from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.monitoring.cost_tracker import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Agent IA Autonome", version="1.0.0", lifespan=lifespan)
app.include_router(router)
