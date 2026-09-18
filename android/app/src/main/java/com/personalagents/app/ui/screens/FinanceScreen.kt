package com.personalagents.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
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
import androidx.compose.ui.unit.dp
import com.personalagents.app.data.ApiService
import com.personalagents.app.data.DivisionResponse
import com.personalagents.app.data.FinanceTransactionIn
import com.personalagents.app.data.FinanceTransactionOut
import kotlinx.coroutines.launch
import java.time.Instant

/** Finance division is manual-entry only in v1 (see DESIGN.md — no live
 * bank connection yet), so this screen is the primary way data gets in. */
@Composable
fun FinanceScreen(apiProvider: () -> ApiService) {
    var transactions by remember { mutableStateOf<List<FinanceTransactionOut>>(emptyList()) }
    var summary by remember { mutableStateOf<DivisionResponse?>(null) }
    var type by remember { mutableStateOf("expense") }
    var typeMenuExpanded by remember { mutableStateOf(false) }
    var category by remember { mutableStateOf("") }
    var amount by remember { mutableStateOf("") }
    val scope = rememberCoroutineScope()

    suspend fun refresh() {
        transactions = apiProvider().listTransactions()
        summary = apiProvider().financeSummary()
    }

    LaunchedEffect(Unit) { refresh() }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Log a transaction")

        Button(onClick = { typeMenuExpanded = true }) { Text(type) }
        DropdownMenu(expanded = typeMenuExpanded, onDismissRequest = { typeMenuExpanded = false }) {
            listOf("expense", "income").forEach { option ->
                DropdownMenuItem(text = { Text(option) }, onClick = { type = option; typeMenuExpanded = false })
            }
        }

        OutlinedTextField(
            value = category,
            onValueChange = { category = it },
            label = { Text("Category") },
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = amount,
            onValueChange = { amount = it },
            label = { Text("Amount") },
            modifier = Modifier.fillMaxWidth(),
        )
        Button(
            onClick = {
                val value = amount.toDoubleOrNull() ?: return@Button
                scope.launch {
                    apiProvider().logTransaction(
                        FinanceTransactionIn(
                            type = type,
                            category = category,
                            amount = value,
                            occurredAt = Instant.now().toString(),
                        )
                    )
                    category = ""
                    amount = ""
                    refresh()
                }
            },
            enabled = category.isNotBlank() && amount.toDoubleOrNull() != null,
        ) {
            Text("Log")
        }

        summary?.let { s ->
            Text(s.summary)
            s.disclaimer?.let { Text(it) }
        }

        Text("Recent transactions")
        LazyColumn(verticalArrangement = Arrangement.spacedBy(4.dp)) {
            items(transactions) { txn ->
                Text("${txn.type}: ${txn.category} — ${txn.amount}")
            }
        }
    }
}
