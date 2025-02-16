import pyotp
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth.token import get_current_user
from app.database.db import get_db
from app.schemas.auth import TwoFASetupResponse, TwoFARequest
from app.models.user import User

router = APIRouter()


@router.get("/2fa/setup", response_model=TwoFASetupResponse, tags=["2FA"])
def twofa_setup(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if current_user.twofa_secret is not None:
        raise HTTPException(status_code=400, detail="2FA is already enabled")
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=current_user.username, issuer_name="TODO APP"
    )
    current_user.pending_twofa_secret = secret
    db.commit()
    return TwoFASetupResponse(secret=secret, provisioning_uri=provisioning_uri)


@router.post("/2fa/enable", tags=["2FA"])
def twofa_enable(
    request: TwoFARequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.twofa_secret is not None:
        raise HTTPException(status_code=400, detail="2FA is already enabled")
    if not current_user.pending_twofa_secret:
        raise HTTPException(status_code=400, detail="2FA setup not initiated")
    totp = pyotp.TOTP(current_user.pending_twofa_secret)
    if not totp.verify(request.totp_code):
        raise HTTPException(status_code=401, detail="Invalid 2FA code")
    current_user.twofa_secret = current_user.pending_twofa_secret
    current_user.pending_twofa_secret = None
    db.commit()
    return {"message": "2FA enabled successfully"}


@router.post("/2fa/disable", tags=["2FA"])
def twofa_disable(
    request: TwoFARequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.twofa_secret:
        raise HTTPException(status_code=400, detail="2FA is not enabled")
    totp = pyotp.TOTP(current_user.twofa_secret)
    if not totp.verify(request.totp_code):
        raise HTTPException(status_code=401, detail="Invalid 2FA code")
    current_user.twofa_secret = None
    current_user.pending_twofa_secret = None
    db.commit()
    return {"message": "2FA disabled successfully"}
