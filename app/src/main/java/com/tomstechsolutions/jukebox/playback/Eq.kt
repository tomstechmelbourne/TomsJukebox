package com.tomstechsolutions.jukebox.playback

import android.media.audiofx.BassBoost
import android.media.audiofx.Equalizer
import android.media.audiofx.LoudnessEnhancer
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.t
import org.json.JSONObject
import kotlin.math.ln

data class EqPreset(val key: String, val en: String, val vi: String, val gains: FloatArray) {
    val name: String get() = t(en, vi)
}

object EqPresets {
    val FREQS = intArrayOf(31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000)
    private fun g(vararg v: Number) = FloatArray(10) { v[it].toFloat() }
    val builtIn = listOf(
        EqPreset("flat", "Flat", "Phẳng", g(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)),
        EqPreset("rock", "Rock", "Rock", g(5, 4, 3, 1, -1, -1, 1, 3, 4, 5)),
        EqPreset("pop", "Pop", "Pop", g(-1, 1, 3, 4, 3, 1, -1, -1, 1, 2)),
        EqPreset("jazz", "Jazz", "Jazz", g(3, 2, 1, 2, -1, -1, 0, 1, 2, 3)),
        EqPreset("classical", "Classical", "Cổ Điển", g(4, 3, 2, 1, -1, -1, 0, 2, 3, 4)),
        EqPreset("bass", "Bass Boost", "Tăng Bass", g(7, 6, 5, 3, 1, 0, 0, 0, 0, 0)),
        EqPreset("treble", "Treble Boost", "Tăng Treble", g(0, 0, 0, 0, 0, 1, 2, 4, 6, 7)),
        EqPreset("vocal", "Vocal", "Giọng Hát", g(-2, -2, -1, 1, 3, 4, 4, 2, 0, -1)),
        EqPreset("bolero", "Bolero", "Bolero", g(2, 2, 1, 1, 2, 3, 3, 2, 1, 1)),
        EqPreset("dance", "Dance", "Dance", g(6, 5, 2, 0, 0, -2, -1, 2, 4, 4)),
        EqPreset("hiphop", "Hip-Hop", "Hip-Hop", g(6, 5, 2, 3, -1, -1, 1, 0, 2, 3)),
        EqPreset("acoustic", "Acoustic", "Acoustic", g(3, 3, 2, 1, 1, 1, 2, 3, 2, 1)),
        EqPreset("piano", "Piano", "Piano", g(2, 1, 0, 2, 3, 1, 3, 4, 2, 2)),
        EqPreset("electronic", "Electronic", "Điện Tử", g(5, 4, 1, 0, -2, 2, 1, 1, 4, 5)),
        EqPreset("cailuong", "Cải Lương / Folk", "Cải Lương / Dân Ca", g(0, 1, 1, 2, 3, 3, 2, 3, 2, 0)),
        EqPreset("headphones", "Headphones", "Tai Nghe", g(4, 3, 1, 0, -1, 0, 1, 2, 3, 2)),
        EqPreset("laptop", "Small Speakers", "Loa Laptop", g(-4, -2, 2, 4, 3, 2, 2, 3, 2, 1)),
        EqPreset("night", "Late Night", "Đêm Khuya", g(-3, -2, -1, 0, 1, 2, 2, 1, -1, -3)),
        EqPreset("bass_light", "Light Bass", "Bass Nhẹ", g(3, 3, 2, 1, 0, 0, 0, 0, 0, 0)),
        EqPreset("bass_super", "Super Bass", "Siêu Bass", g(10, 9, 7, 4, 1, 0, 0, 0, 0, 0)),
        EqPreset("bass_cut", "Less Bass", "Giảm Bass", g(-6, -5, -4, -2, 0, 0, 0, 0, 0, 0)),
        EqPreset("treble_light", "Light Treble", "Treble Nhẹ", g(0, 0, 0, 0, 0, 0, 1, 2, 3, 3)),
        EqPreset("treble_super", "Super Treble", "Siêu Treble", g(0, 0, 0, 0, 0, 1, 3, 6, 8, 9)),
        EqPreset("treble_cut", "Less Treble", "Giảm Treble", g(0, 0, 0, 0, 0, 0, -1, -3, -5, -6)),
        EqPreset("vshape", "Bass + Treble", "Bass + Treble", g(7, 6, 3, 0, -2, -2, 0, 3, 6, 7)),
        EqPreset("loud", "Louder", "Tăng Âm Lượng", g(1, 1, 0, 0, 0, 0, 0, 0, 1, 1)),
        EqPreset("voice", "Clear Voice", "Rõ Giọng Nói", g(-4, -3, -1, 1, 4, 5, 5, 3, 0, -2)),
        EqPreset("car", "In The Car", "Trong Xe Hơi", g(5, 4, 2, 0, -1, 0, 2, 3, 3, 2)),
        EqPreset("bt_speaker", "Bluetooth Speaker", "Loa Bluetooth", g(5, 4, 3, 2, 0, 0, 1, 2, 2, 1)),
        EqPreset("hall", "Concert Hall", "Hội Trường", g(3, 2, 1, 0, 1, 2, 3, 3, 4, 4)),
    )

    fun custom(): List<EqPreset> = try {
        val o = JSONObject(Prefs.eqCustom.value.ifBlank { "{}" })
        o.keys().asSequence().map { k ->
            val a = o.getJSONArray(k); EqPreset("c:$k", k, k, FloatArray(10) { a.optDouble(it, 0.0).toFloat() })
        }.toList()
    } catch (_: Exception) { emptyList() }

    fun saveCustom(name: String, gains: FloatArray) {
        val o = try { JSONObject(Prefs.eqCustom.value.ifBlank { "{}" }) } catch (_: Exception) { JSONObject() }
        o.put(name, org.json.JSONArray(gains.map { it.toDouble() }))
        Prefs.eqCustom.value = o.toString()
    }

    fun all() = builtIn + custom()
    fun byKey(k: String) = all().firstOrNull { it.key == k }

    fun forGenre(genre: String): String? {
        val g = genre.lowercase()
        return when {
            "rock" in g || "metal" in g -> "rock"
            "hip" in g || "rap" in g -> "hiphop"
            "dance" in g || "edm" in g || "house" in g -> "dance"
            "electr" in g || "techno" in g || "trance" in g -> "electronic"
            "jazz" in g || "blues" in g -> "jazz"
            "classic" in g || "opera" in g -> "classical"
            "acoustic" in g || "folk" in g -> "acoustic"
            "piano" in g -> "piano"
            "bolero" in g || "trữ tình" in g || "tru tinh" in g -> "bolero"
            "cải lương" in g || "cai luong" in g || "dân ca" in g -> "cailuong"
            "ballad" in g || "vocal" in g -> "vocal"
            "pop" in g -> "pop"
            else -> null
        }
    }

    fun currentGains(): FloatArray =
        Prefs.eqBands.value.split(',').mapNotNull { it.trim().toFloatOrNull() }.let { l -> FloatArray(10) { l.getOrElse(it) { 0f } } }
}

/** Android's own sound effects attached to the player's audio session. Phones have 5 (or more) bands, so the 10
 *  sliders are spread over them on a log-frequency scale. */
class EqEngine {
    private var eq: Equalizer? = null
    private var bass: BassBoost? = null
    private var loud: LoudnessEnhancer? = null
    var bands = 0; private set
    var error = ""; private set

    fun attach(session: Int) {
        release()
        if (session == 0) return
        try { eq = Equalizer(1000, session); bands = eq!!.numberOfBands.toInt() } catch (e: Exception) { error = e.message ?: "eq" }
        try { bass = BassBoost(1000, session) } catch (_: Exception) { }
        try { loud = LoudnessEnhancer(session) } catch (_: Exception) { }
        apply()
    }

    fun apply() {
        val on = Prefs.eqOn.value
        val gains = EqPresets.currentGains()
        val e = eq ?: return
        try {
            e.enabled = on
            val range = e.bandLevelRange
            for (b in 0 until e.numberOfBands) {
                val hz = e.getCenterFreq(b.toShort()) / 1000.0
                var gDb = interp(gains, hz)
                if (hz >= 3000) gDb += Prefs.treble.value
                if (hz <= 150 && Prefs.bass.value < 0) gDb += Prefs.bass.value
                val mb = (gDb * 100).toInt().coerceIn(range[0].toInt(), range[1].toInt())
                e.setBandLevel(b.toShort(), mb.toShort())
            }
            bass?.let { bb ->
                val st = (Prefs.bass.value.coerceAtLeast(0) * 80).coerceIn(0, 1000)
                bb.enabled = on && st > 0
                if (bb.strengthSupported) bb.setStrength(st.toShort())
            }
            loud?.let { l ->
                val peak = gains.maxOrNull() ?: 0f
                l.setTargetGain(0); l.enabled = false
                if (on && Prefs.eqPreset.value == "loud") { l.setTargetGain(800); l.enabled = true }
                else if (on && peak < 0) { l.setTargetGain((-peak * 60).toInt()); l.enabled = true }
            }
        } catch (_: Exception) { }
    }

    private fun interp(g: FloatArray, hz: Double): Float {
        val f = EqPresets.FREQS
        if (hz <= f[0]) return g[0]
        if (hz >= f[9]) return g[9]
        for (i in 0 until 9) if (hz >= f[i] && hz <= f[i + 1]) {
            val k = (ln(hz) - ln(f[i].toDouble())) / (ln(f[i + 1].toDouble()) - ln(f[i].toDouble()))
            return (g[i] + (g[i + 1] - g[i]) * k).toFloat()
        }
        return 0f
    }

    fun release() {
        try { eq?.release() } catch (_: Exception) { }
        try { bass?.release() } catch (_: Exception) { }
        try { loud?.release() } catch (_: Exception) { }
        eq = null; bass = null; loud = null
    }
}
