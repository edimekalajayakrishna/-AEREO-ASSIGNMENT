# Bulk Certificate Generator

A FastAPI backend that accepts one bulk request, validates recipients, generates PDF certificates from one predefined template, tracks progress, and serves successful certificates.

## Requirements

- Python 3.10+
- pip

## Setup

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

## Run the API

```bash
uvicorn app.main:app --reload
```

- API docs: http://127.0.0.1:8000/docs
- Health check: `GET http://127.0.0.1:8000/health`
- SQLite database defaults to `./certificates.db`; PDF files default to `./certificates/`.

Optional environment variables:
- `DATABASE_URL`, e.g. `sqlite:///./certificates.db` or a PostgreSQL SQLAlchemy URL.
- `CERTIFICATE_DIR`, output directory for generated PDFs.

## Create a bulk generation job

```bash
curl -X POST http://127.0.0.1:8000/api/jobs ^
  -H "Content-Type: application/json" ^
  -d "{\"event_name\":\"Annual Tech Event\",\"course_name\":\"Python Fundamentals\",\"issuer_name\":\"Example Organization\",\"recipients\":[{\"name\":\"Asha Rao\",\"email\":\"asha@example.com\"},{\"name\":\"Rahul Kumar\",\"email\":\"rahul@example.com\"}]}"
```

On macOS/Linux, replace `^` line continuations with `\`. The API returns HTTP `202 Accepted` and a job ID. The response includes each recipient's current state; background processing may finish before or after the response is received.

Recipient list constraints: 1–1000 recipients per job. Each name must be 1–200 characters and each email must be valid. Missing/invalid fields cause HTTP `422` before a job is created.

## Check progress

```bash
curl http://127.0.0.1:8000/api/jobs/1
```

The response includes:
- `status`: `queued`, `processing`, `completed`, `completed_with_errors`, or `failed`
- `total`, `processed`, `succeeded`, and `failed`
- `progress_percent`
- Per-recipient status, error (when failed), and `certificate_url` (when successful)

## Retrieve a certificate

Use the recipient's ID from the job response/status:

```bash
curl -L http://127.0.0.1:8000/api/certificates/1 --output certificate.pdf
```

The endpoint returns `409 Conflict` if generation has not succeeded yet and `404` if the recipient or output file is missing.

## Run tests

```bash
pytest -q
```

Tests cover job creation, schema validation, progress/status, individual generation failure isolation, and PDF retrieval.

## Design decisions

- **FastAPI + Pydantic:** typed request/response contracts and automatic OpenAPI docs.
- **SQLite + SQLAlchemy:** relational persistence for jobs and individual recipient outcomes. Set `DATABASE_URL` to use another SQLAlchemy-supported relational database.
- **Background processing:** FastAPI `BackgroundTasks` returns quickly instead of holding the client connection open for the whole batch. This is intentionally simple for an interview-sized project. For production or very large batches, move processing to a durable queue (Celery/RQ + Redis/RabbitMQ), use multiple workers, add retry policies, and store PDFs in object storage.
- **Per-recipient failure isolation:** each certificate is handled inside its own `try/except`; a failed recipient is marked failed and remaining recipients continue.
- **Single template:** ReportLab creates landscape A4 PDFs with a fixed layout and recipient/event/course/issuer information.
- **Progress:** persisted counters are updated after each recipient so clients can poll `GET /api/jobs/{job_id}`.
- **Validation:** malformed bulk requests are rejected as a whole with `422`; valid recipients are processed independently. If certificate rendering itself fails for one recipient, other recipients continue.
- **Security/production notes:** add authentication/authorization, rate limiting, retention cleanup, stronger job idempotency, structured logging, and durable task execution before production use.

## API summary

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/jobs` | Submit a bulk generation job |
| `GET` | `/api/jobs/{job_id}` | Read status, progress, and recipient results |
| `GET` | `/api/certificates/{recipient_id}` | Download one generated PDF |
| `GET` | `/health` | Health check |
