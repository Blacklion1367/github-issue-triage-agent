"""Offline CLI: print a proposal only after successful local audit."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
from . import audit
from .approval import proposal_digest
from .classification import DeterministicAnalyzer
from .inputs import load_issue
from .models import TriageError
from .proposals import propose


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Offline deterministic issue triage; no GitHub actions.")
    parser.add_argument("issue_file", type=Path, help="Local JSON issue file")
    args = parser.parse_args(argv)
    try:
        issue = load_issue(args.issue_file)
        proposal = propose(issue, DeterministicAnalyzer())
        digest = proposal_digest(proposal)
        audit.record("proposal_created", issue_number=issue.number, digest=digest)
        print(json.dumps({"analyzer": "deterministic_rules", "proposal_digest": digest, "proposal": asdict(proposal)}, indent=2, ensure_ascii=True))
        return 0
    except TriageError as exc:
        message, event = str(exc), "input_rejected"
    except Exception:
        message, event = "Processing failed; no actions were applied.", "processing_failed"
    try:
        audit.record(event)
    except TriageError:
        message += " Local audit unavailable."
    print("Error: " + message, file=sys.stderr)
    return 2
