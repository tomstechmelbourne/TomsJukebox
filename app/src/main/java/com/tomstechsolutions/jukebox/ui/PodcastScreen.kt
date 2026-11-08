package com.tomstechsolutions.jukebox.ui

import androidx.compose.foundation.layout.Column
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

    LaunchedEffect(open) {
        val p = open ?: return@LaunchedEffect
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
        }
    }
}
