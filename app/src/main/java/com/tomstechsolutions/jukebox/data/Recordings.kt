package com.tomstechsolutions.jukebox.data

import android.content.ContentUris
import android.content.ContentValues
import android.content.Context
import android.os.Build
import android.provider.MediaStore
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/** Bản Thâu Âm: files in Music/Tom's Jukebox/Recordings. */
object Recordings {
    data class Rec(val id: Long, val uri: String, val name: String, val date: Long, val durationMs: Long, val size: Long)

    suspend fun list(ctx: Context): List<Rec> = withContext(Dispatchers.IO) {
        val out = ArrayList<Rec>()
        val coll = MediaStore.Audio.Media.EXTERNAL_CONTENT_URI
        @Suppress("DEPRECATION")
        val dataCol = MediaStore.Audio.Media.DATA
        val sel = if (Build.VERSION.SDK_INT >= 29) MediaStore.Audio.Media.RELATIVE_PATH + " LIKE ?" else "$dataCol LIKE ?"
        val args = if (Build.VERSION.SDK_INT >= 29) arrayOf("%Tom's Jukebox/Recordings%") else arrayOf("%/Tom's Jukebox/Recordings/%")
        try {
            ctx.contentResolver.query(coll, arrayOf(MediaStore.Audio.Media._ID, MediaStore.Audio.Media.DISPLAY_NAME, MediaStore.Audio.Media.DATE_ADDED,
                MediaStore.Audio.Media.DURATION, MediaStore.Audio.Media.SIZE), sel, args, MediaStore.Audio.Media.DATE_ADDED + " DESC")?.use { c ->
                while (c.moveToNext()) {
                    val id = c.getLong(0)
                    out += Rec(id, ContentUris.withAppendedId(coll, id).toString(), c.getString(1) ?: "", c.getLong(2) * 1000, c.getLong(3), c.getLong(4))
                }
            }
        } catch (_: Exception) { }
        out
    }

    fun rename(ctx: Context, r: Rec, newName: String): Boolean = try {
        val ext = r.name.substringAfterLast('.', "")
        val name = if (ext.isNotEmpty() && !newName.endsWith(".$ext")) "$newName.$ext" else newName
        ctx.contentResolver.update(android.net.Uri.parse(r.uri), ContentValues().apply { put(MediaStore.Audio.Media.DISPLAY_NAME, name); put(MediaStore.Audio.Media.TITLE, newName) }, null, null) > 0
    } catch (_: Exception) { false }

    fun sizeText(b: Long): String = when { b >= 1_000_000_000 -> "%.1f GB".format(b / 1e9); b >= 1_000_000 -> "%.0f MB".format(b / 1e6); else -> "%.0f KB".format(b / 1e3) }
}
