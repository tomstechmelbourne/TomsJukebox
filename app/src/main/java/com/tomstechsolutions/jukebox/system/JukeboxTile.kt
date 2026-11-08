package com.tomstechsolutions.jukebox.system

import android.os.Build
import android.service.quicksettings.Tile
import android.service.quicksettings.TileService
import android.view.KeyEvent
import androidx.annotation.RequiresApi
import com.tomstechsolutions.jukebox.playback.Core

/** Quick Settings tile: tap to play / pause. */
@RequiresApi(Build.VERSION_CODES.N)
class JukeboxTile : TileService() {
    override fun onStartListening() { refresh() }

    override fun onClick() {
        val svc = Core.service
        if (svc != null) { if (svc.player.isPlaying) svc.player.pause() else { svc.player.prepare(); svc.player.play() } }
        else try { Widgets.button(this, KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE).send() } catch (_: Exception) { }
        refresh()
    }

    private fun refresh() {
        val t = qsTile ?: return
        val playing = Core.service?.player?.isPlaying == true
        t.state = if (playing) Tile.STATE_ACTIVE else Tile.STATE_INACTIVE
        t.label = "Tom's Jukebox"
        if (Build.VERSION.SDK_INT >= 29) t.subtitle = Core.title.value.ifBlank { if (playing) "▶" else "" }
        t.updateTile()
    }
}
