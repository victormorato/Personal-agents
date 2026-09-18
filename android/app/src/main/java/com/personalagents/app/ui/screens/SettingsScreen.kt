package com.personalagents.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.personalagents.app.data.Credentials

/**
 * First-run (and revisitable) screen for the backend URL + bearer token.
 * Neither is ever hardcoded in source — see DESIGN.md, Auth (app<->backend).
 */
@Composable
fun SettingsScreen(credentials: Credentials) {
    var baseUrl by remember { mutableStateOf(credentials.baseUrl ?: "https://personal-agents-api.onrender.com/") }
    var token by remember { mutableStateOf(credentials.authToken ?: "") }
    var saved by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text("Backend connection")
        OutlinedTextField(
            value = baseUrl,
            onValueChange = { baseUrl = it; saved = false },
            label = { Text("Backend URL") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = token,
            onValueChange = { token = it; saved = false },
            label = { Text("API auth token") },
            singleLine = true,
            visualTransformation = PasswordVisualTransformation(),
            modifier = Modifier.fillMaxWidth(),
        )
        Button(
            onClick = {
                credentials.baseUrl = baseUrl.trim()
                credentials.authToken = token.trim()
                saved = true
            },
            enabled = baseUrl.isNotBlank() && token.isNotBlank(),
        ) {
            Text("Save")
        }
        if (saved) {
            Text("Saved. Switch tabs to start using the app.")
        }
    }
}
