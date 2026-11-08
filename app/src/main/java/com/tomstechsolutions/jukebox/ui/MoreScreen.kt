package com.tomstechsolutions.jukebox.ui

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tomstechsolutions.jukebox.App
import com.tomstechsolutions.jukebox.L
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.data.Backup
import com.tomstechsolutions.jukebox.data.Messages
import com.tomstechsolutions.jukebox.t
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/** Hue picker used for every "custom colour". */
@Composable
fun HuePicker(current: Int, th: JTheme, onPick: (Int) -> Unit) {
    val hsv = FloatArray(3); android.graphics.Color.colorToHSV(current, hsv)
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.size(34.dp).clip(RoundedCornerShape(10.dp)).background(Color(current)))
        Spacer(Modifier.width(10.dp))
        Column(Modifier.weight(1f)) {
            Box(Modifier.fillMaxWidth().height(10.dp).clip(RoundedCornerShape(5.dp))
                .background(Brush.horizontalGradient(List(7) { Color.hsv(it * 60f % 360f, 0.8f, 1f) })))
            SliderRow(t("Colour", "Màu"), th, hsv[0], 0f..359f) { onPick(Color.hsv(it, 0.75f, 1f).toArgb()) }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun MoreScreen(act: MainActivity, th: JTheme) {
    val ctx = LocalContext.current
    var about by remember { mutableStateOf(false) }
    var mailFail by remember { mutableStateOf(false) }
    var showMsgs by remember { mutableStateOf(false) }
    var toast by remember { mutableStateOf("") }
    val stamp = SimpleDateFormat("yyyyMMdd", Locale.US).format(Date())
    val backup = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("application/json")) { u: Uri? ->
        if (u != null) toast = if (Backup.write(ctx, u)) t("Backup saved.", "Đã sao lưu.") else t("Backup failed.", "Sao lưu bị lỗi.")
    }
    val restore = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { u: Uri? ->
        if (u != null) {
            toast = if (Backup.read(ctx, u)) { L.vi.value = Prefs.lang.value == "vi"; t("Restored. Settings are back.", "Đã khôi phục cài đặt.") } else t("This file isn't a Tom's Jukebox backup.", "File này không phải bản sao lưu Tom's Jukebox.")
        }
    }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 14.dp)) {
        Text(t("More", "Thêm"), color = th.text, fontSize = 28.sp, fontWeight = FontWeight.Bold)
        if (toast.isNotBlank()) Card(th) { Text(toast, color = th.accent) }

        // ---------- looks ----------
        SectionTitle(t("Colour Theme", "Màu Giao Diện"), th)
        FlowRow {
            Themes.list.forEach { tm ->
                Column(Modifier.padding(end = 10.dp, bottom = 10.dp).clickable { Prefs.theme.value = tm.key }, horizontalAlignment = Alignment.CenterHorizontally) {
                    Box(Modifier.size(width = 64.dp, height = 44.dp).clip(RoundedCornerShape(12.dp)).background(tm.bg)
                        .border(if (Prefs.theme.value == tm.key) 3.dp else 1.dp, if (Prefs.theme.value == tm.key) th.accent else th.muted.copy(alpha = 0.3f), RoundedCornerShape(12.dp)),
                        contentAlignment = Alignment.BottomEnd) { Box(Modifier.padding(6.dp).size(14.dp).clip(RoundedCornerShape(7.dp)).background(tm.accent)) }
                    Text(tm.name.take(14), color = th.text, fontSize = 10.sp, maxLines = 1)
                }
            }
            Column(Modifier.padding(end = 10.dp, bottom = 10.dp).clickable { Prefs.theme.value = "custom" }, horizontalAlignment = Alignment.CenterHorizontally) {
                Box(Modifier.size(width = 64.dp, height = 44.dp).clip(RoundedCornerShape(12.dp)).background(Brush.horizontalGradient(BarColours.gradients["rainbow"]!!))
                    .border(if (Prefs.theme.value == "custom") 3.dp else 1.dp, th.accent, RoundedCornerShape(12.dp)))
                Text(t("Custom", "Tự Chọn"), color = th.text, fontSize = 10.sp)
            }
        }
        if (Prefs.theme.value == "custom") HuePicker(Prefs.customAccent.value, th) { Prefs.customAccent.value = it }

        SectionTitle(t("Skin", "Skin"), th)
        FlowRow { SkinList.keys.forEach { k -> Chip(SkinList.name(k), Prefs.skin.value == k, th) { Prefs.skin.value = k } } }
        when (Prefs.skin.value) {
            "xp" -> FlowRow { Skins.xpColours.forEach { (k, n) -> Chip(n, Prefs.xpColour.value == k, th) { Prefs.xpColour.value = k } } }
            "grain" -> FlowRow { SkinList.woodTypes.forEachIndexed { i, (en, vi) -> Chip(t(en, vi), Prefs.woodType.value == i, th) { Prefs.woodType.value = i } } }
            "marble" -> FlowRow { SkinList.marbleTypes.forEachIndexed { i, (en, vi) -> Chip(t(en, vi), Prefs.marbleType.value == i, th) { Prefs.marbleType.value = i } } }
            "pill", "slim" -> FlowRow { PillColours.list.indices.forEach { i -> Chip(PillColours.name(i), Prefs.pillColour.value == i, th) { Prefs.pillColour.value = i } } }
        }
        Pill(Modifier.padding(vertical = 8.dp), big = true)
        SliderRow(t("Pill Transparency", "Độ Trong Suốt Viên Thuốc"), th, 1f - Prefs.pillAlpha.value, 0f..0.95f, label = "${((1f - Prefs.pillAlpha.value) * 100).toInt()}%") { Prefs.pillAlpha.value = 1f - it }
        SliderRow(t("Wave Strength", "Độ Đậm Sóng Nhạc"), th, Prefs.waveStrength.value, 0f..1.6f, label = "${(Prefs.waveStrength.value * 100).toInt()}%") { Prefs.waveStrength.value = it }
        SliderRow(t("Wave Height", "Độ Cao Sóng"), th, Prefs.waveHeight.value, 0.2f..0.95f, label = "${(Prefs.waveHeight.value * 100).toInt()}%") { Prefs.waveHeight.value = it }
        SwitchRow(t("Double-Tap The Pill To Change Colour", "Nhấp 2 Lần Để Đổi Màu"), th, Prefs.dblTapColour.value,
            t("Off = the small pill opens Now Playing a little faster.", "Tắt thì viên thuốc nhỏ mở trang Đang Phát nhanh hơn một chút.")) { Prefs.dblTapColour.value = it }

        SectionTitle(t("Play Buttons", "Kiểu Nút Phát Nhạc"), th)
        FlowRow {
            ButtonArt.names.indices.forEach { i ->
                Column(Modifier.padding(end = 8.dp, bottom = 8.dp).width(100.dp).clip(RoundedCornerShape(14.dp))
                    .background(if (Prefs.btnStyle.value == i) th.accent.copy(alpha = 0.22f) else th.card).clickable { Prefs.btnStyle.value = i }.padding(6.dp),
                    horizontalAlignment = Alignment.CenterHorizontally) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        for (k in listOf(ButtonArt.PREV, ButtonArt.PLAY, ButtonArt.NEXT)) androidx.compose.foundation.Canvas(Modifier.size(if (k == ButtonArt.PLAY) 30.dp else 22.dp)) {
                            androidx.compose.ui.graphics.drawscope.drawIntoCanvas { c -> ButtonArt.draw(c.nativeCanvas, k, i, size.width, (if (th.light) Color(0xFF1B2733) else Color.White).toArgb()) }
                        }
                    }
                    Text(ButtonArt.name(i), color = th.text, fontSize = 11.sp, maxLines = 1)
                }
            }
        }
        Text(t("Button colour", "Màu nút"), color = th.text)
        FlowRow { listOf("white" to t("White", "Trắng"), "cover" to t("From Cover", "Theo Ảnh Bìa"), "theme" to t("Theme Colour", "Màu Giao Diện"), "custom" to t("Custom", "Tự Chọn"))
            .forEach { (k, n) -> Chip(n, Prefs.btnColour.value == k, th) { Prefs.btnColour.value = k } } }
        if (Prefs.btnColour.value == "custom") HuePicker(Prefs.btnCustom.value, th) { Prefs.btnCustom.value = it }
        Text(t("Button size", "Cỡ nút"), color = th.text)
        FlowRow { listOf(0.85f to t("Small", "Nhỏ"), 1f to t("Medium", "Vừa"), 1.2f to t("Large", "To"), 1.45f to t("Very Large", "Rất To"))
            .forEach { (v, n) -> Chip(n, Prefs.btnScale.value == v, th) { Prefs.btnScale.value = v } } }

        SectionTitle(t("Time Bar Colour", "Màu Thanh Thời Gian"), th)
        FlowRow {
            BarColours.list.forEach { (_, _, key) ->
                val brush = when { key.startsWith("grad:") -> Brush.horizontalGradient(BarColours.gradients[key.removePrefix("grad:")]!!)
                    key == "cover" -> Brush.sweepGradient(com.tomstechsolutions.jukebox.playback.Core.palette.value.map { Color(it) } + Color(com.tomstechsolutions.jukebox.playback.Core.palette.value[0])); else -> null }
                Swatch(if (brush == null) BarColours.hex(key) else Color.Gray, Prefs.barColour.value == key, th, 34.dp, brush) { Prefs.barColour.value = key }
            }
            Swatch(Color(Prefs.customBar.value), Prefs.barColour.value == "custom", th, 34.dp) { Prefs.barColour.value = "custom" }
        }
        Text(BarColours.list.firstOrNull { it.third == Prefs.barColour.value }?.let { t(it.first, it.second) } ?: t("Custom Colour", "Tự Chọn Màu"), color = th.muted, fontSize = 12.sp)
        if (Prefs.barColour.value == "custom") HuePicker(Prefs.customBar.value, th) { Prefs.customBar.value = it }

        SectionTitle(t("Text Size And Language", "Cỡ Chữ Và Ngôn Ngữ"), th)
        Row(Modifier.horizontalScroll(rememberScrollState())) {
            listOf(1.0f to "A", 1.15f to "A+", 1.3f to "A++").forEach { (v, s) -> Chip(s, Prefs.textScale.value == v, th) { Prefs.textScale.value = v } }
            Spacer(Modifier.width(12.dp))
            Chip("EN", Prefs.lang.value == "en", th) { Prefs.lang.value = "en"; L.vi.value = false }
            Chip("VI", Prefs.lang.value == "vi", th) { Prefs.lang.value = "vi"; L.vi.value = true }
        }

        // ---------- edge lighting ----------
        SectionTitle(t("Edge Lighting", "Ánh Sáng Chạy Viền"), th)
        Card(th) {
            SwitchRow(t("Edge Lighting On", "Bật Ánh Sáng Chạy Viền"), th, Prefs.edgeOn.value, t("Only while music is playing.", "Chỉ chạy khi đang phát nhạc.")) { Prefs.edgeOn.value = it }
            FlowRow {
                EdgeEffects.names.indices.forEach { i ->
                    Column(Modifier.padding(end = 8.dp, bottom = 8.dp).width(96.dp).clickable { Prefs.edgeEffect.value = i; Prefs.edgeAuto.value = false; Prefs.edgeRandom.value = false },
                        horizontalAlignment = Alignment.CenterHorizontally) {
                        Box(Modifier.size(96.dp, 56.dp).border(if (Prefs.edgeEffect.value == i && !Prefs.edgeAuto.value) 2.dp else 0.dp, th.accent, RoundedCornerShape(14.dp))) {
                            EdgePreview(i, Modifier.fillMaxSize())
                        }
                        Text(EdgeEffects.name(i), color = th.text, fontSize = 11.sp, maxLines = 2)
                    }
                }
            }
            SliderRow(t("Speed", "Tốc Độ") + "  ( [ ] )", th, Prefs.edgeSpeed.value.toFloat(), 0f..4f, 3, EdgeEffects.speedName(Prefs.edgeSpeed.value)) { Prefs.edgeSpeed.value = it.toInt() }
            Text(t("Colour", "Màu"), color = th.text)
            FlowRow {
                listOf("cover" to t("From Cover", "Theo Ảnh Bìa"), "rainbow" to t("Rainbow", "Cầu Vồng"), "brand" to t("Tom's Colours", "Màu Tom's"), "custom" to t("Custom", "Tự Chọn"))
                    .forEach { (k, s) -> Chip(s, Prefs.edgeColour.value == k, th) { Prefs.edgeColour.value = k } }
            }
            if (Prefs.edgeColour.value == "custom") HuePicker(Prefs.edgeCustom.value, th) { Prefs.edgeCustom.value = it }
            SliderRow(t("Thickness", "Độ Dày"), th, Prefs.edgeThick.value, 2f..10f, label = "${Prefs.edgeThick.value.toInt()}") { Prefs.edgeThick.value = it }
            SliderRow(t("Brightness", "Độ Sáng"), th, Prefs.edgeBright.value, 0.2f..1f, label = "${(Prefs.edgeBright.value * 100).toInt()}%") { Prefs.edgeBright.value = it }
            Text(t("Where", "Chạy Ở Đâu"), color = th.text)
            FlowRow {
                listOf("window" to t("Screen Edge", "Viền Màn Hình"), "pill" to t("Around The Pill", "Quanh Thanh Viên Thuốc"), "both" to t("Both", "Cả Hai"))
                    .forEach { (k, s) -> Chip(s, Prefs.edgeWhere.value == k, th) { Prefs.edgeWhere.value = k } }
            }
            SwitchRow(t("Pulse With The Beat", "Nhấp Nháy Theo Nhịp"), th, Prefs.edgeBeat.value) { Prefs.edgeBeat.value = it }
            SwitchRow(t("Change Effect Automatically", "Tự Đổi Hiệu Ứng"), th, Prefs.edgeAuto.value, t("A new effect every 30 seconds.", "Mỗi 30 giây đổi một kiểu.")) { Prefs.edgeAuto.value = it }
            SwitchRow(t("Random For Each Song", "Ngẫu Nhiên Mỗi Bài"), th, Prefs.edgeRandom.value) { Prefs.edgeRandom.value = it; if (it) Prefs.edgeAuto.value = false }
            SwitchRow(t("Light The Screen Edge", "Chạy Viền Màn Hình"), th, Prefs.edgeScreen.value) { Prefs.edgeScreen.value = it }
            val auto = Prefs.edgeCorner.value < 0f
            SwitchRow(t("Match The Screen Corners Automatically", "Tự Khớp Góc Màn Hình"), th, auto, t("Turn off to set the corner yourself.", "Tắt để tự chỉnh độ bo góc.")) { Prefs.edgeCorner.value = if (it) -1f else 40f }
            if (!auto) SliderRow(t("Corner Roundness", "Độ Bo Góc"), th, Prefs.edgeCorner.value, 0f..80f, label = "${Prefs.edgeCorner.value.toInt()} dp") { Prefs.edgeCorner.value = it }
        }

        // ---------- sleep, driving ----------
        SectionTitle(t("Sleep Timer And Driving", "Hẹn Giờ Và Lái Xe"), th)
        Row { Btn(t("Sleep Timer…", "Hẹn Giờ Tắt Nhạc…"), th, Gl.timer, primary = true) { act.showSleep.value = true } }

        // ---------- phone ----------
        SectionTitle(t("Gestures And Phone", "Cử Chỉ Và Điện Thoại"), th)
        Card(th) {
            SwitchRow(t("Vibrate On Touch", "Rung Nhẹ Khi Bấm"), th, Prefs.haptics.value) { Prefs.haptics.value = it }
            SwitchRow(t("Swipe The Pill To Change Song", "Vuốt Thanh Viên Thuốc Để Đổi Bài"), th, Prefs.swipePill.value) { Prefs.swipePill.value = it }
            SwitchRow(t("Shake To Skip", "Lắc Máy Để Qua Bài"), th, Prefs.shakeSkip.value) { Prefs.shakeSkip.value = it }
            SwitchRow(t("Headset Button: 1 Play · 2 Next · 3 Previous", "Nút Tai Nghe: 1 Phát · 2 Bài Sau · 3 Bài Trước"), th, Prefs.headsetTriple.value) { Prefs.headsetTriple.value = it }
            SwitchRow(t("Play When Headphones / Bluetooth Connect", "Tự Phát Khi Cắm Tai Nghe / Nối Bluetooth"), th, Prefs.autoPlayHeadset.value) { Prefs.autoPlayHeadset.value = it }
            SwitchRow(t("Disc Spins With The Beat", "Đĩa Quay Theo Nhịp"), th, Prefs.spinBeat.value) { Prefs.spinBeat.value = it }
            SwitchRow(t("Blurred Cover Background", "Nền Mờ Theo Ảnh Bìa"), th, Prefs.blurBg.value) { Prefs.blurBg.value = it }
            SwitchRow(t("Battery Saver Below 20 %", "Tiết Kiệm Pin Dưới 20 %"), th, Prefs.batterySaver.value, t("Slows animations, turns edge lighting off.", "Giảm hiệu ứng, tắt ánh sáng chạy viền.")) { Prefs.batterySaver.value = it }
        }

        SectionTitle(t("Lock Screen", "Màn Hình Khoá"), th)
        Card(th) {
            SwitchRow(t("Tom's Jukebox Lock Screen", "Màn Hình Khoá Tom's Jukebox"), th, Prefs.customLock.value,
                t("Pill, edge lighting and a big clock when the screen wakes while music plays.", "Thanh viên thuốc, ánh sáng chạy viền và đồng hồ lớn khi mở màn hình lúc đang nghe nhạc.")) { Prefs.customLock.value = it }
            if (Prefs.customLock.value && Build.VERSION.SDK_INT >= 29 && !Settings.canDrawOverlays(ctx)) {
                Text(t("Android needs \"Display over other apps\" for this.", "Android cần quyền \"Hiển thị trên ứng dụng khác\" cho việc này."), color = th.accent, fontSize = 13.sp)
                Btn(t("Open Permission", "Mở Quyền"), th, Gl.lock) {
                    try { ctx.startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:" + ctx.packageName))) } catch (_: Exception) { }
                }
            }
            Text(t("Samsung Now Bar and the lock screen controls show Tom's Jukebox automatically (Settings › Lock screen and AOD › Now bar). Always On Display can't be drawn by other apps.",
                "Samsung Now Bar và nút điều khiển trên màn hình khoá tự hiện Tom's Jukebox (Cài đặt › Màn hình khoá và AOD › Now bar). Màn hình Always On Display thì ứng dụng khác không vẽ được."),
                color = th.muted, fontSize = 12.sp)
        }

        // ---------- hidden songs ----------
        val hid = Prefs.hiddenSet()
        if (hid.isNotEmpty()) {
            SectionTitle(t("Hidden Songs", "Bài Đã Ẩn") + " (${hid.size})", th)
            Card(th) {
                hid.take(50).forEach { u ->
                    val tr = com.tomstechsolutions.jukebox.data.Library.all.value.firstOrNull { it.uri == u }
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(tr?.title ?: u.substringAfterLast('/'), color = th.text, fontSize = 14.sp, maxLines = 1, modifier = Modifier.weight(1f))
                        Btn(t("Show Again", "Hiện Lại"), th) { Prefs.unhide(u); com.tomstechsolutions.jukebox.data.Library.refilter() }
                    }
                }
            }
        }

        // ---------- data ----------
        SectionTitle(t("Data", "Dữ Liệu"), th)
        Row {
            Btn(t("Backup…", "Sao Lưu…"), th, Gl.up) { backup.launch("TomsJukebox-backup-$stamp.json") }
            Btn(t("Restore…", "Khôi Phục…"), th, Gl.down) { restore.launch(arrayOf("application/json", "*/*")) }
        }
        Text(t("The same backup file opens in Tom's Jukebox for Windows.", "File sao lưu này mở được trong Tom's Jukebox bản Windows."), color = th.muted, fontSize = 12.sp)

        // ---------- shortcuts ----------
        SectionTitle(t("Keyboard Shortcuts (DeX / Keyboard)", "Phím Tắt (DeX / Bàn Phím)"), th)
        Card(th) {
            listOf("Space / X / C" to t("Play / Pause", "Phát / Tạm Dừng"), "Z / B" to t("Previous / Next", "Bài Trước / Bài Sau"), "V" to t("Stop", "Dừng"),
                "← →" to t("Back / forward 5 s (Shift: 30 s)", "Lùi / tới 5 giây (Shift: 30 giây)"), "↑ ↓" to t("Volume", "Âm Lượng"),
                "S / R" to t("Shuffle / Repeat", "Trộn Bài / Lặp Lại"), "[ ]" to t("Edge lighting slower / faster", "Ánh sáng chạy viền chậm / nhanh hơn"),
                "E" to t("Next edge effect", "Hiệu ứng viền kế tiếp"), "G" to t("Next visualisation", "Hiệu ứng sóng kế tiếp"), "L" to t("Lyrics", "Lời Bài Hát"),
                "F" to t("Favourite ★", "Yêu Thích ★"), "Ctrl+Shift+T" to t("Sleep timer", "Hẹn giờ tắt nhạc"), "1 – 5" to t("Pages", "Các trang"), "Esc" to t("Close", "Đóng"))
                .forEach { (k, v) -> Row(Modifier.padding(vertical = 3.dp)) { Text(k, color = th.accent, fontSize = 13.sp, fontWeight = FontWeight.Bold, modifier = Modifier.width(120.dp)); Text(v, color = th.text, fontSize = 13.sp) } }
        }

        // ---------- messages ----------
        if (showMsgs) {
            SectionTitle(t("Messages", "Tin Nhắn"), th)
            Card(th) {
                if (Messages.list.isEmpty()) Text(t("No messages.", "Chưa có tin nhắn."), color = th.muted)
                Messages.list.take(30).forEach { m ->
                    Text(SimpleDateFormat("dd/MM HH:mm", Locale.US).format(Date(m.time)) + "  " + m.text, color = th.text, fontSize = 13.sp,
                        modifier = Modifier.padding(vertical = 3.dp).clickable { if ("Recordings" in m.text) { act.openRecordings.value = true; act.tab.intValue = 1 } })
                }
            }
        }
        Btn(t("About", "Giới Thiệu"), th, Gl.info) { about = true }
        // status row: Messages | Feedback | Version
        Row(Modifier.fillMaxWidth().padding(vertical = 14.dp), verticalAlignment = Alignment.CenterVertically) {
            Text(t("Messages", "Tin Nhắn") + (if (Messages.unread() > 0) " (${Messages.unread()})" else ""), color = th.accent, fontSize = 13.sp,
                modifier = Modifier.clickable { showMsgs = !showMsgs; Messages.markRead() })
            Text("  |  ", color = th.muted, fontSize = 13.sp)
            Text(t("Feedback", "Góp Ý"), color = th.accent, fontSize = 13.sp, modifier = Modifier.clickable { if (!sendFeedback(ctx)) mailFail = true })
            Text("  |  ", color = th.muted, fontSize = 13.sp)
            Text(t("Version ", "Phiên Bản ") + App.VERSION, color = th.muted, fontSize = 13.sp)
        }
        Text("One of Tom's Technology Solutions Products", color = th.muted, fontSize = 11.sp)
        Spacer(Modifier.height(30.dp))
    }
    if (about) AboutDialog(th) { about = false }
    if (mailFail) FeedbackFallback(th) { mailFail = false }
}
