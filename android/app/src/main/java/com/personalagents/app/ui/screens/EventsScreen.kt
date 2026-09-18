package com.personalagents.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.personalagents.app.data.ApiService
import com.personalagents.app.data.SurfacedEventOut
import kotlinx.coroutines.launch

/** History of everything the CEO decided was worth surfacing — GET
 * /ceo/events. Dismissing here calls DELETE /ceo/events/{id}. */
@Composable
fun EventsScreen(apiProvider: () -> ApiService) {
    var events by remember { mutableStateOf<List<SurfacedEventOut>>(emptyList()) }
    val scope = rememberCoroutineScope()

    suspend fun refresh() {
        events = apiProvider().listEvents()
    }

    LaunchedEffect(Unit) { refresh() }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("CEO updates")
        if (events.isEmpty()) {
            Text("Nothing surfaced yet.")
        }
        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(events, key = { it.id }) { event ->
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    Column {
                        Text("[${event.division}] ${event.summary}")
                        event.disclaimer?.let { Text(it) }
                    }
                    Button(onClick = {
                        scope.launch {
                            apiProvider().deleteEvent(event.id)
                            refresh()
                        }
                    }) {
                        Text("Dismiss")
                    }
                }
            }
        }
    }
}
