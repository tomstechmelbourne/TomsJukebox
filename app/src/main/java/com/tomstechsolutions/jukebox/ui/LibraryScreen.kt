package com.tomstechsolutions.jukebox.ui

import android.content.Intent
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.height
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.data.Library
import com.tomstechsolutions.jukebox.data.Playlists
import com.tomstechsolutions.jukebox.data.Track
import com.tomstechsolutions.jukebox.playback.Core
import com.tomstechsolutions.jukebox.t
import kotlinx.coroutines.launch

@Composable
fun SearchBox(value: String, hint: String, th: JTheme, onChange: (String) -> Unit) {
    Row(Modifier.fillMaxWidth().padding(vertical = 6.dp).clip(RoundedCornerShape(16.dp)).background(th.card).padding(horizontal = 12.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically) {
        G(Gl.search, th.muted, 20.dp); Spacer(Modifier.width(8.dp))
        Box(Modifier.weight(1f)) {
            if (value.isEmpty()) Text(hint, color = th.muted, fontSize = 15.sp)
            BasicTextField(value, onChange, singleLine = true, textStyle = TextStyle(color = th.text, fontSize = 15.sp),
                cursorBrush = SolidColor(th.accent), modifier = Modifier.fillMaxWidth())
        }
        if (value.isNotEmpty()) IconBtn(Gl.close, th.muted, 16.dp, pad = 4.dp) { onChange("") }
    }
}

@Composable
fun LibraryScreen(act: MainActivity, th: JTheme) {
    val ctx = LocalContext.current
    val scope = rememberCoroutineScope()
    var view by rememberSaveable { mutableIntStateOf(Prefs.libChip.value.coerceIn(0, 7)) }
    val chipsShown = remember { mutableStateOf(true) }
    val nested = remember { object : androidx.compose.ui.input.nestedscroll.NestedScrollConnection {
        override fun onPreScroll(available: androidx.compose.ui.geometry.Offset, source: androidx.compose.ui.input.nestedscroll.NestedScrollSource): androidx.compose.ui.geometry.Offset {
            if (Prefs.chipsAutoHide.value) { if (available.y < -6f) chipsShown.value = false else if (available.y > 6f) chipsShown.value = true }
            return androidx.compose.ui.geometry.Offset.Zero
        }
    } }
    val chipState = androidx.compose.foundation.lazy.rememberLazyListState()
    androidx.compose.runtime.LaunchedEffect(Unit) { chipState.scrollToItem((view - 1).coerceAtLeast(0)) }
    var query by rememberSaveable { mutableStateOf("") }
    var group by rememberSaveable { mutableStateOf<String?>(null) }
    val addFiles = rememberLauncherForActivityResult(ActivityResultContracts.OpenMultipleDocuments()) { uris ->
        if (uris.isEmpty()) return@rememberLauncherForActivityResult
        val lines = Prefs.folders.value.split('\n').filter { it.isNotBlank() }.toMutableList()
        uris.forEach { u ->
            try { ctx.contentResolver.takePersistableUriPermission(u, Intent.FLAG_GRANT_READ_URI_PERMISSION) } catch (_: Exception) { }
            if ("doc:$u" !in lines) lines += "doc:$u"
        }
        Prefs.folders.value = lines.joinToString("\n")
        scope.launch { Library.scan(ctx) }
    }
    val addFolder = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocumentTree()) { u: Uri? ->
        if (u == null) return@rememberLauncherForActivityResult
        try { ctx.contentResolver.takePersistableUriPermission(u, Intent.FLAG_GRANT_READ_URI_PERMISSION) } catch (_: Exception) { }
        val lines = Prefs.folders.value.split('\n').filter { it.isNotBlank() }.toMutableList()
        if (u.toString() !in lines) lines += u.toString()
        Prefs.folders.value = lines.joinToString("\n")
        scope.launch { Library.scan(ctx) }
    }

    Column(Modifier.fillMaxSize().padding(horizontal = 14.dp)) {
        Text(t("Library", "Thư Viện"), color = th.text, fontSize = 28.sp, fontWeight = FontWeight.Bold)
        if (!act.audioAllowed.value) {
            Card(th) {
                Text(t("Tom's Jukebox needs permission to see the music on this phone.", "Tom's Jukebox cần quyền để xem nhạc trên điện thoại."), color = th.text)
                Btn(t("Allow Music Access", "Cho Phép Truy Cập Nhạc"), th, Gl.check, primary = true) { act.askAudio() }
            }
        }
        SearchBox(query, t("Search songs, artists, albums", "Tìm bài hát, ca sĩ, album"), th) { query = it }
        val tabs = listOf(t("Songs", "Bài Hát"), "Album", t("Artists", "Nghệ Sĩ"), t("Folders", "Thư Mục"), t("Playlists", "Danh Sách"),
            t("Favourites", "Yêu Thích"), t("Now Playing", "Đang Phát"), "● " + t("Recordings", "Bản Thâu Âm"))
        AnimatedVisibility(chipsShown.value || !Prefs.chipsAutoHide.value) { Column {
        // một hàng ngang duy nhất, vuốt ngang để xem thêm
        Box(Modifier.padding(bottom = 6.dp)) {
            androidx.compose.foundation.lazy.LazyRow(state = chipState) {
                itemsIndexed(tabs) { i, s -> SmallChip(s, view == i, th) { view = i; group = null; Prefs.libChip.value = i } }
                item { Spacer(Modifier.width(24.dp)) }
            }
            Box(Modifier.align(Alignment.CenterEnd).width(28.dp).height(32.dp).background(androidx.compose.ui.graphics.Brush.horizontalGradient(listOf(androidx.compose.ui.graphics.Color.Transparent, th.top))))
        }
        Row(Modifier.horizontalScroll(rememberScrollState())) {
            Btn(t("+ Add Songs…", "+ Thêm Bài Hát…"), th) { addFiles.launch(arrayOf("audio/*")) }
            Btn(t("+ Add Folder…", "+ Thêm Thư Mục…"), th) { addFolder.launch(null) }
            Btn(if (Library.scanning.value) t("Scanning…", "Đang Quét…") else t("⟳ Rescan", "⟳ Quét Lại"), th) { scope.launch { Library.scan(ctx) } }
        }
        } }
        val all = Library.tracks.value
        val q = query.trim().lowercase()
        fun match(t: Track) = q.isEmpty() || t.title.lowercase().contains(q) || t.artist.lowercase().contains(q) || t.album.lowercase().contains(q)
        Box(Modifier.weight(1f).nestedScroll(nested)) {
            when {
                view == 7 -> RecordingsScreen(act, th) { view = 0 }
                view == 6 -> QueueView(th.copy(), Modifier.fillMaxSize())
                group != null -> {
                    val list = when (view) {
                        1 -> all.filter { it.album.ifBlank { "—" } == group }.sortedBy { it.trackNo }
                        2 -> all.filter { it.artist.ifBlank { "—" } == group }
                        3 -> all.filter { it.folder.ifBlank { "—" } == group }
                        4 -> (Playlists.all()[group] ?: emptyList()).mapNotNull { Library.byUri(it) }
                        else -> emptyList()
                    }.filter(::match)
                    Column {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            IconBtn(Gl.back, th.text) { group = null }
                            Text(group ?: "", color = th.text, fontSize = 18.sp, fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis, modifier = Modifier.weight(1f))
                            if (view == 4) IconBtn(Gl.trash, th.muted) { Playlists.delete(group ?: ""); group = null }
                        }
                        TrackList(list, th)
                    }
                }
                view == 0 -> TrackList(all.filter(::match), th)
                view == 5 -> { val fav = Prefs.favSet(); TrackList(all.filter { it.uri in fav && match(it) }, th) }
                view == 4 -> {
                    val pls = Playlists.all()
                    LazyColumn {
                        item { Text(t("Long-press a song's ⋯ menu to add it to a playlist.", "Bấm ⋯ ở bài hát để thêm vào danh sách."), color = th.muted, fontSize = 12.sp) }
                        items(pls.keys.toList()) { name -> Row2(name, "${pls[name]?.size ?: 0} " + t("songs", "bài"), th, leading = { G(Gl.list, th.accent, 36.dp) }) { group = name } }
                    }
                }
                else -> {
                    val groups = when (view) { 1 -> Library.albums(); 2 -> Library.artists(); else -> Library.folders() }
                        .filter { (name, l) -> q.isEmpty() || name.lowercase().contains(q) || l.any(::match) }
                    if (view == 1) LazyVerticalGrid(GridCells.Adaptive(150.dp), horizontalArrangement = Arrangement.spacedBy(10.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        items(groups, key = { it.first }) { (name, l) ->
                            Column(Modifier.clip(RoundedCornerShape(16.dp)).clickable { group = name }.padding(4.dp)) {
                                Box(Modifier.fillMaxWidth().aspectRatio(1f)) { CoverFill(l.first(), th) }
                                Text(name, color = th.text, fontSize = 14.sp, fontWeight = FontWeight.SemiBold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                                Text(l.first().artist, color = th.muted, fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                            }
                        }
                    } else LazyColumn {
                        items(groups, key = { it.first }) { (name, l) ->
                            Row2(name, "${l.size} " + t("songs", "bài"), th, leading = { if (view == 3) G(Gl.folder, th.accent, 44.dp) else Cover(l.first().uri, l.first().albumId, 48.dp, th, 24.dp) }) { group = name }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun CoverFill(tr: Track, th: JTheme) {
    androidx.compose.foundation.layout.BoxWithConstraints(Modifier.fillMaxSize()) { Cover(tr.uri, tr.albumId, maxWidth, th, 14.dp) }
}

@Composable
fun TrackList(list: List<Track>, th: JTheme) {
    if (list.isEmpty()) {
        Text(if (Library.scanning.value) t("Looking for music…", "Đang tìm nhạc…") else t("No songs here yet.", "Chưa có bài nào."), color = th.muted, modifier = Modifier.padding(16.dp))
        return
    }
    val act = LocalContext.current as? MainActivity
    val fav = Prefs.favSet()
    var selected by remember { mutableStateOf<Set<String>>(emptySet()) }
    val selecting = selected.isNotEmpty()
    Column {
        if (selecting) Row(Modifier.horizontalScroll(rememberScrollState()), verticalAlignment = Alignment.CenterVertically) {
            Text(t("Selected: ", "Đã chọn: ") + selected.size, color = th.accent, fontWeight = FontWeight.Bold, modifier = Modifier.padding(end = 10.dp))
            Btn(t("Select All", "Chọn Hết"), th) { selected = list.map { it.uri }.toSet() }
            Btn(t("Hide", "Bỏ Khỏi Thư Viện"), th) { act?.hideSongs(selected.toList()); selected = emptySet() }
            Btn(t("Delete", "Xoá") + " (${selected.size})", th, Gl.trash, primary = true) { act?.deleteSongs(selected.toList()); selected = emptySet() }
            Btn(t("Cancel", "Huỷ"), th) { selected = emptySet() }
        } else Row {
            Btn(t("Play All", "Phát Tất Cả"), th, Gl.play, primary = true) { Core.playTracks(list) }
            Btn(t("Shuffle", "Trộn Bài"), th, Gl.shuffle) { Core.playTracks(list, (list.indices).random(), shuffled = true) }
            Text("${list.size} " + t("songs", "bài"), color = th.muted, fontSize = 12.sp, modifier = Modifier.padding(top = 12.dp))
        }
        LazyColumn(verticalArrangement = Rows) {
            itemsIndexed(list, key = { _, it -> it.uri }) { i, tr ->
                var menu by remember { mutableStateOf(false) }
                val isSel = tr.uri in selected
                fun toggleSel() { selected = if (isSel) selected - tr.uri else selected + tr.uri }
                Row2(tr.title, listOf(tr.artist, tr.album).filter { it.isNotBlank() }.joinToString(" · "), th, selected = isSel || (!selecting && tr.uri == Core.uri.value),
                    leading = { if (selecting) G(if (isSel) Gl.check else Gl.plus, if (isSel) th.accent else th.muted, 40.dp) else Cover(tr.uri, tr.albumId, 48.dp, th) },
                    trailing = {
                        if (tr.durationMs > 0) Text(fmtTime(tr.durationMs), color = th.muted, fontSize = 12.sp)
                        if (tr.uri in fav) G(Gl.starFull, ORANGE, 16.dp, Modifier.padding(start = 6.dp))
                        if (!selecting) Box {
                            IconBtn(Gl.more, th.muted, 20.dp, pad = 8.dp) { menu = true }
                            DropdownMenu(menu, { menu = false }) {
                                DropdownMenuItem({ Text(t("Play Next", "Phát Tiếp Theo")) }, { Core.addToQueue(listOf(tr), next = true); menu = false })
                                DropdownMenuItem({ Text(t("Add To Queue", "Thêm Vào Hàng Chờ")) }, { Core.addToQueue(listOf(tr)); menu = false })
                                DropdownMenuItem({ Text(if (tr.uri in fav) t("Remove From Favourites", "Bỏ Khỏi Yêu Thích") else t("Add To Favourites", "Thêm Vào Yêu Thích")) }, { Prefs.toggleFav(tr.uri); menu = false })
                                Playlists.all().keys.forEach { pl -> DropdownMenuItem({ Text(t("Add to: ", "Thêm vào: ") + pl) }, { Playlists.add(pl, listOf(tr.uri)); menu = false }) }
                                DropdownMenuItem({ Text(t("New Playlist With This Song", "Danh Sách Mới Với Bài Này")) }, {
                                    var n = 1; while (Playlists.all().containsKey(t("Playlist ", "Danh Sách ") + n)) n++
                                    Playlists.add(t("Playlist ", "Danh Sách ") + n, listOf(tr.uri)); menu = false
                                })
                                DropdownMenuItem({ Text(t("Select Several…", "Chọn Nhiều Bài…")) }, { menu = false; selected = setOf(tr.uri) })
                                DropdownMenuItem({ Text(t("Hide From Library", "Bỏ Khỏi Thư Viện")) }, { menu = false; act?.hideSongs(listOf(tr.uri)) })
                                DropdownMenuItem({ Text(t("Delete From Phone", "Xoá Khỏi Máy"), color = androidx.compose.ui.graphics.Color(0xFFE53935)) }, { menu = false; act?.deleteSongs(listOf(tr.uri)) })
                            }
                        }
                    }, onLong = { toggleSel() }) { if (selecting) toggleSel() else Core.playTracks(list, i) }
            }
        }
    }
}
