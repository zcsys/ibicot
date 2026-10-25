# Browser account deletion — independent client review

**Decision: no blocking implementation defect found in the reviewed local deletion flow.** The frozen implementation reproduced its HTTP/provider/browser checks and passed additional adversarial controls. One minor reproduction-documentation correction is recommended below. Public deployment and whole-package acceptance remain open.

This is different-author review of M5-03/M7-05 preparation, S27/S39. The reviewer changed only new probes/evidence, not service, factory, UI or publication sources. All **21 author input hashes matched before and after**; exact pins and preserved source copies are in `initial-source.json`, `verification.json` and `source/`.

## Actual verification

| Check | Result | Evidence |
|---|---:|---|
| Original base service/HTTP suite | 65 passed | `base.log`, `base-result.json` |
| Original configured-provider/factory suite | 36 passed | `provider.log`, `provider-result.json` |
| Original actual Chrome scenarios | 8 passed | `author-browser/browser-report.json` |
| Different-author HTTP probes | 6 passed | `review-http.log` |
| Different-author actual Chrome scenarios, final | 10 passed | `review-browser-final/review-browser-report.json` |

These are separate test/scenario counts, not 125 unique user journeys. Author suites include older service coverage. No real account, purchase, provider call, hosted endpoint, Flutter/native command, physical device or study participant was used. Each HTTP run used its own temporary synthetic SQLite database; each browser driver used a quiet loopback service and fresh headless Chrome contexts/profile. Drivers shut down their server and removed the temporary database; final runner metadata records the cleanup. Browser version is recorded by the actual installed Chrome instance in each report.

Independent probes:

- `game/qa/review_web_deletion.py` — SHA-256 `8f8ba5af6e4d21a61dd97e3a11e13589b67a216d28e28ed66e731246e86d31cd`.
- `game/qa/review_web_deletion_browser.py` — `c5a017bfdd2a991e1be6ed360ee34faf9061c398ee92eadfd2808f9ced695ec1`.
- `game/qa/review_web_deletion_browser.cjs` — `19f9172eface394d5a07f435c62015869de61ce44fd2cbfe25f41d59d0d6f86e`.

## Source and boundary assessment

The wrapper requires explicit factory configuration, exact Host/scheme and configured Origin. It serves three frozen same-origin assets, introduces no credential store, and delegates recovery authentication/deletion/revocation to the original transactional API. Page/asset GET and HEAD remain read-only. The new factory wrapper surrounds the original provider chain; absent configuration preserves the old WSGI object. No public URL/operator/contact was invented, and `publication.json` is unchanged.

The browser holds credentials only in flow-local state, clears input fields before the separate irreversible confirmation, sends no authentication request until that confirmation, disables repeated submission while busy, and expires idle confirmation at two minutes. It requires HTTP 200 and three strict boolean success flags to display confirmed deletion. It cannot infer success from a missing account or failed response. A received temporary session is revoked after an unconfirmed attempt; navigation makes a best-effort bounded-body keepalive request for only that session. This does not guarantee cleanup after every browser/network failure, and the copy/docs do not claim it does.

The HTTP suite reproduced actual account/session/data cascading, strict confirmation and recovery checks, transaction rollback versus response-loss-after-commit, provider vault row deletion with key commitment retention, browser origin/metadata rules and default factory behavior. The independent HTTP probes additionally confirmed:

- Duplicate JSON keys reject before authentication/deletion; an otherwise valid subsequent request succeeds.
- Integer/string/null/container confirmation values and another account's recovery code cannot delete this account.
- A session at exact expiry cannot delete; fresh recovery authentication can.
- Concurrent duplicate deletion produces exactly one HTTP 200 and one 401, leaving no account.
- Malformed authentication shapes issue no session; valid authentication still works.
- Cross-origin/null/same-site/cross-site metadata, cookie and invalid UI marker reject mutation.

The final independent browser run exercised:

1. Confirmation remains at 119999ms and expires at 120000ms, with no request and the account retained. This uses Playwright's browser timer, not a real two-minute wait.
2. Repeated click events during a held authentication request produce one authentication and one deletion; actual account/session deletion is verified.
3. Navigation before final confirmation sends no account request and reopening has empty inputs.
4. A real issued authentication token with a deliberately wrong returned account identity cannot trigger deletion; only the temporary session is revoked, and the original session still works.
5. Null, oversized and invalid-JSON authentication responses never trigger deletion.
6. String-valued deletion success never produces confirmed wording.
7. Navigation during an intercepted, uncommitted deletion revokes the observed temporary token and preserves the original session/account. This is an actual browser navigation and real cleanup HTTP request with an explicit held-route fault; it does not prove cancellation of a server commit.
8. At 320px and 200% root text, both labeled action buttons remain fully within the viewport when revealed and exceed 48px. Keyboard/cancel behavior and storage absence are covered by original and new tests.

All request/response fault injections are explicit in the probe; no synthetic success is passed off as an actual deletion. Account/recovery/token values are omitted from logs, reports and captures.

## Preserved failures and minor documentation issue

**WEB-DOC001, P3:** invoking `python3 services/evidence/web-deletion/run_browser.py ...` from the repository root fails with `ModuleNotFoundError: services` unless the repository is on Python's import path. The module itself is not a standalone root-aware entry point, and the reproduction text does not state that environment prerequisite. `browser.log` and `browser-result.json` preserve this failure. The rerun with explicit `PYTHONPATH` pointing at the repository passed all eight scenarios (`browser-reproduced-result.json`). Recommend documenting `PYTHONPATH=. python3 services/evidence/web-deletion/run_browser.py ...` or a tested module invocation. This does not change the deletion runtime or block its local behavior review.

The first independent browser probe passed eight scenarios but failed at navigation because its asynchronous response event listener had not necessarily finished reading the token when the assertion ran. The initial probe source/log/report remain under `review-browser/`. Waiting for that specific real response and its parsed body repaired the probe; all nine scenarios passed in `review-browser-diagnostic/`. The final run adds the compact visual/control capture and passes all ten. No production source was changed or assertion removed to obtain these results.

## Actual visual inspection

Reopened `author-browser/empty-desktop.png` at 1280×1134: development-only notice, service address, irreversible deletion/backup/store/local-save boundaries, fields and progression button are readable and separated. No clipping was seen. The full 320×6420 confirmation capture shows the entire expanded flow but is resized by the image viewer; it is not used to claim fine-text legibility at native pixels.

The additional raw `review-browser-final/compact200-controls.png` is 320×900 and was inspected at its actual pixels. Destructive and Cancel buttons are visibly distinct, fully readable and untruncated; the retained confirmation text is scrollable. Viewport edge truncation of surrounding scroll content is expected, not clipped control geometry. No physical touch, browser zoom matrix, assistive-technology or screen-reader acceptance follows from these samples.

## Separate CTX import-only follow-up

The integrated current-runtime harness differs from the independently reviewed staging only by removal of `import 'package:tideglass_platform/study_native_context.dart';`; the recorder export supplies the same type. Exact text comparison succeeded. The delta is saved as `ctx-live-import-only.diff` and pinned by `ctx-import-review.json`: staged `85f859b2...`, live `d34649a223a50f08b955691be036fc286131718ed9cb619444419f1b701bc155`. No harness assertion, callback or behavior changed. This source review does not claim the lead's separate analyzer/native execution result.

## Remaining external and release obligations

There is no public deletion service here. Approved HTTPS hosting, correct trusted WSGI scheme/Host, operator/contact/privacy/support URLs, backup-retention/deletion operations, infrastructure logging controls, read/concurrency timeouts and operational availability remain to be qualified. The development server is not a production deployment. Browser cleanup is best effort; a lost authentication response can leave an unknown temporary session until the existing bounded lifetime. The page cannot erase local guest saves, personal exports, store purchases or already retained backups. No original scope acceptance or publication record was edited.
