# Personal Agents — Android app

Native Kotlin/Jetpack Compose client for the backend in `../backend`. See
`../DESIGN.md` for the architectural decisions this follows.

## Required before this builds at all

**Firebase project (for push notifications):**

1. Go to the [Firebase Console](https://console.firebase.google.com), create a
   project (any name).
2. Add an Android app to it with package name **`com.personalagents.app`**
   (must match exactly — see `app/build.gradle.kts` `applicationId`).
3. Download the generated `google-services.json` and place it at
   `android/app/google-services.json`.

The `com.google.gms.google-services` Gradle plugin (already wired into
`app/build.gradle.kts`) fails the build immediately if that file is missing —
this isn't optional for compiling, only for whether push notifications
actually work once it's running.

**Health Connect (for exercise sync):**

The Health Connect app itself must be present on the test device/emulator —
built into Android 14+, installable from the Play Store on Android 9–13. No
project-side setup beyond what's already in the manifest/gradle files.

## Opening the project

Open the `android/` folder (not the repo root) in Android Studio — it should
sync Gradle automatically. First build will also need the Android SDK
installed via Android Studio's SDK Manager if you haven't used it before.

## First run

The app has no hardcoded backend URL or auth token (see `DESIGN.md` — Auth
app↔backend: neither is ever committed to source). On first launch it opens
directly to the **Settings** tab — enter:

- **Backend URL**: `https://personal-agents-api.onrender.com/`
- **API auth token**: the same `API_AUTH_TOKEN` value set in Render's
  environment variables for the web service

Both are stored on-device via `EncryptedSharedPreferences` (Android
Keystore-backed — matches the local-encryption decision in `DESIGN.md`).

## What's implemented vs. stubbed

| Feature | Status |
|---|---|
| CEO Q&A (`/ceo/ask`) | Working |
| Exercise logging (manual) | Working |
| Finance logging (manual) | Working |
| CEO notification history + dismiss | Working |
| Health Connect sync | Working (reads `ExerciseSessionRecord`, posts to backend) — needs a real device with Health Connect and at least one logged workout to see data |
| FCM push delivery | Receiving side implemented (`CeoMessagingService`); **device-token registration with the backend is not wired up yet** — the backend's cron worker has a placeholder for this (see `backend/worker/event_check.py`). Until that's connected, the app can receive a push if one were sent, but the backend has no way to address this specific device yet. |

## Known gaps / next steps

- No `strings.xml`-based i18n beyond the app name — fine for a single-user app, revisit if that ever changes.
- No tests yet.
- App icon is a placeholder vector shape, not real branding.
