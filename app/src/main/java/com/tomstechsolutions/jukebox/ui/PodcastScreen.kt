package com.tomstechsolutions.jukebox.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.data.Episode
import com.tomstechsolutions.jukebox.data.Podcast
import com.tomstechsolutions.jukebox.data.Podcasts
import com.tomstechsolutions.jukebox.playback.Core
import com.tomstechsolutions.jukebox.t
import kotlinx.coroutines.launch

object PodcastNav { val openQuery = androidx.compose.runtime.mutableStateOf("") }

private val topics = listOf(
    Triple("Vietnamese", "Tiếng Việt", "tiếng việt"), Triple("Australian News", "Tin Tức Úc", "ABC news Australia"),
    Triple("Technology", "Công Nghệ", "technology"), Triple("Business & Money", "Kinh Doanh & Tài Chính", "business finance"),
    Triple("Health", "Sức Khoẻ", "health"), Triple("Learn English", "Học Tiếng Anh", "learn english"),
    Triple("Sport", "Thể Thao", "AFL football"), Triple("Stories & Audiobooks", "Kể Chuyện & Sách Nói", "audiobook stories"),
    Triple("Comedy", "Hài & Giải Trí", "comedy"), Triple("Music", "Âm Nhạc", "music"),
)

/** A row of podcast covers you can swipe sideways. */
@Composable
private fun CoverRow(title: String, items: List<Podcast>, th: JTheme, onOpen: (Podcast) -> Unit) {
    if (items.isEmpty()) return
    SectionTitle(title, th)
    androidx.compose.foundation.lazy.LazyRow(horizontalArrangement = androidx.compose.foundation.layout.Arrangement.spacedBy(10.dp)) {
        items(items) { p ->
            Column(Modifier.width(118.dp).clickable { onOpen(p) }) {
                Cover(p.image, 0, 118.dp, th, 14.dp)
                Text(p.title, color = th.text, fontSize = 13.sp, fontWeight = FontWeight.SemiBold, maxLines = 2, overflow = TextOverflow.Ellipsis)
                Text(p.author, color = th.muted, fontSize = 11.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
            }
        }
    }
}

@Composable
fun PodcastScreen(th: JTheme) {
    val scope = rememberCoroutineScope()
    var query by remember { mutableStateOf("") }
    var results by remember { mutableStateOf<List<Podcast>>(emptyList()) }
    var open by remember { mutableStateOf<Podcast?>(null) }
    var eps by remember { mutableStateOf<List<Episode>>(emptyList()) }
    var busy by remember { mutableStateOf(false) }
    var msg by remember { mutableStateOf("") }
    @Suppress("UNUSED_VARIABLE") val subsKey = Prefs.podcasts.state.value
    val subs = Podcasts.subscribed()

    var topAu by remember { mutableStateOf<List<Podcast>>(emptyList()) }
    var topVn by remember { mutableStateOf<List<Podcast>>(emptyList()) }
    var byTopic by remember { mutableStateOf<Map<String, List<Podcast>>>(emptyMap()) }
    var mayLike by remember { mutableStateOf<List<Podcast>>(emptyList()) }
    LaunchedEffect(Unit) {
        topAu = try { Podcasts.chart("au") } catch (_: Exception) { emptyList() }
        topVn = try { Podcasts.chart("vn") } catch (_: Exception) { emptyList() }
        val m = LinkedHashMap<String, List<Podcast>>()
        for ((en, vi, q) in topics) { m[t(en, vi)] = try { Podcasts.searchIn(q, if (vi == "Tiếng Việt") "vn" else "au") } catch (_: Exception) { emptyList() }; byTopic = LinkedHashMap(m) }
        val subs0 = Podcasts.subscribed()
        if (subs0.isNotEmpty()) mayLike = try {
            Podcasts.searchIn(subs0.first().title.split(' ').take(2).joinToString(" "), "au", 20).filter { p -> subs0.none { it.feed == p.feed } }
        } catch (_: Exception) { emptyList() }
    }
    LaunchedEffect(PodcastNav.openQuery.value) {
        val q = PodcastNav.openQuery.value
        if (q.isNotBlank()) {
            PodcastNav.openQuery.value = ""
            busy = true
            val r = try { Podcasts.search(q) } catch (_: Exception) { emptyList() }
            results = r; busy = false
            r.firstOrNull { it.title.contains("SBS", true) && it.title.contains("Viet", true) }?.let { open = it }
        }
    }
    LaunchedEffect(open) {
        val p0 = open ?: return@LaunchedEffect
        if (p0.feed.isBlank()) { val r = try { Podcasts.resolve(p0) } catch (_: Exception) { p0 }; if (r.feed.isNotBlank()) { open = r; return@LaunchedEffect } }
        val p = p0
        busy = true; eps = emptyList()
        eps = try { Podcasts.episodes(p) } catch (_: Exception) { msg = t("Couldn't load this podcast.", "Không tải được podcast này."); emptyList() }
        busy = false
    }

    Column(Modifier.fillMaxSize().padding(horizontal = 14.dp)) {
        val p = open
        if (p != null) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconBtn(Gl.back, th.text) { open = null }
                Text(p.title, color = th.text, fontSize = 18.sp, fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis, modifier = Modifier.weight(1f))
            }
            val sub = subs.any { it.feed == p.feed }
            Btn(if (sub) t("Unsubscribe", "Bỏ Theo Dõi") else t("Subscribe", "Theo Dõi"), th, if (sub) Gl.check else Gl.plus, primary = !sub) { Podcasts.toggle(p) }
            if (busy) Text(t("Loading episodes…", "Đang tải các tập…"), color = th.muted)
            LazyColumn(verticalArrangement = Rows) {
                items(eps) { e ->
                    Row2(e.title, listOf(e.date, if (e.durationS > 0) fmtTime(e.durationS * 1000) else "").filter { it.isNotBlank() }.joinToString(" · "), th,
                        selected = Core.uri.value == e.url, leading = { Cover(e.image, 0, 48.dp, th) },
                        trailing = { IconBtn(Gl.play, th.text, 22.dp) { Core.playEpisode(e) } }) { Core.playEpisode(e) }
                }
            }
            return@Column
        }
        Text("Podcast", color = th.text, fontSize = 28.sp, fontWeight = FontWeight.Bold)
        SearchBox(query, t("Search podcasts (e.g. SBS Vietnamese)", "Tìm podcast (vd. SBS Tiếng Việt)"), th) { query = it }
        if (query.length >= 2) Btn(t("Search", "Tìm"), th, Gl.search, primary = true) {
            busy = true
            scope.launch { results = try { Podcasts.search(query) } catch (_: Exception) { msg = t("Can't search right now.", "Hiện chưa tìm được."); emptyList() }; busy = false }
        }
        if (busy) Text(t("Searching…", "Đang tìm…"), color = th.muted)
        if (msg.isNotBlank()) Text(msg, color = th.muted, fontSize = 12.sp)
        LazyColumn(verticalArrangement = Rows) {
            if (results.isNotEmpty()) item { SectionTitle(t("Results", "Kết Quả"), th) }
            items(results) { r -> Row2(r.title, r.author, th, leading = { Cover(r.image, 0, 52.dp, th) }) { open = r } }
            item { SectionTitle(t("Subscribed", "Đang Theo Dõi"), th) }
            if (subs.isEmpty()) item { Text(t("Search above and tap Subscribe to keep a podcast here.", "Tìm ở trên rồi bấm Theo Dõi để giữ podcast ở đây."), color = th.muted, fontSize = 13.sp) }
            items(subs) { s -> Row2(s.title, s.author, th, leading = { Cover(s.image, 0, 52.dp, th) }) { open = s } }
            item { CoverRow(t("You Might Like", "Có Thể Tom Thích"), mayLike, th) { open = it } }
            item { CoverRow(t("Top In Australia", "Top Úc"), topAu, th) { open = it } }
            item { CoverRow(t("Top In Vietnam", "Top Việt Nam"), topVn, th) { open = it } }
            byTopic.forEach { (name, l) -> item(key = name) { CoverRow(name, l, th) { open = it } } }
            item { androidx.compose.foundation.layout.Spacer(Modifier.height(30.dp)) }
        }
    }
}
