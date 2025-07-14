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
)
from app.routers import router

app = FastAPI()

origins = ["https://todoboard.net", "http://localhost:3000"]

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
