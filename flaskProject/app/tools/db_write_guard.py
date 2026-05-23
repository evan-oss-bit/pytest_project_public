# -*- coding: utf-8 -*-
import threading
import time

from sqlalchemy.exc import OperationalError

from app.lib.lib_define import db


_SQLITE_WRITE_LOCK = threading.RLock()
_LOCK_STATE = threading.local()


def is_sqlite_engine():
    try:
        return str(db.engine.url.drivername).startswith("sqlite")
    except Exception:
        return False


def guarded_flush(session=None, retries=5, delay=0.2):
    session = session or db.session
    if not is_sqlite_engine():
        return session.flush()
    _acquire_sqlite_write_lock()
    try:
        return _retry_write(session.flush, session, retries, delay)
    except Exception:
        _release_sqlite_write_lock()
        raise


def guarded_commit(session=None, retries=5, delay=0.2):
    session = session or db.session
    if not is_sqlite_engine():
        return session.commit()
    acquired = _acquire_sqlite_write_lock()
    try:
        return _retry_write(session.commit, session, retries, delay)
    finally:
        _release_sqlite_write_lock(force=acquired)


def guarded_rollback(session=None):
    session = session or db.session
    try:
        return session.rollback()
    finally:
        if is_sqlite_engine():
            _release_sqlite_write_lock()


def _acquire_sqlite_write_lock():
    depth = getattr(_LOCK_STATE, "depth", 0)
    if depth == 0:
        _SQLITE_WRITE_LOCK.acquire()
        _LOCK_STATE.depth = 1
        return True
    return False


def _release_sqlite_write_lock(force=False):
    depth = getattr(_LOCK_STATE, "depth", 0)
    if depth <= 0:
        return
    if force:
        _LOCK_STATE.depth = 0
        _SQLITE_WRITE_LOCK.release()
        return
    depth -= 1
    _LOCK_STATE.depth = depth
    if depth == 0:
        _SQLITE_WRITE_LOCK.release()


def _retry_write(func, session, retries, delay):
    last_error = None
    for index in range(retries):
        try:
            return func()
        except OperationalError as exc:
            if "database is locked" not in str(exc).lower():
                raise
            last_error = exc
            try:
                session.rollback()
            except Exception:
                pass
            time.sleep(delay * (index + 1))
    raise last_error
