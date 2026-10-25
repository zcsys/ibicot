# support.privacy_page

Local draft; not a published policy or support service.

Actual HTML: `release/public-pages/dist/privacy.html`. The following text segments are extracted from that file.

Privacy & data · Tideglass

Skip to privacy information

✦

TIDEGLASS

Support

Privacy & data

Development reference · not a published privacy policy

This describes implemented data flows. The operator, contact details, hosting, backup retention and final third-party disclosures are not approved. No public service or study is running.

Your harbor, your choices

Understand what

stays with you.

Local play works without an account. Cloud recovery, quality reports and study participation are separate choices.

On this page

Local play

Optional account services

Reports, ads & reminders

Optional research study

Retention & deletion

Sharing & providers

Publication status

Local play

The game stores harbor progress, settings and recovery copies on your device. Guest play does not require cloud upload, quality-report consent or a rewarded ad. A local export contains game data; you choose where to keep or share it.

Optional service failure does not block the guest economy or free crew briefing route. It also cannot establish paid ownership. Local reminders start off and use your selected timing and quiet hours; opening one grants no extra reward.

This static local page contains no forms, analytics, cookies, scripts or external fonts. Following an external link in future published material would be a separate visit. Any eventual host's request logging must be disclosed before publication.

Optional account services

Cloud setup asks for consent. The implemented account method uses a random account ID and recovery code; it does not ask for an email address or password. Keep the recovery code private.

Account and session records

Account identifiers, recovery-code verification hashes and session-token hashes support authentication and account recovery. The service does not store the plaintext recovery code or session token.

Cloud snapshots and branches

Explicit uploads contain full gameplay snapshots and branch metadata so you can choose and restore a compatible harbor. Credentials do not belong in a game export. Branches are not merged into a larger wallet.

Purchase and cosmetic records

Verified product, transaction, ownership and acknowledgement records support delivery, restore and revocation. Payment card details are handled by the store, not this service. A configured Google verification adapter stores purchase tokens encrypted for later reconciliation; raw tokens are excluded from account exports and logs.

Offline cosmetic verification

A bounded signed ownership record is stored separately from gameplay in device secure storage. It is tied to the account and harbor. Offline verification may expire and require a new check without changing production.

Shared Support claims

Daily reward source, receipt and delivery records prevent the free briefing and optional ad routes from granting the same slot more than once.

Service protection

The local service uses a short-lived hash of the source address and a time bucket to limit abusive requests. That hash is pseudonymous, not anonymous. Deployment logs are a separate, unconfigured data source.

Reports, ads & reminders

Quality reports start off.

Their consent is separate from cloud consent. Enabled reports use defined session, progression and diagnostic events, without pre-consent history, recovery codes, free-form text or a wallet dump. The temporary client queue is memory-only.

Turning reports off clears the local queue immediately and requests deletion of current service events. If the service cannot be reached, the pending request remains visible for retry. A failed request is not completed remote deletion.

Rewarded ads are optional.

The free briefing gives the same shared-slot reward. Native purchase and advertising libraries may have their own data flows. Their final initialization, consent, identifiers and network behavior have not yet been qualified for a public build; this page does not claim that guest mode makes every third-party SDK network-silent.

Reminders are optional.

Their preferences are stored locally. You can disable them in the game and use the operating system's notification controls.

Optional research study

Normal development builds do not open a study registry or record study history. A separately configured study build would first show its own information, contact and retention terms and ask for explicit participation.

The implemented recorder uses random study install/session/process identifiers, consent and protocol hashes, candidate/configuration labels, coarse device/acquisition categories, timestamps and defined lifecycle/activity/gap events. With the newly disclosed consent, each process start also records the app process number, platform, app identifier, version/build and observation time. These bounded records can be matched to a native diagnostic that a participant separately chooses to provide. Older consent does not authorize collection of this process information. The app does not collect device logs, upload diagnostics, or record device uptime. It does not collect free-form input, account credentials, payment receipts or activity before enrollment.

Study export is a separate, confirmed clipboard action. Default withdrawal stops recording and erases local study identifiers, records and eligibility evidence, leaving a nonidentifying stop marker. A failed erase remains pending for retry. Previously exported copies require handling under the approved study policy; the app cannot recall another application's clipboard or files.

There is no study server, live enrollment or approved participant policy in this workspace. Local test records are synthetic.

Retention & deletion

These are implemented service limits, not a promise about an unconfigured production host or third-party systems.

Sessions

Service sessions expire after 30 days, with up to eight devices per account.

Cloud snapshots

The service caps snapshots at 64 MiB or 10,000 records per account and does not silently delete branches to make room. Confirmed account deletion removes active account snapshots.

Support claims

Current and seven prior account days are retained by the service's explicit pruning operation.

Quality reports

Up to 5,000 events per account and 90 days; consent revocation deletes current events. A production operator must schedule the cleanup work.

Abuse-limit records

The source-address hash records expire after two minutes.

Offline ownership and soundtrack cache

Signed ownership leases last at most 24 hours and can expire sooner. The soundtrack cache reserves up to three exports of at most 64 MiB each. Files older than 24 hours are removed on a later startup or export; the operating system may clear them sooner. A file is not promised to disappear at exactly 24 hours.

Account deletion leaves the local guest harbor

Confirmed deletion removes active service account data, sessions, claims, reports and purchase records. It does not cancel or refund a store transaction or erase personal exports. Signing out and forgetting this device's credentials are different actions.

Backups, operating-system copies, provider records and forensic storage erasure require separate policies. No backup-retention period, international transfer arrangement or support-request retention period has been approved.

See the in-game export and deletion steps.

An accessible public deletion-request route and approved contact are still required before release.

Sharing & providers

Explicit cloud actions send data to the configured Tideglass service. Store verification communicates with the relevant store provider. Rewarded ads require the configured advertising provider and its consent flow. The final list of operators, hosts and third parties must match the shipped configuration and actual native traffic.

Exporting a harbor, study record or soundtrack sends a copy only to the destination you select or paste into. That destination's own storage and retention apply. A completed personal export cannot be recalled by deleting a Tideglass account.

Publication status

The app's legal operator, privacy contact, public URLs, supported territories, age-related practices, backup/deletion terms and third-party disclosures are not finalized. This development reference must not be submitted as a completed privacy policy or used as study consent.

Before release, the approved policy must identify the operator and available requests, describe the final app and providers, and provide working privacy/support and deletion links. There is no request form or monitored inbox here.

Implementation reference updated 21 October 2026.

Support availability

.

Tideglass · Restore a little light.

Support & recovery
