package com.personalagents.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.personalagents.app.data.ApiService
import com.personalagents.app.data.CeoAskIn
import com.personalagents.app.data.CeoResponse
import kotlinx.coroutines.launch

/** On-demand Q&A with the CEO — POST /ceo/ask. Every response that touched a
 * sensitive division carries a disclaimer (see DESIGN.md), rendered inline
 * right under the answer, never as a one-time dismissible banner. */
@Composable
fun HomeScreen(apiProvider: () -> ApiService) {
    var question by remember { mutableStateOf("") }
    var response by remember { mutableStateOf<CeoResponse?>(null) }
    var loading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp)
            .verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text("Ask your CEO")
        OutlinedTextField(
            value = question,
            onValueChange = { question = it },
            label = { Text("Question") },
            modifier = Modifier.fillMaxWidth(),
        )
        Button(
            onClick = {
                error = null
                loading = true
                scope.launch {
                    try {
                        response = apiProvider().askCeo(CeoAskIn(question))
                    } catch (e: Exception) {
                        error = e.message ?: "Something went wrong"
                    } finally {
                        loading = false
                    }
                }
            },
            enabled = question.isNotBlank() && !loading,
        ) {
            Text("Ask")
        }

        if (loading) CircularProgressIndicator()
        error?.let { Text("Error: $it") }
        response?.let { r ->
            Text(r.answer)
            r.disclaimer?.let { Text(it) }
        }
    }
}
