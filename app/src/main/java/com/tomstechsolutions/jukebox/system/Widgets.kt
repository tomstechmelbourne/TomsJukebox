package com.tomstechsolutions.jukebox.system

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.graphics.BitmapFactory
import android.net.Uri
import android.view.KeyEvent
import android.widget.RemoteViews
import androidx.media3.session.MediaButtonReceiver
import com.tomstechsolutions.jukebox.R
import com.tomstechsolutions.jukebox.ui.ButtonArt
import com.tomstechsolutions.jukebox.ui.MainActivity

/** Home-screen widgets in 3 sizes (small pill, medium, large with cover). */
open class BaseWidget(private val layout: Int) : AppWidgetProvider() {
    override fun onUpdate(ctx: Context, mgr: AppWidgetManager, ids: IntArray) {
        Widgets.push(ctx, mgr, ids, layout, Widgets.lastTitle, Widgets.lastArtist, Widgets.lastPlaying, Widgets.lastArt)
    }
}

class WidgetSmall : BaseWidget(R.layout.widget_small)
class WidgetMedium : BaseWidget(R.layout.widget_medium)
class WidgetLarge : BaseWidget(R.layout.widget_large)

object Widgets {
    var lastTitle = ""; var lastArtist = ""; var lastPlaying = false; var lastArt: ByteArray? = null

    fun button(ctx: Context, code: Int): PendingIntent {
        val i = Intent(Intent.ACTION_MEDIA_BUTTON).setClass(ctx, MediaButtonReceiver::class.java)
            .setData(Uri.parse("tomsjukebox://key/$code"))
            .putExtra(Intent.EXTRA_KEY_EVENT, KeyEvent(KeyEvent.ACTION_DOWN, code))
        return PendingIntent.getBroadcast(ctx, code, i, PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
    }

    fun update(ctx: Context, title: String, artist: String, playing: Boolean, art: ByteArray?) {
        if (title == lastTitle && artist == lastArtist && playing == lastPlaying && (art?.size ?: 0) == (lastArt?.size ?: 0)) return
        lastTitle = title; lastArtist = artist; lastPlaying = playing; lastArt = art
        val mgr = AppWidgetManager.getInstance(ctx)
        listOf(WidgetSmall::class.java to R.layout.widget_small, WidgetMedium::class.java to R.layout.widget_medium,
            WidgetLarge::class.java to R.layout.widget_large).forEach { (cls, layout) ->
            val ids = mgr.getAppWidgetIds(ComponentName(ctx, cls))
            if (ids.isNotEmpty()) push(ctx, mgr, ids, layout, title, artist, playing, art)
        }
    }

    fun push(ctx: Context, mgr: AppWidgetManager, ids: IntArray, layout: Int, title: String, artist: String, playing: Boolean, art: ByteArray?) {
        val v = RemoteViews(ctx.packageName, layout)
        v.setTextViewText(R.id.w_title, title.ifBlank { "Tom's Jukebox" })
        v.setTextViewText(R.id.w_artist, artist)
        val style = com.tomstechsolutions.jukebox.Prefs.btnStyle.value
        val col = 0xFFFFFFFF.toInt()
        try {
            v.setImageViewBitmap(R.id.w_play, ButtonArt.bitmap(if (playing) ButtonArt.PAUSE else ButtonArt.PLAY, style, 120, col))
            v.setImageViewBitmap(R.id.w_prev, ButtonArt.bitmap(ButtonArt.PREV, style, 96, col))
            v.setImageViewBitmap(R.id.w_next, ButtonArt.bitmap(ButtonArt.NEXT, style, 96, col))
        } catch (_: Exception) { v.setImageViewResource(R.id.w_play, if (playing) R.drawable.g_pause else R.drawable.g_play) }
        v.setOnClickPendingIntent(R.id.w_play, button(ctx, KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE))
        v.setOnClickPendingIntent(R.id.w_next, button(ctx, KeyEvent.KEYCODE_MEDIA_NEXT))
        v.setOnClickPendingIntent(R.id.w_prev, button(ctx, KeyEvent.KEYCODE_MEDIA_PREVIOUS))
        val open = PendingIntent.getActivity(ctx, 1, Intent(ctx, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE)
        v.setOnClickPendingIntent(R.id.w_root, open)
        val bmp = art?.let { try { BitmapFactory.decodeByteArray(it, 0, it.size, BitmapFactory.Options().apply { inSampleSize = 4 }) } catch (_: Exception) { null } }
        if (bmp != null) v.setImageViewBitmap(R.id.w_art, bmp) else v.setImageViewResource(R.id.w_art, R.drawable.app_logo)
        try { mgr.updateAppWidget(ids, v) } catch (_: Exception) { }
    }
}
