"""
Vietnam Talent Platform - Backend API
"""
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from datetime import datetime
import os

from database import get_db, init_db, Candidate, Employer, Job, Application, FacebookPost
from translator import Translator, quick_translate

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

app = FastAPI(
    title="Vietnam Talent Platform API",
    description="Vietnamese Talent Platform API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

translator = Translator()


@app.on_event("startup")
def startup():
    init_db()
    print("Database initialized")


@app.post("/api/candidates/register")
async def register_candidate(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    existing = db.query(Candidate).filter(Candidate.phone == data.get("phone")).first()
    if existing:
        raise HTTPException(status_code=400, detail="Phone already registered")
    candidate = Candidate(
        full_name=data.get("full_name", ""),
        full_name_vi=data.get("full_name_vi", ""),
        phone=data.get("phone", ""),
        email=data.get("email", ""),
        gender=data.get("gender", ""),
        birth_date=data.get("birth_date", ""),
        visa_type=data.get("visa_type", ""),
        education=data.get("education", ""),
        work_experience_years=data.get("work_experience_years", 0),
        work_experience=data.get("work_experience", []),
        skills=data.get("skills", []),
        chinese_level=data.get("chinese_level", ""),
        english_level=data.get("english_level", ""),
        location=data.get("location", ""),
        preferred_job_type=data.get("preferred_job_type", ""),
        preferred_industry=data.get("preferred_industry", ""),
        expected_salary_min=data.get("expected_salary_min"),
        expected_salary_max=data.get("expected_salary_max"),
        telegram_id=data.get("telegram_id"),
        telegram_username=data.get("telegram_username"),
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return {"success": True, "message": "Registration successful!", "candidate_id": candidate.id}


@app.get("/api/candidates")
async def list_candidates(
    location: Optional[str] = None,
    industry: Optional[str] = None,
    chinese_level: Optional[str] = None,
    page: int = 1, limit: int = 20,
    db: Session = Depends(get_db)
):
    query = db.query(Candidate).filter(Candidate.status == "active")
    if location:
        query = query.filter(Candidate.location.contains(location))
    if industry:
        query = query.filter(Candidate.preferred_industry.contains(industry))
    if chinese_level:
        query = query.filter(Candidate.chinese_level == chinese_level)
    total = query.count()
    candidates = query.offset((page - 1) * limit).limit(limit).all()
    return {
        "total": total, "page": page,
        "candidates": [
            {"id": c.id, "full_name": c.full_name, "education": c.education,
             "work_experience_years": c.work_experience_years, "chinese_level": c.chinese_level,
             "location": c.location, "preferred_job_type": c.preferred_job_type,
             "skills": c.skills, "created_at": str(c.created_at)}
            for c in candidates
        ]
    }


@app.get("/api/candidates/{candidate_id}")
async def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return {
        "id": candidate.id, "full_name": candidate.full_name,
        "phone": candidate.phone, "email": candidate.email,
        "gender": candidate.gender, "visa_type": candidate.visa_type,
        "education": candidate.education,
        "work_experience_years": candidate.work_experience_years,
        "skills": candidate.skills, "chinese_level": candidate.chinese_level,
        "location": candidate.location, "preferred_job_type": candidate.preferred_job_type,
        "created_at": str(candidate.created_at),
    }


@app.post("/api/employers/register")
async def register_employer(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    existing = db.query(Employer).filter(Employer.email == data.get("email")).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    employer = Employer(
        company_name=data.get("company_name", ""),
        contact_person=data.get("contact_person", ""),
        phone=data.get("phone", ""),
        email=data.get("email", ""),
        industry=data.get("industry", ""),
        company_size=data.get("company_size", ""),
        location=data.get("location", ""),
        description_zh=data.get("description_zh", ""),
        website=data.get("website", ""),
        tax_id=data.get("tax_id", ""),
    )
    db.add(employer)
    db.commit()
    db.refresh(employer)
    return {"success": True, "employer_id": employer.id}


@app.post("/api/jobs")
async def create_job(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    translated = await translator.translate_job(data)
    job = Job(
        employer_id=data.get("employer_id"),
        title_zh=data.get("title_zh", ""),
        title_vi=translated.get("title_vi", ""),
        description_zh=data.get("description_zh", ""),
        description_vi=translated.get("description_vi", ""),
        requirements_zh=data.get("requirements_zh", ""),
        requirements_vi=translated.get("requirements_vi", ""),
        job_type=data.get("job_type", "full-time"),
        industry=data.get("industry", ""),
        location=data.get("location", ""),
        salary_min=data.get("salary_min"),
        salary_max=data.get("salary_max"),
        salary_type=data.get("salary_type", "monthly"),
        benefits_zh=data.get("benefits_zh", ""),
        benefits_vi=translated.get("benefits_vi", ""),
        provides_housing=data.get("provides_housing", False),
        provides_meals=data.get("provides_meals", False),
        provides_transport=data.get("provides_transport", False),
        chinese_level_required=data.get("chinese_level_required", ""),
        education_required=data.get("education_required", ""),
        experience_required=data.get("experience_required", 0),
        visa_types_accepted=data.get("visa_types_accepted", []),
        headcount=data.get("headcount", 1),
        deadline=data.get("deadline", ""),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return {"success": True, "job_id": job.id, "translated_title": job.title_vi}


@app.get("/api/jobs")
async def list_jobs(
    location: Optional[str] = None, industry: Optional[str] = None,
    job_type: Optional[str] = None, keyword: Optional[str] = None,
    lang: str = "vi", page: int = 1, limit: int = 20,
    db: Session = Depends(get_db)
):
    query = db.query(Job).filter(Job.status == "open")
    if location:
        query = query.filter(Job.location.contains(location))
    if industry:
        query = query.filter(Job.industry.contains(industry))
    if job_type:
        query = query.filter(Job.job_type == job_type)
    if keyword:
        if lang == "vi":
            query = query.filter(or_(Job.title_vi.contains(keyword), Job.description_vi.contains(keyword)))
        else:
            query = query.filter(or_(Job.title_zh.contains(keyword), Job.description_zh.contains(keyword)))
    total = query.count()
    jobs = query.order_by(Job.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return {
        "total": total, "page": page,
        "jobs": [
            {"id": j.id, "title": j.title_vi if lang == "vi" else j.title_zh,
             "title_zh": j.title_zh, "title_vi": j.title_vi,
             "location": j.location, "salary_min": j.salary_min, "salary_max": j.salary_max,
             "job_type": j.job_type, "industry": j.industry,
             "provides_housing": j.provides_housing, "provides_meals": j.provides_meals,
             "company_name": j.employer.company_name if j.employer else "",
             "created_at": str(j.created_at)}
            for j in jobs
        ]
    }


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: int, lang: str = "vi", db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.views = (job.views or 0) + 1
    db.commit()
    return {
        "id": job.id, "title": job.title_vi if lang == "vi" else job.title_zh,
        "description": job.description_vi if lang == "vi" else job.description_zh,
        "requirements": job.requirements_vi if lang == "vi" else job.requirements_zh,
        "location": job.location, "salary_min": job.salary_min, "salary_max": job.salary_max,
        "job_type": job.job_type, "provides_housing": job.provides_housing,
        "provides_meals": job.provides_meals, "headcount": job.headcount,
        "views": job.views, "created_at": str(job.created_at),
    }


@app.post("/api/applications")
async def apply_job(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    existing = db.query(Application).filter(
        Application.candidate_id == data.get("candidate_id"),
        Application.job_id == data.get("job_id")
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already applied")
    application = Application(
        candidate_id=data.get("candidate_id"),
        job_id=data.get("job_id"),
        cover_letter=data.get("cover_letter", ""),
    )
    db.add(application)
    db.commit()
    return {"success": True, "message": "Application submitted!"}


@app.post("/api/translate")
async def translate_text(request: Request):
    data = await request.json()
    text = data.get("text", "")
    source = data.get("source", "zh-TW")
    target = data.get("target", "vi")
    result = await translator.translate(text, source, target)
    return {"original": text, "translated": result}


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    return {
        "total_candidates": db.query(Candidate).filter(Candidate.status == "active").count(),
        "total_employers": db.query(Employer).filter(Employer.status == "active").count(),
        "total_jobs": db.query(Job).filter(Job.status == "open").count(),
        "total_applications": db.query(Application).count(),
    }


@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    return {"ok": True}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Vietnam Talent Platform API is running", "version": "1.0.0"}


if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def serve_homepage():
        index_path = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse(content="<h1>VietTalent Taiwan</h1>")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
