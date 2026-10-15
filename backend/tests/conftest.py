"""Pytest fixtures."""
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
import app.models  # noqa: F401


@pytest.fixture(scope="function")
def test_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db(test_engine):
    Session = sessionmaker(bind=test_engine)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()