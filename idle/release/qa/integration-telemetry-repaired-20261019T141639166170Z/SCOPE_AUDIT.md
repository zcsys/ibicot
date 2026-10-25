# Telemetry and repair scope check

Source pin: `c3b89321d86675c235c50352b22741e1f73076eee58cf33360b44e96febfb979`.

All 44 requirements and 65 original production packages retain their acceptance text, dependencies and reciprocal links. The four original source fingerprints match. Four prior production acceptances and three separate bootstrap packages are unchanged.

| Scope → evidence | Remaining |
|---|---|
| S08: 24 hours full production plus 48 hours at quarter rate; event-driven saved-policy replay | Full original package acceptance, staging, actual SDK/native network behavior and physical/elapsed evidence remain open. |
| S11: Three daily contracts, 10 Notes and 250 XP each, frozen goals, rerolls and seven-day/21-slot backlog | Full original package acceptance, staging, actual SDK/native network behavior and physical/elapsed evidence remain open. |
| S27: Help, recovery guide, release notes, credits, privacy/support URLs and runbooks | Full original package acceptance, staging, actual SDK/native network behavior and physical/elapsed evidence remain open. |
| S30: 99.5% crash-free sessions over 10,000 observed sessions, per platform/device and critical-flow review | Full original package acceptance, staging, actual SDK/native network behavior and physical/elapsed evidence remain open. |
| S33: 30/90-day simulations of visit/reset/buy/bonus strategies and Note scarcity | Full original package acceptance, staging, actual SDK/native network behavior and physical/elapsed evidence remain open. |
| S37: Monitoring, support diagnostics, backups, feature disables, rollout stops and compatible forward repair | Full original package acceptance, staging, actual SDK/native network behavior and physical/elapsed evidence remain open. |
| S39: Privacy, consent/refusal, account deletion/export and service outages reflect actual SDK behavior | Full original package acceptance, staging, actual SDK/native network behavior and physical/elapsed evidence remain open. |

| Implementation → scope | Evidence |
|---|---|
| GameTelemetry and app lifecycle → S27, S30, S37, S39 | Consented foreground observations, bounded memory queue, lifecycle and no fabricated exit/crash events; no measured population. |
| NativeServicesManager consent reads and platform buffer → S39 | QA015 two original failures repaired; explicit withdrawal, account binding and same-ID unknown-outcome retry verified. |
| HTTP GET consent route → S39 | Two actual HTTP tests; read requires authentication, does not renew consent, and old revisions remain rejected. |
| Controller/worker/simulator availability and final refresh → S08, S11, S33 | QA014/SIM001 six-probe regression passes; complete v3 matrix remains unreviewed. |
| QA tests and immutable evidence → S27, S37, S39 | 68 passing Dart cases and two retained HTTP cases tied to exact repaired pin. |

Original package contracts:

- **M3-02** (in_progress): Seeded contracts, snapshots, offline progress, rerolls and 21-slot backlog preserve claim IDs and do not duplicate rewards. Dependencies: M3-01, M1-06.
- **M5-03** (in_progress): Data inventory matches SDK behavior; consent refusal, export/deletion and service-outage recovery are verified on actual builds. Dependencies: M3-06, M4-04, M4-05.
- **M5-04** (in_progress): Validate economy/session events, entitlement dashboards, alerts, backups, support receipts and feature disable switches in staging. Dependencies: M3-07, M4-04.
- **M5-05** (in_progress): Simulate 30/90 days across visit and bonus policies, audit Note sinks and content pacing, freeze beta config and metric definitions. Dependencies: M4-06, M5-04.

No package, beta freeze or release gate is accepted. Developer accounts, hosting, physical devices and human playtesters remain unavailable.
