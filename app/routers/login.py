from fastapi import APIRouter, Depends, HTTPException
from app.schemas import LoginSchema
from app.utils.password import verify_password
from app.models import User
from app.database.db import get_db
from sqlalchemy.orm import Session
from app.auth.token import create_token
from datetime import timedelta

router = APIRouter()


@router.post("/login")
def login(auth: LoginSchema, db: Session = Depends(get_db), remember_me: bool = False):
    user = db.query(User).filter(User.username == auth.username).first()
    if not user or not verify_password(user.password, auth.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    expires_delta = timedelta(days=30) if remember_me else timedelta(hours=2)

    access_token = create_token(
        data={"sub": user.username}, expires_delta=expires_delta
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
    }
