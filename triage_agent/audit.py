"""Append minimal metadata; never record issue text, secrets, or signatures."""
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path
from .models import TriageError

AUDIT_DIR = Path(__file__).resolve().parent.parent / ".local"


def record(event: str, *, issue_number: int | None = None, digest: str | None = None):
    if event not in {"proposal_created", "input_rejected", "processing_failed",
                     "github_query_started", "github_query_succeeded", "github_query_failed"}:
        raise TriageError("Unsupported audit event.")
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(), "event": event}
    if issue_number is not None:
        entry["issue_number"] = issue_number
    if digest is not None:
        entry["proposal_digest"] = digest
    try:
        AUDIT_DIR.mkdir(mode=0o700, exist_ok=True)
        if AUDIT_DIR.is_symlink() or not AUDIT_DIR.is_dir():
            raise OSError("Unsafe audit directory")
        directory = os.open(AUDIT_DIR, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            fd = os.open("audit.jsonl", os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=directory)
            with os.fdopen(fd, "a", encoding="utf-8") as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise OSError("Unsafe audit file")
                stream.write(json.dumps(entry) + "\n")
        finally:
            os.close(directory)
    except OSError as exc:
        raise TriageError("Unable to write local audit record.") from exc
