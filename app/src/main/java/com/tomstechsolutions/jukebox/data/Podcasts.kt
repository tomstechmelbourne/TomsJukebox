package com.tomstechsolutions.jukebox.data

import android.util.Xml
import com.tomstechsolutions.jukebox.Prefs
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import org.xmlpull.v1.XmlPullParser

object Podcasts {
    suspend fun search(term: String): List<Podcast> = withContext(Dispatchers.IO) {
        val o = JSONObject(Net.get("https://itunes.apple.com/search?media=podcast&limit=40&term=${Net.enc(term)}"))
        val arr = o.optJSONArray("results") ?: JSONArray()
        (0 until arr.length()).map { arr.getJSONObject(it) }.filter { it.optString("feedUrl").isNotBlank() }.map {
            Podcast(it.optString("collectionName"), it.optString("artistName"), it.optString("feedUrl"), it.optString("artworkUrl600"))
        }
    }

    suspend fun episodes(p: Podcast): List<Episode> = withContext(Dispatchers.IO) {
        val xml = Net.get(p.feed, 15000)
        val parser = Xml.newPullParser()
        parser.setFeature(XmlPullParser.FEATURE_PROCESS_NAMESPACES, false)
        parser.setInput(xml.reader())
        val out = ArrayList<Episode>()
        var inItem = false
        var title = ""; var url = ""; var date = ""; var dur = 0L; var desc = ""; var img = ""
        var ev = parser.eventType
        while (ev != XmlPullParser.END_DOCUMENT && out.size < 300) {
            when (ev) {
                XmlPullParser.START_TAG -> when (parser.name) {
                    "item" -> { inItem = true; title = ""; url = ""; date = ""; dur = 0; desc = ""; img = "" }
                    "title" -> if (inItem) title = parser.nextText().trim()
                    "enclosure" -> if (inItem) url = parser.getAttributeValue(null, "url") ?: ""
                    "pubDate" -> if (inItem) date = parser.nextText().trim().take(16)
                    "itunes:duration" -> if (inItem) dur = parseDur(parser.nextText())
                    "description" -> if (inItem) desc = parser.nextText().replace(Regex("<[^>]+>"), "").trim().take(400)
                    "itunes:image" -> if (inItem) img = parser.getAttributeValue(null, "href") ?: ""
                }
                XmlPullParser.END_TAG -> if (parser.name == "item") {
                    inItem = false
                    if (url.isNotBlank()) out += Episode(title, url, date, dur, p.title, img.ifBlank { p.image }, desc)
                }
            }
            ev = parser.next()
        }
        out
    }

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
