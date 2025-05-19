import pytest
from peewee import SqliteDatabase

from clipbarcode.database import proxy
from clipbarcode.models import AppSettings, Leitura


# Fixture to create an in-memory test database (session scope)
@pytest.fixture(scope="session")
def test_database():
    """Fixture to create an in-memory SQLite database for testing."""

    # Initialize an in-memory SQLite database
    test_db = SqliteDatabase(":memory:")

    # Bind the database to your models
    proxy.initialize(test_db)

    # Create tables
    test_db.connect()
    test_db.create_tables([Leitura, AppSettings])  # Add all your models here

    yield test_db

    # Cleanup (optional for in-memory, but good practice)
    test_db.close()


# Fixture to ensure a clean database state for each test (function scope)
@pytest.fixture(scope="function")
def db(test_database):
    """Fixture to ensure a clean database state for each test."""

    for model in [Leitura, AppSettings]:
        model.delete().execute()

    yield test_database
