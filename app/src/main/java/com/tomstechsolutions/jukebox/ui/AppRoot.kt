package com.tomstechsolutions.jukebox.ui

import android.os.Build
import androidx.activity.compose.BackHandler
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.Crossfade
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.R
import com.tomstechsolutions.jukebox.data.Messages
import com.tomstechsolutions.jukebox.playback.Core
import com.tomstechsolutions.jukebox.t
import kotlinx.coroutines.delay
import kotlin.math.exp
import kotlin.math.min

@Composable
fun JukeboxApp(act: MainActivity) {
    val th = Themes.current()
    val scheme = if (th.light) lightColorScheme(primary = th.accent, background = th.top, surface = th.card, onSurface = th.text)
    else darkColorScheme(primary = th.accent, background = th.top, surface = Color(0xFF16242E), onSurface = th.text)
    val d = LocalDensity.current
    CompositionLocalProvider(LocalDensity provides Density(d.density, d.fontScale * Prefs.textScale.state.value)) {
        MaterialTheme(colorScheme = scheme) { AppBody(act, th) }
    }
}

@Composable
private fun AppBody(act: MainActivity, th: JTheme) {
    var splash by remember { mutableStateOf(true) }
    var driving by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) { delay(1300); splash = false }
    BackHandler(act.openNow.value) { act.openNow.value = false }
    BackHandler(driving) { driving = false }

    BoxWithConstraints(Modifier.fillMaxSize().background(th.bg)) {
        val wide = maxWidth >= 600.dp
        val art = Core.art.value
        if (Prefs.blurBg.value && art != null && !th.light) {
            val m = if (Build.VERSION.SDK_INT >= 31) Modifier.fillMaxSize().blur(60.dp) else Modifier.fillMaxSize()
            Image(art.asImageBitmap(), null, m, contentScale = ContentScale.Crop, alpha = if (Build.VERSION.SDK_INT >= 31) 0.35f else 0.12f)
            Box(Modifier.fillMaxSize().background(Brush.verticalGradient(listOf(th.top.copy(alpha = 0.55f), th.bottom.copy(alpha = 0.92f)))))
        }
        if (wide) {
            // landscape / DeX / unfolded: Now Playing on the left, lists on the right
            Row(Modifier.fillMaxSize().windowInsetsPadding(WindowInsets.safeDrawing)) {
                Box(Modifier.weight(0.42f).fillMaxHeight()) { NowPlayingScreen(act, th, embedded = true, onClose = {}, onDriving = { driving = true }) }
                Column(Modifier.weight(0.58f).fillMaxHeight()) {
                    Header(act, th)
                    Box(Modifier.weight(1f)) { Tabs(act, th) }
                    BottomNav(act, th)
                }
            }
        } else {
            Column(Modifier.fillMaxSize().windowInsetsPadding(WindowInsets.safeDrawing)) {
                Header(act, th)
                Box(Modifier.weight(1f)) { Tabs(act, th) }
                Pill(Modifier.padding(horizontal = 10.dp, vertical = 6.dp), big = false, onOpen = { act.openNow.value = true }, onLong = { act.showSleep.value = true })
                BottomNav(act, th)
            }
        }
        if (Prefs.edgeOn.value && Prefs.edgeScreen.value && Prefs.edgeWhere.value != "pill") EdgeLight(Modifier.fillMaxSize(), 30.dp)

        AnimatedVisibility(act.openNow.value && !wide, enter = slideInVertically { it } + fadeIn(), exit = slideOutVertically { it } + fadeOut()) {
            NowPlayingScreen(act, th, embedded = false, onClose = { act.openNow.value = false }, onDriving = { driving = true })
        }
        AnimatedVisibility(driving, enter = fadeIn(), exit = fadeOut()) { DrivingScreen(th) { driving = false } }
        if (act.showSleep.value) SleepDialog(th) { act.showSleep.value = false }
        AnimatedVisibility(splash, enter = fadeIn(), exit = fadeOut()) { Splash() }
    }
}

@Composable
private fun Tabs(act: MainActivity, th: JTheme) {
    Crossfade(act.tab.intValue, label = "tabs") { tab ->
        when (tab) {
            0 -> LibraryScreen(act, th)
            1 -> RadioScreen(act, th)
            2 -> PodcastScreen(th)
            3 -> EqScreen(act, th)
            else -> MoreScreen(act, th)
        }
    }
}

@Composable
fun Header(act: MainActivity, th: JTheme) {
    Row(Modifier.fillMaxWidth().padding(start = 16.dp, end = 8.dp, top = 6.dp, bottom = 2.dp), verticalAlignment = Alignment.CenterVertically) {
        Image(painterResource(R.drawable.app_logo), null, Modifier.size(32.dp))
        Spacer(Modifier.width(8.dp))
        Column(Modifier.weight(1f)) {
            Text(buildAnnotatedString {
                withStyle(SpanStyle(color = SKY)) { append("TOM'S ") }
                withStyle(SpanStyle(color = ORANGE)) { append("JUKEBOX") }
            }, fontSize = 19.sp, fontWeight = FontWeight.Black)
            if (Prefs.textScale.value < 1.2f) Text("Focus On One Thing And Do It Well", color = th.muted, fontSize = 10.sp, maxLines = 1)
        }
        val unread = Messages.unread()
        Box {
            IconBtn(Gl.chat, th.muted) { act.tab.intValue = 4 }
            if (unread > 0) Box(Modifier.align(Alignment.TopEnd).padding(6.dp).size(16.dp).clip(RoundedCornerShape(8.dp)).background(Color(0xFFE53935)),
                contentAlignment = Alignment.Center) { Text("$unread", color = Color.White, fontSize = 9.sp) }
        }
        IconBtn(Gl.timer, if (Core.sleepMode.value != "NONE") th.accent else th.muted) { act.showSleep.value = true }
    }
}

@Composable
fun BottomNav(act: MainActivity, th: JTheme) {
    val items = listOf(Gl.list to t("Library", "Thư Viện"), Gl.radio to "Radio", Gl.podcast to "Podcast", Gl.eq to t("Sound", "Chỉnh Âm"), Gl.more to t("More", "Thêm"))
    val clock by rememberClock()
    Box(Modifier.fillMaxWidth().background(th.nav)) {
        // little music wave along the top edge of the bar
        Canvas(Modifier.fillMaxWidth().height(10.dp)) {
            if (!Core.playing.value || Anim.lowPower.value) return@Canvas
            val lv = levelsAt(clock); val cols = Core.palette.value
            val p = Path().apply { moveTo(0f, 0f) }
            for (k in 0..48) {
                val fx = k / 48f
                var y = 0f
                for (b in 0 until 5) y += lv[(b * 4) % 24] * exp(-((fx - (b * 0.22f + 0.05f + clock * 0.02f) % 1.1f) / 0.07f).let { it * it })
                p.lineTo(fx * size.width, min(1f, y) * size.height)
            }
            p.lineTo(size.width, 0f); p.close()
            drawPath(p, Brush.horizontalGradient(cols.map { Color(it).copy(alpha = 0.55f) }))
        }
        Row(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
            items.forEachIndexed { i, (ic, label) ->
                val on = act.tab.intValue == i
                val hp = haptic()
                Column(Modifier.weight(1f).clip(RoundedCornerShape(16.dp)).clickable { hp(); act.tab.intValue = i }.padding(vertical = 4.dp),
                    horizontalAlignment = Alignment.CenterHorizontally) {
                    Box(Modifier.clip(RoundedCornerShape(15.dp)).background(if (on) th.accent.copy(alpha = 0.18f) else Color.Transparent)
                        .padding(horizontal = 16.dp, vertical = 4.dp)) { G(ic, if (on) th.accent else th.muted, 22.dp) }
                    Text(label, color = if (on) th.accent else th.muted, fontSize = 11.sp, fontWeight = if (on) FontWeight.Bold else FontWeight.Normal, maxLines = 1)
                }
            }
        }
    }
}

@Composable
fun Splash() {
    Box(Modifier.fillMaxSize().background(Brush.verticalGradient(listOf(NAVY, NAVY_D))), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Image(painterResource(R.drawable.app_logo), null, Modifier.size(120.dp))
            Spacer(Modifier.height(16.dp))
            Text(buildAnnotatedString {
                withStyle(SpanStyle(color = SKY)) { append("TOM'S ") }
                withStyle(SpanStyle(color = ORANGE)) { append("JUKEBOX") }
            }, fontSize = 32.sp, fontWeight = FontWeight.Black)
            Text("Focus On One Thing And Do It Well", color = SPLASH_TEXT, fontSize = 14.sp)
            Spacer(Modifier.height(10.dp))
            Text(t("Music · Radio · Podcasts · Lyrics · Recording", "Nhạc · Radio · Podcast · Lời Bài Hát · Thâu Âm"), color = SPLASH_TEXT.copy(alpha = 0.8f), fontSize = 13.sp)
            Spacer(Modifier.height(40.dp))
            Text("One of Tom's Technology Solutions Products", color = ORANGE, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
        }
    }
}

