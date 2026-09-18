package com.personalagents.app.data

import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Interceptor
import okhttp3.Response
import retrofit2.Retrofit

/**
 * Builds a Retrofit client against whatever base URL + token are currently
 * in [Credentials]. Rebuilt whenever those change (e.g. after the user
 * edits them in Settings) rather than cached as a singleton for the app's
 * whole lifetime.
 */
object ApiClient {
    private val json = Json { ignoreUnknownKeys = true }

    fun create(credentials: Credentials): ApiService {
        val baseUrl = credentials.baseUrl?.let { if (it.endsWith("/")) it else "$it/" }
            ?: error("Backend URL not configured — open Settings first.")
        val token = credentials.authToken ?: error("Auth token not configured — open Settings first.")

        val authInterceptor = Interceptor { chain: Interceptor.Chain ->
            val request = chain.request().newBuilder()
                .addHeader("Authorization", "Bearer $token")
                .build()
            chain.proceed(request)
        }

        val client = OkHttpClient.Builder()
            .addInterceptor(authInterceptor)
            .build()

        return Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(client)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
            .create(ApiService::class.java)
    }
}
