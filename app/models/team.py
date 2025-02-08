from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database.db import Base


class Team(Base):
    __tablename__ = "teams"
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    project = relationship("Project", back_populates="team_members")
    user = relationship("User")
