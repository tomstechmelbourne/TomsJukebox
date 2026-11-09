package com.tomstechsolutions.jukebox.data

import android.util.Xml
import com.tomstechsolutions.jukebox.Prefs
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import org.xmlpull.v1.XmlPullParser

data class ChannelInfo(val description: String, val link: String, val language: String, val count: Int, val newest: Long = 0L)

object Podcasts {
    val info = java.util.concurrent.ConcurrentHashMap<String, ChannelInfo>()

    suspend fun search(term: String): List<Podcast> = withContext(Dispatchers.IO) {
        val o = JSONObject(Net.get("https://itunes.apple.com/search?media=podcast&limit=40&term=${Net.enc(term)}"))
        val arr = o.optJSONArray("results") ?: JSONArray()
        (0 until arr.length()).map { arr.getJSONObject(it) }.filter { it.optString("feedUrl").isNotBlank() }.map {
            Podcast(it.optString("collectionName"), it.optString("artistName"), it.optString("feedUrl"), it.optString("artworkUrl600"))
        }
    }

    /** Apple Podcasts top chart for a country (au, vn). Feed addresses are looked up when one is opened. */
    suspend fun chart(country: String): List<Podcast> = withContext(Dispatchers.IO) {
        val o = JSONObject(Net.get("https://rss.applemarketingtools.com/api/v2/$country/podcasts/top/25/podcasts.json"))
        val arr = o.optJSONObject("feed")?.optJSONArray("results") ?: JSONArray()
        (0 until arr.length()).map { arr.getJSONObject(it) }.map {
            Podcast(it.optString("name"), it.optString("artistName"), "", it.optString("artworkUrl100").replace("100x100", "400x400"), it.optString("id"))
        }
    }

    suspend fun searchIn(term: String, country: String = "au", limit: Int = 15): List<Podcast> = withContext(Dispatchers.IO) {
        val o = JSONObject(Net.get("https://itunes.apple.com/search?media=podcast&country=$country&limit=$limit&term=${Net.enc(term)}"))
        val arr = o.optJSONArray("results") ?: JSONArray()
        (0 until arr.length()).map { arr.getJSONObject(it) }.filter { it.optString("feedUrl").isNotBlank() }.map {
            Podcast(it.optString("collectionName"), it.optString("artistName"), it.optString("feedUrl"), it.optString("artworkUrl600"), it.optString("collectionId"))
        }
    }

    suspend fun resolve(p: Podcast): Podcast = withContext(Dispatchers.IO) {
        if (p.feed.isNotBlank() || p.id.isBlank()) return@withContext p
        val o = JSONObject(Net.get("https://itunes.apple.com/lookup?id=${p.id}"))
        val r = o.optJSONArray("results")?.optJSONObject(0)
        p.copy(feed = r?.optString("feedUrl").orEmpty())
    }

    suspend fun episodes(p0: Podcast): List<Episode> = withContext(Dispatchers.IO) {
        val p = resolve(p0)
        val xml = Net.get(p.feed, 15000)
        val parser = Xml.newPullParser()
        parser.setFeature(XmlPullParser.FEATURE_PROCESS_NAMESPACES, false)
        parser.setInput(xml.reader())
        val out = ArrayList<Pair<Long, Episode>>()
        var inItem = false
        var stamp = 0L
        var hq = ""; var hqRate = 0L; var altRate = -1L; var altAudio = false
        var title = ""; var url = ""; var date = ""; var dur = 0L; var desc = ""; var img = ""
        var cDesc = ""; var cLink = ""; var cLang = ""
        var ev = parser.eventType
        while (ev != XmlPullParser.END_DOCUMENT && out.size < 5000) {
            when (ev) {
                XmlPullParser.START_TAG -> when (parser.name) {
                    "item" -> { inItem = true; title = ""; url = ""; date = ""; dur = 0; desc = ""; img = ""; stamp = 0L; hq = ""; hqRate = 0L; altRate = -1L }
                    "title" -> if (inItem) title = parser.nextText().trim()
                    "enclosure" -> if (inItem) url = parser.getAttributeValue(null, "url") ?: ""
                    "podcast:alternateEnclosure" -> if (inItem) {
                        altRate = parser.getAttributeValue(null, "bitrate")?.toDoubleOrNull()?.toLong() ?: 0L
                        altAudio = parser.getAttributeValue(null, "type")?.startsWith("audio") == true
                    }
                    "podcast:source" -> if (inItem && altAudio && altRate > hqRate) {
                        val u = parser.getAttributeValue(null, "uri") ?: ""
                        if (u.startsWith("http")) { hq = u; hqRate = altRate }
                    }
                    "pubDate" -> if (inItem) { val raw = parser.nextText().trim(); stamp = parseDate(raw); date = if (stamp > 0) showDate(stamp) else raw.take(16) }
                    "itunes:duration" -> if (inItem) dur = parseDur(parser.nextText())
                    "description" -> if (inItem) desc = parser.nextText().replace(Regex("<[^>]+>"), "").trim().take(400)
                                     else if (cDesc.isBlank()) cDesc = parser.nextText().replace(Regex("<[^>]+>"), "").trim().take(1500)
                    "link" -> if (!inItem && cLink.isBlank()) cLink = try { parser.nextText().trim() } catch (_: Exception) { "" }
                    "language" -> if (!inItem) cLang = parser.nextText().trim()
                    "itunes:image" -> if (inItem) img = parser.getAttributeValue(null, "href") ?: ""
                }
                XmlPullParser.END_TAG -> if (parser.name == "item") {
                    inItem = false
                    if (url.isNotBlank()) out += stamp to Episode(title, url, date, dur, p.title, img.ifBlank { p.image }, desc, hq)
                }
            }
            ev = parser.next()
        }
        info[p.feed] = ChannelInfo(cDesc, cLink, cLang, out.size, out.maxOfOrNull { it.first } ?: 0L)
        // Feeds don't all list the newest episode first: sort by date, newest first, then keep 300.
        out.sortedByDescending { it.first }.take(300).map { it.second }
    }

    private val dateFormats = listOf("EEE, dd MMM yyyy HH:mm:ss Z", "EEE, d MMM yyyy HH:mm:ss Z", "EEE, dd MMM yyyy HH:mm:ss zzz", "EEE, dd MMM yyyy HH:mm Z",
        "dd MMM yyyy HH:mm:ss Z", "EEE, dd MMM yyyy", "yyyy-MM-dd'T'HH:mm:ssXXX", "yyyy-MM-dd")
    /** RSS dates (RFC 822, sometimes sloppy) → milliseconds; 0 if unreadable. */
    fun parseDate(s: String): Long {
        val t = s.replace(Regex("\\s+"), " ").trim()
        for (f in dateFormats) try {
            val d = java.text.SimpleDateFormat(f, java.util.Locale.ENGLISH).apply { isLenient = true }.parse(t)
            if (d != null) return d.time
        } catch (_: Exception) { }
        return 0L
    }
    private fun showDate(ms: Long) = java.text.SimpleDateFormat("EEE, dd MMM yyyy", java.util.Locale.ENGLISH).format(java.util.Date(ms))

    private fun parseDur(s: String): Long {
        val p = s.trim().split(':').mapNotNull { it.toLongOrNull() }
        return when (p.size) { 3 -> p[0] * 3600 + p[1] * 60 + p[2]; 2 -> p[0] * 60 + p[1]; 1 -> p[0]; else -> 0 }
    }

    fun subscribed(): List<Podcast> = try {
        val a = JSONArray(Prefs.podcasts.value)
        (0 until a.length()).map { a.getJSONObject(it) }.map { Podcast(it.optString("t"), it.optString("a"), it.optString("f"), it.optString("i")) }
    } catch (_: Exception) { emptyList() }

    fun setSubscribed(list: List<Podcast>) {
        val a = JSONArray()
        list.forEach { a.put(JSONObject().put("t", it.title).put("a", it.author).put("f", it.feed).put("i", it.image)) }
        Prefs.podcasts.value = a.toString()
    }

    fun toggle(p: Podcast) {
        val l = subscribed().toMutableList()
        if (l.any { it.feed == p.feed }) l.removeAll { it.feed == p.feed } else l.add(p)
        setSubscribed(l)
    }
}
