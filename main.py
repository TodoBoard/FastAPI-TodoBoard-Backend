import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.db import Base, engine
from app.migrations.migration_runner import run_migrations
from app.models import (
    invite,
    notification,
    project,
    team,
    todo,
    user,
    user_notification,
    user_project_sorting,
    attachment,
)
from app.routers import router
from app.utils import storage


async def storage_maintenance_loop():
    """Purges deleted attachments every 15 min, reconciles R2 with the DB daily."""
    last_full = 0.0
    while True:
        full = time.time() - last_full > 24 * 3600
        await asyncio.to_thread(storage.run_maintenance, full)
        if full:
            last_full = time.time()
        await asyncio.sleep(15 * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(storage_maintenance_loop()) if storage.is_configured() else None
    yield
    if task:
        task.cancel()


app = FastAPI(lifespan=lifespan)

origins = ["https://todoboard.net", "https://www.todoboard.net"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

run_migrations()

app.include_router(router)


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
