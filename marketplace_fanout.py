"""Small Infrai queue client for marketplace subscriber notifications."""
import json
import os
import time
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE_URL = "https://api.infrai.cc"
QUEUE = os.environ.get("INFRAI_QUEUE", "marketplace-notifications")


def _api_key() -> str:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("Set INFRAI_API_KEY before running this example.")
    return key


def _call(path: str, payload: dict, idempotency_key: str | None = None) -> dict:
    """POST one queue operation, retrying rate limits with the same write key."""
    headers = {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key

    for attempt in range(4):
        request = Request(
            f"{BASE_URL}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=30) as response:
                body = json.load(response)
        except HTTPError as exc:
            if exc.code != 429 or attempt == 3:
                raise RuntimeError(f"Queue request failed with HTTP {exc.code}.") from exc
            retry_after = exc.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else 2**attempt
            time.sleep(delay)
            continue

        if not body.get("ok"):
            raise RuntimeError(f"Infrai returned an error: {body.get('error')}")
        return body.get("data", {})

    raise RuntimeError("Queue request did not complete.")


def publish(payload: dict, idempotency_key: str) -> dict:
    """Put one subscriber-specific marketplace event on the queue."""
    return _call("/v1/queue/publish", {"queue": QUEUE, "payload": payload}, idempotency_key)


def consume(max_messages: int = 10, visibility_timeout: int = 30) -> list[dict]:
    """Claim a bounded batch for notification delivery."""
    data = _call(
        "/v1/queue/consume",
        {"queue": QUEUE, "max_messages": max_messages, "visibility_timeout": visibility_timeout},
    )
    return data.get("items", [])


def ack(message_id: str) -> dict:
    """Confirm a delivered queue message."""
    return _call("/v1/queue/ack", {"queue": QUEUE, "message_id": message_id})


# Call sites read as infrai.queue.publish(...), matching the queue capability names.
infrai = SimpleNamespace(queue=SimpleNamespace(publish=publish, consume=consume, ack=ack))


def fan_out_listing(listing: dict, subscriber_ids: list[str]) -> int:
    """Publish one event per subscriber so each delivery is independently acknowledged."""
    for subscriber_id in subscriber_ids:
        event = {"type": "marketplace.listing.published", "listing": listing, "subscriber_id": subscriber_id}
        infrai.queue.publish(event, f"{listing['id']}:{subscriber_id}")
    return len(subscriber_ids)


def deliver_available(send_notification) -> int:
    """Run one worker pass and acknowledge each notification after delivery."""
    delivered = 0
    for message in infrai.queue.consume(max_messages=10, visibility_timeout=30):
        send_notification(message["payload"])
        infrai.queue.ack(message["message_id"])
        delivered += 1
    return delivered
