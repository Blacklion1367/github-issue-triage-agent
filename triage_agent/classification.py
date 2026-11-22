"""Deterministic English keyword rules, intentionally not an AI model."""
import re
from .models import Analysis, Issue

RULES = (
    ("bug", r"\b(bug|crash|crashes|error|broken|regression|data loss|security vulnerability)\b"),
    ("documentation", r"\b(documentation|docs|readme|typo)\b"),
    ("enhancement", r"\b(feature|enhancement|add|support|improve|request)\b"),
    ("question", r"\b(question|how|why|help)\b"),
)


class DeterministicAnalyzer:
    def analyze(self, issue: Issue) -> Analysis:
        text = (issue.title + "\n" + issue.body).lower()
        category = next((name for name, pattern in RULES if re.search(pattern, text)), "question")
        high = re.search(r"\b(data loss|security vulnerability|production down|critical)\b", text)
        priority = "high" if high else "medium" if category in {"bug", "enhancement"} else "low"
        reason = "High-impact keyword detected." if high else f"Default priority for {category}."
        missing = []
        if category == "bug":
            if not re.search(r"(?im)^[ \t]*(steps to reproduce|reproduction steps)[ \t]*:[ \t]*\S", issue.body):
                missing.append("reproduction steps")
            if not re.search(r"(?im)^[ \t]*version[ \t]*:[ \t]*\S", issue.body):
                missing.append("version")
        if not issue.body.strip():
            missing.append("description")
        return Analysis(category, priority, (reason,), tuple(missing))
