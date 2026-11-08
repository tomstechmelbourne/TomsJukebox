package com.tomstechsolutions.jukebox.data

import com.tomstechsolutions.jukebox.Prefs
import org.json.JSONArray
import org.json.JSONObject

object Playlists {
    fun all(): Map<String, List<String>> = try {
        val o = JSONObject(Prefs.playlists.value)
        o.keys().asSequence().associateWith { k -> val a = o.getJSONArray(k); (0 until a.length()).map { a.getString(it) } }
    } catch (_: Exception) { emptyMap() }

    private fun save(m: Map<String, List<String>>) {
        val o = JSONObject()
        m.forEach { (k, v) -> o.put(k, JSONArray(v)) }
        Prefs.playlists.value = o.toString()
    }

    fun add(name: String, uris: List<String>) { val m = all().toMutableMap(); m[name] = (m[name] ?: emptyList()) + uris; save(m) }
    fun delete(name: String) { val m = all().toMutableMap(); m.remove(name); save(m) }
    fun rename(old: String, new: String) { val m = all().toMutableMap(); m.remove(old)?.let { m[new] = it }; save(m) }
}
