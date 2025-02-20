from pydantic import BaseModel


class Form(BaseModel):
    title: str
    contact: str
    message: str
    stars: int
