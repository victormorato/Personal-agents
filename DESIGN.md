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
- Data source: **Health Connect** (not manual-only). Originally scoped as
  "Google Fit" — corrected on 2026-09-18 when starting the Android build,
  since Google has deprecated the old Fitness API in favor of Health
  Connect as the current on-device fitness/health data store. Same intent
  (pull real activity data automatically), different, current API.
- Tracks activity, streaks, goal progress.

### Finance division
- Data source: manual entry / CSV import, **plus a bidirectional Google
  Sheets sync** (added 2026-09-19 — see "Google Sheets integration" below).
  Still no live bank connection (Plaid-style) — the Sheets sync is
  lower-stakes than that and doesn't change that boundary.
- Tracks transactions, accounts, budget usage, flags upcoming known bills.

## Google Sheets integration (added 2026-09-19)

Grilled separately from the original build — see the design tree below.
Started from "integrate finance with my Google Sheet" and reframed once a
real tooling constraint surfaced (Claude has no cell/formula-level Sheets
API access, only whole-file operations via the connected Drive tool).

- **Sync direction**: bidirectional — both the app and the sheet can be the
  point of entry for a transaction; the sync reconciles both.
- **Sync location**: the Render backend holds its own Google credentials
  (a service account, not OAuth — no user present for a repeated consent
  flow) and syncs on its own, independent of any Claude session or the
  Android app being open.
- **Sheet scope — reframed**: the sheet does **not** stay the "smart" layer.
  The user's real sheet ("2026 - Finances") was significantly more complex
  than assumed — 6 real bank/credit accounts, hand-maintained dashboard and
  yearly rollups, a new sheet started each year — and the user wants it
  more dynamic: live projections, month/year comparisons, and predictive
  budget-overrun alerts. Claude cannot build spreadsheet formulas/multi-tab
  structure through any available tool, so **the smart work moves to the
  backend + CEO agent** (which can actually be built and verified) instead
  of trying to force Google Sheets into being dynamic:
  - **Sheet**: simplified to one clean, continuous "Transactions" tab (no
    more per-account column blocks, no yearly sheet restart — one running
    log, filterable by date).
  - **Backend**: gains an `Account` concept and a per-category `Budget`,
    computes projected balances, and forecasts budget-overrun risk.
  - **CEO**: the existing event-check mechanism (already stakes-based, see
    above) is the delivery channel for a "trending over budget" alert —
    no new alerting mechanism needed, this is the one that already exists.
  - **App**: comparison/trend views live here, not in Sheets charts.
- **Dedup / conflict handling**: the sheet gets a backend-written `Synced
  ID` column. A row without one is new (not yet in Postgres) and gets
  imported; a row with one is already synced and skipped on subsequent
  syncs. v1 doesn't handle edits to already-synced rows — only new rows in
  either direction. Revisit if that turns out to matter in practice.
- **Sync trigger**: rides the existing hourly cron job (extends
  `worker/event_check.py`'s cadence) rather than adding a second schedule.
- **Auth setup**: needs a Google Cloud service account with the Sheets API
  enabled, its JSON key stored as a Render secret, and the sheet shared
  with the service account's email — a one-time manual step (Google Cloud
  project creation is account-level, same category as the Firebase setup
  above).

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
