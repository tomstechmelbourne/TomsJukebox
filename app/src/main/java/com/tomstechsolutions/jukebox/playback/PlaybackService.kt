package com.tomstechsolutions.jukebox.playback

import android.app.KeyguardManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.media.AudioDeviceCallback
import android.media.AudioDeviceInfo
import android.media.AudioManager
import android.net.Uri
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.view.KeyEvent
import androidx.annotation.OptIn
import androidx.core.content.ContextCompat
import androidx.media3.common.AudioAttributes
import androidx.media3.common.C
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.common.util.UnstableApi
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.session.MediaSession
import androidx.media3.session.MediaSessionService
import com.google.common.util.concurrent.Futures
import com.google.common.util.concurrent.ListenableFuture
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.system.LockActivity
import com.tomstechsolutions.jukebox.system.Widgets
import com.tomstechsolutions.jukebox.ui.MainActivity
import kotlinx.coroutines.MainScope
import kotlinx.coroutines.cancel
import kotlin.math.sqrt

/** Background playback (foreground service type mediaPlayback, as Android 14–17 require). The session it publishes
 *  is what the lock screen, notification, Samsung Now Bar, Bluetooth cars and watches show. */
@OptIn(UnstableApi::class)
class PlaybackService : MediaSessionService() {
    lateinit var player: ExoPlayer
    private var session: MediaSession? = null
    val eq = EqEngine()
    lateinit var viz: Viz
    lateinit var recorder: Recorder
    private val scope = MainScope()
    val sleep = SleepTimer(scope) { if (::player.isInitialized) player else null }
    private val main = Handler(Looper.getMainLooper())

    override fun onCreate() {
        super.onCreate()
        viz = Viz(this)
        recorder = Recorder(this)
        player = ExoPlayer.Builder(this)
            .setAudioAttributes(AudioAttributes.Builder().setUsage(C.USAGE_MEDIA).setContentType(C.AUDIO_CONTENT_TYPE_MUSIC).build(), true)
            .setHandleAudioBecomingNoisy(true)
            .setWakeMode(C.WAKE_MODE_NETWORK)
            .build()
        player.addListener(object : Player.Listener {
            override fun onAudioSessionIdChanged(audioSessionId: Int) { eq.attach(audioSessionId); viz.attach(audioSessionId) }
            override fun onMediaItemTransition(mediaItem: MediaItem?, reason: Int) {
                if (reason == Player.MEDIA_ITEM_TRANSITION_REASON_AUTO) sleep.onAutoTransition()
                Core.saveQueue(); updateWidgets()
            }
            override fun onPlaybackStateChanged(state: Int) { if (state == Player.STATE_ENDED) sleep.onEnded(); updateWidgets() }
            override fun onIsPlayingChanged(isPlaying: Boolean) {
                updateWidgets()
                main.removeCallbacks(widgetTick); if (isPlaying) main.postDelayed(widgetTick, 20_000)
                if (!isPlaying) { Core.saveQueue(); Core.savePodPos() }
                setShake(isPlaying && Prefs.shakeSkip.value)
            }
            override fun onMediaMetadataChanged(mediaMetadata: androidx.media3.common.MediaMetadata) { updateWidgets() }
        })
        eq.attach(player.audioSessionId)
        viz.attach(player.audioSessionId)

        val open = PendingIntent.getActivity(this, 0, Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP).putExtra("open_now", true),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        session = MediaSession.Builder(this, player).setSessionActivity(open).setCallback(Callback()).build()
        Core.service = this

        ContextCompat.registerReceiver(this, screenReceiver, IntentFilter(Intent.ACTION_SCREEN_ON), ContextCompat.RECEIVER_NOT_EXPORTED)
        audioManager().registerAudioDeviceCallback(deviceCallback, main)
        deviceCallbackSince = System.currentTimeMillis()
    }

    override fun onGetSession(controllerInfo: MediaSession.ControllerInfo): MediaSession? = session

    override fun onTaskRemoved(rootIntent: Intent?) {
        val p = session?.player
        if (p == null || !p.playWhenReady || p.mediaItemCount == 0) stopSelf()
    }

    override fun onDestroy() {
        Core.saveQueue()
        try { unregisterReceiver(screenReceiver) } catch (_: Exception) { }
        try { audioManager().unregisterAudioDeviceCallback(deviceCallback) } catch (_: Exception) { }
        setShake(false)
        sleep.cancel()
        recorder.stop()
        eq.release(); viz.release()
        session?.run { player.release(); release() }
        session = null
        Core.service = null
        scope.cancel()
        super.onDestroy()
    }

    private fun audioManager() = getSystemService(Context.AUDIO_SERVICE) as AudioManager

    fun volumeStep(dir: Int) {
        audioManager().adjustStreamVolume(AudioManager.STREAM_MUSIC, if (dir > 0) AudioManager.ADJUST_RAISE else AudioManager.ADJUST_LOWER, AudioManager.FLAG_SHOW_UI)
    }

    fun refreshViz() { viz.attach(player.audioSessionId) }

    private fun updateWidgets() {
        val md = player.mediaMetadata
        val idx = player.currentMediaItemIndex
        val next = (1..3).mapNotNull { k -> if (idx + k < player.mediaItemCount) player.getMediaItemAt(idx + k).mediaMetadata.title?.toString() else null }
        Widgets.update(this, com.tomstechsolutions.jukebox.system.WState(md.title?.toString() ?: "", md.artist?.toString() ?: "", player.isPlaying, md.artworkData,
            player.currentPosition, if (player.duration > 0) player.duration else 0, next, player.currentMediaItem?.mediaId ?: "",
            player.shuffleModeEnabled, player.repeatMode, md.extras?.getString("kind") ?: ""))
    }

    private val widgetTick = object : Runnable {
        override fun run() { if (::player.isInitialized && player.isPlaying) { updateWidgets(); main.postDelayed(this, 20_000) } }
    }

    // ---------- media buttons: 1 press play/pause, 2 next, 3 previous ----------
    private var presses = 0
    private val pressRunnable = Runnable {
        when (presses) { 1 -> if (player.isPlaying) player.pause() else player.play(); 2 -> player.seekToNextMediaItem(); else -> player.seekToPreviousMediaItem() }
        presses = 0
    }

    private inner class Callback : MediaSession.Callback {
        override fun onAddMediaItems(mediaSession: MediaSession, controller: MediaSession.ControllerInfo, mediaItems: MutableList<MediaItem>): ListenableFuture<MutableList<MediaItem>> {
            val fixed = mediaItems.map { m ->
                val u = m.requestMetadata.mediaUri ?: m.localConfiguration?.uri ?: Uri.parse(m.mediaId)
                val b = m.buildUpon().setUri(u)
                if (u.toString().contains(".m3u8")) b.setMimeType("application/x-mpegURL")
                b.build()
            }.toMutableList()
            return Futures.immediateFuture(fixed)
        }

        @Deprecated("kept for older media3 behaviour")
        override fun onPlaybackResumption(mediaSession: MediaSession, controller: MediaSession.ControllerInfo): ListenableFuture<MediaSession.MediaItemsWithStartPosition> {
            val items = Core.savedItems()
            return Futures.immediateFuture(MediaSession.MediaItemsWithStartPosition(items,
                Prefs.lastIndex.value.coerceIn(0, (items.size - 1).coerceAtLeast(0)), Prefs.lastPos.value))
        }

        override fun onMediaButtonEvent(session: MediaSession, controllerInfo: MediaSession.ControllerInfo, intent: Intent): Boolean {
            if (!Prefs.headsetTriple.value) return false
            @Suppress("DEPRECATION")
            val ev: KeyEvent = (if (Build.VERSION.SDK_INT >= 33) intent.getParcelableExtra(Intent.EXTRA_KEY_EVENT, KeyEvent::class.java)
            else intent.getParcelableExtra(Intent.EXTRA_KEY_EVENT)) ?: return false
            if (ev.keyCode != KeyEvent.KEYCODE_HEADSETHOOK && ev.keyCode != KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE) return false
            if (ev.action == KeyEvent.ACTION_DOWN && ev.repeatCount == 0) {
                presses++
                main.removeCallbacks(pressRunnable)
                main.postDelayed(pressRunnable, 450)
            }
            return true
        }
    }

    // ---------- shake to skip ----------
    private var shakeOn = false
    private var lastShake = 0L
    private val shakeListener = object : SensorEventListener {
        override fun onSensorChanged(e: SensorEvent) {
            val g = sqrt(e.values[0] * e.values[0] + e.values[1] * e.values[1] + e.values[2] * e.values[2]) / SensorManager.GRAVITY_EARTH
            val now = System.currentTimeMillis()
            if (g > 2.7f && now - lastShake > 1200) { lastShake = now; if (player.hasNextMediaItem()) player.seekToNextMediaItem() }
        }
        override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
    }

    private fun setShake(on: Boolean) {
        if (on == shakeOn) return
        val sm = getSystemService(Context.SENSOR_SERVICE) as SensorManager
        if (on) sm.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)?.let { sm.registerListener(shakeListener, it, SensorManager.SENSOR_DELAY_UI) }
        else sm.unregisterListener(shakeListener)
        shakeOn = on
    }

    // ---------- auto-play when headphones / Bluetooth connect ----------
    private var deviceCallbackSince = 0L
    private val deviceCallback = object : AudioDeviceCallback() {
        override fun onAudioDevicesAdded(added: Array<out AudioDeviceInfo>) {
            if (System.currentTimeMillis() - deviceCallbackSince < 3000) return
            if (!Prefs.autoPlayHeadset.value || player.isPlaying || player.mediaItemCount == 0) return
            val types = mutableSetOf(AudioDeviceInfo.TYPE_WIRED_HEADSET, AudioDeviceInfo.TYPE_WIRED_HEADPHONES, AudioDeviceInfo.TYPE_BLUETOOTH_A2DP)
            if (Build.VERSION.SDK_INT >= 26) types += AudioDeviceInfo.TYPE_USB_HEADSET
            if (added.any { it.isSink && it.type in types }) { player.prepare(); player.play() }
        }
    }

    // ---------- Tom's Jukebox lock screen ----------
    private val screenReceiver = object : BroadcastReceiver() {
        override fun onReceive(c: Context, i: Intent) {
            if (!Prefs.customLock.value || !player.isPlaying) return
            val km = getSystemService(Context.KEYGUARD_SERVICE) as KeyguardManager
            if (!km.isKeyguardLocked) return
            if (Build.VERSION.SDK_INT >= 29 && !Settings.canDrawOverlays(c)) return
            try { startActivity(Intent(c, LockActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_NO_USER_ACTION)) } catch (_: Exception) { }
        }
    }
}
