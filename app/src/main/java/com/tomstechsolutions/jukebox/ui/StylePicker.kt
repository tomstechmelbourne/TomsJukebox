package com.tomstechsolutions.jukebox.ui

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.GridItemSpan
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.clipPath
import androidx.compose.ui.graphics.drawscope.inset
import androidx.compose.ui.graphics.drawscope.drawIntoCanvas
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.playback.Core
import com.tomstechsolutions.jukebox.t
import kotlin.math.abs
import kotlin.math.sin

data class PickItem(val id: String, val name: String, val groups: Set<String>)

/** The seven style pickers and the Bộ Chủ Đề picker, all with the same easy page. */
object Pickers {
    val cats = listOf("pack", "theme", "skin", "btn", "btncol", "edge", "bar", "viz")
    fun title(cat: String) = when (cat) {
        "pack" -> t("Theme Packs", "Bộ Chủ Đề"); "theme" -> t("Colour Theme", "Màu Giao Diện"); "skin" -> "Skin"
        "btn" -> t("Play Buttons", "Kiểu Nút Phát Nhạc"); "btncol" -> t("Button Colour", "Màu Nút"); "edge" -> t("Edge Lighting", "Ánh Sáng Chạy Viền")
        "bar" -> t("Time Bar Colour", "Màu Thanh Thời Gian"); else -> t("Visualisation", "Hiệu Ứng Sóng Nhạc")
    }
    private val basic = setOf("basic")
    private fun motifs() = Motifs.list.indices.map { PickItem("m:$it", Motifs.name(it), Motifs.groups(it)) }

    fun items(cat: String): List<PickItem> = when (cat) {
        "pack" -> motifs()
        "theme" -> Themes.list.map { PickItem(it.key, it.name, basic) } + motifs()
        "skin" -> SkinList.keys.map { PickItem(it, SkinList.name(it), basic) } + motifs()
        "btn" -> ButtonArt.names.indices.map { PickItem("b:$it", ButtonArt.name(it), basic) } + motifs()
        "btncol" -> listOf("white" to t("White", "Trắng"), "cover" to t("From Cover", "Theo Ảnh Bìa"), "theme" to t("Theme Colour", "Màu Giao Diện"), "custom" to t("Custom", "Tự Chọn"))
            .map { PickItem(it.first, it.second, basic) } + motifs()
        "edge" -> EdgeEffects.names.indices.map { PickItem("e:$it", EdgeEffects.name(it), basic) } + motifs()
        "bar" -> BarColours.list.map { PickItem(it.third, t(it.first, it.second), basic) } + PickItem("custom", t("Custom Colour", "Tự Chọn Màu"), basic) + motifs()
        else -> VizStyles.names.indices.map { PickItem("v:$it", VizStyles.name(it), Motifs.groups(it) + (if (it < 36) basic else emptySet())) }
    }

    fun current(cat: String): String = when (cat) {
        "pack" -> if (Prefs.pack.value >= 0) "m:${Prefs.pack.value}" else ""
        "theme" -> Prefs.theme.value; "skin" -> Prefs.skin.value; "btncol" -> Prefs.btnColour.value; "bar" -> Prefs.barColour.value
        "btn" -> Prefs.btnStyle.value.let { if (it == -1) "pack" else if (it >= 100) "m:${it - 100}" else "b:$it" }
        "edge" -> Prefs.edgeEffect.value.let { if (it == -1) "pack" else if (it >= 100) "m:${it - 100}" else "e:$it" }
        else -> "v:${Prefs.viz.value}"
    }

    fun nameOf(cat: String, id: String): String = if (id == "pack") t("Follow Theme Pack", "Theo Bộ Chủ Đề") + (Motifs.of("pack")?.let { " · " + Motifs.name(it) } ?: "")
        else items(cat).firstOrNull { it.id == id }?.name ?: if (cat == "theme" && id == "custom") t("Custom Colour", "Màu Tự Chọn") else "—"

    private fun num(id: String) = id.substringAfter(':').toIntOrNull() ?: 0

    fun apply(cat: String, id: String) {
        when (cat) {
            "pack" -> Motifs.applyPack(num(id))
            "theme" -> Prefs.theme.value = id
            "skin" -> Prefs.skin.value = id
            "btncol" -> Prefs.btnColour.value = id
            "bar" -> Prefs.barColour.value = id
            "btn" -> Prefs.btnStyle.value = when { id == "pack" -> -1; id.startsWith("m:") -> 100 + num(id); else -> num(id) }
            "edge" -> { Prefs.edgeEffect.value = when { id == "pack" -> -1; id.startsWith("m:") -> 100 + num(id); else -> num(id) }; Prefs.edgeAuto.value = false; Prefs.edgeRandom.value = false }
            else -> { Prefs.viz.value = num(id); Prefs.vizAuto.value = false }
        }
        if (id != "pack") Motifs.addRecent(cat, id)
        try { com.tomstechsolutions.jukebox.system.Widgets.refresh(com.tomstechsolutions.jukebox.App.ctx) } catch (_: Exception) { }
    }

    /** What to put back with ↶ Hoàn Tác. */
    fun snapshot(): List<Any> = listOf(Prefs.pack.value, Prefs.theme.value, Prefs.skin.value, Prefs.btnStyle.value, Prefs.btnColour.value, Prefs.edgeEffect.value, Prefs.barColour.value, Prefs.viz.value)
    fun restore(s: List<Any>) {
        Prefs.pack.value = s[0] as Int; Prefs.theme.value = s[1] as String; Prefs.skin.value = s[2] as String; Prefs.btnStyle.value = s[3] as Int
        Prefs.btnColour.value = s[4] as String; Prefs.edgeEffect.value = s[5] as Int; Prefs.barColour.value = s[6] as String; Prefs.viz.value = s[7] as Int
    }

    private val sampleLevels = FloatArray(24) { 0.25f + 0.6f * abs(sin(it * 0.72f + 0.4f)) }

    /** Draws the little picture on a tile. */
    fun DrawScope.swatch(cat: String, id: String, th: JTheme) {
        val w = size.width; val h = size.height
        val mi = Motifs.of(id)
        when (cat) {
            "pack" -> { paintMotifSkin(mi ?: 0, 0f); val mo = Motifs.list[mi ?: 0]
                mo.colours.drop(1).forEachIndexed { k, c -> drawCircle(c, h * 0.11f, Offset(w * (0.62f + k * 0.12f), h * 0.78f)) } }
            "theme" -> { val tm = mi?.let { Motifs.theme(it) } ?: Themes.list.firstOrNull { it.key == id } ?: Themes.list[0]
                drawRect(Brush.verticalGradient(listOf(tm.top, tm.bottom))); drawRoundRect(tm.card, Offset(w * 0.1f, h * 0.18f), Size(w * 0.55f, h * 0.18f), CornerRadius(6f))
                drawRoundRect(tm.card, Offset(w * 0.1f, h * 0.44f), Size(w * 0.4f, h * 0.14f), CornerRadius(6f)); drawCircle(tm.accent, h * 0.14f, Offset(w * 0.8f, h * 0.75f)) }
            "skin" -> { drawRect(Color(0xFF0B1720)); val pw = w * 0.9f; val ph = h * 0.5f
                val st = skinStyle(id)
                inset(w * 0.05f, h * 0.25f, w * 0.05f, h * 0.25f) {
                    val path = androidx.compose.ui.graphics.Path().apply { addRoundRect(androidx.compose.ui.geometry.RoundRect(0f, 0f, pw, ph, CornerRadius(ph / 2))) }
                    clipPath(path) { paintSkin(0f, 0f, id) }
                    drawCircle(st.btn, ph * 0.18f, Offset(pw * 0.82f, ph / 2))
                    drawRoundRect(st.text.copy(alpha = 0.8f), Offset(ph * 0.5f, ph * 0.38f), Size(pw * 0.4f, ph * 0.1f), CornerRadius(4f))
                } }
            "btn" -> { drawRect(if (th.light) Color(0xFFE9EEF2) else Color(0xFF0B1720)); val style = when { id == "pack" -> -1; mi != null -> 100 + mi; else -> num(id) }
                val s = h * 0.62f
                drawIntoCanvas { c -> c.save(); c.translate((w - s) / 2, (h - s) / 2); ButtonArt.draw(c.nativeCanvas, ButtonArt.PLAY, style, s, (if (th.light) Color(0xFF1B2733) else Color.White).toArgb()); c.restore() } }
            "btncol" -> { drawRect(Color(0xFF0B1720)); val c = when { mi != null -> Motifs.list[mi].accent; id == "cover" -> Color(Core.palette.value[0]); id == "theme" -> th.accent; id == "custom" -> Color(Prefs.btnCustom.value); else -> Color.White }
                drawCircle(c, h * 0.3f); drawCircle(Color(0xFF0B1720), h * 0.12f) }
            "edge" -> { drawRoundRect(Color(0xFF0B1720), cornerRadius = CornerRadius(14f)); val (eff, mo) = Motifs.edgeStyle(when { id == "pack" -> -1; mi != null -> 100 + mi; else -> num(id) })
                drawEdge(eff, 1.3f, 14f, mo?.colours?.drop(1) ?: edgeColours(), 6f, 1f, 1f) }
            "bar" -> { drawRect(Color(0xFF0B1720)); val cols = BarColours.colours(id, Core.palette.value)
                drawRoundRect(Color(0x55FFFFFF), Offset(w * 0.1f, h * 0.45f), Size(w * 0.8f, h * 0.12f), CornerRadius(h * 0.06f))
                drawRoundRect(if (cols.size > 1) Brush.horizontalGradient(cols, w * 0.1f, w * 0.75f) else Brush.horizontalGradient(listOf(cols[0], cols[0])), Offset(w * 0.1f, h * 0.45f), Size(w * 0.65f, h * 0.12f), CornerRadius(h * 0.06f))
                drawCircle(Color.White, h * 0.11f, Offset(w * 0.75f, h * 0.51f)) }
            else -> { drawRect(Color(0xFF0B1720)); val i = num(id); val cols = (Motifs.list.getOrNull(i)?.colours?.drop(1) ?: listOf(ORANGE, SKY, TEAL))
                drawViz(i, 3.3f, sampleLevels, cols) }
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
fun StylePicker(cat: String, th: JTheme, onClose: () -> Unit) {
    BackHandler { onClose() }
    var query by remember { mutableStateOf("") }
    var filter by remember { mutableStateOf("all") }
    var undo by remember { mutableStateOf<List<Any>?>(null) }
    var favTick by remember { mutableIntStateOf(0) }
    val hp = haptic()
    val all = remember(cat, Prefs.lang.value) { Pickers.items(cat) }
    val cur = Pickers.current(cat)
    fun choose(id: String) { undo = Pickers.snapshot(); hp(); Pickers.apply(cat, id) }
    val tickNow = favTick; if (tickNow < 0) return
    val favs = Motifs.favs(cat).toSet()
    val recent = Motifs.recent(cat)
    val shown = all.filter { it.name.contains(query.trim(), ignoreCase = true) }.filter {
        when (filter) { "all" -> true; "fav" -> it.id in favs; "recent" -> it.id in recent; else -> filter in it.groups }
    }.let { l -> if (filter == "recent") l.sortedBy { recent.indexOf(it.id) } else l }
    val showPackTile = cat != "pack" && cat != "viz" && Prefs.pack.value >= 0

    Column(Modifier.fillMaxSize().background(th.bg).windowInsetsPadding(WindowInsets.safeDrawing)) {
        // top bar: back is always reachable
        Row(Modifier.fillMaxWidth().padding(horizontal = 4.dp, vertical = 2.dp), verticalAlignment = Alignment.CenterVertically) {
            IconBtn(Gl.back, th.text, pad = 12.dp) { onClose() }
            Text(Pickers.title(cat), color = th.text, fontSize = 20.sp, fontWeight = FontWeight.Bold, maxLines = 1, modifier = Modifier.weight(1f))
            Text("🎲", fontSize = 22.sp, modifier = Modifier.clip(RoundedCornerShape(20.dp)).combinedClickable(onClick = {
                val pool = shown.ifEmpty { all }; choose(pool.random().id) }).padding(10.dp))
            Text("↶", color = if (undo != null) th.text else th.muted.copy(alpha = 0.4f), fontSize = 24.sp, modifier = Modifier.clip(RoundedCornerShape(20.dp))
                .combinedClickable(onClick = { undo?.let { Pickers.restore(it) }; undo = null }).padding(horizontal = 12.dp, vertical = 6.dp))
        }
        // live preview
        Box(Modifier.padding(horizontal = 12.dp)) {
            if (cat == "viz") Visualizer(Modifier.fillMaxWidth().height(80.dp).clip(RoundedCornerShape(16.dp)).background(Color(0xFF0B1720)))
            else Pill(Modifier, big = false)
        }
        Text(t("Now: ", "Đang chọn: ") + Pickers.nameOf(cat, cur), color = th.accent, fontSize = 13.sp, maxLines = 1, modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp))
        OutlinedTextField(query, { query = it }, Modifier.fillMaxWidth().padding(horizontal = 12.dp), singleLine = true,
            placeholder = { Text(t("Search…", "Tìm kiểu…"), color = th.muted) },
            colors = OutlinedTextFieldDefaults.colors(focusedTextColor = th.text, unfocusedTextColor = th.text, focusedBorderColor = th.accent, unfocusedBorderColor = th.muted.copy(alpha = 0.4f), cursorColor = th.accent))
        LazyRow(Modifier.padding(top = 8.dp), contentPadding = PaddingValues(horizontal = 12.dp)) {
            items(Motifs.filters.filter { it.first != "basic" || all.any { a -> "basic" in a.groups } }) { (k, _) ->
                SmallChip(Motifs.filterName(k), filter == k, th) { filter = k }
            }
        }
        LazyVerticalGrid(GridCells.Adaptive(104.dp), Modifier.weight(1f), contentPadding = PaddingValues(10.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            if (recent.isNotEmpty() && filter == "all" && query.isBlank()) {
                item(span = { GridItemSpan(maxLineSpan) }) { Text(t("Recent", "Gần Đây"), color = th.muted, fontSize = 13.sp, fontWeight = FontWeight.Bold) }
                items(recent.mapNotNull { r -> all.firstOrNull { it.id == r } }, key = { "r" + it.id }) { it2 -> Tile(cat, it2, cur == it2.id, it2.id in favs, th, { choose(it2.id) }) { Motifs.toggleFav(cat, it2.id); favTick++ } }
                item(span = { GridItemSpan(maxLineSpan) }) { Text(t("All Styles", "Tất Cả Các Kiểu") + " (${all.size})", color = th.muted, fontSize = 13.sp, fontWeight = FontWeight.Bold) }
            }
            if (showPackTile && filter == "all" && query.isBlank()) item(key = "pack") {
                Tile(cat, PickItem("pack", Pickers.nameOf(cat, "pack"), emptySet()), cur == "pack", false, th, { choose("pack") }) {}
            }
            items(shown, key = { it.id }) { it2 -> Tile(cat, it2, cur == it2.id, it2.id in favs, th, { choose(it2.id) }) { Motifs.toggleFav(cat, it2.id); favTick++ } }
            if (shown.isEmpty()) item(span = { GridItemSpan(maxLineSpan) }) {
                Text(if (filter == "fav") t("Long-press a style to add it to ★ Favourites.", "Nhấn giữ một kiểu để thêm vào ★ Yêu Thích.") else t("Nothing found.", "Không tìm thấy kiểu nào."),
                    color = th.muted, modifier = Modifier.padding(20.dp))
            }
        }
        Text(t("Tap to use · long-press for ★ · ↶ undo", "Nhấn để dùng · nhấn giữ để ★ · ↶ hoàn tác"), color = th.muted, fontSize = 11.sp, textAlign = TextAlign.Center,
            modifier = Modifier.fillMaxWidth().padding(bottom = 6.dp))
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun Tile(cat: String, it: PickItem, on: Boolean, fav: Boolean, th: JTheme, onClick: () -> Unit, onLong: () -> Unit) {
    val hp = haptic()
    Column(Modifier.clip(RoundedCornerShape(16.dp)).background(if (on) th.accent.copy(alpha = 0.22f) else th.card)
        .border(if (on) 2.dp else 0.dp, if (on) th.accent else Color.Transparent, RoundedCornerShape(16.dp))
        .combinedClickable(onClick = onClick, onLongClick = { hp(); onLong() }).padding(6.dp),
        horizontalAlignment = Alignment.CenterHorizontally) {
        Box {
            Canvas(Modifier.fillMaxWidth().height(62.dp).clip(RoundedCornerShape(12.dp))) {
                if (it.id == "pack") { val i = Motifs.of("pack") ?: 0; with(Pickers) { swatch("pack", "m:$i", th) } }
                else with(Pickers) { swatch(cat, it.id, th) }
            }
            if (fav) Text("★", color = Color(0xFFFFD54F), fontSize = 16.sp, modifier = Modifier.align(Alignment.TopEnd).padding(4.dp))
            if (Motifs.vn.contains(it.id.substringAfter(':').toIntOrNull() ?: -1) && it.id.contains(':')) Text("VN", color = Color.White, fontSize = 8.sp,
                modifier = Modifier.align(Alignment.TopStart).padding(4.dp).clip(RoundedCornerShape(4.dp)).background(Color(0x99000000)).padding(horizontal = 3.dp))
        }
        Spacer(Modifier.height(4.dp))
        Text(it.name, color = if (on) th.accent else th.text, fontSize = 11.sp, maxLines = 2, textAlign = TextAlign.Center, lineHeight = 13.sp)
    }
}

/** Smaller chip for one-line rows (Thư Viện, pickers). */
@Composable
fun SmallChip(text: String, on: Boolean, th: JTheme, onClick: () -> Unit) {
    val hp = haptic()
    Box(Modifier.padding(end = 6.dp).height(32.dp).clip(RoundedCornerShape(16.dp)).background(if (on) th.accent else th.card)
        .combinedClickableCompat { hp(); onClick() }.padding(horizontal = 12.dp), contentAlignment = Alignment.Center) {
        Text(text, color = if (on) th.onAccent else th.text, fontSize = 13.sp, fontWeight = if (on) FontWeight.Bold else FontWeight.Medium, maxLines = 1)
    }
}

fun Modifier.combinedClickableCompat(onClick: () -> Unit): Modifier = this.clickable(onClick = onClick)

@Composable
fun StyleRow(cat: String, th: JTheme, onOpen: (String) -> Unit) {
    Row(Modifier.fillMaxWidth().padding(vertical = 4.dp).clip(RoundedCornerShape(14.dp)).background(th.card)
        .combinedClickableCompat { onOpen(cat) }.padding(8.dp), verticalAlignment = Alignment.CenterVertically) {
        val cur = Pickers.current(cat)
        Canvas(Modifier.size(width = 56.dp, height = 38.dp).clip(RoundedCornerShape(10.dp))) {
            if (cur == "pack") { val i = Motifs.of("pack") ?: 0; with(Pickers) { swatch("pack", "m:$i", th) } }
            else if (cur.isNotBlank()) with(Pickers) { swatch(cat, cur, th) } else drawRect(Color(0xFF0B1720))
        }
        Spacer(Modifier.width(12.dp))
        Column(Modifier.weight(1f)) {
            Text(Pickers.title(cat), color = th.text, fontSize = 15.sp, fontWeight = FontWeight.SemiBold)
            Text(Pickers.nameOf(cat, cur), color = th.muted, fontSize = 12.sp, maxLines = 1)
        }
        Spacer(Modifier.width(6.dp))
        Box(Modifier.clip(RoundedCornerShape(12.dp)).background(th.accent).padding(horizontal = 10.dp, vertical = 7.dp)) {
            Text(t("Change", "Đổi"), color = th.onAccent, fontSize = 13.sp, fontWeight = FontWeight.Bold, maxLines = 1, softWrap = false)
        }
    }
}
