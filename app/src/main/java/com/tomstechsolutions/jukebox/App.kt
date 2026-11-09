package com.tomstechsolutions.jukebox

import android.app.Application
import android.content.Context
import com.tomstechsolutions.jukebox.data.Messages

class App : Application() {
    override fun onCreate() {
        super.onCreate()
        ctx = applicationContext
        Prefs.init(this)
        removeRetiredStyles()
        L.vi.value = Prefs.lang.value == "vi"
        Messages.init(this)
        try { com.tomstechsolutions.jukebox.data.PodStore.schedule(this) } catch (_: Exception) { }
    }

    companion object {
        lateinit var ctx: Context
        val VERSION: String = BuildConfig.VERSION_NAME
        const val NAME = "Tom's Jukebox"
        const val BRAND = "Tom's Technology Solutions"
        const val SLOGAN = "Focus On One Thing And Do It Well"
        const val EMAIL = "tomstechmelbourne@gmail.com"
    }

    /** Kiểu đã bỏ (số 58): ai đang dùng thì chuyển về kiểu 0, xoá khỏi ★ và Gần Đây. */
    private fun removeRetiredStyles() {
        try {
            val gone = com.tomstechsolutions.jukebox.ui.VizStyles.removed
            if (Prefs.viz.value in gone) Prefs.viz.value = 0
            if (Prefs.pack.value in gone) Prefs.pack.value = 0
            for (g in gone) {
                val k = "m:$g"
                for (pf in listOf(Prefs.theme, Prefs.skin, Prefs.btnColour, Prefs.barColour)) if (pf.value == k) pf.value = "m:0"
                if (Prefs.btnStyle.value == 100 + g) Prefs.btnStyle.value = 100
                if (Prefs.edgeEffect.value == 100 + g) Prefs.edgeEffect.value = 100
                Prefs.favStyles.value = Prefs.favStyles.value.split('\n').filter { !it.endsWith("|m:$g") && !it.endsWith("|v:$g") }.joinToString("\n")
                Prefs.recentStyles.value = Prefs.recentStyles.value.split('\n').filter { !it.endsWith("|m:$g") && !it.endsWith("|v:$g") }.joinToString("\n")
            }
        } catch (_: Exception) { }
    }
}
