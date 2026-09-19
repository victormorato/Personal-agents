package com.personalagents.app.ui

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.DirectionsRun
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material.icons.filled.Paid
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.personalagents.app.data.ApiClient
import com.personalagents.app.data.Credentials
import com.personalagents.app.ui.screens.EventsScreen
import com.personalagents.app.ui.screens.ExerciseScreen
import com.personalagents.app.ui.screens.FinanceScreen
import com.personalagents.app.ui.screens.HomeScreen
import com.personalagents.app.ui.screens.SettingsScreen

private sealed class Destination(val route: String, val label: String, val icon: androidx.compose.ui.graphics.vector.ImageVector) {
    data object Home : Destination("home", "CEO", Icons.Filled.Home)
    data object Exercise : Destination("exercise", "Exercise", Icons.AutoMirrored.Filled.DirectionsRun)
    data object Finance : Destination("finance", "Finance", Icons.Filled.Paid)
    data object Events : Destination("events", "Updates", Icons.Filled.Notifications)
    data object Settings : Destination("settings", "Settings", Icons.Filled.Settings)
}

private val bottomDestinations = listOf(Destination.Home, Destination.Exercise, Destination.Finance, Destination.Events, Destination.Settings)

@Composable
fun AppNav(credentials: Credentials) {
    val navController = rememberNavController()
    // If the app isn't configured yet, Settings is genuinely the only usable
    // screen — every API call would fail without a base URL/token — so it's
    // the start destination rather than Home.
    val startDestination = if (credentials.isConfigured) Destination.Home.route else Destination.Settings.route

    Scaffold(
        bottomBar = {
            NavigationBar {
                val backStackEntry by navController.currentBackStackEntryAsState()
                val currentRoute = backStackEntry?.destination
                bottomDestinations.forEach { destination ->
                    NavigationBarItem(
                        icon = { Icon(destination.icon, contentDescription = destination.label) },
                        label = { androidx.compose.material3.Text(destination.label) },
                        selected = currentRoute?.hierarchy?.any { it.route == destination.route } == true,
                        onClick = {
                            navController.navigate(destination.route) {
                                popUpTo(navController.graph.findStartDestination().id) { saveState = true }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                    )
                }
            }
        },
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = startDestination,
            modifier = Modifier.padding(innerPadding),
        ) {
            composable(Destination.Home.route) {
                HomeScreen(apiProvider = { ApiClient.create(credentials) })
            }
            composable(Destination.Exercise.route) {
                ExerciseScreen(apiProvider = { ApiClient.create(credentials) })
            }
            composable(Destination.Finance.route) {
                FinanceScreen(apiProvider = { ApiClient.create(credentials) })
            }
            composable(Destination.Events.route) {
                EventsScreen(apiProvider = { ApiClient.create(credentials) })
            }
            composable(Destination.Settings.route) {
                SettingsScreen(credentials = credentials)
            }
        }
    }
}
