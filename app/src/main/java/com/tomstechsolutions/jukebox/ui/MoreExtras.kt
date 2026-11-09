package com.tomstechsolutions.jukebox.ui

import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.drawscope.drawIntoCanvas
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.t

/** New settings in 0.9.3: bottom pill size, library chips, navigation effects, opening animation, lock-screen pill, widgets. */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun MoreExtras(act: MainActivity, th: JTheme) {
    SectionTitle(t("Player Style", "Kiểu Thanh Phát Nhạc"), th)
    Card(th) {
        Text(t("In the app", "Trong app"), color = th.text, fontSize = 14.sp)
        FlowRow { listOf("card" to t("Default (Tom's Tech)", "Mặc Định (Tom's Tech)"), "pill" to t("Pill", "Viên Thuốc")).forEach { (k, n) -> Chip(n, Prefs.playerStyle.value == k, th) { Prefs.playerStyle.value = k } } }
        Text(t("Lock screen", "Màn hình khoá"), color = th.text, fontSize = 14.sp)
        FlowRow { listOf("card" to t("Default (Tom's Tech)", "Mặc Định (Tom's Tech)"), "pill" to t("Pill", "Viên Thuốc")).forEach { (k, n) -> Chip(n, Prefs.lockStyle.value == k, th) { Prefs.lockStyle.value = k } } }
        Text(t("Default (Tom's Tech): the cover fills the card, music waves sit on the time bar, buttons in frosted circles. Swipe up on it to open Now Playing.",
            "Mặc Định (Tom's Tech): ảnh bìa làm nền thẻ, sóng nhạc nằm trên thanh thời gian, nút trong vòng kính mờ. Vuốt lên thẻ để mở Đang Phát."), color = th.muted, fontSize = 12.sp)
        Text(t("Waves on the time bar – shape:", "Sóng nhạc trên thanh thời gian – kiểu:"), color = th.text, fontSize = 14.sp)
        FlowRow { WaveColours.shapes.forEachIndexed { i, (en, vi) -> Chip(t(en, vi), Prefs.waveShape.value == i, th) { Prefs.waveShape.value = i } } }
        Text(t("Colours:", "Màu sắc:"), color = th.text, fontSize = 14.sp)
        FlowRow { WaveColours.list.forEach { (k, en, vi) -> Chip(t(en, vi), Prefs.waveCols.value == k, th) { Prefs.waveCols.value = k } } }
    }

    SectionTitle(t("Bottom Pill", "Viên Thuốc Dưới"), th)
    Card(th) {
        FlowRow { listOf("small" to t("Compact", "Gọn"), "medium" to t("Medium", "Vừa"), "large" to t("Large", "To")).forEach { (k, n) -> Chip(n, Prefs.miniSize.value == k, th) { Prefs.miniSize.value = k } } }
        Text(t("Swipe up on the pill to open Now Playing · swipe left/right to change song.", "Vuốt lên viên thuốc để mở Đang Phát · vuốt trái/phải để đổi bài."), color = th.muted, fontSize = 12.sp)
        SwitchRow(t("Hide The Library Chips While Scrolling", "Ẩn Hàng Chọn Mục Khi Cuộn Thư Viện"), th, Prefs.chipsAutoHide.value) { Prefs.chipsAutoHide.value = it }
    }

    SectionTitle(t("Bottom Bar Effects", "Hiệu Ứng Thanh Điều Hướng"), th)
    Card(th) {
        Text(t("Pick one or more – they can be combined.", "Chọn một hay nhiều kiểu – kết hợp được với nhau."), color = th.muted, fontSize = 12.sp)
        FlowRow { NavFx.list.forEach { (k, n) -> Chip((if (NavFx.on(k)) "✓ " else "") + t(n.first, n.second), NavFx.on(k), th) { NavFx.toggle(k) } } }
        SwitchRow(t("Vibrate When Changing Page", "Rung Nhẹ Khi Đổi Mục"), th, Prefs.navHaptic.value) { Prefs.navHaptic.value = it }
        SliderRow(t("Effect Speed", "Tốc Độ Hiệu Ứng"), th, Prefs.fxSpeed.value, 0.5f..2f, label = "${(Prefs.fxSpeed.value * 100).toInt()}%") { Prefs.fxSpeed.value = it }
    }

    SectionTitle(t("Opening Animation", "Hiệu Ứng Mở App"), th)
    Card(th) {
        SwitchRow(t("Play An Animation When The App Opens", "Chạy Hiệu Ứng Khi Mở App"), th, Prefs.splashOn.value,
            t("Opening from the widget or the notification goes straight to Now Playing.", "Mở từ widget hay thông báo thì vào thẳng Đang Phát.")) { Prefs.splashOn.value = it }
        FlowRow { SplashFx.names.indices.forEach { i -> Chip(SplashFx.name(i), Prefs.splashStyle.value == i, th) { Prefs.splashStyle.value = i } } }
        FlowRow {
            Chip(t("Fast", "Nhanh"), Prefs.splashFast.value, th) { Prefs.splashFast.value = true }
            Chip(t("Normal", "Vừa"), !Prefs.splashFast.value, th) { Prefs.splashFast.value = false }
        }
        SwitchRow(t("Vibrate When The Icon Bounces", "Rung Nhẹ Khi Icon Nảy"), th, Prefs.splashHaptic.value) { Prefs.splashHaptic.value = it }
        Row { Btn(t("Preview", "Xem Thử"), th, primary = true) { act.previewSplash.intValue = Prefs.splashStyle.value } }
    }

    SectionTitle(t("Lock Screen Pill", "Viên Thuốc Màn Hình Khoá"), th)
    Card(th) {
        Text(t("On the Tom's Jukebox lock screen: hold the pill for half a second, then drag it anywhere.", "Trên màn hình khoá Tom's Jukebox: nhấn giữ viên thuốc nửa giây rồi kéo đi đâu cũng được."), color = th.muted, fontSize = 12.sp)
        FlowRow {
            listOf(0f to t("Top", "Trên"), 0.5f to t("Middle", "Giữa"), -1f to t("Bottom", "Dưới")).forEach { (v, n) ->
                Chip(n, Prefs.lockY.value == v, th) { Prefs.lockY.value = v; Prefs.lockX.value = 0.5f; Prefs.lockYLand.value = v; Prefs.lockXLand.value = 0.5f }
            }
        }
        SwitchRow(t("Snap To Top / Middle / Bottom", "Tự Hít Vào Trên / Giữa / Dưới"), th, Prefs.lockSnap.value) { Prefs.lockSnap.value = it }
        SwitchRow(t("Lock Position 🔒", "Khoá Vị Trí 🔒"), th, Prefs.lockLocked.value) { Prefs.lockLocked.value = it }
        FlowRow { listOf("small" to t("Compact", "Gọn"), "medium" to t("Medium", "Vừa"), "large" to t("Large", "To")).forEach { (k, n) -> Chip(n, Prefs.lockSize.value == k, th) { Prefs.lockSize.value = k } } }
        SliderRow(t("Transparency", "Độ Trong Suốt"), th, 1f - Prefs.lockAlpha.value, 0f..0.8f, label = "${((1f - Prefs.lockAlpha.value) * 100).toInt()}%") { Prefs.lockAlpha.value = 1f - it }
        Text(t("Double-tap an empty spot on the lock screen to put the pill back at the bottom.", "Nhấp 2 lần vào chỗ trống trên màn hình khoá để đưa viên thuốc về dưới cùng."), color = th.muted, fontSize = 12.sp)
    }

    SectionTitle(t("Fonts", "Font Chữ"), th)
    Card(th) {
        val ctx = androidx.compose.ui.platform.LocalContext.current
        var tick by androidx.compose.runtime.remember { androidx.compose.runtime.mutableIntStateOf(0) }
        val pick = androidx.activity.compose.rememberLauncherForActivityResult(androidx.activity.result.contract.ActivityResultContracts.OpenDocument()) { uri ->
            if (uri != null) { val k = AppFonts.import(ctx, uri); if (k != null) { Prefs.fontTitle.value = k; tick++ }
                else com.tomstechsolutions.jukebox.data.Messages.add(t("That file isn't a font (.ttf / .otf).", "File này không phải font (.ttf / .otf).")) }
        }
        val fonts = androidx.compose.runtime.remember(tick) { AppFonts.all(ctx) }
        for ((which, label, pref) in listOf(Triple(0, t("Titles & song names", "Font tiêu đề & tên bài"), Prefs.fontTitle), Triple(1, t("Normal text", "Font chữ thường"), Prefs.fontBody))) {
            Text(label + ": " + AppFonts.name(pref.value), color = th.text, fontSize = 14.sp, fontWeight = androidx.compose.ui.text.font.FontWeight.SemiBold)
            androidx.compose.foundation.lazy.LazyRow(Modifier.padding(vertical = 4.dp)) {
                items(fonts.size) { i -> val f = fonts[i]; val on = pref.value == f.key
                    androidx.compose.foundation.layout.Column(Modifier.padding(end = 6.dp).clip(androidx.compose.foundation.shape.RoundedCornerShape(14.dp))
                        .background(if (on) th.accent.copy(alpha = 0.25f) else th.card)
                        .androidx_combined({ pref.value = f.key }, { if (f.key.startsWith("file:")) { AppFonts.remove(ctx, f.key); tick++ } }).padding(horizontal = 12.dp, vertical = 8.dp)) {
                        Text(if (which == 0) "Thạch Trắng" else "Chè đậu xanh", color = if (on) th.accent else th.text, fontSize = 20.sp, fontFamily = AppFonts.family(f.key), maxLines = 1)
                        Text(t(f.en, f.vi), color = th.muted, fontSize = 10.sp, maxLines = 1)
                    }
                }
            }
        }
        Text(t("Preview:", "Xem trước:"), color = th.muted, fontSize = 12.sp)
        Text("Tom's Jukebox – Hiền Khánh 718", color = th.text, fontSize = 24.sp, fontFamily = AppFonts.title())
        Text("Thạch trắng, chè đậu xanh thơm ngon tinh khiết", color = th.text, fontSize = 15.sp, fontFamily = AppFonts.body())
        Row { Btn(t("+ Add Font From Phone", "+ Thêm Font Từ Điện Thoại"), th, primary = true) { pick.launch(arrayOf("font/*", "application/x-font-ttf", "application/x-font-otf", "application/octet-stream", "*/*")) } }
        Text(t("\"Saigon 1985\" sign-painting fonts by Thái Hiệu (Fontzin). Long-press a font you added to remove it.",
            "Bộ font biển hiệu Sài Gòn xưa \"Saigon 1985\" do Thái Hiệu (Fontzin) thiết kế. Nhấn giữ font tự thêm để xoá."), color = th.muted, fontSize = 11.sp)
    }

    SectionTitle(t("Record Button", "Nút Thâu Âm"), th)
    Card(th) {
        Text(t("Design (tap to choose):", "Kiểu nút (nhấn để chọn):"), color = th.text, fontSize = 14.sp)
        FlowRow {
            RecArt.names.indices.forEach { i ->
                val on = Prefs.recStyle.value == i
                androidx.compose.foundation.layout.Column(Modifier.padding(3.dp).width(78.dp).clip(androidx.compose.foundation.shape.RoundedCornerShape(14.dp))
                    .background(if (on) th.accent.copy(alpha = 0.25f) else th.card).clickable { Prefs.recStyle.value = i }.padding(6.dp),
                    horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally) {
                    Row {
                        for (stop in listOf(false, true)) androidx.compose.foundation.Canvas(Modifier.size(30.dp)) {
                            drawIntoCanvas { cv -> if (i == 0) ButtonArt.draw(cv.nativeCanvas, if (stop) ButtonArt.REC_STOP else ButtonArt.REC, Prefs.btnStyle.value, size.width, android.graphics.Color.WHITE)
                                else RecArt.draw(cv.nativeCanvas, stop, i, size.width, RecArt.colour()) }
                        }
                    }
                    Text(RecArt.name(i), color = if (on) th.accent else th.text, fontSize = 10.sp, maxLines = 2, textAlign = androidx.compose.ui.text.style.TextAlign.Center, lineHeight = 12.sp)
                }
            }
        }
        Text(t("Colour:", "Màu nút thâu:"), color = th.text, fontSize = 14.sp)
        FlowRow { RecArt.colours.forEach { (k, en, vi) -> Chip(t(en, vi), Prefs.recColour.value == k, th) { Prefs.recColour.value = k } } }
        if (Prefs.recColour.value == "custom") HuePicker(Prefs.recCustom.value, th) { Prefs.recCustom.value = it }
        SwitchRow(t("Blink While Recording", "Nhấp Nháy Khi Đang Thâu"), th, Prefs.recBlink.value) { Prefs.recBlink.value = it }
        Text(t("Left = ready to record, right = recording (tap to stop).", "Hình trái = sẵn sàng thâu, hình phải = đang thâu (bấm để dừng)."), color = th.muted, fontSize = 12.sp)
    }

    SectionTitle("Podcast", th)
    Card(th) {
        SwitchRow(t("Download The Highest Quality", "Tải Bản Chất Lượng Cao"), th, Prefs.podHQ.value,
            t("Always the original file, never re-compressed; the higher-bitrate version when a channel offers one.", "Luôn tải file gốc, không nén lại; kênh nào có bản bitrate cao hơn thì tải bản đó.")) { Prefs.podHQ.value = it }
        Text(t("Auto download keeps the newest:", "Tải tự động giữ số tập mới nhất:"), color = th.text, fontSize = 14.sp)
        FlowRow { listOf(3, 5, 10, 20).forEach { n -> Chip(t("$n episodes", "$n tập"), Prefs.podKeep.value == n, th) { Prefs.podKeep.value = n } } }
        Text(t("Recording a podcast: ● next to Play records from now until you stop; [A B] ✂ on Now Playing cuts a part; long-press an episode › Save Whole Episode. Files go to Recordings › Podcast.",
            "Thâu podcast: ● bên trái Play thâu từ lúc bấm tới lúc dừng; [A B] ✂ ở Đang Phát để cắt một đoạn; nhấn giữ một tập › Lưu Cả Tập. File nằm trong Bản Thâu Âm › Podcast."), color = th.muted, fontSize = 12.sp)
    }

    SectionTitle(t("Home Screen Widgets", "Widget Màn Hình Chính"), th)
    Card(th) {
        Text(t("Hold an empty spot on the home screen › Widgets › Tom's Jukebox. Pill, Radio, Podcast, Sleep Timer and Album Cover widgets; stretch them to any size.",
            "Nhấn giữ chỗ trống trên màn hình chính › Tiện ích (Widgets) › Tom's Jukebox. Có widget Viên Thuốc, Radio, Podcast, Hẹn Giờ và Ảnh Bìa; kéo giãn cỡ nào cũng được. Widget Radio dùng các đài ★ Yêu Thích (nhấn ☆ trong mục Radio)."), color = th.muted, fontSize = 12.sp)
        FlowRow {
            listOf("skin" to t("Same As Skin", "Theo Skin"), "cover" to t("Cover Colour", "Theo Ảnh Bìa"), "clear" to t("Transparent", "Trong Suốt"), "frost" to t("Frosted", "Kính Mờ"), "you" to t("Wallpaper Colours", "Theo Hình Nền"))
                .forEach { (k, n) -> Chip(n, Prefs.widgetBg.value == k, th) { Prefs.widgetBg.value = k; com.tomstechsolutions.jukebox.system.Widgets.refresh(act) } }
        }
        SliderRow(t("Widget Opacity", "Độ Đậm Widget"), th, Prefs.widgetAlpha.value, 0.2f..1f, label = "${(Prefs.widgetAlpha.value * 100).toInt()}%") {
            Prefs.widgetAlpha.value = it; com.tomstechsolutions.jukebox.system.Widgets.refresh(act) }
    }

}

@OptIn(androidx.compose.foundation.ExperimentalFoundationApi::class)
private fun Modifier.androidx_combined(onClick: () -> Unit, onLong: () -> Unit): Modifier = this.then(Modifier.combinedClickable(onClick = onClick, onLongClick = onLong))
