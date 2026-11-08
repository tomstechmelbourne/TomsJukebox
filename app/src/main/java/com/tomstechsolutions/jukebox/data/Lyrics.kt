package com.tomstechsolutions.jukebox.data

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

/** Synced lyrics from LRCLIB (free), cached on the phone. */
object Lyrics {
    suspend fun get(ctx: Context, title: String, artist: String, album: String, durS: Long): List<LyricLine> = withContext(Dispatchers.IO) {
        if (title.isBlank()) return@withContext emptyList()
        val dir = File(ctx.filesDir, "lyrics").apply { mkdirs() }
        val f = File(dir, (artist + "-" + title).replace(Regex("[^\\w\\-]+"), "_").take(120) + ".lrc")
        if (f.exists()) return@withContext parse(f.readText())
        var text = ""
        try {
            val o = JSONObject(Net.get("https://lrclib.net/api/get?artist_name=${Net.enc(artist)}&track_name=${Net.enc(title)}&album_name=${Net.enc(album)}&duration=$durS"))
            text = o.optString("syncedLyrics").ifBlank { o.optString("plainLyrics") }
        } catch (_: Exception) { }
        if (text.isBlank()) try {
            val a = JSONArray(Net.get("https://lrclib.net/api/search?q=${Net.enc("$artist $title")}"))
            if (a.length() > 0) { val o = a.getJSONObject(0); text = o.optString("syncedLyrics").ifBlank { o.optString("plainLyrics") } }
        } catch (_: Exception) { }
        if (text.isNotBlank()) f.writeText(text)
        parse(text)
    }

    fun parse(text: String): List<LyricLine> {
        val re = Regex("\\[(\\d+):(\\d+)(?:[.:](\\d+))?]")
        val out = ArrayList<LyricLine>()
        text.lines().forEach { line ->
            val ms = re.findAll(line).toList()
            val words = line.replace(re, "").trim()
            if (ms.isEmpty()) { if (line.isNotBlank() && !line.startsWith("[")) out += LyricLine(-1, line.trim()) }
            else ms.forEach { m ->
                val frac = m.groupValues[3]
                val fms = if (frac.isEmpty()) 0 else (frac + "00").take(3).toLong()
                out += LyricLine(m.groupValues[1].toLong() * 60000 + m.groupValues[2].toLong() * 1000 + fms, words)
            }
        }
        return if (out.any { it.timeMs >= 0 }) out.filter { it.timeMs >= 0 }.sortedBy { it.timeMs } else out
    }
}
