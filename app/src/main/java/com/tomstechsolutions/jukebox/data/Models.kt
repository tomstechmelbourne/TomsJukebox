package com.tomstechsolutions.jukebox.data

data class Track(
    val id: Long,
    val uri: String,
    val title: String,
    val artist: String,
    val album: String,
    val albumId: Long,
    val durationMs: Long,
    val folder: String,
    val mime: String,
    val genre: String = "",
    val year: Int = 0,
    val trackNo: Int = 0,
    val dateAdded: Long = 0,
)

data class Station(
    val name: String,
    val search: String,        // name used to find the live stream on Radio Browser
    val country: String,       // AU, VN, OS (Vietnamese overseas)
    val group: String,         // NAT, VIC, NSW ... / VOV, VOH, HN, PROV / OS
    val genre: String,         // news, talk, pop, hits, classic, sport, community, jazz, country, dance, kids, viet
    var url: String = "",      // filled when found
    var bitrate: Int = 0,
    var codec: String = "",
    var paused: Boolean = false,  // "Tạm Ngưng" when no working stream was found
)

data class Podcast(val title: String, val author: String, val feed: String, val image: String, val id: String = "")

data class Episode(
    val title: String, val url: String, val date: String, val durationS: Long,
    val podcast: String, val image: String, val description: String,
    val hq: String = "",          // bản chất lượng cao hơn nếu kênh có (podcast:alternateEnclosure)
) {
    /** The file to download: the highest-quality version when "Tải chất lượng cao" is on. */
    fun best(): String = if (com.tomstechsolutions.jukebox.Prefs.podHQ.value && hq.isNotBlank()) hq else url
}

data class LyricLine(val timeMs: Long, val text: String)
