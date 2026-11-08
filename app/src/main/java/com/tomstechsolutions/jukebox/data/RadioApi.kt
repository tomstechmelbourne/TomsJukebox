package com.tomstechsolutions.jukebox.data

import com.tomstechsolutions.jukebox.Prefs
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray

/** Finds live streams on Radio Browser (free, community-run directory). */
object RadioApi {
    private val hosts = listOf("de1.api.radio-browser.info", "nl1.api.radio-browser.info", "at1.api.radio-browser.info", "de2.api.radio-browser.info")

    private fun query(path: String): JSONArray {
        var last: Exception? = null
        for (h in hosts) {
            try { return JSONArray(Net.get("https://$h$path", 9000)) } catch (e: Exception) { last = e }
        }
        throw last ?: java.io.IOException("no server")
    }

    private fun toStations(arr: JSONArray, country: String, group: String): List<Station> {
        val out = ArrayList<Station>()
        for (i in 0 until arr.length()) {
            val o = arr.getJSONObject(i)
            val url = o.optString("url_resolved").ifBlank { o.optString("url") }
            if (url.isBlank()) continue
            out += Station(o.optString("name").trim(), o.optString("name").trim(), country, group,
                o.optString("tags").split(',').firstOrNull()?.trim().orEmpty(), url, o.optInt("bitrate"), o.optString("codec"),
                o.optInt("lastcheckok", 1) == 0)
        }
        return out
    }

    /** Fill in the stream of a built-in station. Returns false (Tạm Ngưng) if nothing works. */
    suspend fun resolve(s: Station): Boolean = withContext(Dispatchers.IO) {
        try {
            val cc = when (s.country) { "AU" -> "&countrycode=AU"; "VN" -> "&countrycode=VN"; else -> "" }
            var arr = query("/json/stations/search?name=${Net.enc(s.search)}$cc&hidebroken=true&order=clickcount&reverse=true&limit=15")
            if (arr.length() == 0 && cc.isNotEmpty() && s.country == "OS") arr = query("/json/stations/search?name=${Net.enc(s.search)}&hidebroken=true&order=clickcount&reverse=true&limit=15")
            val found = toStations(arr, s.country, s.group).filter { !it.paused }
            val pick = (if (Prefs.radioHq.value) found.filter { it.bitrate >= 128 }.ifEmpty { found } else found)
                .maxByOrNull { it.bitrate.coerceAtMost(320) / 64 * 1000 - found.indexOf(it) }
            if (pick == null) { s.paused = true; return@withContext false }
            s.url = pick.url; s.bitrate = pick.bitrate; s.codec = pick.codec; s.paused = false
            true
        } catch (_: Exception) { false }
    }

    suspend fun search(text: String, country: String = ""): List<Station> = withContext(Dispatchers.IO) {
        val cc = if (country.isNotBlank()) "&countrycode=$country" else ""
        val list = toStations(query("/json/stations/search?name=${Net.enc(text)}$cc&hidebroken=true&order=clickcount&reverse=true&limit=60"), country, "SEARCH")
        if (Prefs.radioHq.value) list.filter { it.bitrate >= 128 } else list
    }

    /** Vietnamese-language stations anywhere in the world (Australia first). */
    suspend fun vietnamese(): List<Station> = withContext(Dispatchers.IO) {
        val list = toStations(query("/json/stations/search?language=vietnamese&hidebroken=true&order=clickcount&reverse=true&limit=100"), "OS", "SEARCH")
        list.filter { it.country != "VN" }.sortedByDescending { it.bitrate }
    }

    suspend fun byState(state: String): List<Station> = withContext(Dispatchers.IO) {
        val full = mapOf("VIC" to "Victoria", "NSW" to "New South Wales", "QLD" to "Queensland", "SA" to "South Australia",
            "WA" to "Western Australia", "TAS" to "Tasmania", "NT" to "Northern Territory", "ACT" to "Australian Capital Territory")[state] ?: state
        toStations(query("/json/stations/search?countrycode=AU&state=${Net.enc(full)}&hidebroken=true&order=clickcount&reverse=true&limit=80"), "AU", state)
    }
}
