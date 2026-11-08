package com.tomstechsolutions.jukebox.data

import android.content.ContentUris
import android.content.Context
import android.net.Uri
import android.os.Build
import android.provider.DocumentsContract
import android.provider.MediaStore
import androidx.compose.runtime.mutableStateOf
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.t
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/** The music already on the phone (MediaStore) plus folders Tom adds himself. Loaded lazily, off the main thread. */
object Library {
    val tracks = mutableStateOf<List<Track>>(emptyList())
    val scanning = mutableStateOf(false)
    val loaded = mutableStateOf(false)

    suspend fun scan(ctx: Context) = withContext(Dispatchers.IO) {
        scanning.value = true
        val out = LinkedHashMap<String, Track>()
        try {
            queryMediaStore(ctx).forEach { out[it.uri] = it }
            var n = 0L
            Prefs.folders.value.split('\n').filter { it.isNotBlank() }.forEach { line ->
                try {
                    if (line.startsWith("doc:")) {
                        val u = line.removePrefix("doc:")
                        val name = displayName(ctx, Uri.parse(u))
                        n++
                        out.putIfAbsent(u, Track(-1_000_000 - n, u, name.substringBeforeLast('.'), "", "", 0, 0, t("Added Songs", "Bài Đã Thêm"), ""))
                    } else walkTree(ctx, Uri.parse(line)).forEach { out.putIfAbsent(it.uri, it) }
                } catch (_: Exception) { }
            }
        } catch (_: Exception) { }
        tracks.value = out.values.sortedWith(compareBy({ it.artist.lowercase() }, { it.album.lowercase() }, { it.trackNo }, { it.title.lowercase() }))
        scanning.value = false
        loaded.value = true
    }

    private fun queryMediaStore(ctx: Context): List<Track> {
        val list = ArrayList<Track>()
        val coll = if (Build.VERSION.SDK_INT >= 29) MediaStore.Audio.Media.getContentUri(MediaStore.VOLUME_EXTERNAL)
        else MediaStore.Audio.Media.EXTERNAL_CONTENT_URI
        val cols = mutableListOf(
            MediaStore.Audio.Media._ID, MediaStore.Audio.Media.TITLE, MediaStore.Audio.Media.ARTIST,
            MediaStore.Audio.Media.ALBUM, MediaStore.Audio.Media.ALBUM_ID, MediaStore.Audio.Media.DURATION,
            MediaStore.Audio.Media.MIME_TYPE, MediaStore.Audio.Media.YEAR, MediaStore.Audio.Media.TRACK,
            MediaStore.Audio.Media.DATE_ADDED,
        )
        @Suppress("DEPRECATION")
        cols += MediaStore.Audio.Media.DATA
        if (Build.VERSION.SDK_INT >= 30) cols += MediaStore.Audio.Media.GENRE
        val sel = MediaStore.Audio.Media.IS_MUSIC + " != 0 OR " + MediaStore.Audio.Media.MIME_TYPE + " LIKE 'audio/%'"
        ctx.contentResolver.query(coll, cols.toTypedArray(), sel, null, null)?.use { c ->
            val iId = c.getColumnIndexOrThrow(MediaStore.Audio.Media._ID)
            val iT = c.getColumnIndexOrThrow(MediaStore.Audio.Media.TITLE)
            val iA = c.getColumnIndexOrThrow(MediaStore.Audio.Media.ARTIST)
            val iAl = c.getColumnIndexOrThrow(MediaStore.Audio.Media.ALBUM)
            val iAi = c.getColumnIndexOrThrow(MediaStore.Audio.Media.ALBUM_ID)
            val iD = c.getColumnIndexOrThrow(MediaStore.Audio.Media.DURATION)
            val iM = c.getColumnIndexOrThrow(MediaStore.Audio.Media.MIME_TYPE)
            val iY = c.getColumnIndexOrThrow(MediaStore.Audio.Media.YEAR)
            val iTr = c.getColumnIndexOrThrow(MediaStore.Audio.Media.TRACK)
            val iDa = c.getColumnIndexOrThrow(MediaStore.Audio.Media.DATE_ADDED)
            @Suppress("DEPRECATION") val iP = c.getColumnIndex(MediaStore.Audio.Media.DATA)
            val iG = if (Build.VERSION.SDK_INT >= 30) c.getColumnIndex(MediaStore.Audio.Media.GENRE) else -1
            while (c.moveToNext()) {
                val id = c.getLong(iId)
                val dur = c.getLong(iD)
                if (dur in 1..9_999) continue  // ringtones and clicks
                val path = if (iP >= 0) c.getString(iP) ?: "" else ""
                val folder = path.substringBeforeLast('/', "").substringAfterLast('/')
                list += Track(
                    id = id,
                    uri = ContentUris.withAppendedId(MediaStore.Audio.Media.EXTERNAL_CONTENT_URI, id).toString(),
                    title = c.getString(iT)?.takeIf { it.isNotBlank() } ?: path.substringAfterLast('/'),
                    artist = clean(c.getString(iA)),
                    album = clean(c.getString(iAl)),
                    albumId = c.getLong(iAi),
                    durationMs = dur,
                    folder = folder,
                    mime = c.getString(iM) ?: "",
                    genre = if (iG >= 0) c.getString(iG) ?: "" else "",
                    year = c.getInt(iY),
                    trackNo = c.getInt(iTr) % 1000,
                    dateAdded = c.getLong(iDa),
                )
            }
        }
        return list
    }

    private fun displayName(ctx: Context, u: Uri): String = try {
        ctx.contentResolver.query(u, arrayOf(android.provider.OpenableColumns.DISPLAY_NAME), null, null, null)?.use { c ->
            if (c.moveToFirst()) c.getString(0) else null
        } ?: u.lastPathSegment.orEmpty()
    } catch (_: Exception) { u.lastPathSegment.orEmpty() }

    private fun clean(s: String?): String = if (s == null || s == "<unknown>") "" else s

    private val audioExt = setOf("mp3", "flac", "m4a", "aac", "ogg", "opus", "wav", "wma", "alac", "aiff", "aif", "ape", "dsf", "mka")

    /** Folders added with "+ Thêm Thư Mục…" (Storage Access Framework, works for SD cards and USB drives). */
    private fun walkTree(ctx: Context, tree: Uri): List<Track> {
        val out = ArrayList<Track>()
        val stack = ArrayDeque<Pair<String, String>>()
        stack.add(DocumentsContract.getTreeDocumentId(tree) to "")
        var n = 0L
        while (stack.isNotEmpty() && out.size < 20000) {
            val (docId, folderName) = stack.removeLast()
            val children = DocumentsContract.buildChildDocumentsUriUsingTree(tree, docId)
            ctx.contentResolver.query(children, arrayOf(
                DocumentsContract.Document.COLUMN_DOCUMENT_ID, DocumentsContract.Document.COLUMN_DISPLAY_NAME,
                DocumentsContract.Document.COLUMN_MIME_TYPE), null, null, null)?.use { c ->
                while (c.moveToNext()) {
                    val id = c.getString(0); val name = c.getString(1) ?: ""; val mime = c.getString(2) ?: ""
                    if (mime == DocumentsContract.Document.MIME_TYPE_DIR) { stack.add(id to name); continue }
                    val ext = name.substringAfterLast('.', "").lowercase()
                    if (!mime.startsWith("audio/") && ext !in audioExt) continue
                    val uri = DocumentsContract.buildDocumentUriUsingTree(tree, id)
                    n++
                    out += Track(id = -n, uri = uri.toString(), title = name.substringBeforeLast('.'), artist = "",
                        album = folderName, albumId = 0, durationMs = 0, folder = folderName, mime = mime)
                }
            }
        }
        return out
    }

    fun albums(): List<Pair<String, List<Track>>> = tracks.value.groupBy { it.album.ifBlank { "—" } }.toList().sortedBy { it.first.lowercase() }
    fun artists(): List<Pair<String, List<Track>>> = tracks.value.groupBy { it.artist.ifBlank { "—" } }.toList().sortedBy { it.first.lowercase() }
    fun folders(): List<Pair<String, List<Track>>> = tracks.value.groupBy { it.folder.ifBlank { "—" } }.toList().sortedBy { it.first.lowercase() }
    fun byUri(uri: String): Track? = tracks.value.firstOrNull { it.uri == uri }
}
