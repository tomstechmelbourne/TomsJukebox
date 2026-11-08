package com.tomstechsolutions.jukebox.ui

import android.Manifest
import android.content.pm.PackageManager
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.data.GeoState
import com.tomstechsolutions.jukebox.data.Messages
import com.tomstechsolutions.jukebox.data.RadioApi
import com.tomstechsolutions.jukebox.data.Station
import com.tomstechsolutions.jukebox.data.Stations
import com.tomstechsolutions.jukebox.playback.Core
import com.tomstechsolutions.jukebox.t
import kotlinx.coroutines.launch

@Composable
fun RadioScreen(act: MainActivity, th: JTheme) {
    val ctx = LocalContext.current
    val scope = rememberCoroutineScope()
    var filter by rememberSaveable { mutableStateOf("NEAR") }
    var query by rememberSaveable { mutableStateOf("") }
    var online by remember { mutableStateOf<List<Station>>(emptyList()) }
    var busy by remember { mutableStateOf(false) }
    var note by remember { mutableStateOf("") }

    // follow Tom when he travels to another state
    LaunchedEffect(Unit) {
        if (Prefs.radioAutoState.value) {
            val ok = ContextCompat.checkSelfPermission(ctx, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED
            if (ok) GeoState.current(ctx)?.let { s ->
                if (s != Prefs.radioState.value) {
                    Prefs.radioState.value = s
                    Messages.add(t("Local radio changed to $s.", "Đã đổi đài địa phương sang bang $s."))
                }
            }
        }
    }

    Column(Modifier.fillMaxSize().padding(horizontal = 14.dp)) {
        Text("Radio", color = th.text, fontSize = 28.sp, fontWeight = FontWeight.Bold)
        SearchBox(query, t("Search any station worldwide", "Tìm đài bất kỳ trên thế giới"), th) { query = it }
        if (query.length >= 3) Btn(t("Search", "Tìm") + " \"$query\"", th, Gl.search, primary = true) {
            busy = true; filter = "ONLINE"
            scope.launch { online = try { RadioApi.search(query) } catch (_: Exception) { note = t("Can't reach the station list right now.", "Hiện không kết nối được danh sách đài."); emptyList() }; busy = false }
        }
        val chips = listOf("NEAR" to t("Near Me", "Gần Tôi") + " (${Prefs.radioState.value})", "NAT" to t("Australia-Wide", "Toàn Úc")) +
            Stations.auStates.map { it to it } +
            listOf("VN" to t("Vietnam", "Việt Nam"), "VIET" to t("Vietnamese Overseas", "Tiếng Việt Hải Ngoại"), "GENRE" to t("Genres", "Thể Loại"))
        Row(Modifier.horizontalScroll(rememberScrollState())) { chips.forEach { (k, s) -> Chip(s, filter == k, th) { filter = k; online = emptyList() } } }
        Row(Modifier.horizontalScroll(rememberScrollState()), verticalAlignment = Alignment.CenterVertically) {
            Chip("≥128 kbps", Prefs.radioHq.value, th) { Prefs.radioHq.value = !Prefs.radioHq.value }
            Chip(t("Follow My Location", "Theo Vị Trí"), Prefs.radioAutoState.value, th) {
                Prefs.radioAutoState.value = !Prefs.radioAutoState.value
                if (Prefs.radioAutoState.value) act.ask(Manifest.permission.ACCESS_COARSE_LOCATION)
            }
            if (filter in Stations.auStates || filter == "NEAR") Chip(t("More Online", "Thêm Đài Online"), false, th) {
                busy = true
                val st = if (filter == "NEAR") Prefs.radioState.value else filter
                scope.launch { online = try { RadioApi.byState(st) } catch (_: Exception) { emptyList() }; busy = false; filter = "ONLINE" }
            }
            if (filter == "VIET") Chip(t("Find More", "Tìm Thêm"), false, th) {
                busy = true
                scope.launch { online = try { RadioApi.vietnamese() } catch (_: Exception) { emptyList() }; busy = false; filter = "ONLINE" }
            }
        }
        if (busy) Text(t("Loading…", "Đang tải…"), color = th.muted)
        if (note.isNotBlank()) Text(note, color = th.muted, fontSize = 12.sp)
        val list: List<Station> = when (filter) {
            "ONLINE" -> online
            "NEAR" -> Stations.all.filter { it.group == Prefs.radioState.value || it.group == "NAT" || it.group == "AUVN" }
            "VN" -> Stations.all.filter { it.country == "VN" }
            "VIET" -> Stations.all.filter { it.country == "OS" }
            "GENRE" -> Stations.all.sortedBy { it.genre }
            else -> Stations.all.filter { it.group == filter }
        }
        LazyColumn(verticalArrangement = Rows, modifier = Modifier.weight(1f)) {
            items(list) { s ->
                val playing = Core.kind.value == "radio" && Core.station.value?.name == s.name
                val sub = buildString {
                    append(if (s.country == "AU" && s.group != "NAT") s.group else Stations.groupName(s.group).ifBlank { s.group })
                    if (s.genre.isNotBlank()) append(" · ").append(Stations.genreName(s.genre))
                    if (s.bitrate > 0) append(" · ${s.bitrate} kbps")
                    if (s.paused) append(" · ").append(t("Paused", "Tạm Ngưng"))
                }
                Row2(s.name, sub, th, selected = playing,
                    leading = { G(Gl.radio, if (s.paused) th.muted else th.accent, 36.dp) },
                    trailing = {
                        if (playing) IconBtn(Gl.record, if (Core.recording.value) Color(0xFFFF5252) else th.muted, 20.dp, active = Core.recording.value) {
                            if (Core.recording.value) Core.stopRecording() else Core.startRecording()
                        }
                        IconBtn(if (playing && Core.playing.value) Gl.pause else Gl.play, th.text, 22.dp) { if (playing) Core.toggle() else Core.playStation(s) }
                    }) { if (playing) act.openNow.value = true else Core.playStation(s) }
            }
        }
    }
}
