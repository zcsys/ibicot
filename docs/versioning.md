# Versioning & Product Milestones

This document pins the three release gates — **PoC**, **prototype**, and **MVP** —
and the full product checklist that separates a prototype from an MVP. It is a
versioning and scope note, not a design document: the
[design canon](design_canon.md) remains authoritative for mechanics, and this
document defers to it wherever they overlap.

## Current position

The kernel is a deterministic supply-chain simulation (NumPy + Numba) with a
FastAPI + WebSocket service and a browser dashboard. The market logic is complete
on both sides: production follows a margin ramp, and industrial purchasing is
price-sensitive — latent demand is "fill to brim" (the storage slot), and the
actual T2 request follows the Tier 3 price-response curve with the input's reference
cost as the halving price (elasticity 2), capped by the slot shortage. T1 retains
slot-refill procurement. Distributors retain their incumbent after split or
partial orders; T1/T2 remember the seller after a positive fill. See the
[implemented purchasing contract](design_canon.md#implemented-purchasing-contract)
for the exact ranking, fee and preference boundaries.

## Phase 1 — PoC

**Definition.** The complete market logic proves itself: an equilibrium economy
*may be made to work* on both sides of the market.

**Criteria.**

1. **Supply side.** Pricing, production, and margin behavior of autonomous firms
   settle at an *interior* equilibrium — not pinned to price bounds
   ([§2.6, §12.2](design_canon.md#L65)).
2. **Buy side.** Final demand and — crucially — intermediate (industrial)
   purchasing are price-sensitive and consistent with the supply side. The
   approved T2 procurement rule has no buyer production-margin gate; production
   evaluates its margin separately.

**Honesty caveat.** "An equilibrium exists" is not the same as "the economy is
validated as fair and healthy." A stable aggregate does not by itself prove
healthy firms, sound incentives, or correct accounting. The fairness metric
([§8](design_canon.md#L463)) and long-run health are separate, ongoing
requirements that run alongside and after the PoC, not part of its completion
bar.

**Explicitly deferred (per the canon, "deferred for the PoC").** Service layers
(advertising, financial services, games, utilities, warehouses/land),
[Storage Royalty](design_canon.md#L141), and
[product innovation](design_canon.md#L500). The local (single-machine)
server-client is the PoC's observation and control harness, not a PoC criterion;
network deployment is deferred to MVP.

## Phase 2 — Prototype

**Definition.** A feature-complete game built on the PoC market logic, still
running locally (single machine), with no product concerns and no network
deployment.

- **Scope.** Add the game features on top of the proven market logic.
- **Bound.** Aspirationally comparable to the PoC effort; this is the phase most
  like the PoC in kind (feature work, no external dependencies).
- **Not included.** Everything in the MVP product checklist below — network
  deployment, payments, security, operations, and so on — is out of scope here.

## Phase 3 — MVP

**Definition.** The prototype operated as a product. It is the same game plus
product-ization; the delta is *not* new gameplay but the operational, commercial,
and trust layer required to ship and run it.

**Every item in this checklist is required for MVP.** It differs from the
prototype only in being a product in this sense.

### A. Commercial & legal

| Item | Why it is product, not prototype |
| --- | --- |
| **Payments & billing** | Real-money subscriptions are already specified in [§7](design_canon.md#L448) (Tier 1 ~$5/yr, Tier 2 $15/yr): processor integration, subscription lifecycle (trial, renewal, dunning, refund, cancel), invoices/receipts, VAT/sales tax, chargebacks and payment fraud. |
| **Legal & compliance** | Terms of Service, privacy policy, GDPR/CCPA (erasure, export), age gating (COPPA), a real-money-trading / money-laundering policy review, and a gambling-law check (the game is deterministic skill, but that must be established, not assumed). |

### B. Trust & identity

| Item | Why it is product, not prototype |
| --- | --- |
| **Security guardrails and admin backdoors** | Authentication and authorization, least-privilege admin tooling, and audit of admin actions over a real-money economy. |
| **Anti-cheat / market abuse** | Multi-accounting, collusion, botting, scripting, and market manipulation by players. Distinct from economy edge-cases: this is *players* exploiting the system, and it is a fraud surface in a shared real-money economy. |
| **Account lifecycle** | Registration, email verification, password reset, 2FA, session management, recovery, and account deletion. |
| **Dispute resolution** | Player disputes resolved by auditable replay, enabled by the [determinism axiom](design_canon.md#L58). |

### C. Durability & operations

| Item | Why it is product, not prototype |
| --- | --- |
| **Data durability & migrations** | Automated checkpoint/schema migrations (checkpoint compatibility is already treated as sacred), backups, disaster recovery, retention, and erasure hooks. |
| **Observability & operations** | Structured logs, error tracking, metrics/alerting, on-call runbooks, and a status page. Distinct from user analytics: this is *service* health — is the economy alive and are the books reconciling now. |
| **User metric data acquisition** | Product analytics: how users behave, what they retain on, where they drop off. |

### D. Scale & live change

| Item | Why it is product, not prototype |
| --- | --- |
| **Actual server deployment** | Hosting, networking, and running the service beyond the single-machine loopback. |
| **Real concurrency & scale** | Many simultaneous players on one shared live world: tick scheduling under load, latency budget, and cost per user. |
| **Update deployment cycle** | CI/CD, releases, and rollback. |
| **Live economy change management** | Rebalancing or adding products to a *running* world without breaking conservation or fairness: canary, rollback, mid-flight schema migration of an economy. |
| **Edge-case handling system for the economy** | Robustness against pathological states and bounded recovery from them. |

### E. People & UX operations

| Item | Why it is product, not prototype |
| --- | --- |
| **Support & moderation workflow** | Ban/appeal, ticket systems, and a policy for what admins may and may not touch in a real-money economy — beyond a bare backdoor button. |
| **Onboarding & localization/accessibility** | Tutorial/onboarding, localization, and accessibility, so acquisition metrics are meaningful and users can actually play. |

## Phase character

The three phases are *different kinds* of work, not merely different sizes:

- **PoC** proves the market logic.
- **Prototype** adds game features (bounded like the PoC, same kind of work).
- **MVP** adds the product layer, which carries external dependencies — payment
  processors, legal review, hosting, security audit, scale — that do not compress
  the way feature work does.
