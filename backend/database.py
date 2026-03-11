"""
Database Models - Vietnamese Talent Platform
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./talent_platform.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    full_name_vi = Column(String(100))
    phone = Column(String(20), unique=True, index=True)
    email = Column(String(100), index=True)
    password_hash = Column(String(256))
    avatar_url = Column(String(500))
    nationality = Column(String(50), default="Vietnamese")
    gender = Column(String(10))
    birth_date = Column(String(20))
    visa_type = Column(String(50))
    arc_number = Column(String(50))
    education = Column(String(50))
    education_detail = Column(Text)
    work_experience_years = Column(Integer, default=0)
    work_experience = Column(JSON)
    skills = Column(JSON)
    chinese_level = Column(String(20))
    english_level = Column(String(20))
    other_languages = Column(String(200))
    location = Column(String(100))
    preferred_job_type = Column(String(100))
    preferred_industry = Column(String(100))
    expected_salary_min = Column(Integer)
    expected_salary_max = Column(Integer)
    available_date = Column(String(20))
    resume_url = Column(String(500))
    certificates = Column(JSON)
    telegram_id = Column(String(50), unique=True, index=True)
    telegram_username = Column(String(100))
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    applications = relationship("Application", back_populates="candidate")


class Employer(Base):
    __tablename__ = "employers"
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(200), nullable=False)
    company_name_vi = Column(String(200))
    contact_person = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100), unique=True, index=True)
    password_hash = Column(String(256))
    logo_url = Column(String(500))
    industry = Column(String(100))
    company_size = Column(String(50))
    location = Column(String(200))
    description_zh = Column(Text)
    description_vi = Column(Text)
    website = Column(String(200))
    tax_id = Column(String(50))
    verified = Column(Boolean, default=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    jobs = relationship("Job", back_populates="employer")


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    employer_id = Column(Integer, ForeignKey("employers.id"), nullable=False)
    title_zh = Column(String(200), nullable=False)
    title_vi = Column(String(200))
    description_zh = Column(Text)
    description_vi = Column(Text)
    requirements_zh = Column(Text)
    requirements_vi = Column(Text)
    job_type = Column(String(50))
    industry = Column(String(100))
    location = Column(String(200))
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    salary_type = Column(String(20), default="monthly")
    benefits_zh = Column(Text)
    benefits_vi = Column(Text)
    provides_housing = Column(Boolean, default=False)
    provides_meals = Column(Boolean, default=False)
    provides_transport = Column(Boolean, default=False)
    chinese_level_required = Column(String(20))
    education_required = Column(String(50))
    experience_required = Column(Integer, default=0)
    visa_types_accepted = Column(JSON)
    headcount = Column(Integer, default=1)
    deadline = Column(String(20))
    status = Column(String(20), default="open")
    views = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    employer = relationship("Employer", back_populates="jobs")
    applications = relationship("Application", back_populates="job")


class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    cover_letter = Column(Text)
    status = Column(String(30), default="applied")
    notes = Column(Text)
    applied_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    candidate = relationship("Candidate", back_populates="applications")
    job = relationship("Job", back_populates="applications")


class FacebookPost(Base):
    __tablename__ = "facebook_posts"
    id = Column(Integer, primary_key=True, index=True)
    content_zh = Column(Text)
    content_vi = Column(Text)
    post_type = Column(String(50))
    related_job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    scheduled_at = Column(DateTime)
    posted_at = Column(DateTime)
    platform = Column(String(50))
    status = Column(String(20), default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
