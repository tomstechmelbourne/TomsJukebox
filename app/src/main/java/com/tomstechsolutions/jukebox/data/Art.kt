package com.tomstechsolutions.jukebox.data

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.media.MediaMetadataRetriever
import android.net.Uri
import android.os.Build
import android.util.LruCache
import android.util.Size
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL

/** Album covers (small cache so memory stays low on Android 17) and the lively colours taken from them. */
object Art {
    private val cache = object : LruCache<String, Bitmap>(12 * 1024 * 1024) {
        override fun sizeOf(key: String, value: Bitmap) = value.byteCount
    }
    private val missing = HashSet<String>()
    val BRAND = intArrayOf(0xFF48B0C8.toInt(), 0xFF8ED3E4.toInt(), 0xFFFBB040.toInt(), 0xFF2C9CC0.toInt(), 0xFFC7F0FA.toInt())

    fun cached(key: String): Bitmap? = cache.get(key)

    suspend fun load(ctx: Context, uri: String, albumId: Long = 0, size: Int = 512): Bitmap? = withContext(Dispatchers.IO) {
        if (uri.isBlank()) return@withContext null
        val key = "$uri#$size"
        cache.get(key)?.let { return@withContext it }
        if (key in missing) return@withContext null
        var bmp: Bitmap? = null
        try {
            if (uri.startsWith("http")) {
                val c = URL(uri).openConnection() as HttpURLConnection
                c.connectTimeout = 8000; c.readTimeout = 8000
                c.setRequestProperty("User-Agent", "TomsJukebox/0.9.3 (Android)")
                c.inputStream.use { bmp = decodeScaled(it.readBytes(), size) }
            } else {
                val u = Uri.parse(uri)
                if (Build.VERSION.SDK_INT >= 29) {
                    try { bmp = ctx.contentResolver.loadThumbnail(u, Size(size, size), null) } catch (_: Exception) { }
                }
                if (bmp == null) {
                    val r = MediaMetadataRetriever()
                    try {
                        r.setDataSource(ctx, u)
                        r.embeddedPicture?.let { bmp = decodeScaled(it, size) }
                    } catch (_: Exception) { } finally { try { r.release() } catch (_: Exception) { } }
                }
                if (bmp == null && albumId > 0) {
                    try {
                        val au = Uri.parse("content://media/external/audio/albumart/$albumId")
                        ctx.contentResolver.openInputStream(au)?.use { bmp = decodeScaled(it.readBytes(), size) }
                    } catch (_: Exception) { }
                }
            }
        } catch (_: Exception) { }
        val b = bmp
        if (b != null) cache.put(key, b) else missing.add(key)
        b
    }

    private fun decodeScaled(bytes: ByteArray, size: Int): Bitmap? {
        val o = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeByteArray(bytes, 0, bytes.size, o)
        var s = 1
        while (o.outWidth / (s * 2) >= size && o.outHeight / (s * 2) >= size) s *= 2
        return BitmapFactory.decodeByteArray(bytes, 0, bytes.size, BitmapFactory.Options().apply { inSampleSize = s })
    }

    /** Same as Tom's Dock: hue bins weighted by colourfulness → 5 colours for the waves and edge light. */
    fun palette(bmp: Bitmap?): IntArray {
        if (bmp == null) return BRAND
        val small = Bitmap.createScaledBitmap(bmp, 24, 24, true)
        val bins = HashMap<Int, DoubleArray>()
        val hsv = FloatArray(3)
        for (y in 0 until 24) for (x in 0 until 24) {
            Color.colorToHSV(small.getPixel(x, y), hsv)
            if (hsv[2] < 0.25f || hsv[1] < 0.18f) continue
            val b = ((hsv[0] / 360f) * 12).toInt() % 12
            val w = (hsv[1] * hsv[2]).toDouble()
            val acc = bins.getOrPut(b) { DoubleArray(4) }
            acc[0] += w; acc[1] += hsv[0] * w; acc[2] += hsv[1] * w; acc[3] += hsv[2] * w
        }
        if (bins.isEmpty()) return intArrayOf(0xFFF2E6DA.toInt(), 0xFFFFFFFF.toInt(), 0xFFD9CFC4.toInt(), 0xFFBFB3A6.toInt(), 0xFFFFF6EC.toInt())
        val top = bins.values.sortedByDescending { it[0] }.take(5).map {
            val h = (it[1] / it[0]).toFloat(); val s = (it[2] / it[0]).toFloat().coerceIn(0.45f, 1f)
            val v = (it[3] / it[0]).toFloat().coerceIn(0.75f, 1f)
            Color.HSVToColor(floatArrayOf(h, s, v))
        }
        val out = IntArray(5) { top[it % top.size] }
        return out
    }
}
