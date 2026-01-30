import pytest

from app.core.db import Database


def test_get_session_before_init_raises_error():
    db = Database("sqlite:///:memory:")
    with pytest.raises(RuntimeError, match="Database not initialized"):
        db.get_session()


def test_init_is_idempotent():
    db = Database("sqlite:///:memory:")
    db.init()
    engine = db.engine
    db.init()
    assert db.engine is engine


def test_dispose_resets_state():
    db = Database("sqlite:///:memory:")
    db.init()
    db.dispose()
    assert db.engine is None
    assert db.session_factory is None
