package com.personalagents.app.data

import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

/** Mirrors the route files under backend/app/routers — one interface, matching the backend's flat route layout. */
interface ApiService {

    @POST("exercise/logs")
    suspend fun logExercise(@Body body: ExerciseLogIn): ExerciseLogOut

    @GET("exercise/logs")
    suspend fun listExerciseLogs(): List<ExerciseLogOut>

    @POST("finance/transactions")
    suspend fun logTransaction(@Body body: FinanceTransactionIn): FinanceTransactionOut

    @GET("finance/transactions")
    suspend fun listTransactions(): List<FinanceTransactionOut>

    @GET("finance/summary")
    suspend fun financeSummary(): DivisionResponse

    @POST("ceo/ask")
    suspend fun askCeo(@Body body: CeoAskIn): CeoResponse

    @POST("ceo/event-check")
    suspend fun runEventCheck(): EventCheckResult

    @GET("ceo/events")
    suspend fun listEvents(): List<SurfacedEventOut>

    @DELETE("ceo/events/{id}")
    suspend fun deleteEvent(@Path("id") id: Int)
}
