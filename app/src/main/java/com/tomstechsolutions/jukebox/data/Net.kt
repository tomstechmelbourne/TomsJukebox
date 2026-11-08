package com.tomstechsolutions.jukebox.data

import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

object Net {
    const val UA = "TomsJukebox/0.9.2 (Android; Tom's Technology Solutions)"
    fun enc(s: String): String = URLEncoder.encode(s, "UTF-8")

    fun get(url: String, timeout: Int = 10000): String {
        val c = URL(url).openConnection() as HttpURLConnection
        c.connectTimeout = timeout; c.readTimeout = timeout
        c.instanceFollowRedirects = true
        c.setRequestProperty("User-Agent", UA)
        try {
            if (c.responseCode >= 400) throw java.io.IOException("HTTP ${c.responseCode}")
            return c.inputStream.bufferedReader(Charsets.UTF_8).use { it.readText() }
        } finally { c.disconnect() }
    }
}
