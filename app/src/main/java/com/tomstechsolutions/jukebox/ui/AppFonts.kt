package com.tomstechsolutions.jukebox.ui

import android.content.Context
import android.graphics.Typeface
import android.net.Uri
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import com.tomstechsolutions.jukebox.App
import com.tomstechsolutions.jukebox.Prefs
import com.tomstechsolutions.jukebox.R
import com.tomstechsolutions.jukebox.t
import java.io.File

/**
 * Font chữ: font máy, bộ font biển hiệu Sài Gòn xưa "Saigon 1985" (Thái Hiệu – Fontzin, Tom gửi),
 * và font Tom tự thêm từ điện thoại (.ttf / .otf).
 */
object AppFonts {
    data class F(val key: String, val en: String, val vi: String, val res: Int?)
    val builtIn = listOf(
        F("default", "Phone Default", "Mặc Định Của Máy", null),
        F("sg85_saigon1985", "Saigon 1985 (Script)", "Sài Gòn 1985 (Chữ Viết)", R.font.sg85_saigon1985),
        F("sg85_cua_hang", "Cửa Hàng 99", "Cửa Hàng 99", R.font.sg85_cua_hang),
        F("sg85_chi_son_1", "Chí Sơn 1", "Chí Sơn 1", R.font.sg85_chi_son_1),
        F("sg85_chi_son_2", "Chí Sơn 2", "Chí Sơn 2", R.font.sg85_chi_son_2),
        F("sg85_hien_khanh_1", "Hiền Khánh 1", "Hiền Khánh 1", R.font.sg85_hien_khanh_1),
        F("sg85_hien_khanh_2", "Hiền Khánh 2", "Hiền Khánh 2", R.font.sg85_hien_khanh_2),
        F("sg85_hien_khanh_3", "Hiền Khánh 3", "Hiền Khánh 3", R.font.sg85_hien_khanh_3),
        F("sg85_hong_ky_1", "Hồng Ký 1", "Hồng Ký 1", R.font.sg85_hong_ky_1),
        F("sg85_hong_ky_2", "Hồng Ký 2", "Hồng Ký 2", R.font.sg85_hong_ky_2),
        F("sg85_phat_tai", "Phát Tài", "Phát Tài", R.font.sg85_phat_tai),
    )

    private fun dir(ctx: Context) = File(ctx.filesDir, "fonts").apply { mkdirs() }
    /** Fonts Tom added from the phone: key "file:<name>". */
    fun custom(ctx: Context = App.ctx): List<F> = dir(ctx).listFiles()?.filter { it.extension.lowercase() in setOf("ttf", "otf") }?.sortedBy { it.name }
        ?.map { F("file:" + it.name, it.nameWithoutExtension, it.nameWithoutExtension, null) } ?: emptyList()
    fun all(ctx: Context = App.ctx) = builtIn + custom(ctx)
    fun name(key: String) = all().firstOrNull { it.key == key }?.let { t(it.en, it.vi) } ?: t("Phone Default", "Mặc Định Của Máy")

    private val cache = HashMap<String, FontFamily?>()
    fun family(key: String): FontFamily? = cache.getOrPut(key) {
        when {
            key == "default" || key.isBlank() -> null
            key.startsWith("file:") -> File(dir(App.ctx), key.removePrefix("file:")).takeIf { it.exists() }?.let { try { FontFamily(Font(it)) } catch (_: Exception) { null } }
            else -> builtIn.firstOrNull { it.key == key }?.res?.let { FontFamily(Font(it)) }
        }
    }
    fun title(): FontFamily? = family(Prefs.fontTitle.value)
    fun body(): FontFamily? = family(Prefs.fontBody.value)

    /** "Thêm Font Từ Điện Thoại": copies the chosen .ttf / .otf into the app and checks it opens. */
    fun import(ctx: Context, uri: Uri): String? = try {
        val raw = ctx.contentResolver.query(uri, null, null, null, null)?.use { c -> val i = c.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME); if (c.moveToFirst() && i >= 0) c.getString(i) else null } ?: "font.ttf"
        val name = raw.replace(Regex("[^\\p{L}\\p{N} ._-]"), "_").let { if (it.lowercase().endsWith(".ttf") || it.lowercase().endsWith(".otf")) it else "$it.ttf" }
        val f = File(dir(ctx), name)
        ctx.contentResolver.openInputStream(uri)?.use { inp -> f.outputStream().use { inp.copyTo(it) } }
        Typeface.createFromFile(f)                       // throws if it isn't a real font
        cache.remove("file:$name"); "file:$name"
    } catch (_: Exception) { null }

    fun remove(ctx: Context, key: String) {
        if (!key.startsWith("file:")) return
        File(dir(ctx), key.removePrefix("file:")).delete(); cache.remove(key)
        if (Prefs.fontTitle.value == key) Prefs.fontTitle.value = "default"
        if (Prefs.fontBody.value == key) Prefs.fontBody.value = "default"
    }
}
