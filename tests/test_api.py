from app.worker import process_job

def payload():
    return {
        "event_name": "Annual Tech Event",
        "course_name": "Python Fundamentals",
        "issuer_name": "Example Organization",
        "recipients": [
            {"name": "Asha Rao", "email": "asha@example.com"},
            {"name": "Rahul Kumar", "email": "rahul@example.com"}
        ],
    }

def test_create_job_and_status_progress_and_retrieval(client):
    response = client.post("/api/jobs", json=payload())
    assert response.status_code == 202
    job = response.json()
    assert job["total"] == 2
    assert job["status"] in {"queued", "processing", "completed"}
    process_job(job["id"])

    status = client.get(f"/api/jobs/{job['id']}")
    assert status.status_code == 200
    data = status.json()
    assert data["processed"] == 2
    assert data["succeeded"] == 2
    assert data["failed"] == 0
    assert data["progress_percent"] == 100

    cert_id = data["recipients"][0]["id"]
    cert = client.get(f"/api/certificates/{cert_id}")
    assert cert.status_code == 200
    assert cert.headers["content-type"] == "application/pdf"
    assert cert.content.startswith(b"%PDF")

def test_input_validation(client):
    bad = payload()
    bad["recipients"][0]["email"] = "not-an-email"
    response = client.post("/api/jobs", json=bad)
    assert response.status_code == 422

def test_missing_job_and_certificate(client):
    assert client.get("/api/jobs/999").status_code == 404
    assert client.get("/api/certificates/999").status_code == 404

def test_individual_generation_failure_does_not_stop_batch(client, monkeypatch):
    import app.worker as worker
    original = worker.generate_certificate
    def flaky(**kwargs):
        if kwargs["recipient_name"] == "Asha Rao":
            raise RuntimeError("simulated PDF error")
        return original(**kwargs)
    monkeypatch.setattr(worker, "generate_certificate", flaky)

    response = client.post("/api/jobs", json=payload())
    job_id = response.json()["id"]
    process_job(job_id)
    data = client.get(f"/api/jobs/{job_id}").json()
    assert data["processed"] == 2
    assert data["failed"] == 1
    assert data["succeeded"] == 1
    assert data["status"] == "completed_with_errors"
    statuses = {r["name"]: r["status"] for r in data["recipients"]}
    assert statuses == {"Asha Rao": "failed", "Rahul Kumar": "succeeded"}
