import os
import httpx
import random
import logging

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

APP_URL = os.getenv("APP_URL", "http://app:8000")
EVENT_COUNT = int(os.getenv("EVENT_COUNT", "1000"))

_VALID_PASSWORD = "GenPass1!"
_USERS = [f"gen{i:03d}" for i in range(1, 31)]
_EVENT_TYPES = ["page_view", "purchase", "error"]

_KOREAN_IDS = ["테스터", "사용자", "김찰스", "테스트계정"]
_BAD_PASSWORDS = [
    "short1!",          # invalid_length_short
    "a" * 16 + "A1!",  # invalid_length_long
    "nouppercase1!",    # missing_uppercase
    "NOLOWERCASE1!",    # missing_lowercase
    "NoNumbers!!",      # missing_number
    "NoSpecial123",     # missing_special_char
]


def _register_valid_users(base: str) -> list[str]:
    created: list[str] = []
    with httpx.Client(base_url=base, timeout=10.0) as c:
        for username in _USERS:
            r = c.post("/register", data={"username": username, "password": _VALID_PASSWORD})
            if r.status_code == 200:
                created.append(username)
    logger.info("Valid users created: %d", len(created))
    return created


def _simulate_registration_failures(base: str, valid_users: list[str]) -> None:
    with httpx.Client(base_url=base, timeout=10.0) as c:
        # 한글 아이디 시도 → login_fail_duplicate_id
        for uid in _KOREAN_IDS:
            c.post("/register", data={"username": uid, "password": _VALID_PASSWORD})

        # 중복 아이디 시도 → login_fail_duplicate_id
        for username in random.choices(valid_users, k=10):
            c.post("/register", data={"username": username, "password": _VALID_PASSWORD})

        # 정책 위반 비밀번호 → login_fail_password_policy
        for i, bad_pw in enumerate(_BAD_PASSWORDS * 3):
            c.post("/register", data={"username": f"badpw{i:03d}", "password": bad_pw})

    logger.info("Registration failure simulation complete")


def _emit_events(base: str, valid_users: list[str], total: int) -> int:
    sent = 0
    while sent < total:
        username = random.choice(valid_users)
        with httpx.Client(base_url=base, timeout=10.0) as session:
            r = session.post("/login", data={"username": username, "password": _VALID_PASSWORD})
            if r.status_code != 200:
                logger.warning("Login failed for %s", username)
                continue

            batch = random.randint(1, 15)
            for _ in range(batch):
                if sent >= total:
                    break
                event_type = random.choice(_EVENT_TYPES)
                r = session.post(f"/trigger/{event_type}")
                if r.status_code == 200:
                    sent += 1
                else:
                    logger.warning("Trigger failed: %s %s", event_type, r.text)

            session.post("/logout")

        if sent % 100 == 0:
            logger.info("Events sent: %d / %d", sent, total)

    return sent


def main() -> None:
    logger.info("Generator start — APP_URL=%s, EVENT_COUNT=%d", APP_URL, EVENT_COUNT)

    valid_users = _register_valid_users(APP_URL)
    if not valid_users:
        logger.error("No valid users created, aborting")
        return

    _simulate_registration_failures(APP_URL, valid_users)
    total_sent = _emit_events(APP_URL, valid_users, EVENT_COUNT)

    logger.info("Generator complete — total events sent: %d", total_sent)


if __name__ == "__main__":
    main()
