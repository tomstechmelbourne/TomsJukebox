package com.tomstechsolutions.jukebox.ui

import android.graphics.Bitmap
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.ui.graphics.ColorFilter
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.R
import com.tomstechsolutions.jukebox.data.Art

object Gl {
    val play = R.drawable.g_play; val pause = R.drawable.g_pause; val next = R.drawable.g_next; val prev = R.drawable.g_prev
    val shuffle = R.drawable.g_shuffle; val repeat = R.drawable.g_repeat; val repeatOne = R.drawable.g_repeat_one
    val stop = R.drawable.g_stop; val cast = R.drawable.g_cast; val lyrics = R.drawable.g_lyrics; val queue = R.drawable.g_queue
    val eq = R.drawable.g_eq; val more = R.drawable.g_more; val list = R.drawable.g_list; val radio = R.drawable.g_radio
    val podcast = R.drawable.g_podcast; val back = R.drawable.g_back; val star = R.drawable.g_star; val starFull = R.drawable.g_star_full
    val search = R.drawable.g_search; val timer = R.drawable.g_timer; val record = R.drawable.g_record; val plus = R.drawable.g_plus
    val folder = R.drawable.g_folder; val car = R.drawable.g_car; val gear = R.drawable.g_gear; val palette = R.drawable.g_palette
    val light = R.drawable.g_light; val trash = R.drawable.g_trash; val heart = R.drawable.g_heart; val up = R.drawable.g_up
    val down = R.drawable.g_down; val check = R.drawable.g_check; val location = R.drawable.g_location; val mail = R.drawable.g_mail
    val info = R.drawable.g_info; val chat = R.drawable.g_chat; val close = R.drawable.g_close; val volume = R.drawable.g_volume
    val reconnect = R.drawable.g_reconnect; val note = R.drawable.g_note; val fullscreen = R.drawable.g_fullscreen; val lock = R.drawable.g_lock
}

@Composable
fun G(id: Int, tint: Color, size: Dp = 24.dp, modifier: Modifier = Modifier) {
    Image(painterResource(id), null, modifier.size(size), colorFilter = ColorFilter.tint(tint))
}

@Composable
fun haptic(): () -> Unit {
    val h = LocalHapticFeedback.current
    return { if (Prefs.haptics.value) h.performHapticFeedback(HapticFeedbackType.TextHandleMove) }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
fun IconBtn(id: Int, tint: Color, size: Dp = 24.dp, pad: Dp = 10.dp, active: Boolean = false, accent: Color = ORANGE,
            onLong: (() -> Unit)? = null, onClick: () -> Unit) {
    val hp = haptic()
    Box(
        Modifier.clip(CircleShape).background(if (active) accent.copy(alpha = 0.22f) else Color.Transparent)
            .combinedClickable(onClick = { hp(); onClick() }, onLongClick = onLong?.let { l -> { hp(); l() } })
            .padding(pad),
        contentAlignment = Alignment.Center,
    ) { G(id, if (active) accent else tint, size) }
}

@Composable
fun Chip(text: String, on: Boolean, th: JTheme, onClick: () -> Unit) {
    val hp = haptic()
    Box(
        Modifier.padding(end = 8.dp, bottom = 8.dp).clip(RoundedCornerShape(16.dp))
            .background(if (on) th.accent else th.card).clickable { hp(); onClick() }
            .padding(horizontal = 14.dp, vertical = 8.dp),
    ) { Text(text, color = if (on) th.onAccent else th.text, fontSize = 13.sp, fontWeight = FontWeight.SemiBold, maxLines = 1) }
}

@Composable
fun Btn(text: String, th: JTheme, icon: Int? = null, primary: Boolean = false, modifier: Modifier = Modifier, onClick: () -> Unit) {
    val hp = haptic()
    Row(
        modifier.padding(end = 8.dp, bottom = 8.dp).clip(RoundedCornerShape(14.dp))
            .background(if (primary) th.accent else th.card).clickable { hp(); onClick() }
            .padding(horizontal = 14.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        if (icon != null) { G(icon, if (primary) th.onAccent else th.text, 18.dp); Spacer(Modifier.width(8.dp)) }
        Text(text, color = if (primary) th.onAccent else th.text, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
fun SectionTitle(text: String, th: JTheme) {
    Text(text, color = th.text, fontSize = 18.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(top = 18.dp, bottom = 8.dp))
}

@Composable
fun Card(th: JTheme, modifier: Modifier = Modifier, content: @Composable () -> Unit) {
    Column(modifier.fillMaxWidth().padding(bottom = 10.dp).clip(RoundedCornerShape(20.dp)).background(th.card).padding(14.dp)) { content() }
}

@Composable
fun SwitchRow(title: String, th: JTheme, value: Boolean, hint: String = "", onChange: (Boolean) -> Unit) {
    Row(Modifier.fillMaxWidth().clickable { onChange(!value) }.padding(vertical = 6.dp), verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) {
            Text(title, color = th.text, fontSize = 15.sp)
            if (hint.isNotBlank()) Text(hint, color = th.muted, fontSize = 12.sp)
        }
        Switch(value, onChange, colors = SwitchDefaults.colors(checkedTrackColor = th.accent, checkedThumbColor = th.onAccent))
    }
}

@Composable
fun SliderRow(title: String, th: JTheme, value: Float, range: ClosedFloatingPointRange<Float>, steps: Int = 0, label: String = "", onChange: (Float) -> Unit) {
    Column(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
        Row { Text(title, color = th.text, fontSize = 15.sp, modifier = Modifier.weight(1f)); Text(label, color = th.muted, fontSize = 13.sp) }
        Slider(value, onChange, valueRange = range, steps = steps,
            colors = SliderDefaults.colors(thumbColor = th.accent, activeTrackColor = th.accent, inactiveTrackColor = th.muted.copy(alpha = 0.3f)))
    }
}

/** Cover picture loaded lazily (only when the row is on screen). */
@Composable
fun Cover(uri: String, albumId: Long, size: Dp, th: JTheme, radius: Dp = 10.dp) {
    val ctx = LocalContext.current
    var bmp by remember(uri) { mutableStateOf<Bitmap?>(Art.cached("$uri#160")) }
    LaunchedEffect(uri) { if (bmp == null) bmp = Art.load(ctx, uri, albumId, 160) }
    Box(Modifier.size(size).clip(RoundedCornerShape(radius)).background(th.card), contentAlignment = Alignment.Center) {
        val b = bmp
        if (b != null) Image(b.asImageBitmap(), null, Modifier.size(size), contentScale = ContentScale.Crop)
        else G(Gl.note, th.muted, size * 0.5f)
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
fun Row2(title: String, sub: String, th: JTheme, selected: Boolean = false, leading: @Composable () -> Unit = {},
         trailing: @Composable () -> Unit = {}, onLong: (() -> Unit)? = null, onClick: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(14.dp)).background(if (selected) th.accent.copy(alpha = 0.18f) else Color.Transparent)
            .combinedClickable(onClick = onClick, onLongClick = onLong).padding(horizontal = 8.dp, vertical = 7.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        leading()
        Spacer(Modifier.width(12.dp))
        Column(Modifier.weight(1f)) {
            Text(title, color = if (selected) th.accent else th.text, fontSize = 15.sp, fontWeight = FontWeight.SemiBold, maxLines = 1, overflow = TextOverflow.Ellipsis)
            if (sub.isNotBlank()) Text(sub, color = th.muted, fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
        }
        trailing()
    }
}

@Composable
fun Swatch(c: Color, on: Boolean, th: JTheme, size: Dp = 36.dp, brush: androidx.compose.ui.graphics.Brush? = null, onClick: () -> Unit) {
    Box(
        Modifier.padding(end = 8.dp, bottom = 8.dp).size(size).clip(CircleShape)
            .then(if (brush != null) Modifier.background(brush) else Modifier.background(c))
            .border(if (on) 3.dp else 1.dp, if (on) th.text else th.muted.copy(alpha = 0.4f), CircleShape)
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center,
    ) { if (on) G(Gl.check, if (c.lum() > 0.6f) Color.Black else Color.White, size * 0.5f) }
}

@Composable
fun Gap(h: Dp = 8.dp) = Spacer(Modifier.height(h))

val Rows = Arrangement.spacedBy(4.dp)
