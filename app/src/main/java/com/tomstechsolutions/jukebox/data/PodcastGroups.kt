package com.tomstechsolutions.jukebox.data

import android.content.Context
import com.tomstechsolutions.jukebox.t
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.text.Normalizer

/** One channel to look up on Apple Podcasts. take > 1 = a topic search that keeps the first few results. */
data class PodPick(val query: String, val country: String = "au", val take: Int = 1, val must: String = "")
data class PodGroup(val key: String, val en: String, val vi: String, val picks: List<PodPick>) { val name get() = t(en, vi) }

/** The suggested channel groups on the Podcast page. Names are checked on Apple Podcasts at build time (tools/check_podcasts.py). */
object PodcastGroups {
    val list = listOf(
        PodGroup("vnnews", "Vietnamese News", "Tin Tức Tiếng Việt", listOf(
            PodPick("RFI Tiếng Việt", "vn", must = "rfi"), PodPick("RFA Tiếng Việt", "us", must = "rfa"), PodPick("BBC News Tiếng Việt", "vn", must = "bbc"),
            PodPick("SBS Vietnamese", "au", must = "sbs"), PodPick("Radio Chân Trời Mới", "us", must = "chan troi moi"), PodPick("SBTN", "us", must = "sbtn"),
        )),
        PodGroup("catholic", "Catholic", "Công Giáo", listOf(
            PodPick("Chân Lý Á Châu", "vn", must = "chan ly"), PodPick("Radio Veritas Asia Vietnamese", "vn", must = "veritas"),
            PodPick("Vatican News Tiếng Việt", "vn", must = "vatican"), PodPick("VietCatholic", "us", must = "vietcatholic"), PodPick("VietVatican", "us", must = "vietvatican"),
            PodPick("Lời Chúa Mỗi Ngày", "vn", 2, must = "loi chua"), PodPick("Vatican News", "au", must = "vatican"), PodPick("The Bible in a Year Ascension", "au", must = "bible in a year"),
            PodPick("Catholic Answers Live", "au", must = "catholic answers"), PodPick("EWTN", "au", must = "ewtn"), PodPick("Word on Fire", "au", must = "word on fire"),
            PodPick("Catholic Archdiocese of Melbourne", "au", must = "melbourne"), PodPick("Daily Gospel Reflection", "au", must = "gospel"),
        )),
        PodGroup("aunews", "Australian News", "Tin Tức Úc", listOf(
            PodPick("7NEWS", "au", must = "7news"), PodPick("9News", "au", must = "9news"), PodPick("10 News First", "au", must = "10 news"),
            PodPick("ABC News Daily", "au", must = "abc"), PodPick("SBS News", "au", must = "sbs"), PodPick("The Age", "au", must = "the age"),
            PodPick("Herald Sun", "au", must = "herald sun"), PodPick("ABC Radio Melbourne", "au", must = "melbourne"),
        )),
        PodGroup("music", "Music", "Âm Nhạc", listOf(
            PodPick("triple j", "au", must = "triple j"), PodPick("Double J", "au", must = "double j"), PodPick("ABC Classic", "au", must = "classic"),
            PodPick("Song Exploder", "au", must = "song exploder"), PodPick("nhạc vàng", "vn", 3), PodPick("bolero", "vn", 2), PodPick("nhạc xưa", "vn", 2),
            PodPick("nhạc Trịnh", "vn", 2), PodPick("Thánh ca", "vn", 2),
        )),
        PodGroup("kids", "Kids", "Thiếu Nhi", listOf(
            PodPick("ABC Kids Listen", "au", must = "abc kids"), PodPick("truyện cổ tích", "vn", 3), PodPick("bedtime stories for kids", "au", 2),
            PodPick("học tiếng Anh cho bé", "vn", 2), PodPick("Wow in the World", "au", must = "wow in the world"), PodPick("Story Pirates", "au", must = "story pirates"),
        )),
        PodGroup("stories", "Vietnamese Stories & Audiobooks", "Kể Chuyện & Sách Nói Tiếng Việt", listOf(
            PodPick("sách nói", "vn", 3), PodPick("truyện ngắn", "vn", 2), PodPick("đọc truyện đêm khuya", "vn", 2), PodPick("kể chuyện", "vn", 2),
        )),
    )

    fun norm(s: String) = Normalizer.normalize(s.lowercase().replace('đ', 'd'), Normalizer.Form.NFD).replace(Regex("\\p{Mn}+"), "")

    private suspend fun find(pk: PodPick): List<Podcast> {
        for (c in listOf(pk.country, "us").distinct()) {
            val r = try { Podcasts.searchIn(pk.query, c, if (pk.take > 1) pk.take + 2 else 8) } catch (_: Exception) { emptyList() }
            val ok = if (pk.must.isBlank()) r.take(pk.take) else r.filter { norm(it.title + " " + it.author).contains(norm(pk.must)) }.take(pk.take)
            if (ok.isNotEmpty()) return ok
        }
        return emptyList()
    }

    /** Looks the groups up, keeping the answer for a day so the page opens fast. [onGroup] is called as each group is ready. */
    suspend fun load(ctx: Context, onGroup: (String, List<Podcast>) -> Unit) = withContext(Dispatchers.IO) {
        val sp = ctx.getSharedPreferences("pod_groups", Context.MODE_PRIVATE)
        val fresh = System.currentTimeMillis() - sp.getLong("time", 0) < 24 * 3600_000L
        for (g in list) {
            if (fresh) sp.getString(g.key, null)?.let { js -> val l = fromJson(js); if (l.isNotEmpty()) { withContext(Dispatchers.Main) { onGroup(g.key, l) }; return@let } }
            if (fresh && sp.contains(g.key)) continue
            val out = LinkedHashMap<String, Podcast>()
            for (pk in g.picks) find(pk).forEach { if (it.feed !in out) out[it.feed] = it }
            val l = out.values.toList()
            sp.edit().putString(g.key, toJson(l)).apply()
            withContext(Dispatchers.Main) { onGroup(g.key, l) }
        }
        if (!fresh) sp.edit().putLong("time", System.currentTimeMillis()).apply()
    }

    private fun toJson(l: List<Podcast>) = JSONArray().apply { l.forEach { put(JSONObject().put("t", it.title).put("a", it.author).put("f", it.feed).put("i", it.image).put("id", it.id)) } }.toString()
    private fun fromJson(s: String) = try { val a = JSONArray(s); (0 until a.length()).map { a.getJSONObject(it) }.map { Podcast(it.optString("t"), it.optString("a"), it.optString("f"), it.optString("i"), it.optString("id")) } } catch (_: Exception) { emptyList() }
}
