# GitHub Issue Triage Agent

A Python portfolio project by **Blacklion1367** demonstrating bounded input
processing, event verification, a read-only API adapter, and preparation of
human-reviewed issue triage proposals.

**The runtime uses deterministic rules, not an LLM. It never applies actions to
GitHub.** M1 provides an offline prototype; M2 adds public, unauthenticated GitHub
reads. M3 prepares documentation, CI and a publication audit. Publication itself
has not been performed.

## Features

- Validate fictional local issues or normalize public GitHub issue data.
- Suggest `bug`, `enhancement`, `documentation`, or `question`, with a priority.
- Detect missing descriptions, reproduction steps and versions.
- Generate a metadata summary, response draft and proposed labels.
- Keep all proposals `pending_review`; record minimal local audit metadata.
- Verify simulated webhook signatures and reject duplicate delivery identifiers.
- Run 109 automated tests without internet or third-party Python packages.

## Setup and offline demonstration

Use Python 3.10+ on Linux. Local validation used Python 3.14.10; other versions
have not been verified here. No package installation is required: run directly
from the extracted project directory. No `pip install` step or credentials are
needed.

```bash
cd /path/to/github-issue-triage-agent
python3 --version
python3 -m triage_agent --help
python3 -m triage_agent examples/bug.json
python3 -m triage_agent examples/question.json
python3 -m unittest discover -v
```

The examples and all test fixtures are fictional. For `examples/bug.json`, the
proposal contains category `bug`, priority `medium`, no missing fields, labels
`bug` and `priority:medium`, a response draft, and status `pending_review`. The
question example yields `question` and `low`. No offline demonstration requires
or embeds a real issue's title, body, or author.

Successful output is JSON on stdout. Failures use stderr and exit code 2; success
exits 0. Minimal audit records go to `.local/audit.jsonl`, excluded from publication.
Audit failure prevents proposal output. No action is applied.

## Architecture

```text
Local JSON -> bounded loader -------------------+
                                               |
Explicit public GET -> bounded response -> adapter -> Issue
                                                      |
                                               deterministic analyzer
                                                      |
                                                   proposal
                                                      |
                                              local audit + JSON
                                                      |
                                                human review

Local webhook sample -> HMAC/event/replay validation -> Issue
```

| Module | Responsibility |
| --- | --- |
| `inputs.py` | Bounded file reads, JSON depth check, strict issue validation |
| `models.py` | Immutable data models and analyzer/source protocols |
| `classification.py` | Deterministic classification and missing-information rules |
| `proposals.py` | Summary, draft response and inert action suggestions |
| `approval.py` | Explicit local review receipt bound to proposal content |
| `audit.py` | Minimal local audit events |
| `webhooks.py` | Simulated HMAC, event/action checks and replay detection |
| `github.py` | GET-only transport, response validation and source-aware adaptation |
| `cli.py`, `__main__.py` | Offline file command |
| `github_cli.py` | Explicit public-read command |

`Analyzer.analyze(Issue) -> Analysis` leaves a boundary for a future analyzer;
no LLM implementation exists. The batch API is
`GitHubClient.list_issues(repository) -> IssueBatch`, whose `SourcedIssue` entries
retain the M1 Issue plus source URL. It does not implement the older single-issue
`IssueSource.get_issue()` protocol. There is no action execution stage.

## Deterministic classification

Rules scan the lowercased title and body with whole-word matching. The first
matching category wins in the following order:

| Category | Keywords or phrases |
| --- | --- |
| bug | bug, crash, crashes, error, broken, regression, data loss, security vulnerability |
| documentation | documentation, docs, readme, typo |
| enhancement | feature, enhancement, add, support, improve, request |
| question | question, how, why, help; also the fallback |

Any category receives `high` priority for `data loss`, `security vulnerability`,
`production down`, or `critical`. Otherwise bugs/enhancements are `medium` and
documentation/questions are `low`. The proposal includes the priority reason.

For bugs, missing-information checks look for nonblank values on lines beginning
with `Steps to reproduce:` (or `Reproduction steps:`) and `Version:`, ignoring case.
An empty body adds missing `description` for every category. These checks verify
presence, not factual quality; negation, context and keyword stuffing can mislead
them. Summaries and drafts are templates, not generative analysis.

## Public GitHub integration (explicit network access)

This is a separate command from the offline CLI:

```bash
python3 -m triage_agent.github_cli --help
```

For an intentional live lookup, the syntax is
`python3 -m triage_agent.github_cli OWNER/REPOSITORY`.
For `cli/cli`, use `python3 -m triage_agent.github_cli cli/cli`.
Selecting this module and a repository explicitly activates network access; there
is no additional `--allow-network` flag. Do not include live lookup commands in
offline tests. Every invocation is a new attempt, not a lifetime one-request quota.

The client uses only `GET https://api.github.com/repos/OWNER/REPOSITORY/issues?state=open&per_page=2`:

- Standard-library HTTPS with default certificate/hostname validation and a
  10-second socket timeout; no configurable host or request method.
- GitHub JSON Accept header, descriptive User-Agent and API version `2022-11-28`.
- No authentication, existing token reads, `.netrc` lookup, cookies, proxy discovery,
  retries, pagination, or redirects, even to the same host.
- Validated ASCII repository names; at most two returned items and 65,536 bytes.
- `pull_request` items are excluded without replacement. Zero remaining issues is
  a valid successful result. Missing/null body becomes empty; required fields and
  M1 limits remain strict. Invalid non-PR items reject the entire batch.
- Source URLs are constructed from validated repository/number, not followed from
  remote data. Text remains untrusted and is never executed.

Output identifies `source: github_public_rest`, repository, counts, source URLs
and pending proposals. Raw titles/bodies are retained in memory for analysis but
omitted from CLI output and audit. Lookup errors never become fictional issues.

403 is treated as access-denied-or-rate-limit; 429 as rate limited. 404, 5xx,
redirects, malformed JSON, schema/size failures, DNS, TLS, timeouts and transport
failures have safe error codes. Remote error bodies are not printed. No rate-limit
bypass or automatic waiting is implemented.

### Integration evidence and provenance

The user reported a manual execution from a normal Fedora terminal with:

| Observation | User-reported result |
| --- | --- |
| Repository | `cli/cli` |
| Items received | 2 |
| Pull requests excluded | 1 |
| Issues analyzed | 1 |
| Issue reference | `cli/cli#15129` |
| Suggested category | `bug` |
| Suggested priority | `medium` |
| Proposal status | `pending_review` |
| Authentication / GitHub writes | None / none |

This is **user-provided evidence**, not an independently repeated or observed
live test by Astra/Codex. No raw payload, issue text or personal author data is
included. The earlier Astra environment attempt failed at DNS; its historical
report remains separate. Neither M3 nor M3.1 repeated either request. The 109 offline test
results below were verified directly in the local execution environment.

## Input limits and safety

Local JSON requires exactly `number`, `title`, and `body`. Number must be an
integer from 1 to 2,147,483,647 (not a boolean); title a nonblank string up to 256
Unicode code points; body a string up to 16,000 code points. Empty bodies are valid
but flagged. File/webhook/HTTP bodies are capped at 65,536 bytes, JSON depth at 8.

Malformed UTF-8, duplicate keys, non-finite JSON constants, unpaired surrogates and
invalid field types are rejected. Local inputs must be regular files; leaf
symlinks, directories and devices are rejected. API bodies with unexpected content
types or compression are rejected. Oversized input is not silently truncated.

There is no shell execution, dynamic code evaluation or GitHub write client in
the application. Output uses escaped JSON. Local audit files use restrictive
creation permissions and reject symlinks/hard links. These controls and tests
reduce specific risks; they are not a security certification or an OS sandbox.

## Simulated webhooks

`tests/fixtures/webhook_opened.json` is fictional. Tests use a clearly fictional
signing secret defined only in test code. `WebhookVerifier.verify()` checks:

1. HMAC-SHA256 over the exact body bytes via `X-Hub-Signature-256`.
2. Constant-time comparison with `hmac.compare_digest`.
3. Event `issues`, action `opened`, `edited` or `reopened`, and issue schema.
4. A valid delivery identifier and duplicates within the same verifier instance.

Invalid signatures are rejected. Failed validation does not consume an identifier.
The cache holds at most 10,000 deliveries and rejects new ones when full. It is
in-memory, per-instance, not thread-safe, and resets on restart. Headers are not
covered by the body HMAC; this is not durable or comprehensive replay prevention.
No server or real webhook has been created.

## Human review and audit limitations

All CLI proposals remain `pending_review`. The library can record an explicit
approve/reject decision with reviewer text and confirmation, bound to the proposal
digest; changing content invalidates the receipt. These are unauthenticated,
in-memory records, not durable approval identities. There is no CLI approval UI
and no executor, even for an approved receipt.

The digest does not bind repository/source identity. Any future write integration
must add authenticated review, source-bound integrity and enforcement at the write
boundary. Issue text cannot supply approval. Local audit is minimal and neither
tamper-evident, rotated nor transactional; earlier events may remain if a later
write fails. This is a local CLI, not a multi-user filesystem sandbox.

## Tests and prepared CI

```bash
python3 -m unittest discover -v
```

**109 local tests passed: 61 M1 + 48 M2, zero failures/errors.** The original tests
remain unchanged. They cover validation, classification, approval receipts, audit
failures, malicious text, webhook verification, HTTP errors, TLS configuration,
normalization and resource limits. M2 mocks HTTPS; both suites guard socket
creation, connection helpers and DNS. These checks cover exercised code paths,
not host-wide network isolation or absolute absence of vulnerabilities.

[The prepared GitHub Actions workflow](.github/workflows/tests.yml) uses
`permissions: {}`, no supplied tokens/secrets, no third-party actions, and the
runner's preinstalled Python. It fetches public source anonymously before tests;
that setup requires network access on a future hosted runner. Tests and help
commands make no API calls. No dependencies are installed and no remote writes
or artifacts are published. Private repositories are intentionally skipped.
**Remote CI has not run or been verified.**

## Known limitations

- English keyword rules can misclassify; no LLM or autonomous action execution.
- Conservative schemas/limits may reject valid large GitHub responses or names.
- A page of two items may contain fewer than two issues after filtering PRs.
- The socket timeout is not a total deadline covering DNS or slow streaming.
- Minimal Linux-oriented filesystem behavior; other operating systems are untested.
- Temporary replay/approval state and minimal auditing need redesign before any
  production service or write-capable integration.
- Hosted CI and compatibility beyond the locally tested Python version are pending.

## Development transparency and distribution

ChatGPT and the Astra/Codex development workflow assisted with design, code,
documentation and tests. This assistance does not mean the application uses AI
at runtime. Neither M1 nor M2 calls ChatGPT or another LLM/API for analysis. The
maintainer remains responsible for reviewing generated work.

No third-party Python packages, vendored libraries or external media are bundled.
**Licensed under the [MIT License](LICENSE).**
Copyright (c) 2026 Blacklion1367. The owner approved MIT in M3.1; the full standard
license text is included without changes to its terms. The component review is
not a legal provenance certification.

Publication candidates are listed exactly in
[PUBLICATION_MANIFEST.txt](docs/PUBLICATION_MANIFEST.txt). See the
[M3 publication audit](docs/M3_PUBLICATION_AUDIT.md) for security findings,
validation and outstanding decisions. Historical [M1](docs/M1_EXECUTION_REPORT.md)
and [M2](docs/M2_EXECUTION_REPORT.md) reports retain their milestone context.
Publication requires separate human authorization; M3 has not committed or pushed
anything or created a remote repository.

The [M3.1 precommit report](docs/M3_FINAL_PRECOMMIT_REPORT.md) records the final
27-file inventory, approved license, local checks and Git initialization pending
in the normal Fedora terminal. No commit or publication was performed in M3.1.
