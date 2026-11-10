import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import storage


@pytest.fixture(autouse=True)
def isolated_db_path(tmp_path, monkeypatch):
    """Подменить путь к базе до любого обращения к ней: боевой digest.db тесты не трогают."""
    db_path = tmp_path / "test_digest.db"
    monkeypatch.setattr(storage, "DB_PATH", db_path)
    return db_path


@pytest.fixture
def temp_db(isolated_db_path):
    """Временная база с созданной таблицей sent_news."""
    storage.init_db()
    return isolated_db_path
