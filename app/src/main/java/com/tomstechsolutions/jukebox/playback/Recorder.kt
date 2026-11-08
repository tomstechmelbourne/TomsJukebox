package com.tomstechsolutions.jukebox.playback

import android.content.ContentValues
import android.content.Context
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import com.tomstechsolutions.jukebox.data.Messages
import com.tomstechsolutions.jukebox.data.Net
import com.tomstechsolutions.jukebox.t
import java.io.File
import java.io.OutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlin.concurrent.thread

/** Thâu âm radio: saves the station's original stream bytes (no re-encoding = the best quality the station sends)
 *  into Music/Tom's Jukebox/Recordings. Reconnects if the stream drops. Keeps going when the sleep timer fires. */
class Recorder(private val ctx: Context) {
    @Volatile private var running = false
    private var worker: Thread? = null

    fun start(name: String, url: String, codec: String) {
        if (running) return
        running = true
        Core.recording.value = true
        Core.recordedBytes.value = 0
        worker = thread(name = "recorder") {
            val ext = when {
                codec.contains("AAC", true) -> "aac"
                codec.contains("OGG", true) || codec.contains("VORBIS", true) -> "ogg"
                codec.contains("OPUS", true) -> "opus"
                codec.contains("FLAC", true) -> "flac"
                else -> "mp3"
            }
            val stamp = SimpleDateFormat("yyyy-MM-dd HH.mm", Locale.US).format(Date())
            val file = "${name.replace(Regex("[\\\\/:*?\"<>|]"), "_")} $stamp.$ext"
            var out: OutputStream? = null
            var pendingUri: Uri? = null
            try {
                if (Build.VERSION.SDK_INT >= 29) {
                    val cv = ContentValues().apply {
                        put(MediaStore.Audio.Media.DISPLAY_NAME, file)
                        put(MediaStore.Audio.Media.MIME_TYPE, if (ext == "mp3") "audio/mpeg" else "audio/$ext")
                        put(MediaStore.Audio.Media.RELATIVE_PATH, Environment.DIRECTORY_MUSIC + "/Tom's Jukebox/Recordings")
                        put(MediaStore.Audio.Media.IS_PENDING, 1)
                    }
                    pendingUri = ctx.contentResolver.insert(MediaStore.Audio.Media.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY), cv)
                    out = pendingUri?.let { ctx.contentResolver.openOutputStream(it) }
                } else {
                    @Suppress("DEPRECATION")
                    val dir = File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_MUSIC), "Tom's Jukebox/Recordings")
                    dir.mkdirs()
                    out = File(dir, file).outputStream()
                }
                val o = out ?: throw java.io.IOException("cannot write")
                var tries = 0
                while (running && tries < 20) {
                    try {
                        val c = URL(url).openConnection() as HttpURLConnection
                        c.connectTimeout = 10000; c.readTimeout = 15000
                        c.setRequestProperty("User-Agent", Net.UA)
                        c.inputStream.use { inp ->
                            val buf = ByteArray(16 * 1024)
                            while (running) {
                                val n = inp.read(buf)
                                if (n < 0) break
                                o.write(buf, 0, n)
                                Core.recordedBytes.value = Core.recordedBytes.value + n
                                tries = 0
                            }
                        }
                        c.disconnect()
                    } catch (_: Exception) { }
                    if (running) { tries++; Thread.sleep(2000) }
                }
                o.flush(); o.close()
                if (Build.VERSION.SDK_INT >= 29 && pendingUri != null) {
                    ctx.contentResolver.update(pendingUri, ContentValues().apply { put(MediaStore.Audio.Media.IS_PENDING, 0) }, null, null)
                }
                Messages.add(t("Recording saved: Music/Tom's Jukebox/Recordings/$file", "Đã lưu bản thâu: Music/Tom's Jukebox/Recordings/$file"))
            } catch (e: Exception) {
                try { out?.close() } catch (_: Exception) { }
                Messages.add(t("Recording failed: ", "Thâu âm bị lỗi: ") + (e.message ?: ""))
            }
            running = false
            Core.recording.value = false
        }
    }

    fun stop() { running = false }
    val isRunning get() = running
}
