import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import storage


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test_digest.db"
    monkeypatch.setattr(storage, "DB_PATH", db_path)
    storage._init_db()
    return db_path
