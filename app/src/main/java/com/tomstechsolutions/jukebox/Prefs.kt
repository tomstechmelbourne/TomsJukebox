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
    // visualisations
    val viz = p("viz", 0)
    val vizAuto = p("viz_auto", false)
    val realViz = p("real_viz", false)
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
    val podcasts = p("podcasts", "[]")
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

    fun favSet(): Set<String> = favourites.value.split('\n').filter { it.isNotBlank() }.toSet()
    fun toggleFav(uri: String): Boolean {
        val s = favSet().toMutableSet()
        val now = if (uri in s) { s.remove(uri); false } else { s.add(uri); true }
        favourites.value = s.joinToString("\n")
        return now
    }
}
