from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def utcnow():
    return datetime.now(timezone.utc)

class GenerationJob(Base):
    __tablename__ = "generation_jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_name: Mapped[str] = mapped_column(String(200))
    course_name: Mapped[str] = mapped_column(String(200))
    issuer_name: Mapped[str] = mapped_column(String(200))
    total: Mapped[int] = mapped_column(Integer, default=0)
    processed: Mapped[int] = mapped_column(Integer, default=0)
    succeeded: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="queued")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    recipients: Mapped[list["RecipientCertificate"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )

class RecipientCertificate(Base):
    __tablename__ = "recipient_certificates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("generation_jobs.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    job: Mapped[GenerationJob] = relationship(back_populates="recipients")
