"""Immutable contracts shared by offline components and future adapters."""
from dataclasses import dataclass
from typing import Protocol


class TriageError(ValueError):
    """Expected, safe-to-display input or processing failure."""


@dataclass(frozen=True)
class Issue:
    number: int
    title: str
    body: str


@dataclass(frozen=True)
class Analysis:
    category: str
    priority: str
    reasons: tuple[str, ...]
    missing: tuple[str, ...]


class Analyzer(Protocol):
    """Future LLM implementations must return data, never execute instructions."""
    def analyze(self, issue: Issue) -> Analysis: ...


class IssueSource(Protocol):
    """Read-only boundary for a future REST adapter; M1 has no HTTP client."""
    def get_issue(self, number: int) -> Issue: ...


@dataclass(frozen=True)
class Action:
    kind: str
    labels: tuple[str, ...] = ()
    body: str = ""


@dataclass(frozen=True)
class Proposal:
    issue_number: int
    analysis: Analysis
    summary: str
    draft_response: str
    actions: tuple[Action, ...]
    status: str = "pending_review"
