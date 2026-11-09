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
import com.tomstechsolutions.jukebox.data.Messages
import com.tomstechsolutions.jukebox.t
import com.tomstechsolutions.jukebox.data.Library
import com.tomstechsolutions.jukebox.playback.Core
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    val audioAllowed = mutableStateOf(false)
    val showSleep = mutableStateOf(false)
    val showLyrics = mutableStateOf(false)
    val openNow = mutableStateOf(false)
    val tab = mutableIntStateOf(0)
    val openRecordings = mutableStateOf(false)
    val picker = mutableStateOf("")                 // trang chọn kiểu đang mở
    val fullViz = mutableStateOf(false)
    val previewSplash = mutableIntStateOf(-1)
    var skipSplash = false
    val confirmDelete = mutableStateOf<List<String>>(emptyList())   // Android 9 and older: our own "are you sure"
    private var pendingDelete: List<String> = emptyList()

    private val deleteLauncher = registerForActivityResult(ActivityResultContracts.StartIntentSenderForResult()) { r ->
        if (r.resultCode == RESULT_OK) {
            if (Build.VERSION.SDK_INT == 29) doDelete(pendingDelete, true) else afterDelete(pendingDelete)
        }
    }

    fun hideSongs(uris: List<String>) {
        Prefs.hide(uris); Library.refilter(); Core.removeUris(uris.toSet())
        Messages.add(t("${uris.size} song(s) hidden from the library.", "Đã bỏ ${uris.size} bài khỏi thư viện (file vẫn còn trong máy)."))
    }

    /** Xoá Khỏi Máy: Android 11+ shows its own "Allow Tom's Jukebox to delete…?" box. */
    fun deleteSongs(uris: List<String>) {
        if (uris.isEmpty()) return
        pendingDelete = uris
        val media = uris.filter { it.startsWith("content://media") }.map { android.net.Uri.parse(it) }
        if (Build.VERSION.SDK_INT >= 30 && media.isNotEmpty()) {
            try {
                val pi = android.provider.MediaStore.createDeleteRequest(contentResolver, media)
                deleteLauncher.launch(androidx.activity.result.IntentSenderRequest.Builder(pi.intentSender).build())
                // documents added with "+ Thêm Bài Hát…" are removed here too
                uris.filter { !it.startsWith("content://media") }.forEach { deleteDoc(it) }
                return
            } catch (_: Exception) { }
        }
        confirmDelete.value = uris
    }

    fun doDelete(uris: List<String>, again: Boolean = false) {
        val done = mutableListOf<String>()
        for (u in uris) {
            try {
                if (u.startsWith("content://media")) {
                    if (contentResolver.delete(android.net.Uri.parse(u), null, null) > 0) done += u
                } else if (deleteDoc(u)) done += u
            } catch (e: SecurityException) {
                if (!again && Build.VERSION.SDK_INT >= 29 && e is android.app.RecoverableSecurityException) {
                    pendingDelete = uris
                    deleteLauncher.launch(androidx.activity.result.IntentSenderRequest.Builder(e.userAction.actionIntent.intentSender).build())
                    return
                }
            } catch (_: Exception) { }
        }
        afterDelete(done)
    }

    private fun deleteDoc(u: String): Boolean = try { android.provider.DocumentsContract.deleteDocument(contentResolver, android.net.Uri.parse(u)) } catch (_: Exception) { false }

    private fun afterDelete(uris: List<String>) {
        if (uris.isEmpty()) return
        Prefs.removeFav(uris); Core.removeUris(uris.toSet()); Library.forget(uris)
        val docs = uris.filter { !it.startsWith("content://media") }.map { "doc:$it" }.toSet()
        if (docs.isNotEmpty()) Prefs.folders.value = Prefs.folders.value.split('\n').filter { it !in docs }.joinToString("\n")
        Messages.add(t("Deleted ${uris.size} song(s) from the phone.", "Đã xoá ${uris.size} bài khỏi máy."))
    }

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
        if (intent?.getBooleanExtra("open_now", false) == true) { skipSplash = true; openNow.value = true }
        intent?.let { openFrom(it) }
        audioAllowed.value = hasAudio()
        if (!audioAllowed.value) askAudio()
        else if (!Library.loaded.value) lifecycleScope.launch { Library.scan(this@MainActivity) }
        setContent { JukeboxApp(this) }
    }

    override fun onNewIntent(intent: android.content.Intent) {
        super.onNewIntent(intent)
        if (intent.getBooleanExtra("open_now", false)) openNow.value = true
        intent.getStringExtra("open_tab")?.let { tab.intValue = it.toIntOrNull() ?: tab.intValue }
        openFrom(intent)
    }

    /** Pinned podcast shortcut, "new episode" alert, or a widget page button. */
    private fun openFrom(i: android.content.Intent) {
        i.getStringExtra("open_podcast")?.takeIf { it.isNotBlank() }?.let { feed ->
            PodcastNav.openPodcast.value = com.tomstechsolutions.jukebox.data.Podcast(i.getStringExtra("open_podcast_title") ?: "", "", feed, i.getStringExtra("open_podcast_image") ?: "")
            tab.intValue = 2; openNow.value = false
        }
        i.getStringExtra("open_tab")?.toIntOrNull()?.let { tab.intValue = it; openNow.value = false }
        if (i.getBooleanExtra("open_sleep", false)) showSleep.value = true
        // used by the emulator test to look at the new pages
        i.getIntExtra("apply_pack", -1).takeIf { it in Motifs.list.indices }?.let { Motifs.applyPack(it) }
        i.getIntExtra("set_viz", -1).takeIf { it in VizStyles.names.indices }?.let { Prefs.viz.value = it; Prefs.vizAuto.value = false }
        i.getStringExtra("open_picker")?.takeIf { it in Pickers.cats }?.let { picker.value = it }
        if (i.getBooleanExtra("full_viz", false)) fullViz.value = true
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
            KeyEvent.KEYCODE_E -> { Prefs.edgeEffect.value = (Motifs.edgeStyle().first + 1) % EdgeEffects.names.size; true }
            KeyEvent.KEYCODE_T -> if (ctrl && shift) { showSleep.value = true; true } else false
            KeyEvent.KEYCODE_L -> { if (ctrl) tab.intValue = 0 else if (shift) tab.intValue = 0 else { openNow.value = true; showLyrics.value = !showLyrics.value }; true }
            KeyEvent.KEYCODE_G -> { Prefs.viz.value = (Prefs.viz.value + 1) % VizStyles.names.size; true }
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
