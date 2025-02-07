from fastapi import FastAPI
from app.routers import router
from app.database.db import engine, Base
from app.models import (
    user,
    todo,
    team,
    project,
)  # Import all models to ensure they are registered
from app.auth.token import TokenManager

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(router)


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
