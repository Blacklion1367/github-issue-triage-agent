"""Offline webhook verification; process-local duplicate suppression."""
import hashlib
import hmac
import re
from .inputs import MAX_BYTES, parse_json, validate_issue
from .models import Issue, TriageError


class WebhookVerifier:
    def __init__(self, secret: bytes, *, capacity: int = 10000):
        if not isinstance(secret, bytes) or not secret or type(capacity) is not int or capacity < 1:
            raise TriageError("Secret and positive replay capacity required.")
        self._secret = secret
        self._seen: set[str] = set()
        self._capacity = capacity

    def verify(self, headers: dict[str, str], body: bytes) -> Issue:
        if len(body) > MAX_BYTES:
            raise TriageError("Input exceeds byte limit.")
        normalized = {}
        for key, value in headers.items():
            if not isinstance(key, str) or not isinstance(value, str) or key.lower() in normalized:
                raise TriageError("Invalid or ambiguous webhook headers.")
            normalized[key.lower()] = value
        signature = normalized.get("x-hub-signature-256", "")
        if not re.fullmatch(r"sha256=[0-9a-f]{64}", signature):
            raise TriageError("Invalid webhook signature.")
        expected = "sha256=" + hmac.new(self._secret, body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise TriageError("Invalid webhook signature.")
        if normalized.get("x-github-event") != "issues":
            raise TriageError("Unsupported webhook event.")
        delivery = normalized.get("x-github-delivery", "")
        if not re.fullmatch(r"[A-Za-z0-9-]{1,128}", delivery):
            raise TriageError("Invalid delivery identifier.")
        if delivery in self._seen:
            raise TriageError("Duplicate delivery.")
        payload = parse_json(body)
        if not isinstance(payload, dict) or set(payload) != {"action", "issue"} or payload["action"] not in ("opened", "edited", "reopened"):
            raise TriageError("Unsupported webhook payload or action.")
        issue = validate_issue(payload["issue"])
        if len(self._seen) >= self._capacity:
            raise TriageError("Replay cache full; delivery rejected.")
        self._seen.add(delivery)
        return issue
