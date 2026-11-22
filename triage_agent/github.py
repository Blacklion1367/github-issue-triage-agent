"""Unauthenticated, bounded GitHub public issue listing; GET only."""
from dataclasses import dataclass
import http.client
import re
import socket
import ssl
from .inputs import MAX_BYTES, parse_json, validate_issue
from .models import Issue, TriageError

HOST = "api.github.com"
TIMEOUT_SECONDS = 10
RESULT_LIMIT = 2
API_VERSION = "2022-11-28"


class GitHubError(TriageError):
    """Safe, structured failure; never includes a remote response body."""
    def __init__(self, code: str, message: str, status: int | None = None):
        super().__init__(message)
        self.code = code
        self.status = status


def validate_repository(repository: str) -> str:
    if not isinstance(repository, str) or len(repository) > 140:
        raise GitHubError("repository", "Invalid owner/repository.")
    parts = repository.split("/")
    if len(parts) != 2:
        raise GitHubError("repository", "Explicit owner/repository required.")
    owner, name = parts
    if (not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", owner)
            or "--" in owner or not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", name)
            or name in {".", ".."}):
        raise GitHubError("repository", "Invalid owner/repository.")
    return repository


@dataclass(frozen=True)
class SourcedIssue:
    issue: Issue
    source_url: str


@dataclass(frozen=True)
class IssueBatch:
    repository: str
    received_items: int
    excluded_pull_requests: int
    issues: tuple[SourcedIssue, ...]


def normalize(payload, repository: str) -> IssueBatch:
    repository = validate_repository(repository)
    if not isinstance(payload, list) or len(payload) > RESULT_LIMIT:
        raise GitHubError("schema", "Expected at most two GitHub result items.")
    issues, seen, excluded = [], set(), 0
    for item in payload:
        if not isinstance(item, dict):
            raise GitHubError("schema", "Invalid GitHub result item.")
        if "pull_request" in item:
            excluded += 1
            continue
        try:
            # A missing/null body is legitimate. Required fields remain required.
            issue = validate_issue({"number": item.get("number"), "title": item.get("title"),
                                    "body": "" if item.get("body") is None else item["body"]})
        except TriageError as exc:
            raise GitHubError("schema", "Invalid GitHub issue fields or limits.") from exc
        if issue.number in seen:
            raise GitHubError("schema", "Duplicate issue number in response.")
        seen.add(issue.number)
        # Construct provenance from validated request context, not untrusted URLs.
        issues.append(SourcedIssue(issue, f"https://github.com/{repository}/issues/{issue.number}"))
    return IssueBatch(repository, len(payload), excluded, tuple(issues))


class GitHubClient:
    """No configurable host/method/auth, redirects, proxy discovery, or retries."""
    def list_issues(self, repository: str) -> IssueBatch:
        repository = validate_repository(repository)
        connection = None
        try:
            context = ssl.create_default_context()
            connection = http.client.HTTPSConnection(HOST, timeout=TIMEOUT_SECONDS, context=context)
            connection.request("GET", f"/repos/{repository}/issues?state=open&per_page={RESULT_LIMIT}", headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "Blacklion1367-Issue-Triage-M2/0.2",
                "X-GitHub-Api-Version": API_VERSION,
                "Accept-Encoding": "identity",
            })
            response = connection.getresponse()
            status = response.status
            if status != 200:
                if status == 429:
                    code, message = "rate_limit", "GitHub rate limit response; no retry performed."
                elif status == 403:
                    code, message = "forbidden_or_rate_limit", "GitHub access denied or rate limited; no retry performed."
                elif status == 404:
                    code, message = "not_found", "Public repository not found or unavailable."
                elif 300 <= status < 400:
                    code, message = "redirect", "GitHub redirect rejected."
                elif 500 <= status < 600:
                    code, message = "server", "GitHub server error; no retry performed."
                else:
                    code, message = "http", "Unexpected GitHub HTTP status."
                raise GitHubError(code, message, status)
            if response.getheader("Content-Encoding", "identity").lower() != "identity":
                raise GitHubError("encoding", "Unexpected response encoding.")
            content_type = response.getheader("Content-Type", "").split(";")[0].strip().lower()
            if content_type not in {"application/json", "application/vnd.github+json"}:
                raise GitHubError("content_type", "Expected a GitHub JSON response.")
            length = response.getheader("Content-Length")
            if length is not None:
                if not re.fullmatch(r"[0-9]{1,10}", length):
                    raise GitHubError("size", "Invalid response length.")
                if int(length) > MAX_BYTES:
                    raise GitHubError("size", "GitHub response exceeds byte limit.")
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise GitHubError("size", "GitHub response exceeds byte limit.")
            if length is not None and len(body) != int(length):
                raise GitHubError("transport", "Incomplete GitHub response.")
            try:
                payload = parse_json(body)
            except TriageError as exc:
                raise GitHubError("json", "Invalid or excessively nested GitHub JSON.") from exc
            return normalize(payload, repository)
        except ssl.SSLError as exc:
            raise GitHubError("tls", "TLS validation or handshake failed; no retry performed.") from exc
        except TimeoutError as exc:
            raise GitHubError("timeout", "GitHub request timed out; no retry performed.") from exc
        except socket.gaierror as exc:
            raise GitHubError("dns", "GitHub DNS resolution failed; no retry performed.") from exc
        except (OSError, http.client.HTTPException) as exc:
            raise GitHubError("transport", "GitHub connection failed; no retry performed.") from exc
        finally:
            if connection is not None:
                connection.close()
