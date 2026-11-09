package com.tomstechsolutions.jukebox.ui

import android.Manifest
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.playback.Core
import com.tomstechsolutions.jukebox.playback.EqPresets
import com.tomstechsolutions.jukebox.t

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun EqScreen(act: MainActivity, th: JTheme) {
    var saving by remember { mutableStateOf(false) }
    @Suppress("UNUSED_VARIABLE") val bandsKey = Prefs.eqBands.state.value
    val gains = EqPresets.currentGains()
    fun setBand(i: Int, v: Float) {
        val g = EqPresets.currentGains(); g[i] = (Math.round(v * 2) / 2f).coerceIn(-12f, 12f)
        Prefs.eqBands.value = g.joinToString(","); Prefs.eqPreset.value = "manual"; Core.service?.eq?.apply()
    }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 14.dp)) {
        Text(t("Sound", "Chỉnh Âm"), color = th.text, fontSize = 28.sp, fontWeight = FontWeight.Bold)
        SwitchRow(t("Equaliser On", "Bật Bộ Chỉnh Âm"), th, Prefs.eqOn.value) { Prefs.eqOn.value = it; Core.service?.eq?.apply() }
        Card(th) {
            Row(Modifier.fillMaxWidth().height(200.dp)) {
                EqPresets.FREQS.forEachIndexed { i, f ->
                    Column(Modifier.weight(1f), horizontalAlignment = Alignment.CenterHorizontally) {
                        Text((if (gains[i] > 0) "+" else "") + "%.0f".format(gains[i]), color = th.muted, fontSize = 10.sp)
                        VSlider(gains[i], th, Modifier.weight(1f).fillMaxWidth()) { setBand(i, it) }
                        Text(if (f >= 1000) "${f / 1000}k" else "$f", color = th.muted, fontSize = 10.sp)
                    }
                }
            }
            val bands = Core.service?.eq?.bands ?: 0
            if (bands in 1..9) Text(t("This phone has $bands sound bands; the 10 sliders are spread over them.",
                "Điện thoại này có $bands dải âm; 10 thanh được chia đều lên các dải đó."), color = th.muted, fontSize = 11.sp)
        }
        SectionTitle(t("Presets", "Kiểu Âm Thanh"), th)
        FlowRow { EqPresets.all().forEach { p -> Chip(p.name, Prefs.eqPreset.value == p.key, th) { Core.applyPreset(p.key) } } }
        Row {
            Btn(t("Save As My Preset…", "Lưu Thành Kiểu Riêng…"), th, Gl.plus) { saving = true }
            Btn(t("Reset", "Về Phẳng"), th) { Core.applyPreset("flat") }
        }
        SwitchRow(t("Choose Automatically By Genre", "Tự Chọn Theo Thể Loại Nhạc"), th, Prefs.eqAutoGenre.value,
            t("Rock → Rock, Bolero → Bolero, radio/podcast → Clear Voice…", "Rock → Rock, Bolero → Bolero, radio/podcast → Rõ Giọng Nói…")) { Prefs.eqAutoGenre.value = it }
        SectionTitle(t("Quick Bass / Treble", "Bass / Treble Nhanh"), th)
        SliderRow("Bass", th, Prefs.bass.value.toFloat(), -6f..12f, 17, "${Prefs.bass.value} dB") { Prefs.bass.value = it.toInt(); Core.service?.eq?.apply() }
        SliderRow("Treble", th, Prefs.treble.value.toFloat(), -6f..6f, 11, "${Prefs.treble.value} dB") { Prefs.treble.value = it.toInt(); Core.service?.eq?.apply() }
        Text(t("Balance (left/right) is in the phone's Settings › Accessibility › Audio balance.",
            "Cân bằng trái/phải nằm trong Cài đặt điện thoại › Hỗ trợ › Cân bằng âm thanh."), color = th.muted, fontSize = 12.sp)

        SectionTitle(t("Visualisations", "Hiệu Ứng Sóng Nhạc"), th)
        SwitchRow(t("Visualisations On", "Hiệu Ứng Sóng Nhạc: Bật"), th, Prefs.vizOn.value, t("Off saves battery.", "Tắt hết thì đỡ hao pin.")) { Prefs.vizOn.value = it }
        if (Prefs.vizOn.value) {
            SwitchRow(t("Waves In The Pill", "Sóng trong viên thuốc"), th, Prefs.vizPill.value) { Prefs.vizPill.value = it }
            SwitchRow(t("Strip Under The Song Title", "Dải sóng dưới tên bài (Đang Phát)"), th, Prefs.vizStrip.value) { Prefs.vizStrip.value = it }
            SwitchRow(t("Little Wave On The Bottom Bar", "Sóng nhỏ trên thanh điều hướng"), th, Prefs.vizNav.value) { Prefs.vizNav.value = it }
            Visualizer(Modifier.fillMaxWidth().height(90.dp).padding(bottom = 8.dp))
        }
        StyleRow("viz", th) { act.picker.value = it }
        Row {
            Btn(t("Full Screen", "Xem Toàn Màn Hình"), th, Gl.fullscreen, primary = true) { act.fullViz.value = true }
            Btn(if (Motifs.isFav("viz", "v:${Prefs.viz.value}")) "★ " + t("Favourite", "Yêu Thích") else "☆ " + t("Add To Favourites", "Thêm Yêu Thích"), th) {
                Motifs.toggleFav("viz", "v:${Prefs.viz.value}"); Prefs.vizSpeed.value = Prefs.vizSpeed.value }
        }
        Text(t("Eastern group: Vietnam, China and Tibet – tap \"Change…\" then \"Eastern\".", "Nhóm Phương Đông: Việt Nam, Trung Quốc, Tây Tạng – nhấn \"Đổi…\" rồi chọn \"Phương Đông\"."), color = th.muted, fontSize = 12.sp)
        SliderRow(t("Effect Speed", "Tốc Độ Hiệu Ứng"), th, Prefs.vizSpeed.value, 0.25f..2.5f, label = "${(Prefs.vizSpeed.value * 100).toInt()}%") { Prefs.vizSpeed.value = it }
        SwitchRow(t("Change Automatically", "Tự Đổi Hiệu Ứng"), th, Prefs.vizAuto.value, t("Every 20 s – only among your ★ favourites if you have any.", "Mỗi 20 giây – chỉ đổi trong các kiểu ★ yêu thích nếu có.")) { Prefs.vizAuto.value = it }
        SwitchRow(t("Follow The Real Music", "Theo Nhạc Thật"), th, Prefs.realViz.value,
            t("Android asks for the microphone permission for this; nothing is recorded.", "Android sẽ hỏi quyền micro cho việc này; không thâu gì cả.")) {
            Prefs.realViz.value = it
            if (it) act.ask(Manifest.permission.RECORD_AUDIO) else Core.service?.refreshViz()
        }
        Box(Modifier.height(30.dp))
    }
    if (saving) {
        var name by remember { mutableStateOf("") }
        AlertDialog(onDismissRequest = { saving = false }, title = { Text(t("Preset Name", "Tên Kiểu Âm")) },
            text = { BasicTextField(name, { name = it }, singleLine = true, textStyle = TextStyle(color = th.text, fontSize = 18.sp), cursorBrush = SolidColor(th.accent), modifier = Modifier.fillMaxWidth()) },
            confirmButton = { TextButton(onClick = {
                if (name.isNotBlank()) { EqPresets.saveCustom(name.trim(), EqPresets.currentGains()); Prefs.eqPreset.value = "c:" + name.trim() }
                saving = false
            }) { Text(t("Save", "Lưu"), color = th.accent) } },
            dismissButton = { TextButton(onClick = { saving = false }) { Text(t("Cancel", "Huỷ")) } })
    }
}

@Composable
fun VSlider(value: Float, th: JTheme, modifier: Modifier, onChange: (Float) -> Unit) {
    Canvas(modifier.padding(vertical = 6.dp)
        .pointerInput(Unit) { detectTapGestures { o -> onChange(12f - o.y / size.height * 24f) } }
        .pointerInput(Unit) { detectDragGestures { ch, _ -> ch.consume(); onChange(12f - ch.position.y / size.height * 24f) } }) {
        val x = size.width / 2; val w = 5.dp.toPx()
        drawRoundRect(th.muted.copy(alpha = 0.3f), Offset(x - w / 2, 0f), Size(w, size.height), CornerRadius(w))
        val y = (12f - value) / 24f * size.height
        val mid = size.height / 2
        drawRoundRect(th.accent, Offset(x - w / 2, minOf(y, mid)), Size(w, kotlin.math.abs(y - mid)), CornerRadius(w))
        drawCircle(Color.White, 9.dp.toPx(), Offset(x, y))
        drawCircle(th.accent, 5.dp.toPx(), Offset(x, y))
    }
}

