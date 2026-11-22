"""Human review receipts bound to exact proposal content. No action executor."""
from dataclasses import asdict, dataclass
import hashlib
import json
from .models import Proposal, TriageError


def proposal_digest(proposal: Proposal) -> str:
    raw = json.dumps(asdict(proposal), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode()).hexdigest()


@dataclass(frozen=True)
class Review:
    proposal_digest: str
    reviewer: str
    decision: str


def review(proposal: Proposal, *, reviewer: str, decision: str, confirmed: bool) -> Review:
    if confirmed is not True or not isinstance(reviewer, str) or not reviewer.strip() or len(reviewer) > 100:
        raise TriageError("Explicit human confirmation and reviewer identity required.")
    if decision not in {"approve", "reject"}:
        raise TriageError("Unsupported review decision.")
    return Review(proposal_digest(proposal), reviewer.strip(), decision)


def is_approved(proposal: Proposal, receipt: Review | None) -> bool:
    return receipt is not None and receipt.decision == "approve" and receipt.proposal_digest == proposal_digest(proposal)
