package com.tomstechsolutions.jukebox.ui

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.view.KeyEvent
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.data.Library
import com.tomstechsolutions.jukebox.playback.Core
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    val audioAllowed = mutableStateOf(false)
    val showSleep = mutableStateOf(false)
    val showLyrics = mutableStateOf(false)
    val openNow = mutableStateOf(false)
    val tab = mutableIntStateOf(0)

    val audioPerm = if (Build.VERSION.SDK_INT >= 33) Manifest.permission.READ_MEDIA_AUDIO else Manifest.permission.READ_EXTERNAL_STORAGE

    private val askPerms = registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { res ->
        audioAllowed.value = hasAudio()
        if (audioAllowed.value) lifecycleScope.launch { Library.scan(this@MainActivity) }
        if (res[Manifest.permission.RECORD_AUDIO] == true) Core.service?.refreshViz()
    }

    fun hasAudio() = ContextCompat.checkSelfPermission(this, audioPerm) == PackageManager.PERMISSION_GRANTED

    fun askAudio() {
        val list = mutableListOf(audioPerm)
        if (Build.VERSION.SDK_INT >= 33) list += Manifest.permission.POST_NOTIFICATIONS
        askPerms.launch(list.toTypedArray())
    }

    fun ask(vararg perms: String) = askPerms.launch(arrayOf(*perms))

    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        Core.connect(applicationContext)
        audioAllowed.value = hasAudio()
        if (!audioAllowed.value) askAudio()
        else if (!Library.loaded.value) lifecycleScope.launch { Library.scan(this@MainActivity) }
        setContent { JukeboxApp(this) }
    }

    override fun onResume() {
        super.onResume()
        Anim.checkBattery(this)
        val now = hasAudio()
        if (now && !audioAllowed.value) { audioAllowed.value = true; lifecycleScope.launch { Library.scan(this@MainActivity) } }
    }

    /** Keyboard shortcuts (Samsung DeX, Bluetooth keyboards, Chromebooks) – same letters as Winamp / the Windows version. */
    override fun dispatchKeyEvent(event: KeyEvent): Boolean {
        if (event.action != KeyEvent.ACTION_DOWN) return super.dispatchKeyEvent(event)
        val ctrl = event.isCtrlPressed; val shift = event.isShiftPressed
        if (currentFocus is android.widget.EditText) return super.dispatchKeyEvent(event)
        val handled = when (event.keyCode) {
            KeyEvent.KEYCODE_SPACE, KeyEvent.KEYCODE_X, KeyEvent.KEYCODE_C -> { Core.toggle(); true }
            KeyEvent.KEYCODE_Z -> { Core.prev(); true }
            KeyEvent.KEYCODE_B -> { Core.next(); true }
            KeyEvent.KEYCODE_V -> { Core.stop(); true }
            KeyEvent.KEYCODE_DPAD_RIGHT -> { Core.seekBy(if (shift) 30_000 else 5_000); true }
            KeyEvent.KEYCODE_DPAD_LEFT -> { Core.seekBy(if (shift) -30_000 else -5_000); true }
            KeyEvent.KEYCODE_DPAD_UP -> { Core.volumeUp(); true }
            KeyEvent.KEYCODE_DPAD_DOWN -> { Core.volumeDown(); true }
            KeyEvent.KEYCODE_S -> { Core.toggleShuffle(); true }
            KeyEvent.KEYCODE_R -> { Core.cycleRepeat(); true }
            KeyEvent.KEYCODE_LEFT_BRACKET -> { Prefs.edgeSpeed.value = (Prefs.edgeSpeed.value - 1).coerceAtLeast(0); true }
            KeyEvent.KEYCODE_RIGHT_BRACKET -> { Prefs.edgeSpeed.value = (Prefs.edgeSpeed.value + 1).coerceAtMost(4); true }
            KeyEvent.KEYCODE_E -> { Prefs.edgeEffect.value = (Prefs.edgeEffect.value + 1) % 12; true }
            KeyEvent.KEYCODE_T -> if (ctrl && shift) { showSleep.value = true; true } else false
            KeyEvent.KEYCODE_L -> { if (ctrl) tab.intValue = 0 else if (shift) tab.intValue = 0 else { openNow.value = true; showLyrics.value = !showLyrics.value }; true }
            KeyEvent.KEYCODE_G -> { Prefs.viz.value = (Prefs.viz.value + 1) % 12; true }
            KeyEvent.KEYCODE_F -> { if (Core.uri.value.isNotBlank()) Prefs.toggleFav(Core.uri.value); true }
            KeyEvent.KEYCODE_1 -> { tab.intValue = 0; true }
            KeyEvent.KEYCODE_2 -> { tab.intValue = 1; true }
            KeyEvent.KEYCODE_3 -> { tab.intValue = 2; true }
            KeyEvent.KEYCODE_4 -> { tab.intValue = 3; true }
            KeyEvent.KEYCODE_5 -> { tab.intValue = 4; true }
            KeyEvent.KEYCODE_ESCAPE -> { if (openNow.value) { openNow.value = false; true } else false }
            else -> false
        }
        return handled || super.dispatchKeyEvent(event)
    }
}
