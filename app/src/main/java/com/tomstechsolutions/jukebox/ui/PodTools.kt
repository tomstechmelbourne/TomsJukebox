package com.tomstechsolutions.jukebox.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.RangeSlider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tomstechsolutions.jukebox.data.Episode
import com.tomstechsolutions.jukebox.data.PodSave
import com.tomstechsolutions.jukebox.playback.Core
import com.tomstechsolutions.jukebox.t
import kotlinx.coroutines.launch

/** Podcast tools on Now Playing: ✂ Cắt Đoạn A–B (kéo hai mốc để chỉnh) và ⬇ Lưu Cả Tập vào Bản Thâu Âm. */
@Composable
fun PodTools() {
    if (Core.kind.value != "podcast") return
    val ctx = LocalContext.current
    val scope = rememberCoroutineScope()
    val dur = Core.duration.longValue.coerceAtLeast(1L)
    val a = Core.clipA.longValue; val b = Core.clipB.longValue
    Column(Modifier.fillMaxWidth().padding(bottom = 4.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly, verticalAlignment = Alignment.CenterVertically) {
            ToolChip("[A" + if (a >= 0) " " + fmtTime(a) else "", a >= 0) { Core.markA() }
            ToolChip("B]" + if (b >= 0) " " + fmtTime(b) else "", b >= 0) { Core.markB() }
            ToolChip("✂ " + t("Save Clip", "Lưu Đoạn"), false) { Core.saveAB() }
            ToolChip("⬇ " + t("Whole Episode", "Lưu Cả Tập"), false) {
                val e = Episode(Core.title.value, Core.uri.value, "", 0, Core.artist.value, "", "")
                scope.launch { PodSave.saveWhole(ctx, e) }
            }
        }
        if (a >= 0 && b > a) {
            RangeSlider(value = a.toFloat()..b.toFloat(), onValueChange = { r -> Core.clipA.longValue = r.start.toLong(); Core.clipB.longValue = r.endInclusive.toLong() },
                valueRange = 0f..dur.toFloat(), modifier = Modifier.padding(horizontal = 12.dp),
                colors = SliderDefaults.colors(thumbColor = ORANGE, activeTrackColor = ORANGE, inactiveTrackColor = Color(0x44FFFFFF)))
            Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(t("▶ Listen from A", "▶ Nghe thử từ A"), color = SKY, fontSize = 12.sp, modifier = Modifier.clickable { Core.seekTo(a) })
                Text(t("Clip: ", "Đoạn: ") + fmtTime(b - a), color = Color(0xFFCCCCCC), fontSize = 12.sp)
                Text("✕ " + t("Clear", "Xoá mốc"), color = Color(0xFFCCCCCC), fontSize = 12.sp, modifier = Modifier.clickable { Core.clipA.longValue = -1L; Core.clipB.longValue = -1L })
            }
        }
        if (Core.podRecFrom.longValue >= 0) Text("● " + t("Recording since ", "Đang thâu từ ") + fmtTime(Core.podRecFrom.longValue) + t(" – tap ■ to save", " – bấm ■ để lưu"),
            color = Color(0xFFFF6B6B), fontSize = 12.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(start = 16.dp, top = 2.dp))
    }
}

@Composable
private fun ToolChip(text: String, on: Boolean, onClick: () -> Unit) {
    val hp = haptic()
    Box(Modifier.padding(2.dp).clip(RoundedCornerShape(14.dp)).background(if (on) ORANGE.copy(alpha = 0.85f) else Color(0x33FFFFFF))
        .clickable { hp(); onClick() }.padding(horizontal = 10.dp, vertical = 6.dp)) {
        Text(text, color = if (on) ON_ORANGE else Color.White, fontSize = 12.sp, fontWeight = FontWeight.SemiBold, maxLines = 1)
    }
}
