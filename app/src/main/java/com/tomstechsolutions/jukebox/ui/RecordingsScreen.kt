package com.tomstechsolutions.jukebox.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tomstechsolutions.jukebox.data.Recordings
import com.tomstechsolutions.jukebox.data.Track
import com.tomstechsolutions.jukebox.playback.Core
import com.tomstechsolutions.jukebox.t
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/** Bản Thâu Âm – the radio recordings, right inside the app. */
@Composable
fun RecordingsScreen(act: MainActivity, th: JTheme, onBack: () -> Unit) {
    val ctx = LocalContext.current
    var list by remember { mutableStateOf<List<Recordings.Rec>>(emptyList()) }
    var reload by remember { mutableIntStateOf(0) }
    var renaming by remember { mutableStateOf<Recordings.Rec?>(null) }
    var group by remember { mutableIntStateOf(0) }          // 0 tất cả · 1 radio · 2 podcast
    LaunchedEffect(reload, Core.recording.value, Library_deleted(), group) { list = Recordings.list(ctx).filter { group == 0 || (group == 2) == it.podcast } }
    fun asTracks() = list.map { Track(it.id, it.uri, it.name.substringBeforeLast('.'), t("Recording", "Bản Thâu"), "", 0, it.durationMs, "Recordings", "audio/*") }
    Column(Modifier.fillMaxSize().padding(horizontal = 14.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconBtn(Gl.back, th.text) { onBack() }
            Text(t("Recordings", "Bản Thâu Âm"), color = th.text, fontSize = 22.sp, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
            IconBtn(Gl.reconnect, th.muted) { reload++ }
        }
        Row { listOf(t("All", "Tất Cả"), "Radio", "Podcast").forEachIndexed { i, s -> SmallChip(s, group == i, th) { group = i } } }
        if (Core.recording.value) {
            Row(Modifier.fillMaxWidth().padding(vertical = 6.dp).clip(RoundedCornerShape(16.dp)).background(Color(0x33FF4D4D)).padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                Text("● " + t("Recording: ", "Đang thâu: ") + (if (Core.podRecFrom.longValue >= 0) Core.title.value else (Core.station.value?.name ?: "") + "  ·  " + Recordings.sizeText(Core.recordedBytes.longValue)),
                    color = Color(0xFFFF6B6B), fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                Btn(t("Stop", "Dừng"), th, primary = true) { Core.stopRecording() }
            }
        }
        if (list.isEmpty()) Text(t("No recordings yet. While listening to radio or a podcast, tap ● next to Play.", "Chưa có bản thâu nào. Khi nghe radio hay podcast, bấm ● bên trái nút Play để thâu."), color = th.muted, modifier = Modifier.padding(vertical = 12.dp))
        else Row { Btn(t("Play All", "Phát Tất Cả"), th, Gl.play, primary = true) { Core.playTracks(asTracks()) }; Text("${list.size} " + t("files", "file"), color = th.muted, modifier = Modifier.padding(top = 12.dp)) }
        LazyColumn(verticalArrangement = Rows) {
            items(list, key = { it.uri }) { r ->
                var menu by remember { mutableStateOf(false) }
                val info = listOf(SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.US).format(Date(r.date)),
                    if (r.durationMs > 0) fmtTime(r.durationMs) else "", Recordings.sizeText(r.size)).filter { it.isNotBlank() }.joinToString(" · ")
                Row2(r.name.substringBeforeLast('.'), info, th, selected = Core.uri.value == r.uri,
                    leading = { G(if (r.podcast) Gl.podcast else Gl.record, if (r.podcast) SKY else Color(0xFFFF5252), 34.dp) },
                    trailing = {
                        IconBtn(Gl.play, th.text, 22.dp) { Core.playTracks(asTracks(), list.indexOf(r)) }
                        Box {
                            IconBtn(Gl.more, th.muted, 20.dp) { menu = true }
                            DropdownMenu(menu, { menu = false }) {
                                DropdownMenuItem({ Text(t("Rename", "Đổi Tên")) }, { menu = false; renaming = r })
                                DropdownMenuItem({ Text(t("Share", "Chia Sẻ")) }, {
                                    menu = false
                                    val i = Intent(Intent.ACTION_SEND).setType("audio/*").putExtra(Intent.EXTRA_STREAM, Uri.parse(r.uri)).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                                    try { ctx.startActivity(Intent.createChooser(i, t("Share recording", "Chia sẻ bản thâu"))) } catch (_: Exception) { }
                                })
                                DropdownMenuItem({ Text(t("Delete", "Xoá"), color = Color(0xFFE53935)) }, { menu = false; act.deleteSongs(listOf(r.uri)) })
                            }
                        }
                    }) { Core.playTracks(asTracks(), list.indexOf(r)) }
            }
        }
    }
    renaming?.let { r ->
        var name by remember(r) { mutableStateOf(r.name.substringBeforeLast('.')) }
        AlertDialog(onDismissRequest = { renaming = null }, title = { Text(t("Rename", "Đổi Tên")) },
            text = { BasicTextField(name, { name = it }, singleLine = true, textStyle = TextStyle(color = th.text, fontSize = 17.sp), cursorBrush = SolidColor(th.accent),
                modifier = Modifier.fillMaxWidth().clip(RoundedCornerShape(10.dp)).background(th.card).padding(10.dp)) },
            confirmButton = { TextButton(onClick = {
                if (name.isNotBlank()) { if (!Recordings.rename(ctx, r, name.trim())) com.tomstechsolutions.jukebox.data.Messages.add(t("Couldn't rename (Android may block files from an older install).", "Không đổi tên được (Android có thể chặn file của bản cài trước).")) }
                renaming = null; reload++
            }) { Text(t("Save", "Lưu"), color = th.accent) } },
            dismissButton = { TextButton(onClick = { renaming = null }) { Text(t("Cancel", "Huỷ")) } })
    }
}

/** Changes whenever songs are deleted, so lists refresh. */
@Composable
private fun Library_deleted(): Int = com.tomstechsolutions.jukebox.data.Library.all.value.size
