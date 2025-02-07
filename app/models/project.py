from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.database.db import Base


class Project(Base):
    __tablename__ = "projects"
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    team_members = relationship("Team", back_populates="project")
    todos = relationship("Todo", back_populates="project")
