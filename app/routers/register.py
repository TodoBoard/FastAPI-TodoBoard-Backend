from fastapi import APIRouter
from app.schemas import RegisterSchema

router = APIRouter()


@router.post("/register")
def register(auth: RegisterSchema):
    pass
