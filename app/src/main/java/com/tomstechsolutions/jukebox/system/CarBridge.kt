package com.tomstechsolutions.jukebox.system

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.data.Library
import com.tomstechsolutions.jukebox.data.Playlists
import com.tomstechsolutions.jukebox.data.Podcasts
import com.tomstechsolutions.jukebox.data.RadioApi
import com.tomstechsolutions.jukebox.data.Stations
import com.tomstechsolutions.jukebox.playback.Core
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import org.json.JSONArray
import org.json.JSONObject
import java.text.Normalizer

/**
 * Lets Tom's Car (com.tomstechsolutions.car) drive Tom's Jukebox without opening its screen:
 *  - "play" with kind = resume | playlist | album | artist | track | station | podcast | search | shuffle
 *  - "query" sends back the library summary (playlists, albums, artists, stations, podcasts)
 *    and the current look (theme, skin, buttons, edge light, visualisation, pack).
 * Replies go only to Tom's Car's package.
 */
class CarBridge : BroadcastReceiver() {
    override fun onReceive(ctx: Context, i: Intent) {
        val app = ctx.applicationContext
        val pending = goAsync()
        scope.launch {
            try {
                if (!Library.loaded.value) try { Library.scan(app) } catch (_: Exception) { }
                when (i.getStringExtra("cmd") ?: "query") {
                    "play" -> play(app, i.getStringExtra("kind") ?: "resume", i.getStringExtra("name") ?: "")
                    else -> reply(app, summary())
                }
            } catch (_: Exception) { } finally { pending.finish() }
        }
    }

    private fun norm(s: String) = Normalizer.normalize(s.lowercase(), Normalizer.Form.NFD).replace(Regex("\\p{M}+"), "").replace('đ', 'd').trim()

    private suspend fun play(ctx: Context, kind: String, name: String) {
        val q = norm(name)
        val all = Library.tracks.value
        val run: () -> Unit = when (kind) {
            "playlist" -> {
                val pl = Playlists.all().entries.firstOrNull { norm(it.key) == q } ?: Playlists.all().entries.firstOrNull { norm(it.key).contains(q) }
                val uris = pl?.value ?: emptyList(); val list = uris.mapNotNull { u -> all.firstOrNull { it.uri == u } }
                ({ if (list.isNotEmpty()) Core.playTracks(list) })
            }
            "album" -> { val list = all.filter { norm(it.album).contains(q) }; ({ if (list.isNotEmpty()) Core.playTracks(list) }) }
            "artist" -> { val list = all.filter { norm(it.artist).contains(q) }; ({ if (list.isNotEmpty()) Core.playTracks(list, shuffled = true) }) }
            "shuffle" -> ({ if (all.isNotEmpty()) Core.playTracks(all, shuffled = true) })
            "track", "search" -> {
                val hits = all.filter { norm(it.title).contains(q) || norm(it.artist).contains(q) || norm(it.album).contains(q) }
                ({ if (hits.isNotEmpty()) Core.playTracks(hits) })
            }
            "station" -> {
                val st = Stations.all.firstOrNull { norm(it.name) == q } ?: Stations.all.firstOrNull { norm(it.name).contains(q) }
                if (st != null && st.url.isBlank()) try { RadioApi.resolve(st) } catch (_: Exception) { }
                ({ if (st != null && st.url.isNotBlank()) Core.playStation(st) })
            }
            "podcast" -> {
                val p = Podcasts.subscribed().firstOrNull { norm(it.title).contains(q) }
                val eps = if (p != null) try { Podcasts.episodes(p) } catch (_: Exception) { emptyList() } else emptyList()
                ({ eps.firstOrNull()?.let { Core.playEpisode(it) } })
            }
            else -> ({ Core.controller?.let { c -> if (c.playbackState == androidx.media3.common.Player.STATE_IDLE) c.prepare(); c.play() } })
        }
        kotlinx.coroutines.withContext(Dispatchers.Main) { Core.whenReady(ctx) { run() } }
    }

    private fun summary(): JSONObject {
        val all = Library.tracks.value
        val o = JSONObject().put("ok", true).put("version", com.tomstechsolutions.jukebox.App.VERSION)
        o.put("playlists", JSONArray().apply { Playlists.all().forEach { (k, v) -> put(JSONObject().put("name", k).put("n", v.size)) } })
        o.put("albums", JSONArray().apply { all.groupBy { it.album }.entries.sortedBy { it.key.lowercase() }.take(300).forEach { (k, v) -> put(JSONObject().put("name", k).put("artist", v.first().artist).put("n", v.size)) } })
        o.put("artists", JSONArray().apply { all.groupBy { it.artist }.entries.sortedBy { it.key.lowercase() }.take(300).forEach { (k, v) -> put(JSONObject().put("name", k).put("n", v.size)) } })
        val favs = Prefs.radioFavs.value.split('\n').filter { it.isNotBlank() }.toSet()
        o.put("stations", JSONArray().apply { Stations.all.filter { !it.paused }.sortedBy { if (it.name in favs) 0 else 1 }.take(150).forEach { put(JSONObject().put("name", it.name).put("genre", it.genre).put("group", it.group).put("country", it.country).put("fav", it.name in favs)) } })
        o.put("podcasts", JSONArray().apply { Podcasts.subscribed().forEach { put(JSONObject().put("name", it.title).put("image", it.image)) } })
        o.put("look", JSONObject().put("theme", Prefs.theme.value).put("skin", Prefs.skin.value).put("btnStyle", Prefs.btnStyle.value)
            .put("btnColour", Prefs.btnColour.value).put("barColour", Prefs.barColour.value).put("edgeEffect", Prefs.edgeEffect.value)
            .put("edgeOn", Prefs.edgeOn.value).put("viz", Prefs.viz.value).put("pack", Prefs.pack.value))
        return o
    }

    private fun reply(ctx: Context, o: JSONObject) {
        ctx.sendBroadcast(Intent("com.tomstechsolutions.car.JUKEBOX").setPackage("com.tomstechsolutions.car").putExtra("json", o.toString()))
    }

    companion object { private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO) }
}
