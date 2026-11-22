"""Explicit opt-in public GET command, separate from the offline M1 CLI."""
import argparse
from dataclasses import asdict
import json
import sys
from . import audit
from .classification import DeterministicAnalyzer
from .github import GitHubClient, GitHubError
from .models import TriageError
from .proposals import propose
from .approval import proposal_digest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="One unauthenticated public GitHub GET; no retries or writes.")
    parser.add_argument("repository", help="Explicit public owner/repository")
    args = parser.parse_args(argv)
    try:
        # If audit storage is unavailable, fail before making a network request.
        audit.record("github_query_started")
        batch = GitHubClient().list_issues(args.repository)
        results = []
        for sourced in batch.issues:
            proposal = propose(sourced.issue, DeterministicAnalyzer())
            results.append({"source_url": sourced.source_url,
                            "proposal_digest": proposal_digest(proposal), "proposal": asdict(proposal)})
        audit.record("github_query_succeeded")
        for item in results:
            audit.record("proposal_created", issue_number=item["proposal"]["issue_number"], digest=item["proposal_digest"])
        print(json.dumps({"source": "github_public_rest", "repository": batch.repository,
                          "analyzer": "deterministic_rules", "received_items": batch.received_items,
                          "excluded_pull_requests": batch.excluded_pull_requests,
                          "analyzed_issues": len(results), "results": results}, indent=2, ensure_ascii=True))
        return 0
    except GitHubError as exc:
        error = {"source": "github_public_rest", "error": exc.code, "message": str(exc), "http_status": exc.status}
    except TriageError as exc:
        error = {"error": "local_processing", "message": str(exc)}
    except Exception:
        error = {"error": "processing", "message": "Processing failed; no actions were applied."}
    try:
        audit.record("github_query_failed")
    except TriageError:
        error["audit"] = "unavailable"
    print(json.dumps(error, ensure_ascii=True), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
