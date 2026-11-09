package com.tomstechsolutions.jukebox

import android.content.Context
import android.content.SharedPreferences
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.mutableStateOf
import org.json.JSONObject

/** A setting that is saved at once and that the screen redraws from. */
class Pref<T>(val key: String, val default: T) {
    val state: MutableState<T> = mutableStateOf(default)
    var value: T
        get() = state.value
        set(v) { state.value = v; Prefs.save(key, v) }

    @Suppress("UNCHECKED_CAST")
    fun load(sp: SharedPreferences) {
        state.value = when (default) {
            is Boolean -> sp.getBoolean(key, default) as T
            is Int -> sp.getInt(key, default) as T
            is Float -> sp.getFloat(key, default) as T
            is Long -> sp.getLong(key, default) as T
            is String -> (sp.getString(key, default) ?: default) as T
            else -> default
        }
    }
}

object Prefs {
    private lateinit var sp: SharedPreferences
    private val all = mutableListOf<Pref<*>>()
    private fun <T> p(key: String, d: T) = Pref(key, d).also { all += it }

    // look
    val lang = p("lang", "vi")
    val theme = p("theme", "toms")
    val customAccent = p("custom_accent", 0xFFFBB040.toInt())
    val skin = p("skin", "pill")
    val xpColour = p("xp_colour", "blue")
    val barColour = p("bar_colour", "#FBB040")
    val customBar = p("custom_bar", 0xFF48B0C8.toInt())
    val textScale = p("text_scale", 1.0f)
    val pillAlpha = p("pill_alpha", 1.0f)        // Độ Trong Suốt Viên Thuốc (1 = đặc)
    val waveStrength = p("wave_strength", 1.0f)  // Độ Đậm Sóng Nhạc
    val waveHeight = p("wave_height", 0.6f)      // Độ Cao Sóng
    val pillColour = p("pill_colour", 0)         // màu nền khi nhấp 2 lần
    val dblTapColour = p("dbl_tap_colour", true)
    val woodType = p("wood_type", 0)
    val marbleType = p("marble_type", 0)
    val btnStyle = p("btn_style", 0)
    val btnColour = p("btn_colour", "white")
    val btnCustom = p("btn_custom", 0xFFFFFFFF.toInt())
    val btnScale = p("btn_scale", 1.0f)
    val pack = p("pack", -1)                      // Bộ Chủ Đề đang chọn (-1 = chưa chọn)
    val favStyles = p("fav_styles", "")           // "picker|id" mỗi dòng
    val recentStyles = p("recent_styles", "")
    val miniSize = p("mini_size", "medium")       // viên thuốc dưới: small / medium / large
    val playerStyle = p("player_style", "card")   // trong app: card (Mặc Định (Tom's Tech)) / pill (Viên Thuốc)
    val lockStyle = p("lock_style", "card")       // màn hình khoá: card (Mặc Định (Tom's Tech)) / pill
    val navFx = p("nav_fx", "glow")               // hiệu ứng thanh điều hướng, nhiều kiểu cách nhau dấu phẩy
    val navHaptic = p("nav_haptic", true)
    val fxSpeed = p("fx_speed", 1.0f)
    val splashStyle = p("splash_style", 0)        // 0 Icon Nở Ra .. 4 Theo Màu Ảnh Bìa, 5 Ngẫu Nhiên
    val splashOn = p("splash_on", true)
    val splashFast = p("splash_fast", false)
    val splashHaptic = p("splash_haptic", true)
    val chipsAutoHide = p("chips_auto_hide", true)
    val libChip = p("lib_chip", 0)
    // visualisations
    val viz = p("viz", 0)
    val vizAuto = p("viz_auto", false)
    val vizOn = p("viz_on", true)
    val vizPill = p("viz_pill", true)
    val vizStrip = p("viz_strip", true)
    val vizNav = p("viz_nav", true)
    val realViz = p("real_viz", false)
    val vizSpeed = p("viz_speed", 1.0f)
    // edge lighting
    val edgeOn = p("edge_on", true)
    val edgeEffect = p("edge_effect", 0)
    val edgeSpeed = p("edge_speed", 2)          // 0 very slow .. 4 very fast
    val edgeColour = p("edge_colour", "cover")  // cover / rainbow / brand / custom
    val edgeCustom = p("edge_custom", 0xFF48B0C8.toInt())
    val edgeThick = p("edge_thick", 4f)
    val edgeBright = p("edge_bright", 0.9f)
    val edgeWhere = p("edge_where", "both")     // window / pill / both
    val edgeBeat = p("edge_beat", true)
    val edgeAuto = p("edge_auto", false)
    val edgeScreen = p("edge_screen", true)
    val edgeRandom = p("edge_random", false)
    val edgeCorner = p("edge_corner", -1f)       // -1 = tự lấy theo màn hình
    // sound
    val eqPreset = p("eq_preset", "flat")
    val eqCustom = p("eq_custom", "")          // json name -> 10 gains
    val eqBands = p("eq_bands", "0,0,0,0,0,0,0,0,0,0")
    val eqAutoGenre = p("eq_auto_genre", false)
    val eqOn = p("eq_on", true)
    val bass = p("bass", 0)
    val treble = p("treble", 0)
    // sleep timer (last setting)
    val sleepMinutes = p("sleep_minutes", 30)
    val sleepFade = p("sleep_fade", 60)
    val sleepBluetooth = p("sleep_bt", false)
    // gestures and phone things
    val haptics = p("haptics", true)
    val shakeSkip = p("shake_skip", false)
    val swipePill = p("swipe_pill", true)
    val autoPlayHeadset = p("autoplay_headset", false)
    val customLock = p("custom_lock", false)
    val lockY = p("lock_y", -1f)                  // vị trí viên thuốc màn hình khoá (0..1, -1 = dưới cùng)
    val lockX = p("lock_x", 0.5f)
    val lockYLand = p("lock_y_land", -1f)
    val lockXLand = p("lock_x_land", 0.5f)
    val lockLocked = p("lock_locked", false)
    val lockSnap = p("lock_snap", true)
    val lockSize = p("lock_size", "medium")
    val lockAlpha = p("lock_alpha", 1.0f)
    val widgetBg = p("widget_bg", "skin")         // skin / cover / clear / frost / you
    val widgetAlpha = p("widget_alpha", 0.85f)
    val batterySaver = p("battery_saver", true)
    val spinBeat = p("spin_beat", true)
    val blurBg = p("blur_bg", true)
    val headsetTriple = p("headset_triple", true)
    // radio
    val radioState = p("radio_state", "VIC")
    val radioAutoState = p("radio_auto_state", true)
    val radioHq = p("radio_hq", false)
    val recFolder = p("rec_folder", "")
    // library
    val folders = p("folders", "")              // tree uris, one per line
    val favourites = p("favourites", "")        // uris, one per line
    val hidden = p("hidden", "")                // songs hidden from the library
    val podcasts = p("podcasts", "[]")
    val podNotify = p("pod_notify", "")           // id kênh báo tập mới, mỗi dòng
    val podAutoDl = p("pod_auto_dl", "")          // id kênh tự tải
    val podKeep = p("pod_keep", 5)
    val podSpeed = p("pod_speed", "{}")           // id -> tốc độ
    val podSkip = p("pod_skip", "{}")             // id -> giây bỏ qua đầu
    val podHidden = p("pod_hidden", "")
    val podPlayed = p("pod_played", "")           // url tập đã nghe
    val podSeen = p("pod_seen", "{}")             // feed -> tập mới nhất đã thấy
    val podNew = p("pod_new", "")                 // feed có tập mới chưa mở (chấm đỏ trên widget)
    val radioFavs = p("radio_favs", "")
    val podHQ = p("pod_hq", true)
    val waveCols = p("wave_cols", "vivid")        // màu sóng trên thanh thời gian (giao diện Mặc Định)
    val waveShape = p("wave_shape", 0)            // 0 đồi mềm · 1 dải lụa · 2 đối xứng phát sáng · 3 cột bo tròn                 // tải bản chất lượng cao nhất kênh có
    val podAutoSave = p("pod_auto_save", "")      // ⏰ kênh tự lưu tập mới vào Bản Thâu Âm
    val podSavedUrls = p("pod_saved_urls", "")           // tên đài yêu thích, mỗi dòng
    val playlists = p("playlists", "{}")
    val lastQueue = p("last_queue", "[]")
    val lastIndex = p("last_index", 0)
    val lastPos = p("last_pos", 0L)
    val shortcuts = p("shortcuts", "")
    val lastBackup = p("last_backup", 0L)

    fun init(ctx: Context) {
        sp = ctx.getSharedPreferences("tomsjukebox", Context.MODE_PRIVATE)
        all.forEach { it.load(sp) }
    }

    fun save(key: String, v: Any?) {
        val e = sp.edit()
        when (v) {
            is Boolean -> e.putBoolean(key, v)
            is Int -> e.putInt(key, v)
            is Float -> e.putFloat(key, v)
            is Long -> e.putLong(key, v)
            is String -> e.putString(key, v)
        }
        e.apply()
    }

    fun toJson(): JSONObject {
        val o = JSONObject()
        all.forEach { o.put(it.key, it.value) }
        return o
    }

    @Suppress("UNCHECKED_CAST")
    fun fromJson(o: JSONObject) {
        all.forEach { pr ->
            if (!o.has(pr.key)) return@forEach
            val p = pr as Pref<Any?>
            p.value = when (p.default) {
                is Boolean -> o.optBoolean(p.key, p.default)
                is Int -> o.optInt(p.key, p.default)
                is Float -> o.optDouble(p.key, (p.default as Float).toDouble()).toFloat()
                is Long -> o.optLong(p.key, p.default)
                is String -> o.optString(p.key, p.default)
                else -> p.default
            }
        }
    }

    fun hiddenSet(): Set<String> = hidden.value.split('\n').filter { it.isNotBlank() }.toSet()
    fun hide(uris: Collection<String>) { hidden.value = (hiddenSet() + uris).joinToString("\n") }
    fun unhide(uri: String) { hidden.value = (hiddenSet() - uri).joinToString("\n") }
    fun removeFav(uris: Collection<String>) { favourites.value = (favSet() - uris.toSet()).joinToString("\n") }

    fun favSet(): Set<String> = favourites.value.split('\n').filter { it.isNotBlank() }.toSet()
    fun toggleFav(uri: String): Boolean {
        val s = favSet().toMutableSet()
        val now = if (uri in s) { s.remove(uri); false } else { s.add(uri); true }
        favourites.value = s.joinToString("\n")
        return now
    }
}
