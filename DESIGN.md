# Personal Agent Company — Design Decisions

Captured from a grill-me session on 2026-09-18. This is the source of truth for
architectural decisions — update it when a decision changes, don't let the
code and this doc drift apart.

## Architecture

| Area | Decision |
|---|---|
| Platform | Standalone app/service (not a Claude Code skill set) |
| Interface | Native Android app (Kotlin) |
| Backend hosting | Render (web service + managed Postgres + cron job) |
| Backend stack | Python (FastAPI) + PostgreSQL |
| Users | Single-user only — no multi-tenant auth/data isolation |
| Budget | Not a constraint — optimize for capability over cost |

## Data & privacy

- Source of truth: Postgres on Render, encrypted at rest.
- Local backup: encrypted copy on the Android device for offline resilience.
- **Note**: this is a managed third-party cloud (Render), not self-hosted
  hardware. Data is encrypted and account-controlled, but not literally
  "your own infrastructure." Worth remembering given the data involved.

## The CEO agent

- **Trigger model**: proactive but event-driven, not a fixed schedule.
- **Event definition**: the CEO uses its own judgment on what's worth a push
  notification (not hardcoded rules) — a Render cron job periodically feeds
  recent division data to the CEO, which decides whether anything warrants
  surfacing.
- **Division conflicts**: resolved by stakes. Low-stakes conflicts (e.g. minor
  schedule overlap) are auto-resolved by the CEO. Anything touching health,
  money, or legal risk is surfaced to the user explicitly rather than decided
  silently.

## Divisions (v1 scope: Exercise + Finance only)

Medical, legal, nutrition, and other divisions are deferred to a later phase.
The CEO + these two divisions prove the pattern first.

### Sensitive-output framing
Both current and future divisions (especially medical/legal/finance) operate
as **decision-support with strong disclaimers** — they synthesize personal
data into suggestions, but every output that touches health, legal, or
financial decisions is explicitly flagged as not a substitute for a licensed
professional. This is not optional framing; it's a correctness requirement
given the liability and accuracy stakes involved.

### Exercise division
- Data source: Google Fit / wearable sync (not manual-only).
- Tracks activity, streaks, goal progress.

### Finance division
- Data source: manual entry / CSV import (no live bank connection in v1 —
  deferred to avoid the security/compliance weight of a service like Plaid
  in a first version).
- Tracks transactions, budget usage, flags upcoming known bills.

## Second-tier decisions (made pragmatically during build, not separately grilled)

These were explicitly deferred from the grill session — "make sensible calls
as we build." Documented here as each one is decided, so they don't just
live in code comments:

- **Auth (app↔backend)**: single static bearer token (env-configured),
  matching the single-user scope. Not a full auth system — would need
  revisiting if this ever became multi-user.
- **Push notifications**: Firebase Cloud Messaging (the standard for Android).
- **CEO polling cadence**: TBD when the Render cron job is provisioned —
  starting assumption is hourly, adjustable without a redesign.
- **Local backup encryption**: Android Keystore-backed SQLCipher for the
  on-device copy.
- **Disclaimer UX**: attached to every division response object as a
  `disclaimer` field, not just a one-time banner — so it can't be scrolled
  past and forgotten, and the Android UI is expected to render it inline
  with the relevant content every time.

## Explicitly out of scope for v1
- Medical, legal, nutrition divisions
- Bank/Plaid integration
- Multi-user support
- iOS
