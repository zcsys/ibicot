# Tideglass launch operations handover — local preparation

**Status:** implementation and local rehearsal only; no launch approved, no service hosted, no operational coverage staffed. This handover is not a record of 14 elapsed days. Apple/Google developer accounts, physical test devices, hosting and human playtest resources have not been supplied. The [14-day coverage template](launch-coverage-template.json) has deliberately empty dates, owners, contact channels and evidence fields.

## Authority and release decision

| Responsibility | Required before launch | Current assignment |
|---|---|---|
| Launch/rollout authority | Human or organization authorized to publish, spend, stop rollout and accept operating risk | Unassigned |
| Primary service/incident owner | Named responder with access to the qualified deployment, monitoring and runbooks | Unassigned |
| Secondary responder | Independent reachable coverage for absence and escalation | Unassigned |
| Privacy/recovery authority | Controls deletion/consent journal, key recovery and safe activation decisions | Unassigned |
| Store/provider operator | Actual Apple/Google/advertising accounts, signed notifications, reconciliation and refund workflows | Unassigned |
| Support owner | Working public support endpoint, response process and minimal diagnostic handling | Unassigned |
| Season 2 decision owner | Reviews the bounded brief after launch evidence, without silently funding or shipping extra production | Unassigned |

The AI implementation team can prepare and check local artifacts. It has not assumed deployment authority, committed an operating budget, created a scheduler, or promised unattended availability. A review of source code or synthetic data is not a staffed incident response shift.

## Preflight record

The launch authority must attach an immutable release/candidate identity and independently reviewed source-to-scope matrix, then record the following evidence. An empty entry stops rollout.

| Evidence | Required record |
|---|---|
| Product acceptance | Original v1 package/dependency gates, 44-item scope audit in both directions and unresolved-defect disposition; do not replace external gates with local tests. |
| Native qualification | Actual supported iOS/Android devices, secure storage, resume/save/reinstall, privacy/consent, purchases/refunds, ads/no-fill, accessibility and performance results. |
| Store/product configuration | Signed identities, actual product catalog/prices, sandbox purchase/restore/interruptions, completed store/legal/privacy declarations and working support/privacy URLs. |
| Hosted capacity and safety | TLS origin, worker/request/resource limits, traffic/latency/capacity evidence, production logs/secret handling, bounded reconcile/prune schedule and tested optional-feature disables. |
| Observability | Alert delivery verified end to end to the named primary and secondary; acknowledgements recorded. Local JSON signals alone are not delivery. |
| Recovery | Qualified encrypted backup storage and retention; matching retained keys; independent deletion/consent/revocation history; compatible restore rehearsal and recovery authority approval. |
| Empirical quality | Required 99.5% crash-free over 10,000 observed sessions with platform/device and critical-flow review, mature cohorts and original calendar gates. The health event failure ratio is a different operational measure. |
| Coverage | Actual UTC start/end dates, primary/secondary ownership, escalation contact, response targets and cost authority for every shift across 14 actual days. |

Use [OPERATIONS.md](../../services/docs/OPERATIONS.md) for exact local commands and health thresholds. The current database schema is 1; native saves/content have their own versions and must be checked independently. Do not infer one format's compatibility from another.

## Routine operating cycle to configure and rehearse

These are proposed operating actions, not installed tasks or observed coverage. The deployment owner must set and test their cadence against qualified capacity before activation.

1. Capture local health JSON and backup integrity/age signals; inspect every critical, unknown and warning item. Verify the monitoring destination receives the signal. A missing sample/worker/backup is unknown, not healthy.
2. Run the configured bounded provider reconciliation batch and check durable failure/due counts. Never grant from a client completion or retry acknowledgement before durable grant. Apple native completion has no proven server observation in this implementation.
3. Check critical save/resume failures, service errors and branch conflicts through the deployed measurement instruments. Retain no raw save, credential, purchase token or provider payload in incident logs. Current local health does not count endpoint latency or branch-conflict rate.
4. Create a unique consistent backup, preserve its identity and authenticated creation record in the qualified store, verify available matching keys, and prune only under the approved retention/deletion policy. Independently record privacy changes that must survive a backup rollback.
5. Rehearse the disposable restore drill against the selected backup and approved reconciliation manifest. A passing local drill remains ineligible for live activation until the authority resolves post-backup deletion, consent, revocation, ownership and branch history.
6. Update the day's actual incident, support, ongoing-cost and evidence record. Do not fill an empty day from simulation or a future schedule.

## Stop and escalation conditions

| Signal or condition | Immediate containment | Required disposition |
|---|---|---|
| Unsupported/newer schema/save, corrupt database, unexplained balance/ownership changes, save loss or critical-flow crash | Stop rollout and affected write path; preserve original files and evidence. Keep offline guest play available where safe. | Compatible forward repair and independent reproduction/review; never lower a schema marker or merge branches. |
| Account isolation/privacy breach, telemetry retained after confirmed withdrawal, leaked credentials | Stop affected optional service/collection; restrict access under authorized incident procedure. | Privacy/recovery authority evaluates scope, lawful obligations and verified cleanup; do not publish guessed legal notices. |
| Purchase/refund/reconciliation failures, stale ownership, duplicate delivery | Disable new purchases or affected verified delivery through qualified controls; preserve legitimate ownership recovery reads. | Reverify through actual provider, reconcile durable receipts and prove retry/idempotency before enabling. No compensated gameplay power. |
| Ad verification, consent or no-fill regression | Disable ads; retain the equal free briefing route. | Verify callback/consent path and six shared slots on actual devices before re-enabling. |
| Low disk, failed/stale backup, overdue cleanup, exhausted capacity or missing alerts | Stop rollout; disable affected optional service if needed; preserve remaining space for safe transactions. | Operator verifies storage/capacity, qualified backup and signal delivery. Never delete arbitrary player branches for capacity relief. |
| Missing/unreachable primary and secondary, absent launch authority, unqualified public URL or external acceptance gate | Do not start or advance rollout. | Resolve ownership and qualification explicitly; a local green check cannot override the gate. |

The assigned primary acknowledges and opens an incident; the secondary takes over if the configured response target is missed. Escalation contacts and deadlines are currently **unset**. No messages are sent by this repository. The authority must configure a working channel and rehearse delivery before release. Serious issues stay open until a verified fix, affected-user recovery decision, independent check, and rollout decision are recorded.

## Incident record template

Create a separate private incident record with: incident ID; UTC detected/acknowledged/contained/resolved times; severity and affected feature/platform/build; minimal reproduction; scope and known unknowns; owner/secondary/authority; stop/disable decision; evidence hashes; compatible fix/recovery choice; independent verification; support communication approval; reopening criteria; actual costs; follow-up owner/deadline. Use aggregate diagnostics or explicitly consented minimal exports. Do not attach bearer/recovery credentials, raw purchase proofs, vault keys, complete telemetry bodies or unredacted gameplay saves to public tickets.

## Fourteen-day handover and Season 2

The JSON coverage template contains 14 numbered days, each unassigned and without a calendar date. Before launch, each day needs primary/secondary, UTC coverage boundaries, escalation route and response target. During launch, record actual check/incident/support/cost evidence and handover acknowledgement. After day 14, review actual gaps, carry-forward incidents, ongoing cost authority and ownership. Only a dated verified operating record can satisfy S38/OPS-14; this file cannot.

Season 2 preparation is limited to a decision brief: evaluate actual feedback, retention and economic evidence; propose one bounded content hypothesis and validation budget; preserve isolated season economy, single selected pass, paid archive continuation and cosmetic-only rewards; define acceptance and fallback. Root-owned `release/season-2-brief.md` is the intended brief artifact. No future production, event schedule, funding or external publication is authorized by this handover.

## Acceptance mapping

This artifact supports preparation of M7-04/S37 and M7-08/S37,S38. The local health/recovery source and fault checks support M5-04/S27,S30,S37 and the **service recovery portion only** of M6-08/S21,S37. No S21 pass/season behavior is verified here. Conversely, every command, threshold, replay limit and coverage field serves those operational requirements; no gameplay/economy feature is introduced. All original source acceptance and upstream dependencies remain intact.
