package com.personalagents.app.data

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

/**
 * Holds the backend base URL and bearer token on-device, encrypted via the
 * Android Keystore (see DESIGN.md — local backup/secret encryption). Never
 * hardcoded in source: the app prompts for both on first launch via
 * SettingsScreen, matching the single-user, no-hardcoded-secrets decision.
 */
class Credentials(context: Context) {
    private val prefs: SharedPreferences

    init {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        prefs = EncryptedSharedPreferences.create(
            context,
            "personal_agents_secure_prefs",
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
        )
    }

    var baseUrl: String?
        get() = prefs.getString(KEY_BASE_URL, null)
        set(value) = prefs.edit().putString(KEY_BASE_URL, value).apply()

    var authToken: String?
        get() = prefs.getString(KEY_AUTH_TOKEN, null)
        set(value) = prefs.edit().putString(KEY_AUTH_TOKEN, value).apply()

    val isConfigured: Boolean
        get() = !baseUrl.isNullOrBlank() && !authToken.isNullOrBlank()

    private companion object {
        const val KEY_BASE_URL = "base_url"
        const val KEY_AUTH_TOKEN = "auth_token"
    }
}
