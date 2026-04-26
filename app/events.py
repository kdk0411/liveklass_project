import os
import json
import httpx
import logging

logger = logging.getLogger(__name__)

TELEGRAF_URL = os.getenv("TELEGRAF_URL", "http://telegraf:8186/telegraf")


def emit_event(
    event_type: str,
    user_id: str,
    status: str,
    message: str = "",
    page: str = "/",
    metadata: dict = {},
) -> None:
    payload = {
        "event_type": event_type,
        "user_id": user_id,
        "status": status,
        "message": message,
        "page": page,
        "metadata": json.dumps(metadata),
    }
    try:
        httpx.post(TELEGRAF_URL, json=payload, timeout=2)
    except Exception as e:
        logger.warning("emit_event failed (non-blocking): %s", e)
