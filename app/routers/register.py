from fastapi import APIRouter, Depends, HTTPException
from app.schemas.auth import RegisterSchema
from app.models import User
from app.database.db import get_db
from sqlalchemy.orm import Session
from app.auth.token import create_token
from app.utils.password import hash_password
from uuid import uuid4
import random

router = APIRouter()


@router.post("/register", status_code=201)
async def register(auth: RegisterSchema, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == auth.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    avatar_id = random.randint(1, 20)
    new_user = User(
        id=str(uuid4()),
        username=auth.username,
        password=hash_password(auth.password),
        avatar_id=avatar_id,
    )
    access_token = create_token(data={"sub": new_user.username})
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {
            "message": "You have successfully registered",
            "token_type": "bearer",
            "access_token": access_token,
            "username": new_user.username,
            "avatar_id": new_user.avatar_id,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to register user")
