from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.database.db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True)
    username = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    todos = relationship("Todo", back_populates="user")
    team_members = relationship("Team", back_populates="user")
