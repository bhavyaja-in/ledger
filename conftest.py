import os

import pytest


@pytest.fixture(autouse=True, scope="session")
def protect_production_db():
    prod_db = "financial_data.db"
    if os.path.exists(prod_db):
        os.chmod(prod_db, 0o444)  # Make file read-only for all users
