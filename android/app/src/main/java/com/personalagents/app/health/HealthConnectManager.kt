package com.personalagents.app.health

import android.content.Context
import androidx.health.connect.client.HealthConnectClient
import androidx.health.connect.client.permission.HealthPermission
import androidx.health.connect.client.records.ExerciseSessionRecord
import androidx.health.connect.client.request.ReadRecordsRequest
import androidx.health.connect.client.time.TimeRangeFilter
import com.personalagents.app.data.ExerciseLogIn
import java.time.Instant
import java.time.temporal.ChronoUnit

/**
 * Reads workout sessions from Health Connect (on-device, permission-gated —
 * see DESIGN.md, Exercise division: replaced the deprecated Google Fit API
 * on 2026-09-18) and converts them to the shape the backend expects.
 *
 * This only reads; nothing is written back to Health Connect.
 */
class HealthConnectManager(private val context: Context) {

    val permissions = setOf(
        HealthPermission.getReadPermission(ExerciseSessionRecord::class),
    )

    fun isAvailable(): Boolean =
        HealthConnectClient.getSdkStatus(context) == HealthConnectClient.SDK_AVAILABLE

    suspend fun hasPermissions(): Boolean {
        val client = HealthConnectClient.getOrCreate(context)
        return client.permissionController.getGrantedPermissions().containsAll(permissions)
    }

    /** Fetches sessions from the last [days] days and maps them to the
     * backend's ExerciseLogIn shape. Caller is responsible for POSTing each
     * one to ApiService.logExercise — this class only reads Health Connect,
     * it doesn't know about the network layer. */
    suspend fun recentSessions(days: Long = 7): List<ExerciseLogIn> {
        val client = HealthConnectClient.getOrCreate(context)
        val now = Instant.now()
        val request = ReadRecordsRequest(
            recordType = ExerciseSessionRecord::class,
            timeRangeFilter = TimeRangeFilter.between(now.minus(days, ChronoUnit.DAYS), now),
        )
        val response = client.readRecords(request)
        return response.records.map { session ->
            val minutes = ChronoUnit.MINUTES.between(session.startTime, session.endTime).toDouble()
            ExerciseLogIn(
                source = "health_connect",
                activityType = session.exerciseType.toString(),
                durationMinutes = minutes,
                notes = session.title,
                occurredAt = session.startTime.toString(),
            )
        }
    }
}
