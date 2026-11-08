package com.tomstechsolutions.jukebox.data

import com.tomstechsolutions.jukebox.t

/**
 * Built-in stations (109). Each one is looked up live on Radio Browser (radio-browser.info) by name when played,
 * so a station that changes its stream address keeps working; one that can't be found is shown as "Tạm Ngưng".
 */
object Stations {
    /** SBS Việt ngữ is a daily programme on SBS Radio 1 (SBS's own stream server). */
    val sbsViet = Station("SBS Tiếng Việt (SBS Radio 1)", "SBS Radio 1", "AU", "AUVN", "viet", "https://sbs-ice.streamguys1.com/sbs1-sbs-web", 0, "AAC")

    val all: List<Station> = listOf(
        sbsViet,
        Station("ABC NewsRadio", "ABC NewsRadio", "AU", "NAT", "news"),
        Station("ABC Radio National", "ABC Radio National", "AU", "NAT", "news"),
        Station("triple j", "triple j", "AU", "NAT", "pop"),
        Station("Double J", "Double J", "AU", "NAT", "pop"),
        Station("triple j Unearthed", "triple j Unearthed", "AU", "NAT", "pop"),
        Station("ABC Classic", "ABC Classic", "AU", "NAT", "classic"),
        Station("ABC Classic 2", "ABC Classic 2", "AU", "NAT", "classic"),
        Station("ABC Jazz", "ABC Jazz", "AU", "NAT", "jazz"),
        Station("ABC Country", "ABC Country", "AU", "NAT", "country"),
        Station("ABC Kids Listen", "ABC Kids listen", "AU", "NAT", "kids"),
        Station("SBS Radio 1", "SBS Radio 1", "AU", "NAT", "talk"),
        Station("SBS PopAsia", "SBS PopAsia", "AU", "NAT", "pop"),
        Station("SBS Chill", "SBS Chill", "AU", "NAT", "pop"),
        Station("ABC Sport", "ABC Sport", "AU", "NAT", "sport"),
        Station("ABC Melbourne 774", "ABC Radio Melbourne", "AU", "VIC", "talk"),
        Station("3AW 693", "3AW", "AU", "VIC", "talk"),
        Station("Gold 104.3", "Gold 104.3", "AU", "VIC", "classic"),
        Station("smoothfm 91.5", "Smooth FM 91.5", "AU", "VIC", "classic"),
        Station("3MBS 103.5", "3MBS", "AU", "VIC", "classic"),
        Station("Nova 100", "Nova 100", "AU", "VIC", "hits"),
        Station("KIIS 101.1", "KIIS 101.1", "AU", "VIC", "hits"),
        Station("Triple M Melbourne", "Triple M Melbourne", "AU", "VIC", "hits"),
        Station("RSN 927", "RSN 927", "AU", "VIC", "sport"),
        Station("PBS 106.7", "PBS 106.7", "AU", "VIC", "community"),
        Station("Triple R 102.7", "3RRR", "AU", "VIC", "community"),
        Station("3CR 855", "3CR", "AU", "VIC", "community"),
        Station("3ZZZ 92.3", "3ZZZ", "AU", "VIC", "community"),
        Station("JOY 94.9", "JOY 94.9", "AU", "VIC", "community"),
        Station("ABC Ballarat", "ABC Ballarat", "AU", "VIC", "talk"),
        Station("ABC Sydney 702", "ABC Radio Sydney", "AU", "NSW", "talk"),
        Station("2GB 873", "2GB", "AU", "NSW", "talk"),
        Station("KIIS 1065", "KIIS 1065", "AU", "NSW", "hits"),
        Station("Nova 96.9", "Nova 96.9", "AU", "NSW", "hits"),
        Station("Triple M Sydney", "Triple M Sydney", "AU", "NSW", "hits"),
        Station("2Day FM 104.1", "2Day FM", "AU", "NSW", "hits"),
        Station("smoothfm 95.3", "Smooth FM 95.3", "AU", "NSW", "classic"),
        Station("WSFM 101.7", "WSFM", "AU", "NSW", "classic"),
        Station("2SER 107.3", "2SER", "AU", "NSW", "community"),
        Station("Hope 103.2", "Hope 103.2", "AU", "NSW", "community"),
        Station("ABC Newcastle", "ABC Radio Newcastle", "AU", "NSW", "talk"),
        Station("ABC Brisbane 612", "ABC Radio Brisbane", "AU", "QLD", "talk"),
        Station("4BC 882", "4BC", "AU", "QLD", "talk"),
        Station("ABC Gold Coast", "ABC Radio Gold Coast", "AU", "QLD", "talk"),
        Station("Nova 106.9", "Nova 106.9", "AU", "QLD", "hits"),
        Station("KIIS 97.3", "KIIS 97.3", "AU", "QLD", "hits"),
        Station("Triple M Brisbane", "Triple M Brisbane", "AU", "QLD", "hits"),
        Station("Hot Tomato", "Hot Tomato", "AU", "QLD", "hits"),
        Station("4ZZZ 102.1", "4ZZZ", "AU", "QLD", "community"),
        Station("4MBS Classic FM", "4MBS", "AU", "QLD", "community"),
        Station("ABC Adelaide 891", "ABC Radio Adelaide", "AU", "SA", "talk"),
        Station("FIVEaa", "FIVEaa", "AU", "SA", "talk"),
        Station("Mix 102.3", "Mix 102.3", "AU", "SA", "hits"),
        Station("Nova 91.9", "Nova 91.9", "AU", "SA", "hits"),
        Station("Triple M Adelaide", "Triple M Adelaide", "AU", "SA", "hits"),
        Station("Cruise 1323", "Cruise 1323", "AU", "SA", "classic"),
        Station("Three D Radio", "Three D Radio", "AU", "SA", "community"),
        Station("ABC Perth 720", "ABC Radio Perth", "AU", "WA", "talk"),
        Station("6PR 882", "6PR", "AU", "WA", "talk"),
        Station("Mix 94.5", "Mix 94.5", "AU", "WA", "hits"),
        Station("Nova 93.7", "Nova 93.7", "AU", "WA", "hits"),
        Station("RTRFM 92.1", "RTR FM", "AU", "WA", "community"),
        Station("6iX", "6iX", "AU", "WA", "classic"),
        Station("ABC Hobart 936", "ABC Radio Hobart", "AU", "TAS", "talk"),
        Station("ABC Northern Tasmania", "ABC Radio Northern Tasmania", "AU", "TAS", "talk"),
        Station("Edge Radio 99.3", "Edge Radio", "AU", "TAS", "community"),
        Station("ABC Darwin 105.7", "ABC Radio Darwin", "AU", "NT", "talk"),
        Station("Hot 100 Darwin", "Hot 100", "AU", "NT", "hits"),
        Station("Mix 104.9 Darwin", "Mix 104.9", "AU", "NT", "hits"),
        Station("Territory FM", "Territory FM", "AU", "NT", "hits"),
        Station("ABC Canberra 666", "ABC Radio Canberra", "AU", "ACT", "talk"),
        Station("2CC 1206", "2CC", "AU", "ACT", "talk"),
        Station("Mix 106.3", "Mix 106.3", "AU", "ACT", "hits"),
        Station("ArtSound FM 92.7", "ArtSound", "AU", "ACT", "community"),
        Station("2XX 98.3", "2XX", "AU", "ACT", "community"),
        Station("VOV1 – Thời Sự", "VOV1", "VN", "VOV", "news"),
        Station("VOV2 – Văn Hoá Xã Hội", "VOV2", "VN", "VOV", "talk"),
        Station("VOV3 – Âm Nhạc", "VOV3", "VN", "VOV", "pop"),
        Station("VOV Giao Thông Hà Nội", "VOV Giao Thong Ha Noi", "VN", "VOV", "talk"),
        Station("VOV Giao Thông TP.HCM", "VOV GT HCM", "VN", "VOV", "talk"),
        Station("Hà Nội FM 90", "FM HANOI 90", "VN", "HN", "talk"),
        Station("Hà Nội FM 96", "FM HANOI 96", "VN", "HN", "talk"),
        Station("Hải Phòng FM 102.2", "Hai Phong FM", "VN", "PROV", "talk"),
        Station("3ZZZ (Có Giờ Tiếng Việt)", "3ZZZ", "OS", "AUVN", "viet"),
        Station("Little Saigon Radio", "Little Saigon Radio", "OS", "OS", "viet"),
        Station("SEN Track", "SEN Track", "AU", "VIC", "sport"),
        Station("ABC Gippsland", "ABC Radio Gippsland", "AU", "VIC", "talk"),
        Station("1170 SEN Sydney", "1170 SEN", "AU", "NSW", "sport"),
        Station("ABC Illawarra", "ABC Radio Illawarra", "AU", "NSW", "talk"),
        Station("SENQ", "SENQ", "AU", "QLD", "sport"),
        Station("Smooth FM Brisbane", "Smooth FM Brisbane", "AU", "QLD", "classic"),
        Station("ABC Sunshine Coast", "ABC Radio Sunshine Coast", "AU", "QLD", "talk"),
        Station("Smooth FM Adelaide", "Smooth FM Adelaide", "AU", "SA", "classic"),
        Station("Smooth FM Perth", "Smooth FM Perth", "AU", "WA", "classic"),
        Station("7HO FM Hobart", "7HOFM", "AU", "TAS", "classic"),
        Station("Ultra 106.5 Hobart", "Ultra 106.5", "AU", "TAS", "hits"),
        Station("ABC Alice Springs", "ABC Radio Alice Springs", "AU", "NT", "talk"),
        Station("SBS PopDesi", "SBS PopDesi", "AU", "NAT", "pop"),
        Station("Hà Nội Community Radio", "Hà Nội Community", "VN", "HN", "community"),
        Station("RFI Tiếng Việt", "RFI Tiếng Việt", "OS", "OS", "news"),
        Station("RVA Tiếng Việt (Vatican)", "RVA Vietnamese", "OS", "OS", "talk"),
        Station("Bolsa Radio", "Bolsa Radio VN", "OS", "OS", "viet"),
        Station("Saigon Houston AM900", "Saigon Houston AM900", "OS", "OS", "viet"),
        Station("Saigon Radio 106.3 FM", "Saigon Radio 106.3", "OS", "OS", "viet"),
        Station("Viet Washington DC", "VIET WASHINGTON DC", "OS", "OS", "viet"),
        Station("Viet Radio 1560", "VIET RADIO 1560", "OS", "OS", "viet"),
        Station("TNT Atlanta Radio", "TNT Atlanta Radio", "OS", "OS", "viet"),
        Station("Kali Saigon", "KALI SAIGON", "OS", "OS", "viet"),
        Station("Zing Bolero", "ZING BOLERO", "OS", "OS", "viet"),
        Station("M Radio Vietnam", "M Radio Vietnam", "OS", "OS", "pop")
    )

    val auStates = listOf("VIC", "NSW", "QLD", "SA", "WA", "TAS", "NT", "ACT")

    fun groupName(g: String): String = when (g) {
        "NAT" -> t("Australia-Wide", "Toàn Úc")
        "VOV" -> "VOV"
        "VOH" -> "VOH"
        "HN" -> t("Hanoi", "Hà Nội")
        "PROV" -> t("Provinces", "Các Tỉnh")
        "AUVN" -> t("Vietnamese In Australia", "Tiếng Việt Tại Úc")
        "OS" -> t("Vietnamese Overseas", "Người Việt Hải Ngoại")
        else -> g
    }

    fun genreName(g: String): String = when (g) {
        "news" -> t("News", "Tin Tức")
        "talk" -> t("Talk", "Nói Chuyện")
        "pop" -> t("Pop", "Nhạc Trẻ")
        "hits" -> t("Hits", "Nhạc Hits")
        "classic" -> t("Classic Hits", "Nhạc Xưa")
        "sport" -> t("Sport", "Thể Thao")
        "community" -> t("Community", "Cộng Đồng")
        "jazz" -> "Jazz"
        "country" -> t("Country", "Đồng Quê")
        "kids" -> t("Kids", "Thiếu Nhi")
        "viet" -> t("Vietnamese", "Tiếng Việt")
        else -> g
    }
}
