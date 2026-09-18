package com.personalagents.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.health.connect.client.PermissionController
import androidx.compose.material3.Button
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.personalagents.app.data.ApiService
import com.personalagents.app.data.ExerciseLogIn
import com.personalagents.app.data.ExerciseLogOut
import com.personalagents.app.health.HealthConnectManager
import kotlinx.coroutines.launch
import java.time.Instant

@Composable
fun ExerciseScreen(apiProvider: () -> ApiService) {
    val context = LocalContext.current
    val healthConnect = remember { HealthConnectManager(context) }
    var logs by remember { mutableStateOf<List<ExerciseLogOut>>(emptyList()) }
    var activityType by remember { mutableStateOf("") }
    var minutes by remember { mutableStateOf("") }
    var syncStatus by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()

    val permissionLauncher = rememberLauncherForActivityResult(
        PermissionController.createRequestPermissionResultContract()
    ) { granted ->
        syncStatus = if (granted.containsAll(healthConnect.permissions)) {
            "Permission granted — tap Sync again."
        } else {
            "Permission was not granted."
        }
    }

    suspend fun refresh() {
        logs = apiProvider().listExerciseLogs()
    }

    LaunchedEffect(Unit) { refresh() }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Log a workout")
        OutlinedTextField(
            value = activityType,
            onValueChange = { activityType = it },
            label = { Text("Activity (e.g. running)") },
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = minutes,
            onValueChange = { minutes = it },
            label = { Text("Duration (minutes)") },
            modifier = Modifier.fillMaxWidth(),
        )
        Button(
            onClick = {
                val durationMinutes = minutes.toDoubleOrNull() ?: return@Button
                scope.launch {
                    apiProvider().logExercise(
                        ExerciseLogIn(
                            activityType = activityType,
                            durationMinutes = durationMinutes,
                            occurredAt = Instant.now().toString(),
                        )
                    )
                    activityType = ""
                    minutes = ""
                    refresh()
                }
            },
            enabled = activityType.isNotBlank() && minutes.toDoubleOrNull() != null,
        ) {
            Text("Log")
        }

        Button(
            onClick = {
                scope.launch {
                    if (!healthConnect.isAvailable()) {
                        syncStatus = "Health Connect isn't installed on this device."
                        return@launch
                    }
                    if (!healthConnect.hasPermissions()) {
                        syncStatus = "Requesting Health Connect permission…"
                        permissionLauncher.launch(healthConnect.permissions)
                        return@launch
                    }
                    val sessions = healthConnect.recentSessions()
                    sessions.forEach { apiProvider().logExercise(it) }
                    syncStatus = "Synced ${sessions.size} session(s) from Health Connect."
                    refresh()
                }
            },
        ) {
            Text("Sync from Health Connect")
        }
        syncStatus?.let { Text(it) }

        Text("Recent logs")
        LazyColumn(verticalArrangement = Arrangement.spacedBy(4.dp)) {
            items(logs) { log ->
                Text("${log.activityType} — ${log.durationMinutes.toInt()} min (${log.source})")
            }
        }
    }
}
