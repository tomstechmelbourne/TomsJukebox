package com.tomstechsolutions.jukebox.data

import android.annotation.SuppressLint
import android.content.Context
import android.location.LocationManager

/** Which Australian state the phone is in (offline, simplified borders) – used to change the local radio list. */
object GeoState {
    private val vicNsw = listOf(140.97 to -34.0, 142.15 to -34.15, 142.77 to -34.6, 143.55 to -35.30, 144.75 to -36.10,
        145.5 to -35.85, 146.38 to -35.97, 146.9 to -36.10, 147.4 to -36.02, 148.2 to -36.8, 149.98 to -37.5)

    private fun interp(x: Double): Double {
        if (x <= vicNsw.first().first) return vicNsw.first().second
        for (i in 0 until vicNsw.size - 1) {
            val (x0, y0) = vicNsw[i]; val (x1, y1) = vicNsw[i + 1]
            if (x in x0..x1) return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
        }
        return vicNsw.last().second
    }

    fun stateOf(lat: Double, lon: Double): String? {
        if (!(lat > -44.5 && lat < -9 && lon > 112 && lon < 154.5)) return null
        if (lon in 148.76..149.4 && lat in -35.92..-35.12) return "ACT"
        if (lat < -39.4 && lon > 143.5) return "TAS"
        if (lon < 129) return "WA"
        if (lon < 138) return if (lat > -26) "NT" else "SA"
        if (lon < 141) return if (lat > -26) "QLD" else "SA"
        val border = if (lon <= 150) -29.0 else -29.0 + (lon - 150) * (0.84 / 3.6)
        if (lat > border) return "QLD"
        if (lat < interp(lon)) return "VIC"
        return "NSW"
    }

    @SuppressLint("MissingPermission")
    fun current(ctx: Context): String? = try {
        val lm = ctx.getSystemService(Context.LOCATION_SERVICE) as LocationManager
        val loc = lm.getProviders(true).mapNotNull { runCatching { lm.getLastKnownLocation(it) }.getOrNull() }.maxByOrNull { it.time }
        loc?.let { stateOf(it.latitude, it.longitude) }
    } catch (_: Exception) { null }
}
