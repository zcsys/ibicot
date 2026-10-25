# Optional browser account deletion

`DeletionWebApplication` serves a local implementation of `/account/delete` and its two same-origin assets. It calls the existing `POST /v1/sessions`, `DELETE /v1/account` and `POST /v1/sessions/revoke` endpoints. Authentication and deletion still execute inside the existing API transactions. There is no new recovery bypass, credential database, automatic deletion job or public endpoint.

The wrapper is disabled when `web_deletion` is absent. The default factory/loopback runner retains its existing API behavior and serves no deletion page. `release/public-pages/publication.json` remains an unpublished draft with null operator, contacts and URLs; enabling a local test does not change it. Existing native public-link activation is a separate configuration.

## Local activation

Use the existing pinned service environment; the configured factory already imports the optional provider configuration/cryptography runtime even when only this wrapper is selected. No new dependency was added. Create an owner-only local JSON configuration:

```json
{"version":1,"web_deletion":{"origin":"http://127.0.0.1:8765","allow_loopback_http":true}}
```

Run the existing loopback-only development server with a disposable synthetic database:

```sh
.tooling/services-venv/bin/python -m services.tideglass_service --database /absolute/private/synthetic.sqlite3 --port 8765 --config /absolute/private/service.json
```

Open `http://127.0.0.1:8765/account/delete` only for accounts deliberately created in that isolated test service. Never point a test at an existing user database. Configuration must be a regular owner-only file as required by the existing factory. The local page prominently identifies itself as a development tool. No server is left running by the author checks.

For eventual production, an approved real HTTPS DNS origin replaces the example and `allow_loopback_http` is omitted. Exact Host and `wsgi.url_scheme` must match that origin for **all wrapped requests**, including health checks and native/provider API routes. The wrapper never trusts arbitrary `X-Forwarded-Host` or `X-Forwarded-Proto`. A trusted TLS gateway/application server must establish the correct WSGI scheme, enforce request/body-read/concurrency timeouts and avoid body, authorization, cookie or raw-query logging. The development `wsgiref` server is not a production deployment. DNS, certificate, operator identity, privacy/support links, backup-retention policy, logging, backup deletion and hosted availability still require actual qualification. A shared origin must not contain untrusted scripts or service workers.

## Browser behavior and boundaries

1. The player enters the saved account ID and recovery code. Format validation is local. Continuing clears the DOM inputs and opens a distinct irreversible confirmation. No account/session request has occurred yet.
2. A separate checkbox enables **Delete account permanently**. Cancelling or leaving before confirmation performs no account request; an idle confirmation expires after two minutes.
3. Confirmation authenticates through the existing recovery-code endpoint, then sends authenticated deletion with `confirm_delete:true` and the same recovery code. Duplicate submission and cancellation controls are disabled while the request is active.
4. Only HTTP200 plus all three expected positive deletion flags produces confirmed wording. Authentication failure, malformed response, HTTP failure, timeout or connection loss never infer deletion from a missing account/session. A server can commit deletion and lose its response; the UI explicitly says that outcome is unconfirmed.
5. If deletion is not confirmed and a temporary token was received, the page attempts to revoke **only that session**. Navigation away also attempts bounded keepalive revocation. These attempts are best effort; failed cleanup is not displayed as completed. If a login response is lost before its token arrives, the browser cannot revoke an unknown token. Any such session retains the existing API lifetime (30days, at most eight active sessions), not a new indefinite credential.

Requests use same-origin mode, omitted cookies, no-store, no-referrer and error-on-redirect. Tokens exist only in JavaScript request state; inputs are cleared and references released. There is no local/session storage, analytics, external font/script/resource, account data in a URL, credential logging, server-side session proxy or service worker. This does not claim forensic erasure of browser process memory, browser password managers, external copies or upstream infrastructure logs.

The wrapper rejects wrong/null Origin, cross-site/same-site Fetch Metadata, query strings/cookies/transfer-encoding on the UI path, unsafe Host/scheme, missing UI marker on browser auth routes, unapproved UI endpoints and non-JSON/oversized browser bodies. UI bodies are bounded to1024bytes; the browser reads at most8KiB of response data and aborts requests after15seconds (cleanup after5). A server/body-read deadline is still an application-server obligation. Page/asset GET and HEAD never enter the API/database. Restrictive CSP, no framing, no referrer, no-cache, same-origin resource/opener headers and HTTPS HSTS accompany the UI and its marked API responses. There are no CORS grants or Set-Cookie responses.

Account deletion cascades through current account records and sessions. The optional encrypted provider token row also cascades; non-account key commitments remain to prevent key-ID reuse. Deletion does not modify a native guest save, recall personal exports, cancel/refund store purchases or confirm retained-backup erasure. No real purchase/provider request is part of these checks.

## Reproduction and evidence

- Base HTTP/SQLite regression: `python3 -m unittest discover -s tests/services -p 'test_*.py' -v` —65 passed, including15 new HTTP cases.
- Configured provider regression: `.tooling/services-venv/bin/python -m unittest discover -s tests/services/providers -p 'test_*.py' -v` —36 passed, including4 new factory/vault cases.
- Run browser qualification from the repository root with `PYTHONPATH=.` (for example, `PYTHONPATH=. .tooling/services-venv/bin/python services/evidence/web-deletion/run_browser.py --node /absolute/path/to/node --node-modules /absolute/path/to/node_modules --output /absolute/path/to/new-proof`). Supply actual local runtime paths and a new output directory.
- Actual browser qualification: `services/evidence/web-deletion/run_browser.py` starts a quiet loopback server and disposable database, invokes `tests/services/web_deletion_browser.cjs` with a supplied Node/Playwright runtime, and shuts down/removes the database. Use `--node`, `--node-modules`, and a **new** `--output` directory. It launches headless Chrome with a fresh browser context; it does not use the user's browser profile.
- Eight actual browser scenarios passed against final copy: page/storage, explicit confirmation/cancel, wrong code, actual deletion, failed deletion with temporary-token revocation, lost response after an actual commit,320px/200% root-text keyboard operation, and final storage/input checks. Actual viewport captures are raw PNGs; no account/recovery/token values are captured. This is sampled host-browser presentation, not physical accessibility or a screen-reader acceptance claim.

The first HTTP run correctly failed when its configured-factory case ran under stdlib Python without existing cryptography dependencies. That case was moved to the explicit pinned provider lane; no skip or synthetic provider success replaced it. The first browser launch lacked the bundled Playwright Chromium binary; the successful runs explicitly use installed Chrome in a new automated context. Both failures are preserved. The final UI removes an irrelevant subscription-reference phrase; the final browser run covers that copy. Earlier backend/provider passes concern unchanged Python behavior.

This work fills the local implementation gap identified in `release/qa/integration-local-remaining-20261021T131244958842Z/LOCAL_REMAINING_REVIEW.md`, row1: M5-03/M7-05 and S27/S39. It does not accept those whole packages, publish a URL, supply an operator/contact, approve a policy or alter any original release criterion. The user still has no hosting, store accounts, physical devices or human testers.
