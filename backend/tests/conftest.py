"""
Test configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.models.models import User, Lead

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_user(db):
    user = User(
        email="test@example.com",
        hashed_password="$2b$12$test_hash",  # pre-hashed "password"
        name="Test User",
        company="Test Company",
        plan="pro",
        leads_quota=100,
        leads_used=0
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user):
    return create_access_token({"sub": str(test_user.id)})


@pytest.fixture
def authorized_client(client, auth_token):
    client.headers = {"Authorization": f"Bearer {auth_token}"}
    return client


@pytest.fixture
def test_lead(db, test_user):
    lead = Lead(
        user_id=test_user.id,
        name="John Doe",
        email="john@example.com",
        company="Acme Corp",
        title="CEO",
        status="new",
        ai_score=75
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@pytest.fixture
def multiple_leads(db, test_user):
    leads = []
    for i in range(10):
        lead = Lead(
            user_id=test_user.id,
            name=f"Lead {i}",
            email=f"lead{i}@example.com",
            company=f"Company {i}",
            status="new" if i < 5 else "contacted",
            ai_score=50 + i * 5
        )
        db.add(lead)
        leads.append(lead)
    db.commit()
    for lead in leads:
        db.refresh(lead)
    return leads
