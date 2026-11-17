import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

load_dotenv()

import rate_limit
from database import get_db
from main import app
from models import Base, User
from security import hash_password

TEST_DB = f"{os.getenv('POSTGRES_DB')}_test"
assert TEST_DB.endswith("_test"), "Las pruebas solo pueden usar una base _test"

test_engine = create_engine(
    URL.create(
        "postgresql+psycopg",
        username=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host="127.0.0.1",
        port=5432,
        database=TEST_DB,
    ),
    pool_pre_ping=True,
)
TestSession = sessionmaker(bind=test_engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def base_limpia():
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    rate_limit._fallos.clear()
    rate_limit._bloqueados.clear()

    db = TestSession()
    db.add(
        User(
            username="admin_test",
            hashed_password=hash_password("ClaveAdmin123"),
            role="admin",
        )
    )
    db.add(
        User(
            username="tecnico_test",
            hashed_password=hash_password("ClaveTecnico123"),
            role="tecnico",
        )
    )
    db.commit()
    db.close()
    yield