package com.personalagents.app.notifications

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import com.personalagents.app.R

/**
 * Receives the CEO's proactive pushes (see DESIGN.md — CEO agent, backend
 * worker/event_check.py). Device-token registration with the backend isn't
 * wired up yet (see backend TODO in worker/event_check.py) — this service
 * will start receiving real pushes once that's connected.
 */
class CeoMessagingService : FirebaseMessagingService() {

    override fun onMessageReceived(message: RemoteMessage) {
        val title = message.notification?.title ?: "Personal Agents"
        val body = message.notification?.body ?: return
        showNotification(title, body)
    }

    override fun onNewToken(token: String) {
        // TODO: POST this token to the backend once a device-token-registration
        // endpoint exists there (see worker/event_check.py's _DEVICE_TOKEN_PLACEHOLDER).
    }

    private fun showNotification(title: String, body: String) {
        val channelId = "ceo_events"
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            manager.createNotificationChannel(
                NotificationChannel(channelId, "CEO updates", NotificationManager.IMPORTANCE_DEFAULT)
            )
        }
        val notification = NotificationCompat.Builder(this, channelId)
            .setSmallIcon(R.mipmap.ic_launcher)
            .setContentTitle(title)
            .setContentText(body)
            .setAutoCancel(true)
            .build()
        NotificationManagerCompat.from(this).notify(System.currentTimeMillis().toInt(), notification)
    }
}
