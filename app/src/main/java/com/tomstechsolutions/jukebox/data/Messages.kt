package com.tomstechsolutions.jukebox.data

import android.content.Context
import androidx.compose.runtime.mutableStateListOf
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

/** "Tin Nhắn": short notes from the program (station paused, backup reminder, sleep timer…). */
object Messages {
    data class Msg(val time: Long, val text: String, var read: Boolean = false)
    val list = mutableStateListOf<Msg>()
    private var file: File? = null

    fun init(ctx: Context) {
        file = File(ctx.filesDir, "messages.json")
        try {
            val a = JSONArray(file!!.readText())
            for (i in 0 until a.length()) { val o = a.getJSONObject(i); list += Msg(o.getLong("t"), o.getString("x"), o.optBoolean("r")) }
        } catch (_: Exception) { }
    }

    fun add(text: String) {
        if (list.firstOrNull()?.text == text) return
        list.add(0, Msg(System.currentTimeMillis(), text))
        while (list.size > 100) list.removeAt(list.size - 1)
        save()
    }

    fun markRead() { list.forEach { it.read = true }; save() }
    fun unread() = list.count { !it.read }

    private fun save() {
        val a = JSONArray()
        list.forEach { a.put(JSONObject().put("t", it.time).put("x", it.text).put("r", it.read)) }
        try { file?.writeText(a.toString()) } catch (_: Exception) { }
    }
}
