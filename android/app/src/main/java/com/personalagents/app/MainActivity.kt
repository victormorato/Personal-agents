package com.personalagents.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.personalagents.app.data.Credentials
import com.personalagents.app.ui.AppNav
import com.personalagents.app.ui.theme.PersonalAgentsTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val credentials = Credentials(applicationContext)
        setContent {
            PersonalAgentsTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    AppNav(credentials = credentials)
                }
            }
        }
    }
}
