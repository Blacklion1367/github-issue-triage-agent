# M3 Publication Audit

Historical M3 audit with an M3.1 documentation update: MIT is now approved and
included, and the user supplied the category/priority below. The 25-file inventory
and test timing here describe M3; the current 27-file inventory and checks are in
[M3_FINAL_PRECOMMIT_REPORT.md](M3_FINAL_PRECOMMIT_REPORT.md).

Scope: preparation and local audit only. No publication is authorized by this
report. No live query, external connection, installation, commit, push, remote
repository creation, or change to another project was performed during M3.

## 1. Publication inventory

At the end of M3, the manifest contained the following **25 candidate files**.
This is the historical selection; [PUBLICATION_MANIFEST.txt](PUBLICATION_MANIFEST.txt)
now contains 27 files after M3.1:

```text
.github/workflows/tests.yml
.gitignore
README.md
docs/M1_EXECUTION_REPORT.md
docs/M2_EXECUTION_REPORT.md
docs/M3_PUBLICATION_AUDIT.md
docs/PUBLICATION_MANIFEST.txt
examples/bug.json
examples/question.json
tests/__init__.py
tests/fixtures/webhook_opened.json
tests/test_m1.py
tests/test_m2.py
triage_agent/__init__.py
triage_agent/__main__.py
triage_agent/approval.py
triage_agent/audit.py
triage_agent/classification.py
triage_agent/cli.py
triage_agent/github.py
triage_agent/github_cli.py
triage_agent/inputs.py
triage_agent/models.py
triage_agent/proposals.py
triage_agent/webhooks.py
```

Selection was checked using an isolated temporary Git metadata directory and
`GIT_INDEX_FILE` under ignored `.local/` storage, with this project as the worktree.
The temporary index contained exactly the manifest paths, all regular files.
Indexed contents were checked against the worktree, and representative sensitive
or generated paths were checked against `.gitignore`. No existing index, history,
remote configuration, or refs were changed. Temporary Git metadata was removed.
This verifies candidate selection, not any pre-existing Git history.

Excluded: runtime audit data, test logs, bytecode, environments, databases,
private/local configuration, credential files and agent state. `.gitignore` was
expanded to cover these categories. It does not retroactively protect an already
tracked secret and is not a substitute for reviewing the explicit manifest.

## 2. Security review

The review combined source inspection, manifest-scoped pattern scanning, import
inspection, unchanged-file hashes and the original automated tests. No excluded
credential stores were opened. Findings apply to these candidate files only,
not the whole workstation, ignored files or unknown history.

| Area | Finding and evidence | Limits |
| --- | --- | --- |
| Credentials/tokens | No real credential or token found in candidates. No private-key blocks or recognizable provider-token patterns found. Test token/secret strings are explicitly fictional. | Pattern scanning cannot detect every secret format. Test literals are not usable credentials. |
| Personal data | Removed machine-specific home paths from historical reports. No real issue text, authors, email addresses or unnecessary personal data included. | The intentional portfolio handle and public issue identifier remain. |
| Input handling | 65,536-byte cap, depth 8, title/body limits, strict scalar/schema validation and regular-file checks. | Not a filesystem sandbox; valid larger inputs are rejected. |
| HTTP safety | Fixed HTTPS host, verified TLS/hostname, GET-only, validated repo, two-item cap, explicit timeout; no credentials, redirects, retries or pagination. | Socket timeout is not a total deadline including DNS/slow streaming. No live request was made in M3. |
| GitHub writes | No application write methods or action executor. CI has no push, comment, label, issue or deployment steps. | Proposals are suggestions only; this is not a production write-authorization system. |
| API errors | Safe handling of 403/429/404/5xx, malformed JSON, oversized response, TLS, DNS and timeout failures; errors never become issues. | 403 may be access denial or rate limiting; no retries or rate-budget management. |
| Webhooks | HMAC-SHA256, `compare_digest`, event/action/schema validation, duplicate delivery checks. | Simulated only; cache resets on restart, is per-instance and not thread-safe. Delivery/event headers are not authenticated by the body HMAC. |
| Human review | Explicit confirmation and proposal-digest-bound receipt; CLI outputs pending review. | Reviewer text is not authentication; receipts are in-memory and do not bind repository identity. No executor exists. |
| Audit/privacy | Minimal metadata, no raw issue body/title or response headers; restrictive local file creation and symlink/hard-link checks. | Not tamper-evident, rotated, durable across arbitrary storage failures, or transactional. |

The application treats received text as data, not instructions. Existing tests
exercise malicious text without executing it. These checks do not provide absolute
security guarantees, comprehensive prompt-injection resistance, or an independent
penetration-test certification.

## 3. Directly verified local tests

Environment: Python 3.14.10 on Linux; Git 2.56.1 available for the temporary index.

```text
python3 -m unittest discover -v
Ran 109 tests in 0.194s
OK
```

| Suite | PASS | FAIL | Errors | Skipped |
| --- | ---: | ---: | ---: | ---: |
| M1 original | 61 | 0 | 0 | 0 |
| M2 original | 48 | 0 | 0 | 0 |
| Total | 109 | 0 | 0 | 0 |

All 15 Python files across application and tests matched their pre-M3 SHA-256
hashes. No original test or runtime code was modified. No new runtime feature was
added. Both CLI help commands exited 0 without a live request:

```text
python3 -m triage_agent --help
python3 -m triage_agent.github_cli --help
```

M2 tests mock the HTTPS connection; both suites guard socket creation, connection
helpers and DNS. No network guards were invoked. This is evidence about executed
paths, not host-wide network isolation. Local validation logs are ignored and are
not candidates for publication.

## 4. Documentation and CI prepared

- Rewrote `README.md` in English with setup (no package installation required),
  fictional offline demonstrations, architecture, rules, public-read command,
  webhook simulation, human review, limits, tests and AI-development transparency.
- Anonymized local personal paths in M1/M2 reports and added historical-context
  notes. Their original milestone outcomes remain unchanged.
- Expanded `.gitignore` and added the exact publication manifest and this audit.
- Added `.github/workflows/tests.yml` with push, pull-request and manual triggers,
  a five-minute job limit, and `permissions: {}`.

The workflow intentionally uses no third-party actions, secrets, supplied tokens,
package installations, API queries, artifact uploads or remote write operations.
It fetches the public repository anonymously using Git before running tests and
CLI help with the runner's preinstalled Python on Ubuntu 24.04. Git credential
helpers, prompts, global/system configuration and hooks are disabled for setup;
redirects are rejected. Private repositories are skipped. A GitHub-hosted workflow
requires platform networking and a source fetch; only the test/help phase is
intended to run without network calls.

Local checks reviewed the workflow structure and policy and validated embedded
shell syntax with `bash -n`; they did not execute the fetch. **Remote GitHub Actions
has not run, and no remote PASS is claimed.** GitHub's workflow parser, runner Python
compatibility and anonymous fetch of event/PR refs remain to be verified after
separate publication authorization. No local YAML-specific dependency was installed.

## 5. Real integration evidence provided by the user

The user reported a subsequent manual execution from a normal Fedora terminal:

| Field | User-provided evidence |
| --- | --- |
| Repository | `cli/cli` |
| Items received | 2 |
| Pull requests excluded | 1 |
| Issues analyzed | 1 |
| Issue reference | `cli/cli#15129` |
| Suggested category (user clarification in M3.1) | `bug` |
| Suggested priority (user clarification in M3.1) | `medium` |
| Proposal status | `pending_review` |
| Authentication | None |
| GitHub writes | None |

Astra/Codex did not independently witness or repeat that execution, inspect a raw
response, or verify the current live issue during M3. Its timestamp and contents
are not inferred. The report records the user's statement as such. Reproducible
offline demos and fixtures remain fictional; no live issue content was copied.

The previous Astra-environment M2 attempt failed at DNS, as preserved in the
historical report. That earlier failure and the later user-reported success are
separate observations. The 109 test results in section 3 were directly verified
locally during this audit.

## 6. Third-party distribution and license review

Candidate files contain Python source, fictional JSON examples/fixtures,
documentation and a workflow. Import inspection found only standard-library and
internal application imports. There are no vendored libraries, bundled Python
runtime, copied third-party assets, dependency lockfiles, or third-party GitHub
Actions in this selection. GitHub documentation is referenced by links rather
than copied wholesale. Only the public issue reference is retained as evidence.

No component requiring an additional third-party distribution notice was identified
in this source-tree review. This is not exhaustive authorship verification or legal
advice. Git/Python/hosted runner tools are used, not redistributed with the files.

At M3 completion, no license had been added. **Resolved in M3.1:** the owner
approved MIT and the standard [LICENSE](../LICENSE) was added with
`Copyright (c) 2026 Blacklion1367`. No incompatible bundled component was identified
in the scoped source-tree review.

## 7. Pending observations

- The M3 license observation was resolved in M3.1 with approved MIT.
- Hosted CI and the hosted runner's interpreter have not been verified remotely.
- Keyword rules and template drafts are limited; no real LLM exists.
- Approval identity, source-bound integrity, durable replay protection and stronger
  audit storage remain prerequisites for any future write-capable service.
- Linux-specific filesystem behavior and conservative input/HTTP limits remain.
- The client may return zero/one issue after PR filtering and makes no replacement
  requests. It has no lifetime request quota.
- Secret scanning and simulated network tests are scoped checks, not absolute
  guarantees or an audit of excluded files and historical commits.

## 8. Publication recommendation

**READY WITH OBSERVATIONS** was the M3 outcome for its 25-file candidate set.
The license decision is now resolved in M3.1. Review the current manifest and documentation and obtain
explicit publication authorization before creating/pushing a remote repository.
After authorized publication, verify the prepared workflow remotely before claiming
CI success. No publication, remote repository creation or next milestone was
performed as part of M3.
