# M2 Execution Report — Public GitHub REST Reads

Historical milestone report. Local personal paths were redacted for M3 publication preparation.
Later user-reported integration evidence is recorded in `M3_PUBLICATION_AUDIT.md`.

Date: 2026-11-22. Scope: public, unauthenticated issue reads only.

## 1. Architecture implemented

A standard-library `http.client.HTTPSConnection` client issues only GET to the fixed
host `api.github.com` with default TLS certificate/hostname validation, explicit
10-second socket timeout, GitHub JSON Accept header, descriptive User-Agent and
API version `2022-11-28`. It sends no authentication and reads no tokens, `.netrc`,
or proxy credentials. It accepts a validated repository name, not an arbitrary URL.

Each invocation requests only `state=open&per_page=2`. It never follows redirects,
paginates, retries or backfills excluded PRs. Responses are limited to 65,536 bytes,
JSON depth 8, and two items. Non-JSON content types and compressed bodies are rejected.

Normalization returns an `IssueBatch` of `SourcedIssue` records wrapping the
unchanged M1 Issue model and a constructed GitHub source reference. Pull requests
are excluded. Missing/null body becomes empty; number/title remain required. Invalid
non-PR records reject the whole batch. No truncation or fictional fallback occurs.

The separate `github_cli` command passes validated issues through M1's unchanged
deterministic analyzer and proposal generator. It emits source-marked pending
proposals, omits raw remote text, and uses local audit events. Empty success is
distinct from failure. There is no action executor, write method or LLM integration.

## 2. Files created or modified

Created:

- `triage_agent/github.py`: transport, normalization and source contracts.
- `triage_agent/github_cli.py`: explicit read-only network CLI.
- `tests/test_m2.py`: 48 offline tests with mocked HTTPS and network guards.
- `docs/M2_EXECUTION_REPORT.md`: this report.

Modified:

- `triage_agent/audit.py`: allows query-started/succeeded/failed event names.
- `README.md`: current scope, commands, transport policy, provenance, tests and limits.

Local ignored artifacts:

- `.local/m2-offline-tests.txt`: verbose test results.
- `.local/m2-public-result.json`: empty stdout from the failed live attempt.
- `.local/m2-public-error.json`: sanitized DNS failure result.
- `.local/audit.jsonl`: appended query-started and query-failed metadata.
- Python bytecode caches generated during tests.

The README, M1 report and source were reviewed before implementation. Work stayed
inside `<project-root>`; temporary
test directories were cleaned automatically. No other project was accessed.

The original M1 test file and classifier were not modified, verified by identical
SHA-256 hashes before and after implementation:

```text
tests/test_m1.py
ac3921074853452d90e2ab60c7b9de159985b6c8c8a43047a5f5afc7450cb06f
triage_agent/classification.py
fd8bf1c9ccd407e080201f0bf94ef6c12e88835b07309153f54c99335b2d3fdf
```

## 3. Offline validation

Environment: Python 3.14.10. No dependencies were installed.

Executed before the live attempt:

```text
python3 -m unittest discover -v
Ran 109 tests in 0.189s
OK
```

| Suite | PASS | FAIL | Errors | Skipped |
| --- | ---: | ---: | ---: | ---: |
| Existing M1 | 61 | 0 | 0 | 0 |
| New M2 | 48 | 0 | 0 | 0 |
| Total | 109 | 0 | 0 | 0 |

Simulations cover 200, 403, 429, 404, 500, 503, unexpected status, redirects to the
same and other hosts, malformed/oversized/deep JSON, missing required and optional
fields, DNS/timeout/TLS/transport failures, empty lists, mixed/all pull requests,
result caps, duplicate issue numbers, no pagination, no authentication, preserved
text, constructed provenance, malicious instructions, CLI errors and audit failure.

All tests work offline. The HTTPS connection is mocked in M2 tests; fail-on-use
socket and DNS guards were not invoked. TLS certificate and hostname verification,
fixed host, GET method, request headers, timeout and bounded read are asserted.
No tests were removed, weakened, or modified to force PASS.

## 4. One controlled public request attempt

Only after all 109 tests passed, executed once:

```bash
python3 -m triage_agent.github_cli cli/cli
```

Intended exact URL:
`https://api.github.com/repos/cli/cli/issues?state=open&per_page=2`

Exit code: **2**. Sanitized stderr:

```json
{
  "source": "github_public_rest",
  "error": "dns",
  "message": "GitHub DNS resolution failed; no retry performed.",
  "http_status": null
}
```

There was one application-level request attempt. DNS resolution failed before an
HTTP exchange could complete; no HTTP status was received and no successful GET
was observed. This was not an empty successful query. No connectivity probes,
second attempt, alternative transport, permission escalation, configuration change,
or documentation fetch was performed. The network validation is blocked by DNS,
while the authorized implementation and offline validation are complete.

## 5. Counts

| Live result | Count |
| --- | ---: |
| Application-level query attempts | 1 |
| HTTP responses received | 0 |
| Items received | 0 |
| Real issues analyzed | 0 |
| Real proposals generated | 0 |

Simulated test records are fictional and are not reported as real GitHub results.
No remote response content was saved because none was received.

## 6. No GitHub writes

No POST, PATCH, PUT, DELETE, comments, labels, issue state changes, repositories,
webhooks, commits or pushes were performed. No keys, tokens, authentication,
private repositories, paid APIs, global installations or real LLM were used.
The application wrote only local audit/test-result artifacts in this project.
The client has no write or arbitrary-method interface.

## 7. Remaining M1 observations

- Classification remains deterministic English keyword matching; contextual and
  adversarial misclassification is possible. Human review is still required.
- Approval receipts remain unauthenticated/in-memory; the M1 digest does not bind
  repository identity. Source-aware authenticated approval is required before any
  future action execution and is not implemented here.
- Webhook replay protection remains per-instance/in-memory, bounded and not
  thread-safe. No real webhook was created.
- Local audit is minimal, not tamper-evident, rotated, or transactional.
- No publication, automatic execution or generative AI has been added.

## 8. Limitations and recommended next steps

The live service contract could not be confirmed due to DNS failure. Only the
unauthenticated public endpoint is supported. Two returned items may yield fewer
than two issues after PR filtering. Valid large GitHub issues or large metadata
responses can exceed M1 limits and are deliberately rejected. Repository validation
is conservative. The socket timeout is not a total deadline for DNS or a slowly
streaming response. Rate limits are reported without waiting/retrying; 403 can
also indicate access denial. API version `2022-11-28` is pinned but was not checked
against a live response.

A future explicitly authorized validation may repeat one public read in an
environment with working DNS. Before any write-capable milestone, define approval
identity, source-bound proposal integrity, persistent replay/audit behavior and
write-boundary enforcement. These are recommendations only; no next stage began.

## Final status

**PASS CON OBSERVACIONES** — the M2 read-only implementation and all 109 offline
tests pass; the single live verification attempt was blocked by DNS and remains
unverified. No GitHub write or subsequent milestone was attempted.
