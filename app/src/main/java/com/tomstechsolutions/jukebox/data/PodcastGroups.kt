package com.tomstechsolutions.jukebox.data

import android.content.Context
import com.tomstechsolutions.jukebox.t
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

/** A group of suggested channels, by their Apple Podcasts id (checked with tools/check_podcasts.py at build time). */
data class PodGroup(val key: String, val en: String, val vi: String, val ids: List<String>, val news: Boolean = false) { val name get() = t(en, vi) }

/** The suggested channel groups on the Podcast page. */
object PodcastGroups {
    val list = listOf(
        // RFI 60' · RFI Tạp chí Đặc Biệt · RFA Việt Nam Tuần Này · SBS Việt ngữ   (BBC Tiếng Việt, Radio Chân Trời Mới, SBTN: chưa có trên Apple Podcasts)
        PodGroup("vnnews", "Vietnamese News", "Tin Tức Tiếng Việt", listOf("1571503601", "1574624782", "1731182745", "161320292"), news = true),
        // Vatican News Tiếng Việt ×2 · Radio Công Giáo · Lời Chúa Mỗi Ngày · 365 Ngày Cầu Nguyện (Dòng Tên) · 40 Ngày Kinh Thánh · Suy Niệm Tin Mừng · Cà Phê Lời Chúa ·
        // Bible in a Year · Catholic Answers Live · EWTN News Nightly · Word on Fire · FaithND Daily Gospel · Vatican & World News   (Chân Lý Á Châu, VietCatholic, VietVatican: chưa có)
        PodGroup("catholic", "Catholic", "Công Giáo", listOf("1551917143", "1676412067", "1587296543", "1853452424", "1884241839", "1555201608", "1586455389", "1801959745",
            "1539568321", "129684370", "1151970163", "1065019039", "1709182712", "1649296291")),
        // 7News Just In · 9News · ABC News Daily · ABC AM · ABC PM · ABC The World Today · SBS News In Depth · The Morning Edition (The Age) ·
        // The Splash (Herald Sun) · That's ACA (A Current Affair) · LiSTNR Melbourne Local News · 3AW Mornings · The Conversation Hour (ABC Melbourne)
        // (10 News: không còn podcast tin tức nào đang cập nhật)
        PodGroup("aunews", "Australian News", "Tin Tức Úc", listOf("1713274928", "1896828280", "1349523628", "297778503", "297778504", "297778505", "73329715",
            "1436450976", "1444390972", "1821376327", "1775573992", "291212440", "92455788"), news = true),
        // triple j J Files · Like A Version · Double J · ABC The Music Show · ABC Classics · Song Exploder · SBS Giọng Ca Việt Úc · RFI Tạp chí Âm Nhạc · Thánh Ca Dòng Xitô
        PodGroup("music", "Music", "Âm Nhạc", listOf("919801673", "364978669", "1441212236", "156556864", "1535418229", "788236947", "1868596227", "1495217848", "1516748346")),
        // ABC Kids Listen: Play School · Story Salad · Little Yarns · ABC Classic Kids · Noisy by Nature · Short & Curly ·
        // Truyện cổ tích · Kho Truyện Cổ Tích · Kể Truyện Cho Bé · Truyện cổ tích và hát ru · Mr Bedtime Stories · Wow in the World · Story Pirates
        PodGroup("kids", "Kids", "Thiếu Nhi", listOf("1851914571", "1674951226", "1468817120", "1376821352", "1491841381", "1093699006",
            "1450698399", "1532630528", "1610576181", "1454826120", "1257569536", "1233834541", "719585944")),
        // Fonos · Kho Sách Nói · Sách Nói Mỗi Ngày · Truyện Ngắn Chọn Lọc · Truyện Ngắn (Nghe Kể) · Truyện Ngắn Thế Giới · Đọc Truyện Đêm Khuya (VOV, Đài Hà Nội) ·
        // Bóng Đèn Kể Chuyện · Chị Sophie Kể Chuyện · Nguyễn Ngọc Ngạn · Vua Truyện
        PodGroup("stories", "Vietnamese Stories & Audiobooks", "Kể Chuyện & Sách Nói Tiếng Việt", listOf("1571282770", "1505235567", "1573541336", "1651180294", "1833727223",
            "1538340531", "6814196004", "1702660933", "1567914655", "1671433065", "1734826819", "1517025287")),
    )

    /** News channels whose newest episode is older than this are left out (a news show that stopped is no use). */
    private const val NEWS_MAX_AGE_MS = 60L * 24 * 3600_000
    private val stale = HashSet<String>()

    private suspend fun lookup(ids: List<String>, news: Boolean): List<Podcast> {
        val got = LinkedHashMap<String, Podcast>()
        for (country in listOf("", "&country=vn", "&country=au")) {
            val need = ids.filter { it !in got }
            if (need.isEmpty()) break
            val o = try { JSONObject(Net.get("https://itunes.apple.com/lookup?id=${need.joinToString(",")}$country", 15000)) } catch (_: Exception) { continue }
            val a = o.optJSONArray("results") ?: continue
            for (k in 0 until a.length()) { val r = a.getJSONObject(k); val id = r.optString("collectionId"); if (r.optString("feedUrl").isNotBlank() && id in need) {
                val rel = try { Podcasts.parseDate(r.optString("releaseDate")) } catch (_: Exception) { 0L }
                if (news && rel > 0 && System.currentTimeMillis() - rel > NEWS_MAX_AGE_MS) { stale += id; got[id] = Podcast("", "", "", "", id); continue }
                got[id] = Podcast(r.optString("collectionName"), r.optString("artistName"), r.optString("feedUrl"), r.optString("artworkUrl600"), id) } }
        }
        return ids.mapNotNull { got[it] }.filter { it.feed.isNotBlank() }
    }

    /** Looks the groups up (one request per group), keeping the answer for a day so the page opens fast. */
    suspend fun load(ctx: Context, onGroup: (String, List<Podcast>) -> Unit) = withContext(Dispatchers.IO) {
        val sp = ctx.getSharedPreferences("pod_groups3", Context.MODE_PRIVATE)
        val fresh = System.currentTimeMillis() - sp.getLong("time", 0) < 24 * 3600_000L
        var all = true
        for (g in list) {
            val cached = if (fresh) sp.getString(g.key, null)?.let { fromJson(it) } else null
            val l = if (!cached.isNullOrEmpty()) cached else lookup(g.ids, g.news).also { if (it.isNotEmpty()) sp.edit().putString(g.key, toJson(it)).apply() else all = false }
            withContext(Dispatchers.Main) { onGroup(g.key, l) }
        }
        if (!fresh && all) sp.edit().putLong("time", System.currentTimeMillis()).apply()
    }

    private fun toJson(l: List<Podcast>) = JSONArray().apply { l.forEach { put(JSONObject().put("t", it.title).put("a", it.author).put("f", it.feed).put("i", it.image).put("id", it.id)) } }.toString()
    private fun fromJson(s: String) = try { val a = JSONArray(s); (0 until a.length()).map { a.getJSONObject(it) }.map { Podcast(it.optString("t"), it.optString("a"), it.optString("f"), it.optString("i"), it.optString("id")) } } catch (_: Exception) { emptyList() }
}
