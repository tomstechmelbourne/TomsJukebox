package com.tomstechsolutions.jukebox

import android.app.Application
import android.content.Context
import com.tomstechsolutions.jukebox.data.Messages

class App : Application() {
    override fun onCreate() {
        super.onCreate()
        ctx = applicationContext
        Prefs.init(this)
        L.vi.value = Prefs.lang.value == "vi"
        Messages.init(this)
    }

    companion object {
        lateinit var ctx: Context
        val VERSION: String = BuildConfig.VERSION_NAME
        const val NAME = "Tom's Jukebox"
        const val BRAND = "Tom's Technology Solutions"
        const val SLOGAN = "Focus On One Thing And Do It Well"
        const val EMAIL = "tomstechmelbourne@gmail.com"
    }
}
