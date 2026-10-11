from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import GenerationJob, RecipientCertificate
from .certificates import generate_certificate

def process_job(job_id: int) -> None:
    """Process recipients independently; one bad certificate does not stop the batch."""
    db: Session = SessionLocal()
    try:
        job = db.get(GenerationJob, job_id)
        if job is None:
            return
        job.status = "processing"
        db.commit()

        recipient_ids = [r.id for r in job.recipients]
        for recipient_id in recipient_ids:
            recipient = db.get(RecipientCertificate, recipient_id)
            if recipient is None or recipient.status != "pending":
                continue
            recipient.status = "processing"
            db.commit()
            try:
                path = generate_certificate(
                    recipient_name=recipient.name,
                    event_name=job.event_name,
                    course_name=job.course_name,
                    issuer_name=job.issuer_name,
                    job_id=job.id,
                    recipient_id=recipient.id,
                )
                recipient.file_path = path
                recipient.status = "succeeded"
                recipient.error = None
                job.succeeded += 1
            except Exception as exc:
                recipient.status = "failed"
                recipient.error = f"{type(exc).__name__}: {str(exc)[:500]}"
                job.failed += 1
            finally:
                job.processed += 1
                db.commit()

        job.status = "completed" if job.failed == 0 else (
            "completed_with_errors" if job.succeeded else "failed"
        )
        db.commit()
    except Exception:
        db.rollback()
        job = db.get(GenerationJob, job_id)
        if job:
            job.status = "failed"
            db.commit()
    finally:
        db.close()
