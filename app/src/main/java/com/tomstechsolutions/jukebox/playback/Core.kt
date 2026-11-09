package com.tomstechsolutions.jukebox.playback

import com.tomstechsolutions.jukebox.data.PodSave

import android.content.ComponentName
import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Bundle
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.core.content.ContextCompat
import androidx.media3.common.MediaItem
import androidx.media3.common.MediaMetadata
import androidx.media3.common.Player
import androidx.media3.session.MediaController
import androidx.media3.session.SessionToken
import com.tomstechsolutions.jukebox.App
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.data.Art
import com.tomstechsolutions.jukebox.data.Episode
import com.tomstechsolutions.jukebox.data.PodStore
import com.tomstechsolutions.jukebox.data.Library
import com.tomstechsolutions.jukebox.data.Messages
import com.tomstechsolutions.jukebox.data.RadioApi
import com.tomstechsolutions.jukebox.data.Station
import com.tomstechsolutions.jukebox.data.Track
import com.tomstechsolutions.jukebox.t
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.MainScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

data class QItem(val uri: String, val title: String, val artist: String, val album: String, val kind: String, val albumId: Long)

/** What the screens show (state) and what they can ask for. Talks to the background service through a MediaController. */
object Core {
    val scope = MainScope()
    var service: PlaybackService? = null
    var controller: MediaController? = null
    private var connecting = false

    val playing = mutableStateOf(false)
    val buffering = mutableStateOf(false)
    val title = mutableStateOf("")
    val artist = mutableStateOf("")
    val album = mutableStateOf("")
    val uri = mutableStateOf("")
    val kind = mutableStateOf("")           // track / radio / podcast
    val format = mutableStateOf("")
    val position = mutableLongStateOf(0L)
    val duration = mutableLongStateOf(0L)
    val shuffle = mutableStateOf(false)
    val repeat = mutableStateOf(Player.REPEAT_MODE_OFF)
    val queue = mutableStateOf<List<QItem>>(emptyList())
    val index = mutableStateOf(0)
    val art = mutableStateOf<Bitmap?>(null)
    val palette = mutableStateOf(Art.BRAND)
    val levels = mutableStateOf(FloatArray(24))
    val beat = mutableLongStateOf(0L)
    @Volatile var realLevels = false
    val sleepMode = mutableStateOf("NONE")
    val sleepRemaining = mutableLongStateOf(-1L)
    val recording = mutableStateOf(false)
    val recordedBytes = mutableLongStateOf(0L)
    val error = mutableStateOf("")
    val station = mutableStateOf<Station?>(null)

    fun connect(ctx: Context) {
        if (controller != null || connecting) return
        connecting = true
        val token = SessionToken(ctx, ComponentName(ctx, PlaybackService::class.java))
        val fut = MediaController.Builder(ctx, token).buildAsync()
        fut.addListener({
            connecting = false
            try {
                val c = fut.get()
                controller = c
                c.addListener(listener)
                refresh()
                if (c.mediaItemCount == 0) restoreQueue()
            } catch (e: Exception) { error.value = e.message ?: "" }
        }, ContextCompat.getMainExecutor(ctx))
        scope.launch {
            while (true) {
                controller?.let { c ->
                    position.longValue = c.currentPosition.coerceAtLeast(0)
                    duration.longValue = c.duration.let { if (it < 0) 0 else it }
                }
                delay(if (playing.value) 250 else 800)
            }
        }
    }

    private val listener = object : Player.Listener {
        override fun onEvents(player: Player, events: Player.Events) { refresh() }
    }

    private var lastArtKey = ""

    fun refresh() {
        val c = controller ?: return
        playing.value = c.isPlaying
        buffering.value = c.playbackState == Player.STATE_BUFFERING
        shuffle.value = c.shuffleModeEnabled
        repeat.value = c.repeatMode
        index.value = c.currentMediaItemIndex
        val items = (0 until c.mediaItemCount).map { toQ(c.getMediaItemAt(it)) }
        if (items != queue.value) queue.value = items
        val cur = c.currentMediaItem
        val md = c.mediaMetadata
        val q = cur?.let { toQ(it) }
        title.value = md.title?.toString()?.ifBlank { null } ?: q?.title ?: ""
        artist.value = md.artist?.toString()?.ifBlank { null } ?: q?.artist ?: ""
        album.value = md.albumTitle?.toString()?.ifBlank { null } ?: q?.album ?: ""
        uri.value = q?.uri ?: ""
        kind.value = q?.kind ?: ""
        val key = (q?.uri ?: "") + (md.artworkData?.size ?: 0)
        if (key != lastArtKey) {
            lastArtKey = key
            val data = md.artworkData
            scope.launch {
                val bmp = withContext(Dispatchers.IO) {
                    if (data != null) try { BitmapFactory.decodeByteArray(data, 0, data.size) } catch (_: Exception) { null }
                    else if (q != null) Art.load(com.tomstechsolutions.jukebox.App.ctx,
                        if (q.kind == "track") q.uri else (cur?.mediaMetadata?.artworkUri?.toString() ?: ""), q.albumId)
                    else null
                }
                art.value = bmp
                palette.value = Art.palette(bmp)
            }
        }
        val tr = q?.let { if (it.kind == "track") Library.byUri(it.uri) else null }
        format.value = when (q?.kind) {
            "radio" -> station.value?.let { s -> listOf(s.codec, if (s.bitrate > 0) "${s.bitrate} kbps" else "").filter { it.isNotBlank() }.joinToString(" · ") } ?: "Radio"
            "podcast" -> "Podcast"
            else -> tr?.mime?.substringAfter('/')?.uppercase()?.replace("MPEG", "MP3")?.replace("X-FLAC", "FLAC") ?: ""
        }
        if (Prefs.eqAutoGenre.value && (q?.kind == "radio" || q?.kind == "podcast") && Prefs.eqPreset.value != "voice") applyPreset("voice")
        if (Prefs.eqAutoGenre.value && tr != null && tr.genre.isNotBlank()) {
            EqPresets.forGenre(tr.genre)?.let { k -> if (k != Prefs.eqPreset.value) applyPreset(k) }
        }
    }

    private fun toQ(m: MediaItem): QItem {
        val e = m.mediaMetadata.extras
        return QItem(m.mediaId, m.mediaMetadata.title?.toString() ?: "", m.mediaMetadata.artist?.toString() ?: "",
            m.mediaMetadata.albumTitle?.toString() ?: "", e?.getString("kind") ?: "track", e?.getLong("albumId") ?: 0)
    }

    fun item(q: QItem, artwork: String = ""): MediaItem {
        val extras = Bundle().apply { putString("kind", q.kind); putLong("albumId", q.albumId) }
        val md = MediaMetadata.Builder().setTitle(q.title).setArtist(q.artist).setAlbumTitle(q.album).setExtras(extras)
            .setIsPlayable(true).setIsBrowsable(false)
        if (artwork.isNotBlank()) md.setArtworkUri(Uri.parse(artwork))
        else if (q.albumId > 0) md.setArtworkUri(Uri.parse("content://media/external/audio/albumart/${q.albumId}"))
        val b = MediaItem.Builder().setMediaId(q.uri).setUri(q.uri).setMediaMetadata(md.build())
            .setRequestMetadata(MediaItem.RequestMetadata.Builder().setMediaUri(Uri.parse(q.uri)).build())
        if (q.uri.contains(".m3u8")) b.setMimeType("application/x-mpegURL")
        return b.build()
    }

    fun trackQ(t: Track) = QItem(t.uri, t.title, t.artist, t.album, "track", t.albumId)

    fun playTracks(list: List<Track>, start: Int = 0, shuffled: Boolean = false) {
        val c = controller ?: return
        station.value = null
        c.setPlaybackSpeed(1f)
        c.setMediaItems(list.map { item(trackQ(it)) }, start.coerceIn(0, (list.size - 1).coerceAtLeast(0)), 0L)
        c.shuffleModeEnabled = shuffled
        c.prepare(); c.play()
    }

    fun addToQueue(list: List<Track>, next: Boolean = false) {
        val c = controller ?: return
        val items = list.map { item(trackQ(it)) }
        if (c.mediaItemCount == 0) { c.setMediaItems(items); c.prepare(); return }
        if (next) c.addMediaItems(c.currentMediaItemIndex + 1, items) else c.addMediaItems(items)
    }

    fun playStation(s: Station) {
        station.value = s
        error.value = ""
        scope.launch {
            if (s.url.isBlank()) {
                buffering.value = true
                val ok = RadioApi.resolve(s)
                buffering.value = false
                if (!ok) {
                    error.value = t("${s.name}: no working stream right now (Paused).", "${s.name}: hiện chưa tìm được luồng phát (Tạm Ngưng).")
                    Messages.add(error.value)
                    return@launch
                }
            }
            val c = controller ?: return@launch
            c.setPlaybackSpeed(1f)
            c.setMediaItem(item(QItem(s.url, s.name, if (s.country == "AU") "Radio · ${s.group}" else "Radio", s.group, "radio", 0)))
            c.prepare(); c.play()
        }
    }

    /** Plays a podcast episode: the downloaded file if there is one, from where it stopped, at the channel's own speed. */
    fun playEpisode(e: Episode, fromStart: Boolean = false) {
        val c = controller ?: return
        station.value = null
        val start = if (fromStart) 0L else PodStore.pos(e.url).takeIf { it > 0 } ?: (PodStore.skip(e.podcast) * 1000L)
        c.setMediaItem(episodeItem(e), start)
        c.setPlaybackSpeed(PodStore.speed(e.podcast))
        c.prepare(); c.play()
    }

    private fun episodeItem(e: Episode): MediaItem {
        val base = item(QItem(e.url, e.title, e.podcast, e.podcast, "podcast", 0), e.image)
        val local = PodStore.localFile(App.ctx, e) ?: return base
        val u = Uri.fromFile(local)
        return base.buildUpon().setUri(u).setRequestMetadata(MediaItem.RequestMetadata.Builder().setMediaUri(u).build()).build()
    }

    fun queueEpisode(e: Episode) {
        val c = controller ?: return
        if (c.mediaItemCount == 0) { playEpisode(e); return }
        c.addMediaItem(episodeItem(e))
    }

    /** Remembers where a podcast episode stopped. */
    fun savePodPos() {
        val c = controller ?: return
        if (kind.value == "podcast" && uri.value.isNotBlank()) PodStore.setPos(uri.value, c.currentPosition, c.duration)
    }

    /** Runs [block] once the player connection is up (widgets, shortcuts). Gives up waiting after 5 s. */
    fun whenReady(ctx: Context, block: () -> Unit) {
        connect(ctx)
        if (controller != null) { block(); return }
        scope.launch { var n = 0; while (controller == null && n < 50) { delay(100); n++ }; block() }
    }

    fun toggle() { controller?.let { if (it.isPlaying) it.pause() else { if (it.playbackState == Player.STATE_IDLE) it.prepare(); it.play() } } }
    fun next() { controller?.let { if (it.hasNextMediaItem()) it.seekToNextMediaItem() } }
    fun prev() { controller?.let { if (it.currentPosition > 4000 || !it.hasPreviousMediaItem()) it.seekTo(0) else it.seekToPreviousMediaItem() } }
    fun stop() { controller?.let { it.pause(); it.seekTo(0) } }
    fun seekTo(ms: Long) { controller?.seekTo(ms.coerceAtLeast(0)) }
    fun seekBy(ms: Long) { controller?.let { it.seekTo((it.currentPosition + ms).coerceAtLeast(0)) } }
    fun playAt(i: Int) { controller?.let { it.seekTo(i, 0); it.play() } }
    fun toggleShuffle() { controller?.let { it.shuffleModeEnabled = !it.shuffleModeEnabled } }
    fun cycleRepeat() {
        controller?.let {
            it.repeatMode = when (it.repeatMode) { Player.REPEAT_MODE_OFF -> Player.REPEAT_MODE_ALL; Player.REPEAT_MODE_ALL -> Player.REPEAT_MODE_ONE; else -> Player.REPEAT_MODE_OFF }
        }
    }
    fun removeAt(i: Int) { controller?.removeMediaItem(i) }
    fun move(from: Int, to: Int) { controller?.let { if (to in 0 until it.mediaItemCount) it.moveMediaItem(from, to) } }
    fun clearQueue() { controller?.clearMediaItems() }
    fun removeUris(uris: Set<String>) { controller?.let { c -> for (i in c.mediaItemCount - 1 downTo 0) if (c.getMediaItemAt(i).mediaId in uris) c.removeMediaItem(i) } }

    /** Stations shown when one was started, so ⏭ goes to the next station. */
    var radioList: List<Station> = emptyList()
    fun nextStation() {
        val cur = station.value ?: return
        if (radioList.isEmpty()) return
        val i = radioList.indexOfFirst { it.name == cur.name }
        playStation(radioList[(i + 1).mod(radioList.size)])
    }
    fun volumeUp() { service?.volumeStep(+1) }
    fun volumeDown() { service?.volumeStep(-1) }

    fun applyPreset(key: String) {
        val p = EqPresets.byKey(key) ?: return
        Prefs.eqPreset.value = key
        Prefs.eqBands.value = p.gains.joinToString(",")
        service?.eq?.apply()
    }

    // ---- ● Thâu: radio records the live stream; a podcast saves the part between start and stop (cut from the original file) ----
    val podRecFrom = mutableLongStateOf(-1L)
    val clipA = mutableLongStateOf(-1L)
    val clipB = mutableLongStateOf(-1L)

    /** Where to read the current podcast episode from: the downloaded file if there is one. */
    fun podSource(): String {
        val c = controller ?: return uri.value
        val local = c.currentMediaItem?.localConfiguration?.uri?.toString()
        return if (local != null && local.startsWith("file:")) local.removePrefix("file://") else uri.value
    }

    fun startRecording() {
        if (kind.value == "podcast") {
            val c = controller ?: return
            podRecFrom.longValue = c.currentPosition; recording.value = true
            Messages.add(t("Recording this podcast from ", "Bắt đầu thâu podcast từ ") + fmt(c.currentPosition))
            return
        }
        val s = station.value ?: return
        service?.recorder?.start(s.name, s.url, s.codec)
    }
    fun stopRecording() {
        if (podRecFrom.longValue >= 0) {
            val c = controller; val a = podRecFrom.longValue; val b = c?.currentPosition ?: a
            podRecFrom.longValue = -1L; recording.value = false
            val src = podSource(); val ti = title.value; val pod = artist.value
            scope.launch { PodSave.saveClip(App.ctx, src, ti, pod, a, b) }
            return
        }
        service?.recorder?.stop()
    }

    /** ✂ Cắt Đoạn A–B */
    fun markA() { controller?.let { clipA.longValue = it.currentPosition; if (clipB.longValue in 0..clipA.longValue) clipB.longValue = -1L } }
    fun markB() { controller?.let { clipB.longValue = it.currentPosition; if (clipA.longValue < 0) clipA.longValue = 0L } }
    fun saveAB() {
        val a = clipA.longValue; val b = clipB.longValue
        if (a < 0 || b <= a) { Messages.add(t("Set both A and B first.", "Hãy đặt cả mốc A và B trước.")); return }
        val src = podSource(); val ti = title.value; val pod = artist.value
        scope.launch { PodSave.saveClip(App.ctx, src, ti, pod, a, b) }
    }
    private fun fmt(ms: Long): String { val s = ms / 1000; return if (s >= 3600) "%d:%02d:%02d".format(s / 3600, s / 60 % 60, s % 60) else "%d:%02d".format(s / 60, s % 60) }

    fun saveQueue() {
        val c = controller ?: return
        val a = JSONArray()
        for (i in 0 until c.mediaItemCount) {
            val q = toQ(c.getMediaItemAt(i))
            if (q.kind == "track") a.put(JSONObject().put("u", q.uri).put("t", q.title).put("a", q.artist).put("al", q.album).put("id", q.albumId))
        }
        Prefs.lastQueue.value = a.toString()
        Prefs.lastIndex.value = c.currentMediaItemIndex
        Prefs.lastPos.value = c.currentPosition
    }

    fun savedItems(): List<MediaItem> = try {
        val a = JSONArray(Prefs.lastQueue.value)
        (0 until a.length()).map { a.getJSONObject(it) }.map {
            item(QItem(it.getString("u"), it.optString("t"), it.optString("a"), it.optString("al"), "track", it.optLong("id")))
        }
    } catch (_: Exception) { emptyList() }

    private fun restoreQueue() {
        val c = controller ?: return
        val items = savedItems()
        if (items.isEmpty()) return
        c.setMediaItems(items, Prefs.lastIndex.value.coerceIn(0, items.size - 1), Prefs.lastPos.value)
        c.prepare()
    }
}
