package com.tomstechsolutions.jukebox.data

import com.tomstechsolutions.jukebox.t

/**
 * Built-in stations (126). Each one is looked up live on Radio Browser (radio-browser.info) by name when played,
 * so a station that changes its stream address keeps working; one that can't be found is shown as "Tạm Ngưng".
 */
object Stations {
    val all: List<Station> = listOf(
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
        Station("SBS Radio 2", "SBS Radio 2", "AU", "NAT", "talk"),
        Station("SBS Radio 3", "SBS Radio 3", "AU", "NAT", "talk"),
        Station("SBS PopAsia", "SBS PopAsia", "AU", "NAT", "pop"),
        Station("SBS Chill", "SBS Chill", "AU", "NAT", "pop"),
        Station("ABC Sport", "ABC Sport", "AU", "NAT", "sport"),
        Station("ABC Melbourne 774", "ABC Radio Melbourne", "AU", "VIC", "talk"),
        Station("3AW 693", "3AW", "AU", "VIC", "talk"),
        Station("Gold 104.3", "Gold 104.3", "AU", "VIC", "classic"),
        Station("smoothfm 91.5", "smoothfm 91.5", "AU", "VIC", "classic"),
        Station("Magic 1278", "Magic 1278", "AU", "VIC", "classic"),
        Station("3MBS 103.5", "3MBS", "AU", "VIC", "classic"),
        Station("Nova 100", "Nova 100", "AU", "VIC", "hits"),
        Station("Fox FM 101.9", "Fox FM", "AU", "VIC", "hits"),
        Station("KIIS 101.1", "KIIS 101.1", "AU", "VIC", "hits"),
        Station("Triple M Melbourne", "Triple M Melbourne", "AU", "VIC", "hits"),
        Station("SEN 1116", "SEN 1116", "AU", "VIC", "sport"),
        Station("RSN 927", "RSN Racing", "AU", "VIC", "sport"),
        Station("PBS 106.7", "PBS 106.7", "AU", "VIC", "community"),
        Station("Triple R 102.7", "3RRR", "AU", "VIC", "community"),
        Station("3CR 855", "3CR", "AU", "VIC", "community"),
        Station("3ZZZ 92.3", "3ZZZ", "AU", "VIC", "community"),
        Station("JOY 94.9", "JOY 94.9", "AU", "VIC", "community"),
        Station("ABC Ballarat", "ABC Ballarat", "AU", "VIC", "talk"),
        Station("ABC Central Victoria", "ABC Central Victoria", "AU", "VIC", "talk"),
        Station("ABC Sydney 702", "ABC Radio Sydney", "AU", "NSW", "talk"),
        Station("2GB 873", "2GB", "AU", "NSW", "talk"),
        Station("2CH 1170", "2CH", "AU", "NSW", "talk"),
        Station("KIIS 1065", "KIIS 1065", "AU", "NSW", "hits"),
        Station("Nova 96.9", "Nova 96.9", "AU", "NSW", "hits"),
        Station("Triple M Sydney", "Triple M Sydney", "AU", "NSW", "hits"),
        Station("2Day FM 104.1", "2Day FM", "AU", "NSW", "hits"),
        Station("smoothfm 95.3", "smoothfm 95.3", "AU", "NSW", "classic"),
        Station("WSFM 101.7", "WSFM", "AU", "NSW", "classic"),
        Station("2SER 107.3", "2SER", "AU", "NSW", "community"),
        Station("2000FM", "2000FM", "AU", "NSW", "community"),
        Station("Hope 103.2", "Hope 103.2", "AU", "NSW", "community"),
        Station("ABC Newcastle", "ABC Newcastle", "AU", "NSW", "talk"),
        Station("ABC Brisbane 612", "ABC Radio Brisbane", "AU", "QLD", "talk"),
        Station("4BC 882", "4BC", "AU", "QLD", "talk"),
        Station("ABC Gold Coast", "ABC Gold Coast", "AU", "QLD", "talk"),
        Station("B105", "B105", "AU", "QLD", "hits"),
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
        Station("Radio Adelaide", "Radio Adelaide", "AU", "SA", "community"),
        Station("ABC Perth 720", "ABC Radio Perth", "AU", "WA", "talk"),
        Station("6PR 882", "6PR", "AU", "WA", "talk"),
        Station("Mix 94.5", "Mix 94.5", "AU", "WA", "hits"),
        Station("Nova 93.7", "Nova 93.7", "AU", "WA", "hits"),
        Station("96FM", "96FM", "AU", "WA", "hits"),
        Station("RTRFM 92.1", "RTRFM", "AU", "WA", "community"),
        Station("6iX", "6iX", "AU", "WA", "classic"),
        Station("ABC Hobart 936", "ABC Radio Hobart", "AU", "TAS", "talk"),
        Station("ABC Northern Tasmania", "ABC Northern Tasmania", "AU", "TAS", "talk"),
        Station("Triple M Hobart", "Triple M Hobart", "AU", "TAS", "hits"),
        Station("HIT100.9 Hobart", "Hit 100.9", "AU", "TAS", "hits"),
        Station("Edge Radio 99.3", "Edge Radio", "AU", "TAS", "community"),
        Station("ABC Darwin 105.7", "ABC Radio Darwin", "AU", "NT", "talk"),
        Station("Hot 100 Darwin", "Hot 100", "AU", "NT", "hits"),
        Station("Mix 104.9 Darwin", "Mix 104.9", "AU", "NT", "hits"),
        Station("Territory FM", "Territory FM", "AU", "NT", "hits"),
        Station("ABC Canberra 666", "ABC Radio Canberra", "AU", "ACT", "talk"),
        Station("2CC 1206", "2CC", "AU", "ACT", "talk"),
        Station("Mix 106.3", "Mix 106.3", "AU", "ACT", "hits"),
        Station("Hit 104.7", "Hit 104.7", "AU", "ACT", "hits"),
        Station("ArtSound FM 92.7", "ArtSound", "AU", "ACT", "community"),
        Station("2XX 98.3", "2XX", "AU", "ACT", "community"),
        Station("VOV1 – Thời Sự", "VOV1", "VN", "VOV", "news"),
        Station("VOV2 – Văn Hoá Xã Hội", "VOV2", "VN", "VOV", "talk"),
        Station("VOV3 – Âm Nhạc", "VOV3", "VN", "VOV", "pop"),
        Station("VOV4 – Dân Tộc", "VOV4", "VN", "VOV", "talk"),
        Station("VOV5 – Đối Ngoại", "VOV5", "VN", "VOV", "talk"),
        Station("VOV6 – Văn Học Nghệ Thuật", "VOV6", "VN", "VOV", "talk"),
        Station("VOV Giao Thông Hà Nội", "VOV Giao Thong Ha Noi", "VN", "VOV", "talk"),
        Station("VOV Giao Thông TP.HCM", "VOV Giao Thong Ho Chi Minh", "VN", "VOV", "talk"),
        Station("VOV Mekong FM 90", "VOV Mekong", "VN", "VOV", "talk"),
        Station("VOH FM 99.9", "VOH 99.9", "VN", "VOH", "talk"),
        Station("VOH FM 95.6", "VOH 95.6", "VN", "VOH", "talk"),
        Station("VOH FM 87.7", "VOH 87.7", "VN", "VOH", "talk"),
        Station("VOH AM 610", "VOH 610", "VN", "VOH", "talk"),
        Station("Hà Nội FM 90", "Ha Noi FM90", "VN", "HN", "talk"),
        Station("Hà Nội FM 96", "Ha Noi FM96", "VN", "HN", "talk"),
        Station("Joy FM 98.9", "Joy FM 98.9", "VN", "HN", "pop"),
        Station("Đà Nẵng FM", "Da Nang", "VN", "PROV", "talk"),
        Station("Bình Dương FM 92.5", "Binh Duong", "VN", "PROV", "talk"),
        Station("Đồng Nai FM", "Dong Nai", "VN", "PROV", "talk"),
        Station("Cần Thơ FM", "Can Tho", "VN", "PROV", "talk"),
        Station("Hải Phòng FM", "Hai Phong", "VN", "PROV", "talk"),
        Station("Quảng Ninh FM", "Quang Ninh", "VN", "PROV", "talk"),
        Station("Huế FM", "Hue", "VN", "PROV", "talk"),
        Station("Khánh Hoà FM", "Khanh Hoa", "VN", "PROV", "talk"),
        Station("Lâm Đồng FM", "Lam Dong", "VN", "PROV", "talk"),
        Station("Vĩnh Long FM", "Vinh Long", "VN", "PROV", "talk"),
        Station("Long An FM", "Long An", "VN", "PROV", "talk"),
        Station("Nghệ An FM", "Nghe An", "VN", "PROV", "talk"),
        Station("SBS Tiếng Việt", "SBS Vietnamese", "OS", "AUVN", "viet"),
        Station("3ZZZ Tiếng Việt", "3ZZZ", "OS", "AUVN", "viet"),
        Station("Vietnamese Community Radio", "Vietnamese", "OS", "AUVN", "viet"),
        Station("Little Saigon Radio", "Little Saigon Radio", "OS", "OS", "viet"),
        Station("Radio Saigon Houston", "Radio Saigon Houston", "OS", "OS", "viet"),
        Station("Saigon Radio Hải Ngoại", "Saigon Radio", "OS", "OS", "viet"),
        Station("RFA Tiếng Việt", "RFA Vietnamese", "OS", "OS", "viet"),
        Station("Radio Bolsa", "Radio Bolsa", "OS", "OS", "viet"),
        Station("VNCR Nhạc Việt", "Nhac Viet", "OS", "OS", "viet"),
        Station("Nhạc Vàng Hải Ngoại", "Nhac Vang", "OS", "OS", "viet")
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
