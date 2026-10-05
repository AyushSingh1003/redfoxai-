import os
import pytest
from database import engine, Base, SessionLocal
from models.domain import *  # ensure all models registered on Base


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Ensure all database tables exist for test runs."""
    Base.metadata.create_all(bind=engine)
    yield
    # We leave SQLite for inspection or clean up if desired
