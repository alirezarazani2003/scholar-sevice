from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base   # ایمپورت Base از database.py

class ScholarProfile(Base):
    __tablename__ = "scholar_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    affiliation = Column(String)
    email = Column(String)

    h_index_all = Column(Integer, default=0)
    h_index_recent = Column(Integer, default=0)
    i10_index_all = Column(Integer, default=0)
    i10_index_recent = Column(Integer, default=0)
    citations_all = Column(Integer, default=0)
    citations_recent = Column(Integer, default=0)

    updated_at = Column(DateTime, default=datetime.utcnow)

    articles = relationship("Article", back_populates="profile", cascade="all, delete-orphan")

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("scholar_profiles.id"), nullable=False)

    title = Column(String, nullable=False)
    link = Column(String)
    year = Column(String)
    citations = Column(Integer, default=0)

    profile = relationship("ScholarProfile", back_populates="articles")
