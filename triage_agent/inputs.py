"""Bounded local JSON loading. No eval, subprocesses, or network access."""
import json
import os
import stat
from pathlib import Path
from .models import Issue, TriageError

MAX_BYTES = 65536
MAX_DEPTH = 8
MAX_TITLE = 256
MAX_BODY = 16000


def read_bytes(path: Path) -> bytes:
    try:
        # Reject directories, devices, FIFOs, and symlinks before reading.
        if not stat.S_ISREG(path.lstat().st_mode):
            raise TriageError("Input must be a regular local file.")
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise TriageError("Input must be a regular local file.")
            data = stream.read(MAX_BYTES + 1)
    except OSError as exc:
        raise TriageError("Unable to read input file.") from exc
    if len(data) > MAX_BYTES:
        raise TriageError("Input exceeds byte limit.")
    return data


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise TriageError("Duplicate JSON keys are not allowed.")
        result[key] = value
    return result


def _constant(value):
    raise TriageError("Non-finite JSON numbers are not allowed.")


def parse_json(data: bytes):
    if len(data) > MAX_BYTES:
        raise TriageError("Input exceeds byte limit.")
    try:
        text = data.decode("utf-8")
        # Scan nesting BEFORE json.loads to bound parser stack usage.
        depth, quoted, escaped = 0, False, False
        for char in text:
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char in "[{":
                depth += 1
                if depth > MAX_DEPTH:
                    raise TriageError("JSON exceeds nesting limit.")
            elif char in "]}":
                depth -= 1
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)
    except (UnicodeError, ValueError, RecursionError) as exc:
        if isinstance(exc, TriageError):
            raise
        raise TriageError("Invalid UTF-8 JSON input.") from exc


def validate_issue(value) -> Issue:
    if not isinstance(value, dict) or set(value) != {"number", "title", "body"}:
        raise TriageError("Issue requires exactly number, title, and body.")
    number, title, body = value["number"], value["title"], value["body"]
    if type(number) is not int or not 1 <= number <= 2147483647:
        raise TriageError("Issue number must be a positive 32-bit integer.")
    for field, text, limit in (("title", title, MAX_TITLE), ("body", body, MAX_BODY)):
        if not isinstance(text, str) or len(text) > limit:
            raise TriageError(f"Invalid {field} type or length.")
        if any(0xD800 <= ord(c) <= 0xDFFF for c in text):
            raise TriageError("Invalid Unicode scalar value.")
    if not title.strip():
        raise TriageError("Title must not be empty.")
    return Issue(number, title, body)


def load_issue(path: Path) -> Issue:
    return validate_issue(parse_json(read_bytes(path)))
