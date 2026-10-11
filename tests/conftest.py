import os
import tempfile
import pytest
from fastapi.testclient import TestClient

@pytest.fixture()
def client(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"
    cert_dir = tmp_path / "certificates"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("CERTIFICATE_DIR", str(cert_dir))

    # Reload modules so each test uses its isolated database and output directory.
    import app.database as database
    import app.models as models
    import app.certificates as certificates
    import app.worker as worker
    import app.main as main
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    database.engine = engine
    database.SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    database.get_db.__globals__["SessionLocal"] = database.SessionLocal
    certificates.OUTPUT_DIR = str(cert_dir)
    worker.SessionLocal = database.SessionLocal
    main.engine = engine
    models.Base.metadata.create_all(bind=engine)
    with TestClient(main.app) as test_client:
        yield test_client
    engine.dispose()
