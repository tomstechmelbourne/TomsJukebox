package com.tomstechsolutions.jukebox.playback

import android.annotation.SuppressLint
import android.bluetooth.BluetoothAdapter
import android.os.Build
import androidx.media3.common.Player
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.data.Messages
import com.tomstechsolutions.jukebox.t
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

/** Hẹn Giờ Tắt Nhạc: after N minutes, at a time, at the end of the song or of the list; fades out gently. */
class SleepTimer(private val scope: CoroutineScope, private val player: () -> Player?) {
    enum class Mode { NONE, MINUTES, AT, END_TRACK, END_QUEUE }

    private var job: Job? = null
    var mode = Mode.NONE; private set
    private var endAt = 0L

    fun start(m: Mode, minutes: Int = 0, atMillis: Long = 0) {
        cancel(false)
        mode = m
        endAt = when (m) {
            Mode.MINUTES -> System.currentTimeMillis() + minutes * 60_000L
            Mode.AT -> atMillis
            else -> 0L
        }
        publish()
        job = scope.launch {
            while (isActive && mode != Mode.NONE) {
                tick()
                delay(500)
            }
        }
    }

    fun addMinutes(m: Int) {
        if (mode == Mode.MINUTES || mode == Mode.AT) { endAt += m * 60_000L; publish(); player()?.volume = 1f }
        else start(Mode.MINUTES, m)
    }

    private fun remainingMs(): Long {
        val p = player() ?: return Long.MAX_VALUE
        return when (mode) {
            Mode.MINUTES, Mode.AT -> endAt - System.currentTimeMillis()
            Mode.END_TRACK -> if (p.duration > 0) p.duration - p.currentPosition else Long.MAX_VALUE
            Mode.END_QUEUE -> {
                if (p.duration <= 0) Long.MAX_VALUE
                else if (p.hasNextMediaItem() && p.repeatMode != Player.REPEAT_MODE_ONE) Long.MAX_VALUE
                else p.duration - p.currentPosition
            }
            Mode.NONE -> Long.MAX_VALUE
        }
    }

    private fun tick() {
        val p = player() ?: return
        val rem = remainingMs()
        Core.sleepRemaining.value = if (rem == Long.MAX_VALUE) -1L else rem.coerceAtLeast(0L)
        val fadeMs = Prefs.sleepFade.value * 1000L
        if (rem <= fadeMs && fadeMs > 0 && rem != Long.MAX_VALUE) p.volume = (rem.toFloat() / fadeMs).coerceIn(0f, 1f)
        if (rem <= 250) fire()
    }

    /** Called by the service when a song ends naturally (for "end of song"). */
    fun onAutoTransition() { if (mode == Mode.END_TRACK) fire() }
    fun onEnded() { if (mode == Mode.END_QUEUE || mode == Mode.END_TRACK) fire() }

    @SuppressLint("MissingPermission")
    private fun fire() {
        val p = player()
        p?.pause()
        p?.volume = 1f
        mode = Mode.NONE
        job?.cancel()
        publish()
        Messages.add(t("Sleep timer stopped the music.", "Hẹn giờ đã tắt nhạc."))
        if (Prefs.sleepBluetooth.value && Build.VERSION.SDK_INT < 31) {
            @Suppress("DEPRECATION")
            try { BluetoothAdapter.getDefaultAdapter()?.disable() } catch (_: Exception) { }
        }
    }

    fun cancel(publishIt: Boolean = true) {
        job?.cancel(); job = null
        mode = Mode.NONE
        player()?.volume = 1f
        if (publishIt) publish()
    }

    private fun publish() {
        Core.sleepMode.value = mode.name
        Core.sleepRemaining.value = if (mode == Mode.NONE) -1L else remainingMs().let { if (it == Long.MAX_VALUE) -1L else it }
    }
}
