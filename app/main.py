from pathlib import Path
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, selectinload
from .database import Base, engine, get_db
from .models import GenerationJob, RecipientCertificate
from .schemas import JobCreate, JobResult
from .worker import process_job

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Bulk Certificate Generator", version="1.0.0")

def serialize_job(job: GenerationJob) -> dict:
    recipients = []
    for recipient in job.recipients:
        recipients.append({
            "id": recipient.id,
            "name": recipient.name,
            "email": recipient.email,
            "status": recipient.status,
            "error": recipient.error,
            "certificate_url": (
                f"/api/certificates/{recipient.id}"
                if recipient.status == "succeeded" and recipient.file_path else None
            ),
        })
    return {
        "id": job.id, "event_name": job.event_name,
        "course_name": job.course_name, "issuer_name": job.issuer_name,
        "status": job.status, "total": job.total, "processed": job.processed,
        "succeeded": job.succeeded, "failed": job.failed,
        "progress_percent": round(job.processed / job.total * 100, 2) if job.total else 0,
        "recipients": recipients,
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/jobs", response_model=JobResult, status_code=202)
def create_job(payload: JobCreate, background_tasks: BackgroundTasks,
               db: Session = Depends(get_db)):
    # Pydantic validates the complete payload before this endpoint runs.
    job = GenerationJob(
        event_name=payload.event_name.strip(),
        course_name=payload.course_name.strip(),
        issuer_name=payload.issuer_name.strip(),
        total=len(payload.recipients),
        status="queued",
    )
    for item in payload.recipients:
        job.recipients.append(RecipientCertificate(
            name=item.name.strip(), email=str(item.email), status="pending"
        ))
    db.add(job)
    db.commit()
    db.refresh(job)
    background_tasks.add_task(process_job, job.id)
    db.refresh(job)
    return serialize_job(job)

@app.get("/api/jobs/{job_id}", response_model=JobResult)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(GenerationJob).options(selectinload(GenerationJob.recipients)).filter(
        GenerationJob.id == job_id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")
    return serialize_job(job)

@app.get("/api/certificates/{recipient_id}")
def get_certificate(recipient_id: int, db: Session = Depends(get_db)):
    recipient = db.get(RecipientCertificate, recipient_id)
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient certificate not found")
    if recipient.status != "succeeded" or not recipient.file_path:
        raise HTTPException(status_code=409, detail="Certificate is not available")
    path = Path(recipient.file_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Certificate file is missing")
    return FileResponse(path, media_type="application/pdf", filename=path.name)
