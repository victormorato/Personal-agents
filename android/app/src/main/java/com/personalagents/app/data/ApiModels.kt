package com.personalagents.app.data

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// Mirrors backend/app/schemas.py — keep these two in sync by hand; there's
// no shared-schema codegen for a project this size (see DESIGN.md).

@Serializable
data class ExerciseLogIn(
    val source: String = "manual",
    @SerialName("activity_type") val activityType: String,
    @SerialName("duration_minutes") val durationMinutes: Double,
    val calories: Double? = null,
    val notes: String? = null,
    @SerialName("occurred_at") val occurredAt: String,
)

@Serializable
data class ExerciseLogOut(
    val id: Int,
    val source: String,
    @SerialName("activity_type") val activityType: String,
    @SerialName("duration_minutes") val durationMinutes: Double,
    val calories: Double? = null,
    val notes: String? = null,
    @SerialName("occurred_at") val occurredAt: String,
)

@Serializable
data class FinanceTransactionIn(
    val type: String, // "income" | "expense"
    val category: String,
    val amount: Double,
    val description: String? = null,
    @SerialName("occurred_at") val occurredAt: String,
)

@Serializable
data class FinanceTransactionOut(
    val id: Int,
    val type: String,
    val category: String,
    val amount: Double,
    val description: String? = null,
    @SerialName("occurred_at") val occurredAt: String,
)

@Serializable
data class DivisionResponse(
    val summary: String,
    val disclaimer: String? = null,
)

@Serializable
data class CeoAskIn(val question: String)

@Serializable
data class CeoResponse(
    val answer: String,
    val disclaimer: String? = null,
)

@Serializable
data class SurfacedEventOut(
    val id: Int,
    val division: String,
    val summary: String,
    val stakes: String,
    val disclaimer: String? = null,
    @SerialName("created_at") val createdAt: String,
    val delivered: Boolean,
)

@Serializable
data class EventCheckResult(@SerialName("surfaced_count") val surfacedCount: Int)
