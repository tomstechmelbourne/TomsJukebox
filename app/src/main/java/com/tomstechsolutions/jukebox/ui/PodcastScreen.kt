package com.tomstechsolutions.jukebox.ui

import android.content.Intent
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.core.content.pm.ShortcutInfoCompat
import androidx.core.content.pm.ShortcutManagerCompat
import androidx.core.graphics.drawable.IconCompat
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.R
import com.tomstechsolutions.jukebox.data.Episode
import com.tomstechsolutions.jukebox.data.PodSave
import com.tomstechsolutions.jukebox.data.PodStore
import com.tomstechsolutions.jukebox.data.Podcast
import com.tomstechsolutions.jukebox.data.PodcastGroups
import com.tomstechsolutions.jukebox.data.Podcasts
import com.tomstechsolutions.jukebox.playback.Core
import com.tomstechsolutions.jukebox.t
import kotlinx.coroutines.launch

object PodcastNav {
    val openQuery = mutableStateOf("")
    val openPodcast = mutableStateOf<Podcast?>(null)       // from a pinned shortcut or a "new episode" alert
}

private val topics = listOf(
    Triple("Technology", "Công Nghệ", "technology"), Triple("Business & Money", "Kinh Doanh & Tài Chính", "business finance"),
    Triple("Health", "Sức Khoẻ", "health"), Triple("Learn English", "Học Tiếng Anh", "learn english"),
    Triple("Sport", "Thể Thao", "AFL football"), Triple("Comedy", "Hài & Giải Trí", "comedy"),
)

/** A row of podcast covers you can swipe sideways. Long-press for the channel menu. */
@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun CoverRow(title: String, items: List<Podcast>, th: JTheme, selected: Set<String>, onLong: (Podcast) -> Unit, onOpen: (Podcast) -> Unit) {
    val shown = items.filter { !PodStore.hidden(it) }
    if (shown.isEmpty()) return
    SectionTitle(title, th)
    LazyRow(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        items(shown) { p ->
            val sel = p.feed in selected && p.feed.isNotBlank() || (p.id.isNotBlank() && p.id in selected)
            Column(Modifier.width(118.dp).clip(RoundedCornerShape(14.dp)).border(if (sel) 3.dp else 0.dp, if (sel) th.accent else Color.Transparent, RoundedCornerShape(14.dp))
                .combinedClickable(onClick = { onOpen(p) }, onLongClick = { onLong(p) })) {
                Cover(p.image, 0, 118.dp, th, 14.dp)
                Text(p.title, color = th.text, fontSize = 13.sp, fontWeight = FontWeight.SemiBold, maxLines = 2, overflow = TextOverflow.Ellipsis)
                Text(p.author, color = th.muted, fontSize = 11.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
            }
        }
    }
}

private fun key(p: Podcast) = p.feed.ifBlank { p.id.ifBlank { p.title } }

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun PodcastScreen(th: JTheme) {
    val ctx = LocalContext.current
    val scope = rememberCoroutineScope()
    var query by remember { mutableStateOf("") }
    var results by remember { mutableStateOf<List<Podcast>>(emptyList()) }
    var open by remember { mutableStateOf<Podcast?>(null) }
    var eps by remember { mutableStateOf<List<Episode>>(emptyList()) }
    var busy by remember { mutableStateOf(false) }
    var msg by remember { mutableStateOf("") }
    var menuFor by remember { mutableStateOf<Podcast?>(null) }
    var epMenu by remember { mutableStateOf<Episode?>(null) }
    var speedFor by remember { mutableStateOf<Podcast?>(null) }
    var skipFor by remember { mutableStateOf<Podcast?>(null) }
    var infoFor by remember { mutableStateOf<Podcast?>(null) }
    var selecting by remember { mutableStateOf(false) }
    var selected by remember { mutableStateOf<Map<String, Podcast>>(emptyMap()) }
    var tick by remember { mutableStateOf(0) }
    @Suppress("UNUSED_VARIABLE") val subsKey = Prefs.podcasts.state.value + Prefs.podHidden.state.value + Prefs.podNotify.state.value + Prefs.podAutoDl.state.value + tick
    val subs = Podcasts.subscribed()

    var topAu by remember { mutableStateOf<List<Podcast>>(emptyList()) }
    var topVn by remember { mutableStateOf<List<Podcast>>(emptyList()) }
    var groups by remember { mutableStateOf<Map<String, List<Podcast>>>(emptyMap()) }
    var byTopic by remember { mutableStateOf<Map<String, List<Podcast>>>(emptyMap()) }
    var mayLike by remember { mutableStateOf<List<Podcast>>(emptyList()) }
    LaunchedEffect(Unit) {
        launch { PodcastGroups.load(ctx) { k, l -> groups = groups + (k to l) } }
        topAu = try { Podcasts.chart("au") } catch (_: Exception) { emptyList() }
        topVn = try { Podcasts.chart("vn") } catch (_: Exception) { emptyList() }
        val subs0 = Podcasts.subscribed()
        if (subs0.isNotEmpty()) mayLike = try {
            Podcasts.searchIn(subs0.first().title.split(' ').take(2).joinToString(" "), "au", 20).filter { p -> subs0.none { it.feed == p.feed } }
        } catch (_: Exception) { emptyList() }
        val m = LinkedHashMap<String, List<Podcast>>()
        for ((en, vi, q) in topics) { m[t(en, vi)] = try { Podcasts.searchIn(q, "au") } catch (_: Exception) { emptyList() }; byTopic = LinkedHashMap(m) }
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
    LaunchedEffect(PodcastNav.openPodcast.value) { PodcastNav.openPodcast.value?.let { open = it; PodcastNav.openPodcast.value = null } }
    LaunchedEffect(open) {
        val p0 = open ?: return@LaunchedEffect
        if (p0.feed.isBlank()) { val r = try { Podcasts.resolve(p0) } catch (_: Exception) { p0 }; if (r.feed.isNotBlank()) { open = r; return@LaunchedEffect } }
        busy = true; eps = emptyList(); msg = ""
        if (p0.feed in Prefs.podNew.value) Prefs.podNew.value = Prefs.podNew.value.split('\n').filter { it.isNotBlank() && it != p0.feed }.joinToString("\n")
        eps = try { Podcasts.episodes(p0) } catch (_: Exception) { msg = t("Couldn't load this podcast.", "Không tải được podcast này."); emptyList() }
        busy = false
    }
    BackHandler(open != null) { open = null }
    BackHandler(selecting) { selecting = false; selected = emptyMap() }

    fun latest(p: Podcast, then: (Episode) -> Unit) { scope.launch { val l = try { Podcasts.episodes(p) } catch (_: Exception) { emptyList() }; l.firstOrNull()?.let(then) ?: run { msg = t("No episodes found.", "Không có tập nào.") } } }
    fun longPress(p: Podcast) { if (selecting) selected = if (key(p) in selected) selected - key(p) else selected + (key(p) to p) else menuFor = p }
    fun tap(p: Podcast) { if (selecting) longPress(p) else open = p }

    Column(Modifier.fillMaxSize().padding(horizontal = 14.dp)) {
        val p = open
        if (p != null) { ChannelPage(p, eps, busy, msg, th, onBack = { open = null }, onMenu = { menuFor = p }, onEpLong = { epMenu = it },
            onLatest = { eps.firstOrNull()?.let { Core.playEpisode(it) } }); return@Column }

        if (selecting) Row(Modifier.fillMaxWidth().padding(vertical = 4.dp).clip(RoundedCornerShape(14.dp)).background(th.accent.copy(alpha = 0.18f)).padding(6.dp),
            verticalAlignment = Alignment.CenterVertically) {
            Text(t("Selected: ", "Đã chọn: ") + selected.size, color = th.text, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f).padding(start = 6.dp))
            Btn(t("Follow", "Theo Dõi"), th) { scope.launch { selected.values.forEach { val r = try { Podcasts.resolve(it) } catch (_: Exception) { it }; if (r.feed.isNotBlank() && Podcasts.subscribed().none { s -> s.feed == r.feed }) Podcasts.toggle(r) }; selecting = false; selected = emptyMap() } }
            Btn(t("Hide", "Ẩn"), th) { selected.values.forEach { PodStore.hide(it) }; selecting = false; selected = emptyMap() }
            Btn("⬇", th) { scope.launch { selected.values.forEach { val r = try { Podcasts.resolve(it) } catch (_: Exception) { it }; if (r.feed.isNotBlank() && !PodStore.autoDlOn(r)) PodStore.toggleAutoDl(ctx, r) }; selecting = false; selected = emptyMap() } }
            IconBtn(Gl.close, th.text) { selecting = false; selected = emptyMap() }
        } else Text("Podcast", color = th.text, fontSize = 28.sp, fontWeight = FontWeight.Bold)
        SearchBox(query, t("Search podcasts (e.g. SBS Vietnamese)", "Tìm podcast (vd. SBS Tiếng Việt)"), th) { query = it }
        if (query.length >= 2) Btn(t("Search", "Tìm"), th, Gl.search, primary = true) {
            busy = true
            scope.launch { results = try { Podcasts.search(query) } catch (_: Exception) { msg = t("Can't search right now.", "Hiện chưa tìm được."); emptyList() }; busy = false }
        }
        if (busy) Text(t("Searching…", "Đang tìm…"), color = th.muted)
        if (msg.isNotBlank()) Text(msg, color = th.muted, fontSize = 12.sp)
        val selKeys = selected.keys
        LazyColumn(verticalArrangement = Rows) {
            if (results.isNotEmpty()) item { SectionTitle(t("Results", "Kết Quả"), th) }
            items(results) { r -> Row2(r.title, r.author, th, selected = key(r) in selKeys, leading = { Cover(r.image, 0, 52.dp, th) }, onLong = { longPress(r) }) { tap(r) } }
            item { SectionTitle(t("Following", "Đang Theo Dõi"), th) }
            if (subs.isEmpty()) item { Text(t("Search above or long-press a channel below, then tap Follow.", "Tìm ở trên hoặc nhấn giữ một kênh bên dưới, rồi chọn Theo Dõi."), color = th.muted, fontSize = 13.sp) }
            items(subs) { s -> Row2(s.title, listOfNotNull(s.author.ifBlank { null }, if (PodStore.notifyOn(s)) "🔔" else null, if (PodStore.autoDlOn(s)) "⬇" else null).joinToString("  "), th,
                selected = key(s) in selKeys, leading = { Cover(s.image, 0, 52.dp, th) }, onLong = { longPress(s) }) { tap(s) } }
            PodcastGroups.list.forEach { g -> item(key = "g_" + g.key) { CoverRow(g.name, groups[g.key] ?: emptyList(), th, selKeys, ::longPress, ::tap) } }
            item { CoverRow(t("You Might Like", "Có Thể Tom Thích"), mayLike, th, selKeys, ::longPress, ::tap) }
            item { CoverRow(t("Top In Australia", "Top Úc"), topAu, th, selKeys, ::longPress, ::tap) }
            item { CoverRow(t("Top In Vietnam", "Top Việt Nam"), topVn, th, selKeys, ::longPress, ::tap) }
            byTopic.forEach { (name, l) -> item(key = name) { CoverRow(name, l, th, selKeys, ::longPress, ::tap) } }
            val hid = PodStore.hiddenList()
            if (hid.isNotEmpty()) item {
                SectionTitle(t("Hidden Channels", "Kênh Đã Ẩn") + " (${hid.size})", th)
                FlowRow { hid.forEach { h -> Chip("↺ " + h.title.take(28), false, th) { PodStore.unhide(h.title); tick++ } } }
            }
            item { Spacer(Modifier.height(30.dp)) }
        }
    }

    // ---------- channel menu (long-press or ⋯) ----------
    menuFor?.let { mp ->
        val sub = subs.any { it.feed == mp.feed && mp.feed.isNotBlank() }
        MenuDialog(mp.title, th, { menuFor = null }, listOf(
            "▶  " + t("Play Latest Episode", "Phát Tập Mới Nhất") to { latest(mp) { Core.playEpisode(it) } },
            (if (sub) "★  " + t("Unfollow", "Bỏ Theo Dõi") else "☆  " + t("Follow", "Theo Dõi")) to { scope.launch { val r = try { Podcasts.resolve(mp) } catch (_: Exception) { mp }; if (r.feed.isNotBlank()) Podcasts.toggle(r) } },
            (if (PodStore.notifyOn(mp)) "🔔  " + t("New Episode Alerts: On", "Báo Tập Mới: Đang Bật") else "🔕  " + t("Alert Me About New Episodes", "Báo Tập Mới")) to { scope.launch { val r = try { Podcasts.resolve(mp) } catch (_: Exception) { mp }; if (r.feed.isNotBlank()) PodStore.toggleNotify(ctx, r) } },
            (if (PodStore.autoDlOn(mp)) "⬇  " + t("Auto Download (Wi-Fi): On", "Tải Tự Động (Wi-Fi): Đang Bật") else "⬇  " + t("Auto Download New Episodes (Wi-Fi)", "Tải Tự Động Tập Mới (Wi-Fi)")) to {
                scope.launch { val r = try { Podcasts.resolve(mp) } catch (_: Exception) { mp }; if (r.feed.isNotBlank()) PodStore.toggleAutoDl(ctx, r) } },
            "➕  " + t("Add Latest To Queue", "Thêm Vào Danh Sách Chờ") to { latest(mp) { Core.queueEpisode(it) } },
            (if (PodSave.autoSaveOn(mp)) "⏰  " + t("Auto-Save New Episodes: On", "Tự Lưu Tập Mới Vào Bản Thâu: Đang Bật") else "⏰  " + t("Auto-Save Each New Episode To Recordings", "Tự Lưu Tập Mới Mỗi Ngày Vào Bản Thâu Âm")) to {
                scope.launch { val r = try { Podcasts.resolve(mp) } catch (_: Exception) { mp }; if (r.feed.isNotBlank()) { val was = PodSave.autoSaveOn(r); PodSave.toggleAutoSave(ctx, r)
                    if (!was) latest(r) { e -> scope.launch { if (!PodSave.alreadySaved(e.url) && PodSave.saveWhole(ctx, e)) PodSave.markSaved(e.url) } } } } },
            "💾  " + t("Save Latest Episode To Recordings", "Lưu Tập Mới Nhất Vào Bản Thâu Âm") to { latest(mp) { e -> scope.launch { PodSave.saveWhole(ctx, e) } } },
            "📌  " + t("Pin To Home Screen", "Ghim Ra Màn Hình Chính") to { scope.launch { val r = try { Podcasts.resolve(mp) } catch (_: Exception) { mp }; pin(ctx, r) } },
            "⏩  " + t("Speed For This Channel", "Tốc Độ Riêng Cho Kênh") + " (${fmtSpeed(PodStore.speed(mp.title))})" to { speedFor = mp },
            "⏭  " + t("Skip The Intro", "Bỏ Qua Phần Đầu") + (PodStore.skip(mp.title).let { if (it > 0) " (${it}s)" else "" }) to { skipFor = mp },
            "ℹ  " + t("Channel Info", "Thông Tin Kênh") to { infoFor = mp },
            "📤  " + t("Share Channel", "Chia Sẻ Kênh") to { share(ctx, mp) },
            "🚫  " + t("Hide This Channel", "Ẩn Kênh Này") to { PodStore.hide(mp); if (open == mp) open = null },
            "☑  " + t("Select Several Channels", "Chọn Nhiều Kênh") to { selecting = true; selected = mapOf(key(mp) to mp) },
        ))
    }
    epMenu?.let { e ->
        val played = PodStore.played(e.url); val local = PodStore.localFile(ctx, e) != null; val pos = PodStore.pos(e.url)
        MenuDialog(e.title, th, { epMenu = null }, listOfNotNull(
            (if (pos > 0) "▶  " + t("Resume From ", "Nghe Tiếp Từ ") + fmtTime(pos) else "▶  " + t("Play", "Phát")) to { Core.playEpisode(e) },
            if (pos > 0) "⏮  " + t("Play From The Start", "Nghe Từ Đầu") to { Core.playEpisode(e, fromStart = true) } else null,
            (if (played) "○  " + t("Mark As Not Played", "Đánh Dấu Chưa Nghe") else "✓  " + t("Mark As Played", "Đánh Dấu Đã Nghe")) to { PodStore.setPlayed(e.url, !played); tick++ },
            if (local) "🗑  " + t("Delete Download", "Xoá Bản Tải") to { PodStore.localFile(ctx, e)?.delete(); tick++ }
            else "⬇  " + t("Download", "Tải Về") to { msg = t("Downloading…", "Đang tải…"); scope.launch { msg = if (PodStore.download(ctx, e)) t("Downloaded.", "Đã tải xong.") else t("Download failed.", "Tải không được."); tick++ } },
            "💾  " + t("Save Whole Episode To Recordings", "Lưu Cả Tập Vào Bản Thâu Âm") to { scope.launch { PodSave.saveWhole(ctx, e) } },
            "➕  " + t("Add To Queue", "Thêm Vào Danh Sách Chờ") to { Core.queueEpisode(e) },
        ))
    }
    speedFor?.let { sp ->
        MenuDialog(t("Speed: ", "Tốc độ: ") + sp.title, th, { speedFor = null }, listOf(0.8f, 1f, 1.1f, 1.25f, 1.5f, 1.75f, 2f).map { v ->
            ((if (PodStore.speed(sp.title) == v) "● " else "○ ") + fmtSpeed(v)) to { PodStore.setSpeed(sp.title, v); if (Core.kind.value == "podcast" && Core.artist.value == sp.title) Core.controller?.setPlaybackSpeed(v) } })
    }
    skipFor?.let { sp ->
        MenuDialog(t("Skip the first…", "Bỏ qua phần đầu…"), th, { skipFor = null }, listOf(0, 10, 15, 30, 45, 60, 90, 120).map { v ->
            ((if (PodStore.skip(sp.title) == v) "● " else "○ ") + if (v == 0) t("Don't skip", "Không bỏ qua") else t("$v seconds", "$v giây")) to { PodStore.setSkip(sp.title, v) } })
    }
    infoFor?.let { ip ->
        var info by remember(ip) { mutableStateOf(Podcasts.info[ip.feed]) }
        LaunchedEffect(ip) { if (info == null) { val r = try { Podcasts.resolve(ip) } catch (_: Exception) { ip }; try { Podcasts.episodes(r) } catch (_: Exception) { }; info = Podcasts.info[r.feed] } }
        Dialog(onDismissRequest = { infoFor = null }) {
            Column(Modifier.clip(RoundedCornerShape(22.dp)).background(if (th.light) Color.White else Color(0xFF16242E)).padding(18.dp).heightIn(max = 520.dp).verticalScroll(rememberScrollState())) {
                Row(verticalAlignment = Alignment.CenterVertically) { Cover(ip.image, 0, 72.dp, th, 12.dp); Spacer(Modifier.width(12.dp))
                    Column { Text(ip.title, color = th.text, fontSize = 17.sp, fontWeight = FontWeight.Bold); Text(ip.author, color = th.muted, fontSize = 13.sp) } }
                Spacer(Modifier.height(10.dp))
                val i = info
                if (i == null) Text(t("Loading…", "Đang tải…"), color = th.muted)
                else {
                    Text(t("Episodes: ", "Số tập: ") + i.count + (if (i.language.isNotBlank()) "  ·  " + t("Language: ", "Ngôn ngữ: ") + i.language else ""), color = th.accent, fontSize = 13.sp)
                    Spacer(Modifier.height(8.dp))
                    Text(i.description.ifBlank { t("No description.", "Không có mô tả.") }, color = th.text, fontSize = 14.sp)
                    if (i.link.isNotBlank()) Text(i.link, color = th.accent, fontSize = 13.sp, modifier = Modifier.padding(top = 8.dp).clickable {
                        try { ctx.startActivity(Intent(Intent.ACTION_VIEW, android.net.Uri.parse(i.link))) } catch (_: Exception) { } })
                }
                Row(Modifier.fillMaxWidth().padding(top = 12.dp), horizontalArrangement = Arrangement.End) { Btn(t("Close", "Đóng"), th) { infoFor = null } }
            }
        }
    }
}

private fun fmtSpeed(v: Float) = (if (v == v.toInt().toFloat()) "${v.toInt()}" else "$v").replace(".0", "") + "x"

/** Trang một kênh: ← luôn ở góc trái, ⋯ góc phải, nút Phát Mới Nhất và Theo Dõi cỡ vừa ở dưới phần đầu. */
@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun ChannelPage(p: Podcast, eps: List<Episode>, busy: Boolean, msg: String, th: JTheme, onBack: () -> Unit, onMenu: () -> Unit, onEpLong: (Episode) -> Unit, onLatest: () -> Unit) {
    val ctx = LocalContext.current
    val list = rememberLazyListState()
    @Suppress("UNUSED_VARIABLE") val k = Prefs.podcasts.state.value + Prefs.podPlayed.state.value
    val sub = Podcasts.subscribed().any { it.feed == p.feed }
    val collapsed = list.firstVisibleItemIndex > 0
    Column {
        Row(Modifier.fillMaxWidth().height(52.dp), verticalAlignment = Alignment.CenterVertically) {
            IconBtn(Gl.back, th.text, pad = 12.dp) { onBack() }
            Text(p.title, color = th.text, fontSize = 17.sp, fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis, modifier = Modifier.weight(1f))
            if (collapsed) IconBtn(if (sub) Gl.starFull else Gl.star, if (sub) th.accent else th.muted) { Podcasts.toggle(p) }
            IconBtn(Gl.more, th.text) { onMenu() }
        }
        LazyColumn(state = list, verticalArrangement = Rows) {
            item {
                Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(vertical = 6.dp)) {
                    Cover(p.image, 0, 96.dp, th, 16.dp)
                    Spacer(Modifier.width(12.dp))
                    Column(Modifier.weight(1f)) {
                        Text(p.title, color = th.text, fontSize = 18.sp, fontWeight = FontWeight.Bold, maxLines = 2, overflow = TextOverflow.Ellipsis)
                        if (p.author.isNotBlank()) Text(p.author, color = th.muted, fontSize = 13.sp, maxLines = 1)
                        val total = Podcasts.info[p.feed]?.count ?: eps.size
                        if (eps.isNotEmpty()) Text(t("$total episodes", "$total tập") + if (total > eps.size) t(" (newest ${eps.size} shown)", " (hiện ${eps.size} tập mới nhất)") else "", color = th.muted, fontSize = 12.sp)
                    }
                }
                FlowRow {
                    Btn("▶ " + t("Play Latest", "Phát Mới Nhất"), th, primary = true) { onLatest() }
                    Btn(if (sub) "★ " + t("Following", "Đang Theo Dõi") else "☆ " + t("Follow", "Theo Dõi"), th) { Podcasts.toggle(p) }
                }
                val newest = Podcasts.info[p.feed]?.newest ?: 0L
                if (!busy && newest > 0 && System.currentTimeMillis() - newest > 60L * 24 * 3600_000) Text(
                    t("⚠ This channel stopped publishing – last episode ", "⚠ Kênh này đã ngưng cập nhật – tập mới nhất ngày ") +
                        java.text.SimpleDateFormat("dd/MM/yyyy", java.util.Locale.getDefault()).format(java.util.Date(newest)),
                    color = Color(0xFFFFB74D), fontSize = 13.sp, modifier = Modifier.padding(top = 6.dp))
                if (busy) Text(t("Loading episodes…", "Đang tải các tập…"), color = th.muted)
                if (msg.isNotBlank()) Text(msg, color = th.muted, fontSize = 12.sp)
            }
            items(eps) { e ->
                val played = PodStore.played(e.url); val local = PodStore.localFile(ctx, e) != null; val pos = PodStore.pos(e.url)
                val info = listOfNotNull(e.date.ifBlank { null }, if (e.durationS > 0) fmtTime(e.durationS * 1000) else null,
                    if (pos > 0) "⏸ " + fmtTime(pos) else null, if (local) "⬇" else null, if (played) "✓" else null).joinToString(" · ")
                Row2((if (played) "✓ " else "") + e.title, info, th, selected = Core.uri.value == e.url, leading = { Cover(e.image, 0, 48.dp, th) },
                    trailing = { IconBtn(Gl.play, th.text, 22.dp) { Core.playEpisode(e) } }, onLong = { onEpLong(e) }) { Core.playEpisode(e) }
            }
            item { Spacer(Modifier.height(24.dp)) }
        }
    }
}

@Composable
fun MenuDialog(title: String, th: JTheme, onDismiss: () -> Unit, items: List<Pair<String, () -> Any?>>) {
    val hp = haptic()
    Dialog(onDismissRequest = onDismiss) {
        Column(Modifier.clip(RoundedCornerShape(22.dp)).background(if (th.light) Color.White else Color(0xFF16242E)).padding(vertical = 10.dp).heightIn(max = 560.dp).verticalScroll(rememberScrollState())) {
            Text(title, color = th.text, fontSize = 16.sp, fontWeight = FontWeight.Bold, maxLines = 2, overflow = TextOverflow.Ellipsis, modifier = Modifier.padding(horizontal = 18.dp, vertical = 6.dp))
            items.forEach { (label, action) ->
                Box(Modifier.fillMaxWidth().clickable { hp(); onDismiss(); action() }.padding(horizontal = 18.dp, vertical = 12.dp)) { Text(label, color = th.text, fontSize = 15.sp) }
            }
        }
    }
}

private fun pin(ctx: android.content.Context, p: Podcast) {
    if (!ShortcutManagerCompat.isRequestPinShortcutSupported(ctx)) return
    val i = Intent(ctx, MainActivity::class.java).setAction(Intent.ACTION_VIEW).putExtra("open_podcast", p.feed).putExtra("open_podcast_title", p.title).putExtra("open_podcast_image", p.image)
    val sc = ShortcutInfoCompat.Builder(ctx, "pod_" + p.feed.hashCode()).setShortLabel(p.title.take(24).ifBlank { "Podcast" }).setLongLabel(p.title.take(60).ifBlank { "Podcast" })
        .setIcon(IconCompat.createWithResource(ctx, R.mipmap.ic_launcher)).setIntent(i).build()
    try { ShortcutManagerCompat.requestPinShortcut(ctx, sc, null) } catch (_: Exception) { }
}

private fun share(ctx: android.content.Context, p: Podcast) {
    val link = if (p.id.isNotBlank()) "https://podcasts.apple.com/podcast/id${p.id}" else p.feed
    val i = Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT, "${p.title}\n$link")
    try { ctx.startActivity(Intent.createChooser(i, t("Share Channel", "Chia Sẻ Kênh")).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) } catch (_: Exception) { }
}
