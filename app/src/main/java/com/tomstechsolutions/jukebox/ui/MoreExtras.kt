package com.tomstechsolutions.jukebox.ui

import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.t

/** New settings in 0.9.3: bottom pill size, library chips, navigation effects, opening animation, lock-screen pill, widgets. */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun MoreExtras(act: MainActivity, th: JTheme) {
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
