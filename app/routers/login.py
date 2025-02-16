from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.token import create_token
from app.database.db import get_db
from app.models import User
from app.schemas.auth import LoginSchema
from app.utils.password import verify_password

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
        "message": "You have successfully logged in",
        "token_type": "bearer",
        "access_token": access_token,
        "username": user.username,
        "avatar_id": user.avatar_id,
    }
