package com.tomstechsolutions.jukebox.data

import android.content.Context
import android.net.Uri
import com.tomstechsolutions.jukebox.App
import com.tomstechsolutions.jukebox.Prefs
import org.json.JSONObject

/** One backup file with every setting, favourites, playlists and podcasts. The Windows version reads the same file. */
object Backup {
    fun write(ctx: Context, uri: Uri): Boolean = try {
        val o = JSONObject()
        o.put("app", App.NAME); o.put("version", App.VERSION); o.put("platform", "android"); o.put("time", System.currentTimeMillis())
        o.put("settings", Prefs.toJson())
        ctx.contentResolver.openOutputStream(uri, "wt")?.use { it.write(o.toString(2).toByteArray()) }
        Prefs.lastBackup.value = System.currentTimeMillis()
        true
    } catch (_: Exception) { false }

    fun read(ctx: Context, uri: Uri): Boolean = try {
        val text = ctx.contentResolver.openInputStream(uri)?.use { it.readBytes().toString(Charsets.UTF_8) } ?: ""
        val o = JSONObject(text)
        val s = o.optJSONObject("settings") ?: o
        Prefs.fromJson(s)
        true
    } catch (_: Exception) { false }
}
