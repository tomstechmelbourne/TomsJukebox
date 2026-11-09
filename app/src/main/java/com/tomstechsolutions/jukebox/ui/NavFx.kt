package com.tomstechsolutions.jukebox.ui

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.animation.expandHorizontally
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkHorizontally
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.BlendMode
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.CompositingStrategy
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.R
import com.tomstechsolutions.jukebox.playback.Core
import com.tomstechsolutions.jukebox.t
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.exp
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin

/** The 8 tap effects for the bottom navigation bar. */
object NavFx {
    val list = listOf(
        "glow" to ("Light Up" to "Sáng Lên"), "slide" to ("Sliding Pill" to "Viên Thuốc Trượt"), "bounce" to ("Bounce" to "Nảy Nhẹ"),
        "ripple" to ("Ripple" to "Gợn Sóng"), "streak" to ("Running Light" to "Vệt Sáng Chạy"), "icon" to ("Icon Change" to "Đổi Icon"),
        "dot" to ("Light Dot" to "Chấm Sáng Dưới"), "label" to ("Name Slides Out" to "Tên Hiện Ra"),
    )
    fun on(k: String) = k in Prefs.navFx.value.split(',')
    fun toggle(k: String) {
        val s = Prefs.navFx.value.split(',').filter { it.isNotBlank() }.toMutableSet()
        if (k in s) s.remove(k) else s.add(k)
        Prefs.navFx.value = s.joinToString(",")
    }
    fun ms(base: Int) = (base / Prefs.fxSpeed.value.coerceIn(0.4f, 2.5f)).toInt()
}

@Composable
fun BottomNav(act: MainActivity, th: JTheme) {
    val items = listOf(Gl.list to t("Library", "Thư Viện"), Gl.radio to "Radio", Gl.podcast to "Podcast", Gl.eq to t("Sound", "Chỉnh Âm"), Gl.more to t("More", "Thêm"))
    val clock by rememberClock()
    val sel = act.tab.intValue
    val pos by animateFloatAsState(sel.toFloat(), if (NavFx.on("slide") || NavFx.on("dot")) spring(dampingRatio = 0.7f, stiffness = Spring.StiffnessMediumLow) else tween(0), label = "navpos")
    val glowCol = Color(Core.palette.value[0]).let { if (it.lum() < 0.15f) th.accent else it }
    val hpf = LocalHapticFeedback.current
    Box(Modifier.fillMaxWidth().background(th.nav)) {
        // little music wave along the top edge of the bar
        Canvas(Modifier.fillMaxWidth().height(10.dp)) {
            if (!Core.playing.value || Anim.lowPower.value || !Prefs.vizOn.value || !Prefs.vizNav.value) return@Canvas
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
        // sliding pill and dot under the chosen page
        Canvas(Modifier.matchParentSize()) {
            val iw = size.width / items.size; val cx = (pos + 0.5f) * iw
            if (NavFx.on("slide")) drawRoundRect(th.accent.copy(alpha = 0.2f), Offset(cx - iw * 0.4f, 8.dp.toPx()), Size(iw * 0.8f, size.height - 16.dp.toPx()), CornerRadius(20.dp.toPx()))
            if (NavFx.on("dot")) {
                drawCircle(glowCol.copy(alpha = 0.35f), 7.dp.toPx(), Offset(cx, size.height - 6.dp.toPx()))
                drawCircle(glowCol, 3.dp.toPx(), Offset(cx, size.height - 6.dp.toPx()))
            }
        }
        Row(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
            items.forEachIndexed { i, (ic, label) ->
                val on = sel == i
                val scale = remember { Animatable(1f) }
                val spin = remember { Animatable(0f) }
                val ring = remember { Animatable(1f) }
                LaunchedEffect(on) {
                    if (!on) return@LaunchedEffect
                    if (NavFx.on("ripple")) { ring.snapTo(0f); ring.animateTo(1f, tween(NavFx.ms(650), easing = LinearEasing)) }
                }
                LaunchedEffect(on) {
                    if (on && NavFx.on("bounce")) { scale.animateTo(1.3f, tween(NavFx.ms(110))); scale.animateTo(1f, spring(dampingRatio = 0.35f, stiffness = Spring.StiffnessMedium)) }
                }
                LaunchedEffect(on) {
                    if (on && NavFx.on("icon")) { spin.snapTo(0f); spin.animateTo(1f, tween(NavFx.ms(700))) }
                }
                Column(Modifier.weight(1f).clip(RoundedCornerShape(16.dp)).clickable(remember { MutableInteractionSource() }, null) {
                    if (Prefs.navHaptic.value && Prefs.haptics.value) hpf.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                    act.tab.intValue = i
                }.padding(vertical = 4.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                    val iconFx = on && NavFx.on("icon")
                    val p = spin.value
                    Box(Modifier
                        .drawBehind {
                            if (on && NavFx.on("glow")) drawCircle(Brush.radialGradient(listOf(glowCol.copy(alpha = 0.55f), Color.Transparent), center, size.maxDimension * 0.75f), size.maxDimension * 0.75f)
                            if (on && !NavFx.on("slide")) drawRoundRect(th.accent.copy(alpha = if (iconFx) 0.32f else 0.18f), cornerRadius = CornerRadius(15.dp.toPx()))
                            if (on && NavFx.on("ripple") && ring.value < 1f) drawCircle(glowCol.copy(alpha = (1 - ring.value) * 0.7f), size.maxDimension * (0.3f + ring.value * 0.9f), style = Stroke(3.dp.toPx()))
                            if (on && NavFx.on("streak")) drawEdge(0, clock, 15.dp.toPx(), listOf(glowCol, th.accent), 2.dp.toPx(), 1f, 1.4f * Prefs.fxSpeed.value)
                            if (iconFx && i == 1 && p < 1f) for (k in 0..2) { val f = ((p * 1.5f + k * 0.25f) % 1f)   // Radio: sóng phát ra
                                drawArc(glowCol.copy(alpha = 1 - f), -60f, 120f, false, Offset(center.x - size.height * (0.4f + f), center.y - size.height * (0.4f + f)), Size(size.height * (0.8f + 2 * f), size.height * (0.8f + 2 * f)), style = Stroke(2.dp.toPx())) }
                        }
                        .padding(horizontal = 16.dp, vertical = 4.dp)
                        .graphicsLayer {
                            scaleX = scale.value; scaleY = scale.value
                            if (iconFx) when (i) {
                                0 -> rotationZ = p * 360f                                       // Thư Viện: đĩa xoay một vòng
                                2 -> rotationZ = sin(p * PI.toFloat() * 6) * 14f * (1 - p)       // Podcast: micro rung nhẹ
                                3 -> { val k = 1f + sin(p * PI.toFloat()) * 0.18f; scaleY = scale.value * k }   // Chỉnh Âm: nhún
                                4 -> rotationZ = p * 180f
                            }
                        }) { G(ic, if (on) th.accent else th.muted, 22.dp) }
                    val showLabel = !NavFx.on("label") || on
                    AnimatedVisibility(showLabel, enter = fadeIn() + expandHorizontally(), exit = fadeOut() + shrinkHorizontally()) {
                        Text(label, color = if (on) th.accent else th.muted, fontSize = 11.sp, fontWeight = if (on) FontWeight.Bold else FontWeight.Normal, maxLines = 1)
                    }
                }
            }
        }
    }
}

/** Màn hình mở app: 5 kiểu + Ngẫu Nhiên, theo phong cách Pixel mới (icon động, nở ra thành app). */
object SplashFx {
    val names = listOf("Icon Blooms Open" to "Icon Nở Ra", "Disc Spins In" to "Đĩa Quay Vào", "Music Wave Wake-Up" to "Sóng Nhạc Đánh Thức",
        "Morphing Shape" to "Hình Khối Biến Hình", "Album Cover Colour" to "Theo Màu Ảnh Bìa", "Random" to "Ngẫu Nhiên")
    fun name(i: Int) = names.getOrNull(i)?.let { t(it.first, it.second) } ?: ""
}

@Composable
fun AnimatedSplash(styleIn: Int, onDone: () -> Unit) {
    val style = remember { if (styleIn == 5) (0..4).random() else styleIn.coerceIn(0, 4) }
    val total = if (Prefs.splashFast.value) 950 else 1600
    val p = remember { Animatable(0f) }
    val hpf = LocalHapticFeedback.current
    LaunchedEffect(Unit) {
        p.animateTo(0.42f, tween((total * 0.42f).toInt()))
        if (Prefs.splashHaptic.value && Prefs.haptics.value) hpf.performHapticFeedback(HapticFeedbackType.LongPress)
        p.animateTo(1f, tween((total * 0.58f).toInt(), easing = LinearEasing))
        onDone()
    }
    val v = p.value
    val bg = if (style == 4) Core.palette.value.map { Color(it) }.let { listOf(it[0].darken(0.7f), it.getOrElse(1) { it[0] }.darken(0.35f)) } else listOf(NAVY, NAVY_D)
    val corner = screenCorner()
    // phase 1 (0..0.42): the icon appears with a springy bounce; phase 2: it opens into the app
    val pop = if (v < 0.42f) { val f = v / 0.42f; 0.4f + 0.75f * f - 0.15f * sin(f * PI.toFloat()) * (1 - f) + sin(f * PI.toFloat() * 2.5f) * 0.12f * (1 - f) } else 1f
    val open = ((v - 0.42f) / 0.58f).coerceIn(0f, 1f)
    BoxWithConstraints(Modifier.fillMaxSize().graphicsLayer { compositingStrategy = CompositingStrategy.Offscreen; alpha = if (style == 1) 1f - open else 1f }) {
        Canvas(Modifier.fillMaxSize()) {
            drawRect(Brush.verticalGradient(bg))
            val c = center; val maxR = kotlin.math.hypot(size.width, size.height) / 2
            when (style) {
                2 -> {                                                  // rings, then light around the screen
                    for (k in 0..2) { val f = ((v * 2.2f - k * 0.18f).coerceIn(0f, 1f)); if (f > 0f && f < 1f) drawCircle(ORANGE.copy(alpha = 1 - f), 60.dp.toPx() + f * size.minDimension * 0.6f, c, style = Stroke(3.dp.toPx())) }
                    if (v > 0.3f) drawEdge(0, v * 6f, corner.toPx(), listOf(SKY, ORANGE), 4.dp.toPx(), (1 - open).coerceIn(0f, 1f), 1.6f)
                }
                3 -> {                                                  // morphing shape behind the icon
                    val k = listOf(0f, 8f, 5f, 4f)[((v * 8).toInt()) % 4]; val r0 = 78.dp.toPx() * pop
                    val path = Path(); for (a in 0..120) { val th0 = a / 120f * 2 * PI.toFloat(); val rr = r0 * (1 + 0.09f * cos(k * th0 + v * 6)); val pt = Offset(c.x + cos(th0) * rr, c.y + sin(th0) * rr); if (a == 0) path.moveTo(pt.x, pt.y) else path.lineTo(pt.x, pt.y) }
                    path.close(); drawPath(path, SKY.copy(alpha = 0.3f))
                }
                1 -> for (k in 0 until 6) {                             // music notes rising
                    val f = ((v * 1.6f + k * 0.17f) % 1f); val x = c.x + (k - 2.5f) * 26.dp.toPx(); val y = c.y + 40.dp.toPx() - f * 160.dp.toPx()
                    drawCircle(ORANGE.copy(alpha = 1 - f), 5.dp.toPx(), Offset(x, y)); drawLine(ORANGE.copy(alpha = 1 - f), Offset(x + 5.dp.toPx(), y), Offset(x + 5.dp.toPx(), y - 16.dp.toPx()), 2.dp.toPx())
                }
                else -> drawCircle(Brush.radialGradient(listOf(ORANGE.copy(alpha = 0.35f), Color.Transparent), c, 150.dp.toPx() * pop), 150.dp.toPx() * pop, c)
            }
            // the "bloom": a growing hole shows the app underneath
            if (open > 0f && style != 1) drawCircle(Color.Black, maxR * open * open, c, blendMode = BlendMode.Clear)
        }
        val iconAlpha = if (style == 1) 1f - open else (1f - open * 1.6f).coerceIn(0f, 1f)
        val iconScale = if (style == 1) pop * (1f - open * 0.6f) else pop * (1f + open * 1.4f)
        Column(Modifier.fillMaxSize(), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = androidx.compose.foundation.layout.Arrangement.Center) {
            Image(painterResource(R.drawable.app_logo), null, Modifier.size(120.dp).graphicsLayer {
                scaleX = iconScale; scaleY = iconScale; alpha = iconAlpha
                rotationZ = if (style == 1) v * 360f else 0f
                translationY = if (style == 1) open * 300f else 0f
            })
            Spacer(Modifier.height(16.dp))
            Text(buildAnnotatedString {
                withStyle(SpanStyle(color = SKY)) { append("TOM'S ") }
                withStyle(SpanStyle(color = ORANGE)) { append("JUKEBOX") }
            }, fontSize = 30.sp, fontWeight = FontWeight.Black, modifier = Modifier.graphicsLayer { alpha = (min(1f, v * 3f) - open * 2f).coerceIn(0f, 1f) })
            Text("Focus On One Thing And Do It Well", color = SPLASH_TEXT, fontSize = 13.sp, modifier = Modifier.graphicsLayer { alpha = (min(1f, v * 2.5f - 0.3f) - open * 2f).coerceIn(0f, 1f) })
        }
    }
}
