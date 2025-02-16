from app.database.db import get_db
from app.models.user import User
from app.schemas.auth import PasswordResetCheckSchema, PasswordResetSchema
from app.utils.password import hash_password
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import pyotp

router = APIRouter()


@router.post("/password-reset/check", tags=["auth"])
def password_reset_check(
    request: PasswordResetCheckSchema, db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.twofa_secret:
        raise HTTPException(
            status_code=400, detail="2FA is not enabled for this account"
        )
    return {"message": "User exists and 2FA is enabled"}


@router.post("/password-reset/confirm", tags=["auth"])
def password_reset_confirm(request: PasswordResetSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.twofa_secret:
        raise HTTPException(
            status_code=400, detail="2FA is not enabled for this account"
        )
    totp = pyotp.TOTP(user.twofa_secret)
    if not totp.verify(request.totp_code):
        raise HTTPException(status_code=401, detail="Invalid 2FA code")
    user.password = hash_password(request.new_password)
    db.commit()
    return {"message": "Password reset successfully"}
