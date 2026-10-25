# Public support, privacy and deletion links

The native Help index and relevant Help articles now contain optional public-page actions. The player sees the exact configured address and explicitly chooses to open it in the system browser. No account identifier, recovery code, token, harbor state, query string or fragment is added. Merely opening the deletion page never authenticates or deletes an account.

All three values are empty by default. Each destination is independently enabled by a compile-time Dart definition:

| Definition | Destination |
|---|---|
| `TIDEGLASS_SUPPORT_URL` | Approved public support page |
| `TIDEGLASS_PRIVACY_URL` | Approved public privacy page |
| `TIDEGLASS_DELETION_URL` | Approved account deletion page |

Configure canonical lowercase HTTPS DNS URLs with an optional path. Values are limited to2048characters. Credentials, query/fragment, local/IP/reserved hosts, alternate ports, whitespace, backslashes, encoded control characters and values requiring URI normalization are rejected. Internationalized names must use a supported canonical ASCII DNS spelling. Do not use example addresses as release settings. A malformed or absent destination displays its unavailable state; it never falls back to an unrelated page. Partial configurations are supported and visibly incomplete.

The low-level Flutter build can receive `--dart-define=NAME=VALUE` for each approved destination. The current reproducible `tool/build_native.py` intentionally builds the empty default configuration; its candidate manifest does not yet define a released endpoint profile. Before qualifying an enabled release, incorporate exact approved values into the frozen candidate/build receipt and rerun native browser handoff against those destinations. A manual build with changed definitions is not the same candidate as an already qualified default build.

`url_launcher`6.3.3 is locked in the native package. The UI requests `LaunchMode.externalApplication`, serializes taps while launch is pending, and shows a retry message after an unavailable browser or exception. It checks mounted state before later updates. Missing configuration causes no launcher call. The tests inject a launcher to verify these boundaries; they do not establish actual browser availability on iOS/Android.

The separately implemented service deletion page is documented in `services/docs/WEB_DELETION.md`. It requires its own exact origin/TLS/operator setup, recovery-code authentication and explicit irreversible confirmation. No hosted endpoint, operator/contact, policy approval or store submission exists yet. The user has not authorized publication or supplied hosting.

## Verification

- Author: `release/native-proof/root-support-links-20261021T132724.154746Z/verification.json`, clean analysis and11English+11expanded-text-language Help/public-link tests, stable captured inputs. Earlier compile/layout failures remain in their original proof folders.
- Different-agent source review: `release/qa/integration-public-links-20261021T131837163201Z/PUBLIC_LINKS_SOURCE_REVIEW.md`. URL normalization and encoded-control rejection were corrected before final checks.
- Different-agent actual UI sample: `release/qa/integration-current-ui-20261021T133115456638Z/CURRENT_UI_REVIEW.md`, including the same22Help/public-link checks and other critical navigation tests.

This establishes bounded local implementation. Configured public destinations, actual native browser handoff, policy approval, hosted operations and physical assistive interaction remain separate requirements.
