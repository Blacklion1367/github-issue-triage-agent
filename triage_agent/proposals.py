"""Produce data-only suggestions; issue text is never executable."""
from .models import Action, Analyzer, Issue, Proposal, TriageError


def propose(issue: Issue, analyzer: Analyzer) -> Proposal:
    result = analyzer.analyze(issue)
    if result.category not in {"bug", "enhancement", "documentation", "question"} or result.priority not in {"low", "medium", "high"}:
        raise TriageError("Analyzer returned unsupported category or priority.")
    summary = f"Issue #{issue.number}: {result.category}; suggested priority {result.priority}."
    draft = "Thank you for reporting this issue. A maintainer will review it."
    if result.missing:
        draft += " Please provide: " + ", ".join(result.missing) + "."
    labels = (result.category, "priority:" + result.priority)
    return Proposal(issue.number, result, summary, draft, (
        Action("suggest_labels", labels=labels), Action("draft_comment", body=draft),
    ))
