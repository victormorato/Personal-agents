# Personal Agents — Android app

Native Kotlin/Jetpack Compose client for the backend in `../backend`. See
`../DESIGN.md` for the architectural decisions this follows.

## Build status

**Verified building on Windows via command line** (2026-09-19) —
`.\gradlew.bat assembleDebug` succeeds cleanly with zero warnings, producing
`app/build/outputs/apk/debug/app-debug.apk`. Local toolchain used: Temurin
JDK 17, Android SDK platform 35 + build-tools 35.0.0 (installed via Google's
official [Android CLI](https://developer.android.com/tools/agents/android-cli)),
Gradle 8.9 (wrapper committed — `gradlew`/`gradlew.bat`/`gradle-wrapper.jar`).

**Firebase is live** (2026-09-19) — `google-services.json` is in place at
`android/app/google-services.json` and the `com.google.gms.google-services`
plugin is enabled. `processDebugGoogleServices` runs and the build stays
clean. **That file is gitignored, not committed** — a Claude Code auto-mode
guardrail flagged committing it as credential-leakage risk, and the cautious
default (keep it out of the public repo) was kept rather than overridden.
If you set this project up on a different machine, you'll need to re-download
`google-services.json` from the Firebase console and place it there again.

## If you need to redo the Firebase setup from scratch

1. Go to the [Firebase Console](https://console.firebase.google.com), create a
   project (any name).
2. Add an Android app to it with package name **`com.personalagents.app`**
   (must match exactly — see `app/build.gradle.kts` `applicationId`).
3. Download the generated `google-services.json` and place it at
   `android/app/google-services.json`.

**Health Connect (for exercise sync):**

The Health Connect app itself must be present on the test device/emulator —
built into Android 14+, installable from the Play Store on Android 9–13. No
project-side setup beyond what's already in the manifest/gradle files.

## Building locally

```powershell
cd android
.\gradlew.bat assembleDebug
```

Requires `JAVA_HOME` set to a JDK 17 install and `local.properties` pointing
`sdk.dir` at your Android SDK (both are machine-specific and gitignored —
set them up once per machine, not committed).

## Opening the project in Android Studio

Open the `android/` folder (not the repo root) — it should detect the
existing SDK/Gradle setup and sync automatically.

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
