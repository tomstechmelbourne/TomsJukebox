package com.tomstechsolutions.jukebox.ui

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tomstechsolutions.jukebox.App
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.R
import com.tomstechsolutions.jukebox.playback.Core
import com.tomstechsolutions.jukebox.playback.SleepTimer
import com.tomstechsolutions.jukebox.t
import java.util.Calendar

/** Hẹn Giờ Tắt Nhạc. Ctrl+Shift+T on a keyboard, long-press the pill, or the clock button. */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun SleepDialog(th: JTheme, onClose: () -> Unit) {
    var custom by remember { mutableFloatStateOf(Prefs.sleepMinutes.value.toFloat()) }
    val now = Calendar.getInstance()
    var hour by remember { mutableIntStateOf((now.get(Calendar.HOUR_OF_DAY) + 1) % 24) }
    var minute by remember { mutableIntStateOf(0) }
    val sleep = Core.service?.sleep
    fun go(m: SleepTimer.Mode, minutes: Int = 0, at: Long = 0) {
        if (m == SleepTimer.Mode.MINUTES) Prefs.sleepMinutes.value = minutes
        sleep?.start(m, minutes, at); onClose()
    }
    AlertDialog(onDismissRequest = onClose, containerColor = if (th.light) Color.White else Color(0xFF14232D),
        title = { Text(t("Sleep Timer", "Hẹn Giờ Tắt Nhạc"), color = th.text, fontWeight = FontWeight.Bold) },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState())) {
                if (Core.sleepMode.value != "NONE") {
                    Text(t("Running: ", "Đang chạy: ") + (if (Core.sleepRemaining.longValue >= 0) fmtTime(Core.sleepRemaining.longValue) else
                        if (Core.sleepMode.value == "END_TRACK") t("end of song", "hết bài") else t("end of list", "hết danh sách")),
                        color = th.accent, fontWeight = FontWeight.Bold)
                    Row { Btn("+15 " + t("min", "phút"), th, primary = true) { sleep?.addMinutes(15) }; Btn(t("Cancel Timer", "Huỷ Hẹn Giờ"), th) { sleep?.cancel(); onClose() } }
                }
                Text(t("Stop after", "Tắt sau"), color = th.muted, fontSize = 13.sp)
                FlowRow { listOf(15, 30, 45, 60, 90).forEach { m -> Chip("$m " + t("min", "phút"), false, th) { go(SleepTimer.Mode.MINUTES, m) } } }
                SliderRow(t("Custom", "Tự Chọn"), th, custom, 5f..240f, label = "${custom.toInt()} " + t("min", "phút")) { custom = it }
                Btn(t("Start", "Bắt Đầu") + " ${custom.toInt()} " + t("min", "phút"), th, Gl.timer, primary = true) { go(SleepTimer.Mode.MINUTES, custom.toInt()) }
                Text(t("At a set time", "Vào lúc"), color = th.muted, fontSize = 13.sp)
                Row(verticalAlignment = Alignment.CenterVertically) {
                    IconBtn(Gl.down, th.text, 18.dp) { hour = (hour + 23) % 24 }
                    Text("%02d".format(hour), color = th.text, fontSize = 22.sp, fontWeight = FontWeight.Bold)
                    IconBtn(Gl.up, th.text, 18.dp) { hour = (hour + 1) % 24 }
                    Text(":", color = th.text, fontSize = 22.sp)
                    IconBtn(Gl.down, th.text, 18.dp) { minute = (minute + 55) % 60 }
                    Text("%02d".format(minute), color = th.text, fontSize = 22.sp, fontWeight = FontWeight.Bold)
                    IconBtn(Gl.up, th.text, 18.dp) { minute = (minute + 5) % 60 }
                    Spacer(Modifier.width(6.dp))
                    Btn("OK", th) {
                        val c = Calendar.getInstance(); c.set(Calendar.HOUR_OF_DAY, hour); c.set(Calendar.MINUTE, minute); c.set(Calendar.SECOND, 0)
                        if (c.timeInMillis < System.currentTimeMillis()) c.add(Calendar.DAY_OF_MONTH, 1)
                        go(SleepTimer.Mode.AT, at = c.timeInMillis)
                    }
                }
                FlowRow {
                    Chip(t("End Of Song", "Hết Bài Này"), false, th) { go(SleepTimer.Mode.END_TRACK) }
                    Chip(t("End Of Album / List", "Hết Album / Danh Sách"), false, th) { go(SleepTimer.Mode.END_QUEUE) }
                }
                Text(t("Fade out", "Giảm dần âm lượng"), color = th.muted, fontSize = 13.sp)
                FlowRow { listOf(0, 30, 60, 90, 120).forEach { s -> Chip(if (s == 0) t("Off", "Tắt") else if (s < 60) "${s}s" else "${s / 60} " + t("min", "phút") + if (s % 60 > 0) " 30s" else "", Prefs.sleepFade.value == s, th) { Prefs.sleepFade.value = s } } }
                if (Build.VERSION.SDK_INT < 31) SwitchRow(t("Turn Bluetooth off too", "Tắt luôn Bluetooth"), th, Prefs.sleepBluetooth.value) { Prefs.sleepBluetooth.value = it }
                else Text(t("Android 12+ doesn't let apps turn Bluetooth off by themselves.", "Từ Android 12 trở lên, ứng dụng không được tự tắt Bluetooth."), color = th.muted, fontSize = 12.sp)
                Text(t("Radio recordings keep going when the timer stops the music.", "Đang thâu radio thì vẫn thâu tiếp khi hẹn giờ tắt nhạc."), color = th.muted, fontSize = 12.sp)
            }
        },
        confirmButton = { TextButton(onClick = onClose) { Text(t("Close", "Đóng"), color = th.accent) } })
}

fun sendFeedback(ctx: Context): Boolean {
    val body = "\n\n---\n${App.NAME} ${App.VERSION}\nAndroid ${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})\n${Build.MANUFACTURER} ${Build.MODEL}"
    val i = Intent(Intent.ACTION_SENDTO, Uri.parse("mailto:")).putExtra(Intent.EXTRA_EMAIL, arrayOf(App.EMAIL))
        .putExtra(Intent.EXTRA_SUBJECT, "Góp Ý ${App.NAME} ${App.VERSION}").putExtra(Intent.EXTRA_TEXT, body)
    return try { ctx.startActivity(i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)); true } catch (_: Exception) { false }
}

@Composable
fun FeedbackFallback(th: JTheme, onClose: () -> Unit) {
    val ctx = LocalContext.current
    AlertDialog(onDismissRequest = onClose, title = { Text(t("Feedback", "Góp Ý")) },
        text = { Text(t("No e-mail app opened. Please write to:", "Không mở được ứng dụng e-mail. Tom gửi góp ý tới:") + "\n" + App.EMAIL) },
        confirmButton = {
            TextButton(onClick = {
                (ctx.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager).setPrimaryClip(ClipData.newPlainText("email", App.EMAIL)); onClose()
            }) { Text(t("Copy Address", "Chép Địa Chỉ"), color = th.accent) }
        }, dismissButton = { TextButton(onClick = onClose) { Text(t("Close", "Đóng")) } })
}

@Composable
fun AboutDialog(th: JTheme, onClose: () -> Unit) {
    AlertDialog(onDismissRequest = onClose, containerColor = if (th.light) Color.White else Color(0xFF14232D),
        title = {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Image(painterResource(R.drawable.app_logo), null, Modifier.size(44.dp)); Spacer(Modifier.width(10.dp))
                Column { Text(App.NAME, color = th.text, fontWeight = FontWeight.Bold); Text(t("Version ", "Phiên Bản ") + App.VERSION, color = th.muted, fontSize = 13.sp) }
            }
        },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState())) {
                Text(t("A music player for the music on your phone,\nAustralian and Vietnamese radio, podcasts and lyrics.",
                    "Chương trình nghe nhạc có sẵn trên điện thoại,\nradio Úc và Việt Nam, podcast và lời bài hát."), color = th.text)
                Spacer(Modifier.height(10.dp))
                Text(t("Idea: ", "Ý Tưởng: ") + App.BRAND, color = th.text, fontSize = 14.sp)
                Text(t("Built by: ", "Xây Dựng Bởi: ") + "Claude (Anthropic)", color = th.text, fontSize = 14.sp)
                Text(App.SLOGAN, color = ORANGE, fontSize = 13.sp, fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(vertical = 8.dp))
                Text(t("Online data: Radio Browser (radio-browser.info), LRCLIB (lyrics), Apple Podcasts search. Station names and logos belong to their owners. Samsung, One UI, Windows and iPod are trademarks of their owners; the skins here are original drawings.",
                    "Dữ liệu trực tuyến: Radio Browser (radio-browser.info), LRCLIB (lời bài hát), tìm kiếm Apple Podcasts. Tên và logo đài thuộc về chủ sở hữu. Samsung, One UI, Windows và iPod là nhãn hiệu của chủ sở hữu; các skin ở đây là hình vẽ riêng."),
                    color = th.muted, fontSize = 12.sp)
                Spacer(Modifier.height(8.dp))
                Text("© ${Calendar.getInstance().get(Calendar.YEAR)} ${App.BRAND}", color = th.muted, fontSize = 12.sp,
                    modifier = Modifier.clip(RoundedCornerShape(6.dp)).background(Color.Transparent))
            }
        },
        confirmButton = { TextButton(onClick = onClose) { Text(t("Close", "Đóng"), color = th.accent) } })
}
