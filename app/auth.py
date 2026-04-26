import os
import re
import bcrypt
import logging
from typing import Optional

import psycopg2
from psycopg2.pool import ThreadedConnectionPool

from events import emit_event

logger = logging.getLogger(__name__)

_pool: Optional[ThreadedConnectionPool] = None

_SPECIAL_CHARS = r'[!@#$%^&*()\-_=+\[\]{};:\'",.<>?/\\|`~]'

_VIOLATION_KO: dict[str, str] = {
    "invalid_length_short": "비밀번호는 8자 이상이어야 합니다.",
    "invalid_length_long":  "비밀번호는 15자 이하여야 합니다.",
    "missing_uppercase":    "대문자를 포함해야 합니다.",
    "missing_lowercase":    "소문자를 포함해야 합니다.",
    "missing_number":       "숫자를 포함해야 합니다.",
    "missing_special_char": "특수문자를 포함해야 합니다.",
}


def _get_pool() -> ThreadedConnectionPool:
    global _pool
    if _pool is None:
        _pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            dbname=os.getenv("POSTGRES_DB", "events_db"),
            user=os.getenv("POSTGRES_USER", "admin"),
            password=os.getenv("POSTGRES_PASSWORD", "secret"),
        )
    return _pool


def validate_password(password: str) -> list[str]:
    if len(password) < 8:
        return ["invalid_length_short"]
    if len(password) > 15:
        return ["invalid_length_long"]
    if not re.search(r"[A-Z]", password):
        return ["missing_uppercase"]
    if not re.search(r"[a-z]", password):
        return ["missing_lowercase"]
    if not re.search(r"[0-9]", password):
        return ["missing_number"]
    if not re.search(_SPECIAL_CHARS, password):
        return ["missing_special_char"]
    return []


def register_user(username: str, password: str) -> tuple[bool, str]:
    if not re.match(r"^[a-zA-Z0-9]+$", username):
        emit_event(
            "login_fail_duplicate_id", username, "fail",
            message="invalid_username_format", page="/register",
        )
        return False, "사용자명은 영어와 숫자로만 구성할 수 있습니다."

    violations = validate_password(password)
    if violations:
        emit_event(
            "login_fail_password_policy", username, "fail",
            message=violations[0], page="/register",
        )
        return False, _VIOLATION_KO[violations[0]]

    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                emit_event(
                    "login_fail_duplicate_id", username, "fail",
                    message="duplicate_username", page="/register",
                )
                return False, "중복된 사용자명입니다."

            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, password_hash),
            )
            conn.commit()
            return True, "ok"
    except Exception:
        conn.rollback()
        logger.exception("register_user failed for username=%s", username)
        raise
    finally:
        pool.putconn(conn)


def authenticate_user(username: str, password: str) -> tuple[bool, str]:
    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT password_hash FROM users WHERE username = %s", (username,)
            )
            row = cur.fetchone()
            if not row:
                return False, "등록된 사용자가 아닙니다."

            if not bcrypt.checkpw(password.encode(), row[0].encode()):
                return False, "PW가 틀렸습니다."

            emit_event("login_success", username, "success", page="/login")
            return True, "ok"
    except Exception:
        logger.exception("authenticate_user failed for username=%s", username)
        raise
    finally:
        pool.putconn(conn)
