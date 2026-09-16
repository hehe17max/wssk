# -*- coding: utf-8 -*-
"""
外设水库 · 品牌注册表（源数据）
================================
按用户提供的 6 大外设类型品牌清单整理，保留原始分组标签（地区/定位）。
所有品牌初始核验状态均为「待核验」，由 pipeline/verify.py 自动访问官网完成真实性确认。

数据结构：
    CATEGORIES : {type_id: 中文名}
    SPEC       : [(type_id, 分组标签, [(key, 中文名, 英文名), ...]), ...]
    CURATED    : {key: [域名, ...]}  仅收录公开常识级官网域名，供核验流水线优先探测，
                 verified 一律以流水线实测为准。
"""

# 六大外设类型
CATEGORIES = {
    "earphone": "耳机",
    "mouse": "鼠标",
    "keyboard": "键盘",
    "gamepad": "手柄",
    "speaker": "音响",
    "mousepad": "鼠标垫",
}

# 分组标签即地区时，自动作为 brand.region
REGION_GROUPS = {
    "美国", "瑞士", "日本", "德国", "奥地利", "英国", "丹麦", "法国",
    "荷兰", "韩国", "新加坡", "中国台湾", "中国香港", "芬兰", "意大利", "加拿大",
}

# 地区覆盖（分组标签不是地区名、但品牌实际地区不同的场景）
REGION_OVERRIDE = {
    "logitech": "瑞士",   # 鼠标垫分组写作「美国：罗技（瑞士）」
}

SPEC = [
    # ---------------- 1. 耳机 ----------------
    ("earphone", "手机/生态", [
        ("huawei", "华为", "Huawei"), ("xiaomi", "小米", "Xiaomi"), ("redmi", "红米", "Redmi"),
        ("oppo", "OPPO", "OPPO"), ("vivo", "vivo", "vivo"), ("honor", "荣耀", "HONOR"),
        ("meizu", "魅族", "MEIZU"), ("lenovo", "联想", "Lenovo"), ("zte", "中兴", "ZTE"),
        ("nubia", "努比亚", "nubia"),
    ]),
    ("earphone", "传统音频", [
        ("edifier", "漫步者", "Edifier"), ("hivi", "惠威", "HiVi"), ("somic", "硕美科", "Somic"),
        ("shanshui-cn", "山水（国内授权）", "SANSUI CN"), ("fenda", "奋达", "Fenda"),
        ("ikf", "iKF", "iKF"), ("misiom", "觅声", "Misiom"), ("kna", "KNA", "KNA"),
        ("microlab", "麦博", "Microlab"), ("3nod", "三诺", "3NOD"), ("aigo", "爱国者", "aigo"),
        ("newsmy", "纽曼", "Newsmy"), ("teclast", "台电", "Teclast"), ("soaiy", "索爱", "Soaiy"),
    ]),
    ("earphone", "TWS 新锐", [
        ("1more", "万魔", "1MORE"), ("soundcore", "声阔", "Soundcore"), ("qcy", "QCY", "QCY"),
        ("baseus", "倍思", "Baseus"), ("ugreen", "绿联", "UGREEN"), ("pisen", "品胜", "PISEN"),
        ("nank", "南卡", "NANK"), ("sanag", "塞那", "SANAG"), ("torras", "图拉斯", "Torras"),
        ("haylou", "嘿喽", "Haylou"), ("hongmi", "虹觅", "HongMi"),
    ]),
    ("earphone", "HiFi/耳烧", [
        ("moondrop", "水月雨", "Moondrop"), ("simgot", "兴戈", "Simgot"), ("tangzu", "天使吉米", "TANGZU"),
        ("astrotec", "阿思翠", "Astrotec"), ("tfz", "锦瑟香也", "TFZ"), ("rose-technics", "弱水时砂", "Rose Technics"),
        ("dunu", "达音科", "DUNU"), ("fiio", "飞傲", "FiiO"), ("shanling", "山灵", "SHANLING"),
        ("cayin", "凯音", "Cayin"), ("xduoo", "乂度", "xDuoo"), ("nf-audio", "宁梵声学", "NF Audio"),
        ("hifiman", "头领科技", "HIFIMAN"),
    ]),
    ("earphone", "骨传导", [("shokz", "韶音", "Shokz")]),
    ("earphone", "电竞", [
        ("rapoo", "雷柏", "Rapoo"), ("dareu", "达尔优", "DAREU"), ("a4tech", "双飞燕", "A4Tech"),
        ("bloody", "血手幽灵", "Bloody"), ("aula", "狼蛛", "AULA"), ("thunderobot", "雷神", "ThundeRobot"),
        ("machenike", "机械师", "Machenike"), ("colorful", "七彩虹", "Colorful"),
        ("goldenfield", "金河田", "Goldenfield"),
    ]),
    ("earphone", "麦克风/监听", [("takstar", "得胜", "Takstar")]),
    ("earphone", "美国", [
        ("apple", "苹果", "Apple"), ("beats", "Beats", "Beats"), ("bose", "Bose", "Bose"),
        ("jbl", "JBL", "JBL"), ("shure", "舒尔", "Shure"), ("grado", "歌德", "Grado"),
        ("audeze", "Audeze", "Audeze"), ("etymotic", "音特美", "Etymotic"),
        ("westone", "威士顿", "Westone"), ("campfire", "Campfire Audio", "Campfire Audio"),
        ("klipsch", "杰士", "Klipsch"), ("corsair", "海盗船", "Corsair"),
        ("hyperx", "HyperX", "HyperX"), ("steelseries", "赛睿", "SteelSeries"),
        ("alienware", "外星人", "Alienware"),
    ]),
    ("earphone", "瑞士", [("logitech", "罗技", "Logitech")]),
    ("earphone", "日本", [
        ("sony", "索尼", "Sony"), ("audio-technica", "铁三角", "Audio-Technica"),
        ("panasonic", "松下", "Panasonic"), ("jvc", "JVC", "JVC"), ("pioneer", "先锋", "Pioneer"),
        ("yamaha", "雅马哈", "Yamaha"), ("denon", "天龙", "Denon"), ("fostex", "丰达", "Fostex"),
        ("onkyo", "安桥", "Onkyo"), ("final", "Final", "Final"),
    ]),
    ("earphone", "德国", [
        ("sennheiser", "森海塞尔", "Sennheiser"), ("beyerdynamic", "拜亚动力", "beyerdynamic"),
        ("neumann", "纽曼", "Neumann"),
    ]),
    ("earphone", "奥地利", [("akg", "AKG", "AKG")]),
    ("earphone", "英国", [
        ("bowers-wilkins", "宝华韦健", "Bowers & Wilkins"), ("kef", "KEF", "KEF"),
        ("marshall", "马歇尔", "Marshall"),
    ]),
    ("earphone", "丹麦", [("bang-olufsen", "B&O", "Bang & Olufsen")]),
    ("earphone", "法国", [("focal", "劲浪", "Focal"), ("devialet", "帝瓦雷", "Devialet")]),
    ("earphone", "荷兰", [("philips", "飞利浦", "Philips")]),
    ("earphone", "韩国", [("samsung", "三星", "Samsung")]),
    ("earphone", "新加坡", [("creative", "创新", "Creative")]),
    ("earphone", "中国台湾", [
        ("asus-rog", "华硕 ROG", "ASUS ROG"), ("msi", "微星", "MSI"), ("gigabyte", "技嘉", "GIGABYTE"),
    ]),

    # ---------------- 2. 鼠标 ----------------
    ("mouse", "传统外设厂", [
        ("rapoo", "雷柏", "Rapoo"), ("dareu", "达尔优", "DAREU"), ("a4tech", "双飞燕", "A4Tech"),
        ("bloody", "血手幽灵", "Bloody"), ("aula", "狼蛛", "AULA"), ("delux", "多彩", "Delux"),
        ("fuhlen", "富勒", "Fuhlen"), ("inphic", "英菲克", "inphic"), ("newmen", "新贵", "Newmen"),
        ("lenovo", "联想", "Lenovo"), ("huawei", "华为", "Huawei"), ("xiaomi", "小米", "Xiaomi"),
        ("machenike", "机械师", "Machenike"), ("thunderobot", "雷神", "ThundeRobot"),
        ("ipason", "攀升", "IPASON"), ("colorful", "七彩虹", "Colorful"), ("goldenfield", "金河田", "Goldenfield"),
    ]),
    ("mouse", "电竞新锐", [
        ("vgn", "VGN", "VGN"), ("mchose", "迈从", "MCHOSE"), ("atk", "ATK", "ATK"),
        ("vxe", "VXE", "VXE"), ("g-wolves", "游狼", "G-Wolves"), ("ajazz", "黑爵", "AJAZZ"),
        ("lofree", "洛斐", "LOFREE"), ("kzzi", "珂芝", "KZZI"), ("fulin", "腹灵", "FULIN"),
        ("yunzii", "御斧", "Yunzii"), ("lamzu", "兰族", "Lamzu"),
    ]),
    ("mouse", "瑞士", [("logitech", "罗技", "Logitech")]),
    ("mouse", "美国", [
        ("razer", "雷蛇", "Razer"), ("steelseries", "赛睿", "SteelSeries"),
        ("corsair", "海盗船", "Corsair"), ("turtlebeach", "乌龟海岸", "Turtle Beach"),
        ("finalmouse", "Finalmouse", "Finalmouse"), ("microsoft", "微软", "Microsoft"),
        ("apple", "苹果", "Apple"),
    ]),
    ("mouse", "德国", [
        ("cherry", "樱桃", "Cherry"), ("roccat", "冰豹", "ROCCAT"),
        ("endgame-gear", "Endgame Gear", "Endgame Gear"),
    ]),
    ("mouse", "韩国", [("pulsar", "Pulsar", "Pulsar")]),
    ("mouse", "中国台湾", [
        ("zowie", "卓威", "ZOWIE"), ("vaxee", "VAXEE", "VAXEE"), ("asus-rog", "华硕 ROG", "ASUS ROG"),
        ("msi", "微星", "MSI"), ("gigabyte", "技嘉", "GIGABYTE"), ("thermaltake", "曜越 Tt", "Thermaltake"),
        ("coolermaster", "酷冷至尊", "Cooler Master"), ("tesoro", "铁修罗", "Tesoro"),
    ]),
    ("mouse", "中国香港", [("keychron", "Keychron", "Keychron")]),

    # ---------------- 3. 键盘（磁轴 / 机械） ----------------
    ("keyboard", "传统外设厂", [
        ("a4tech", "双飞燕", "A4Tech"), ("rapoo", "雷柏", "Rapoo"), ("dareu", "达尔优", "DAREU"),
        ("aula", "狼蛛", "AULA"), ("lenovo", "联想", "Lenovo"), ("huawei", "华为", "Huawei"),
        ("xiaomi", "小米", "Xiaomi"), ("thunderobot", "雷神", "ThundeRobot"),
        ("machenike", "机械师", "Machenike"), ("ipason", "攀升", "IPASON"),
        ("colorful", "七彩虹", "Colorful"), ("goldenfield", "金河田", "Goldenfield"),
    ]),
    ("keyboard", "客制化/外设厂", [
        ("ajazz", "黑爵", "AJAZZ"), ("blackcanyon", "黑峡谷", "BlackCanyon"), ("yunzii", "御斧", "Yunzii"),
        ("varmilo", "阿米洛", "Varmilo"), ("ganss", "高斯", "GANSS"), ("durgod", "杜伽", "Durgod"),
        ("lofree", "洛斐", "LOFREE"), ("kzzi", "珂芝", "KZZI"), ("fulin", "腹灵", "FULIN"),
        ("mchose", "迈从", "MCHOSE"), ("xinmeng", "新盟", "Xinmeng"), ("shouxi-player", "首席玩家", "Chief Player"),
        ("rk", "雷咖泽", "RK"), ("vgn", "VGN", "VGN"), ("langtu", "狼途", "Langtu"),
        ("wob", "WOB", "WOB"), ("angrymiao", "怒喵", "AngryMiao"),
    ]),
    ("keyboard", "瑞士", [("logitech", "罗技", "Logitech")]),
    ("keyboard", "美国", [
        ("razer", "雷蛇", "Razer"), ("corsair", "海盗船", "Corsair"), ("steelseries", "赛睿", "SteelSeries"),
        ("alienware", "外星人", "Alienware"), ("microsoft", "微软", "Microsoft"), ("apple", "苹果", "Apple"),
    ]),
    ("keyboard", "德国", [("cherry", "樱桃", "Cherry")]),
    ("keyboard", "荷兰", [("wooting", "Wooting", "Wooting")]),
    ("keyboard", "中国台湾", [
        ("asus-rog", "华硕 ROG", "ASUS ROG"), ("msi", "微星", "MSI"), ("gigabyte", "技嘉", "GIGABYTE"),
        ("coolermaster", "酷冷至尊", "Cooler Master"), ("thermaltake", "曜越 Tt", "Thermaltake"),
        ("tesoro", "铁修罗", "Tesoro"), ("ikbc", "ikbc", "ikbc"), ("ducky", "Ducky", "Ducky"),
        ("vortex", "Vortex", "Vortex"),
    ]),
    ("keyboard", "中国香港", [("keychron", "Keychron", "Keychron")]),
    ("keyboard", "韩国", [("leopold", "Leopold", "Leopold")]),
    ("keyboard", "日本", [
        ("hhkb", "HHKB", "HHKB"), ("realforce", "Realforce（燃风）", "Realforce"),
        ("filco", "斐尔可", "FILCO"),
    ]),

    # ---------------- 4. 手柄 ----------------
    ("gamepad", "国内品牌", [
        ("betop", "北通", "Betop"), ("8bitdo", "八位堂", "8BitDo"), ("pxn", "莱仕达", "PXN"),
        ("flydigi", "飞智", "Flydigi"), ("gamesir", "盖世小鸡", "GameSir"), ("mojiang", "墨将", "MoJiang"),
        ("liangzhi", "良值", "Liangzhi"), ("mobapad", "魔派", "Mobapad"), ("gulikit", "谷粒", "GuliKit"),
        ("aojiashi", "澳加狮", "Aojiashi"), ("chike", "炽壳", "Chike"), ("coopreme", "Coopreme", "Coopreme"),
        ("yuyou", "御游", "YuYou"), ("yisuma", "易速马", "YiSuMa"), ("jixiang", "极想", "JiXiang"),
        ("zhidong", "致动", "ZhiDong"), ("subor", "小霸王", "Subor"), ("baishipai", "佰世派", "BaiShiPai"),
        ("leadjoy", "Leadjoy", "Leadjoy"), ("machenike", "机械师", "Machenike"),
        ("lenovo", "联想", "Lenovo"), ("nubia", "努比亚", "nubia"),
    ]),
    ("gamepad", "御三家", [
        ("sony", "索尼", "Sony"), ("microsoft", "微软", "Microsoft"), ("nintendo", "任天堂", "Nintendo"),
    ]),
    ("gamepad", "美国", [
        ("razer", "雷蛇", "Razer"), ("powera", "PowerA", "PowerA"), ("pdp", "PDP", "PDP"),
        ("scuf", "SCUF", "SCUF"), ("victrix", "Victrix", "Victrix"),
        ("turtlebeach", "乌龟海岸", "Turtle Beach"),
    ]),
    ("gamepad", "法国", [("thrustmaster", "图马思特", "Thrustmaster"), ("nacon", "Nacon", "Nacon")]),
    ("gamepad", "日本", [("hori", "HORI", "HORI")]),
    ("gamepad", "瑞士", [("logitech", "罗技", "Logitech")]),

    # ---------------- 5. 音响 ----------------
    ("speaker", "传统音箱", [
        ("edifier", "漫步者", "Edifier"), ("hivi", "惠威", "HiVi"), ("microlab", "麦博", "Microlab"),
        ("fenda", "奋达", "Fenda"), ("3nod", "三诺", "3NOD"), ("qingqibing", "轻骑兵", "QingQiBing"),
        ("shanshui-cn", "山水（国内授权）", "SANSUI CN"), ("goldenfield", "金河田", "Goldenfield"),
        ("chongjibo", "冲击波", "ChongJiBo"), ("shenghui", "声荟", "ShengHui"), ("tianyi", "天逸", "TianYi"),
    ]),
    ("speaker", "智能音箱", [
        ("tmall-genie", "天猫精灵", "Tmall Genie"), ("xiaodu", "小度", "Xiaodu"),
        ("xiaoai", "小爱同学", "XiaoAI"), ("huawei", "华为 Sound", "Huawei Sound"),
        ("dingdong", "叮咚", "DingDong"), ("iflytek", "科大讯飞", "iFlytek"),
    ]),
    ("speaker", "便携/桌面", [
        ("maoking", "猫王", "MaoKing"), ("divoom", "Divoom 点音", "Divoom"), ("soaiy", "索爱", "Soaiy"),
        ("newsmy", "纽曼", "Newsmy"), ("teclast", "台电", "Teclast"), ("baseus", "倍思", "Baseus"),
        ("ugreen", "绿联", "UGREEN"), ("changba", "唱吧", "Changba"),
    ]),
    ("speaker", "HiFi/台式", [
        ("topping", "拓品", "Topping"), ("gustard", "歌诗德", "Gustard"), ("matrix", "矩声", "Matrix Audio"),
        ("qls", "乾龙盛", "QLS"), ("fiio", "飞傲", "FiiO"), ("shanling", "山灵", "SHANLING"),
        ("cayin", "凯音", "Cayin"), ("smsl", "双木三林", "SMSL"), ("xduoo", "乂度", "xDuoo"),
        ("yulong", "钰龙", "Yulong"), ("amazon", "亚马逊 Echo", "Amazon Echo"),
        ("google", "谷歌 Nest", "Google Nest"), ("mcintosh", "麦景图", "McIntosh"),
    ]),
    ("speaker", "日本", [
        ("sony", "索尼", "Sony"), ("yamaha", "雅马哈", "Yamaha"), ("denon", "天龙", "Denon"),
        ("marantz", "马兰士", "Marantz"), ("jvc", "JVC", "JVC"), ("pioneer", "先锋", "Pioneer"),
        ("panasonic", "松下", "Panasonic"), ("onkyo", "安桥", "Onkyo"), ("teac", "TEAC", "TEAC"),
        ("kenwood", "建伍", "Kenwood"), ("sansui", "山水 Sansui", "SANSUI"),
    ]),
    ("speaker", "英国", [
        ("bowers-wilkins", "宝华韦健", "Bowers & Wilkins"), ("kef", "KEF", "KEF"),
        ("monitor-audio", "猛牌", "Monitor Audio"), ("tannoy", "天朗", "Tannoy"),
        ("mission", "美声", "Mission"), ("wharfedale", "乐富豪", "Wharfedale"), ("atc", "ATC", "ATC"),
        ("linn", "Linn", "Linn"), ("naim", "Naim", "Naim"), ("marshall", "马歇尔", "Marshall"),
    ]),
    ("speaker", "丹麦", [
        ("bang-olufsen", "B&O", "Bang & Olufsen"), ("jamo", "尊宝", "Jamo"),
        ("dali", "达尼", "DALI"), ("dynaudio", "丹拿", "Dynaudio"),
    ]),
    ("speaker", "德国", [
        ("elac", "意力", "ELAC"), ("burmester", "柏林之声", "Burmester"), ("canton", "金榜", "Canton"),
    ]),
    ("speaker", "芬兰", [("genelec", "真力", "Genelec")]),
    ("speaker", "法国", [
        ("focal", "劲浪", "Focal"), ("devialet", "帝瓦雷", "Devialet"), ("triangle", "三角", "Triangle"),
    ]),
    ("speaker", "意大利", [("sonus-faber", "世霸", "Sonus Faber"), ("chario", "卓丽", "Chario")]),
    ("speaker", "荷兰", [("philips", "飞利浦", "Philips")]),
    ("speaker", "韩国", [("samsung", "三星", "Samsung"), ("lg", "LG", "LG")]),
    ("speaker", "新加坡", [("creative", "创新", "Creative")]),
    ("speaker", "中国台湾", [("asus-rog", "华硕 ROG", "ASUS ROG")]),

    # ---------------- 6. 鼠标垫 ----------------
    ("mousepad", "电竞垫新锐", [
        ("hufu", "虎符", "HuFu"), ("zhenhuo", "臻火", "ZhenHuo"), ("quaoar", "夸瓦", "QUAOAR"),
        ("lingluqianyu", "铃鹿千羽", "LingLuQianYu"), ("d-glow", "D-glow", "D-glow"),
        ("lajitong", "垃圾桶", "LaJiTong"), ("baize", "白泽", "BaiZe"), ("qingsui", "青穗", "QingSui"),
        ("tianlu", "天路", "TianLu"), ("lingwoke", "凌沃克", "LingWoKe"),
    ]),
    ("mousepad", "键鼠外设厂", [
        ("rapoo", "雷柏", "Rapoo"), ("dareu", "达尔优", "DAREU"), ("aula", "狼蛛", "AULA"),
        ("a4tech", "双飞燕", "A4Tech"), ("bloody", "血手幽灵", "Bloody"), ("thunderobot", "雷神", "ThundeRobot"),
        ("machenike", "机械师", "Machenike"), ("ipason", "攀升", "IPASON"), ("colorful", "七彩虹", "Colorful"),
        ("newsmy", "纽曼", "Newsmy"), ("soaiy", "索爱", "Soaiy"), ("baseus", "倍思", "Baseus"),
        ("ugreen", "绿联", "UGREEN"), ("pisen", "品胜", "PISEN"), ("lofree", "洛斐", "LOFREE"),
        ("xiaomi", "小米", "Xiaomi"), ("huawei", "华为", "Huawei"), ("lenovo", "联想", "Lenovo"),
    ]),
    ("mousepad", "美国", [
        ("razer", "雷蛇", "Razer"), ("logitech", "罗技", "Logitech"), ("steelseries", "赛睿", "SteelSeries"),
        ("corsair", "海盗船", "Corsair"), ("hyperx", "HyperX", "HyperX"),
        ("alienware", "外星人", "Alienware"), ("lethal", "Lethal Gaming Gear", "Lethal Gaming Gear"),
    ]),
    ("mousepad", "日本", [("artisan", "剑匠", "Artisan")]),
    ("mousepad", "德国", [("roccat", "冰豹", "ROCCAT")]),
    ("mousepad", "中国台湾", [
        ("zowie", "卓威", "ZOWIE"), ("vaxee", "VAXEE", "VAXEE"), ("coolermaster", "酷冷至尊", "Cooler Master"),
        ("thermaltake", "曜越 Tt", "Thermaltake"), ("asus-rog", "华硕 ROG", "ASUS ROG"),
        ("msi", "微星", "MSI"),
    ]),
]

# 公开常识级官网域名（供核验流水线优先探测；verified 以实测为准）
CURATED = {
    # 耳机 / 音频
    "huawei": ["consumer.huawei.com"], "xiaomi": ["mi.com"], "oppo": ["oppo.com"], "vivo": ["vivo.com"],
    "honor": ["honor.com"], "meizu": ["meizu.com"], "lenovo": ["lenovo.com.cn"], "zte": ["zte.com.cn"],
    "nubia": ["nubia.com"], "edifier": ["edifier.com"], "hivi": ["hivi.com"], "microlab": ["microlab.com.cn"],
    "3nod": ["3nod.com.cn"], "aigo": ["aigo.com"], "newsmy": ["newsmy.com.cn"], "teclast": ["teclast.com"],
    "1more": ["1more.com"], "soundcore": ["soundcore.com"], "qcy": ["qcy.com"], "baseus": ["baseus.com"],
    "ugreen": ["ugreen.com"], "pisen": ["pisen.com.cn"], "torras": ["torras.com"], "haylou": ["haylou.com"],
    "moondrop": ["moondroplab.com"], "simgot": ["simgotaudio.com"], "dunu": ["duni.com.cn"],
    "fiio": ["fiio.com"], "shanling": ["shanling.com"], "cayin": ["cayin.com"], "xduoo": ["xduoo.com"],
    "nf-audio": ["nfaudio.com"], "hifiman": ["hifiman.com"], "shokz": ["shokz.com"],
    "rapoo": ["rapoo.com"], "dareu": ["dareu.com"], "a4tech": ["a4tech.com"], "bloody": ["bloody.com"],
    "thunderobot": ["thunderobot.com"], "machenike": ["machenike.com"], "colorful": ["colorful.cn"],
    "goldenfield": ["goldenfield.com.cn"], "takstar": ["takstar.com"], "apple": ["apple.com"],
    "ikf": ["ikfaudio.com"], "misiom": ["misiom.cn"], "kna": ["kna-audio.com"],
    "beats": ["beatsbydre.com"], "bose": ["bose.com"], "jbl": ["jbl.com"], "shure": ["shure.com"],
    "grado": ["gradolabs.com"], "audeze": ["audeze.com"], "etymotic": ["etymotic.com"],
    "westone": ["westone.com"], "campfire": ["campfireaudio.com"], "klipsch": ["klipsch.com"],
    "corsair": ["corsair.com"], "hyperx": ["hyperx.com"], "steelseries": ["steelseries.com"],
    "alienware": ["alienware.com"], "logitech": ["logitech.com"], "sony": ["sony.com"],
    "audio-technica": ["audio-technica.com"], "panasonic": ["panasonic.com"], "jvc": ["jvc.com"],
    "pioneer": ["pioneerelectronics.com"], "yamaha": ["yamaha.com"], "denon": ["denon.com"],
    "fostex": ["fostex.com"], "onkyo": ["onkyo.com"], "final": ["final-inc.com"],
    "sennheiser": ["sennheiser.com"], "beyerdynamic": ["beyerdynamic.com"], "neumann": ["neumann.com"],
    "akg": ["akg.com"], "bowers-wilkins": ["bowerswilkins.com"], "kef": ["kef.com"],
    "marshall": ["marshallheadphones.com"], "bang-olufsen": ["bang-olufsen.com"], "focal": ["focal.com"],
    "devialet": ["devialet.com"], "philips": ["philips.com"], "samsung": ["samsung.com"],
    "creative": ["creative.com"], "asus-rog": ["rog.asus.com"], "msi": ["msi.com"], "gigabyte": ["gigabyte.com"],
    # 鼠标
    "delux": ["deluxworld.com"], "inphic": ["inphic.com"], "mchose": ["mchose.net"],
    "atk": ["atkgear.com.cn"], "g-wolves": ["g-wolves.com"], "ajazz": ["a-jazz.com"],
    "lofree": ["lofree.co"], "kzzi": ["kzzi.com"], "yunzii": ["yunzii.com"], "lamzu": ["lamzu.com"],
    "razer": ["razer.com"], "turtlebeach": ["turtlebeach.com"], "finalmouse": ["finalmouse.com"],
    "microsoft": ["microsoft.com"], "cherry": ["cherry.de"], "roccat": ["roccat.com"],
    "endgame-gear": ["endgamegear.com"], "pulsar": ["pulsargaming.com"], "zowie": ["zowie.com"],
    "vaxee": ["vaxee.co"], "thermaltake": ["thermaltake.com"], "coolermaster": ["coolermaster.com"],
    "tesoro": ["tesorotec.com"], "keychron": ["keychron.com"],
    # 键盘
    "blackcanyon": ["blackcanyon.com"], "varmilo": ["varmilo.com"], "durgod": ["durgod.com"],
    "wooting": ["wooting.io"], "ikbc": ["ikbc.com"], "ducky": ["duckychannel.com"],
    "vortex": ["vortexgear.com"], "leopold": ["leopold.co.kr"], "hhkb": ["hhkb.io"],
    "realforce": ["realforce.com"], "filco": ["diatec.co.jp"], "angrymiao": ["angrymiao.com"],
    # 手柄
    "betop": ["betopgame.com"], "8bitdo": ["8bitdo.com"], "pxn": ["pxn.com"], "flydigi": ["flydigi.com"],
    "gamesir": ["gamesir.com"], "mobapad": ["mobapad.com"], "gulikit": ["gulikit.com"],
    "subor": ["subor.com.cn"], "nintendo": ["nintendo.com"],
    "powera": ["powera.com"], "pdp": ["pdp.com"], "scuf": ["scufgaming.com"], "victrix": ["victrixpro.com"],
    "thrustmaster": ["thrustmaster.com"], "nacon": ["nacon.com"], "hori": ["hori.co.jp"],
    # 音响
    "tmall-genie": ["aligenie.com"], "xiaodu": ["xiaodu.com"], "iflytek": ["iflytek.com"],
    "divoom": ["divoom.com"], "changba": ["changba.com"], "smsl": ["smsl-audio.com"],
    "yulong": ["yulongaudio.com"], "amazon": ["amazon.com"], "google": ["store.google.com"],
    "mcintosh": ["mcintoshlabs.com"], "marantz": ["marantz.com"], "teac": ["teac-audio.com"],
    "kenwood": ["kenwood.com"], "monitor-audio": ["monitoraudio.com"], "tannoy": ["tannoy.com"],
    "mission": ["mission.co.uk"], "wharfedale": ["wharfedale.co.uk"], "atc": ["atc.audio"],
    "linn": ["linn.co.uk"], "naim": ["naimaudio.com"], "jamo": ["jamo.com"], "dali": ["daliloudspeakers.com"],
    "dynaudio": ["dynaudio.com"], "elac": ["elac.com"], "burmester": ["burmester.de"],
    "canton": ["canton.de"], "genelec": ["genelec.com"], "triangle": ["trianglehifi.com"],
    "sonus-faber": ["sonusfaber.com"], "chario": ["chario.it"], "lg": ["lg.com"],
    # 鼠标垫
    "artisan": ["artisan-jp.com"], "lethal": ["lethal.gg"],
}


def build_brands():
    """由 SPEC 生成品牌注册表列表。"""
    brands = {}
    for cat, group, items in SPEC:
        for key, zh, en in items:
            b = brands.setdefault(key, {
                "key": key, "zh": zh, "en": en,
                "categories": [], "groups": {}, "region": "中国",
                "official_url": None, "curated": False,
                "verified": False, "status": "待核验",
            })
            if cat not in b["categories"]:
                b["categories"].append(cat)
            b["groups"][cat] = group
            if group in REGION_GROUPS:
                b["region"] = group
    for key, region in REGION_OVERRIDE.items():
        if key in brands:
            brands[key]["region"] = region
    for key, domains in CURATED.items():
        if key in brands:
            brands[key]["official_url"] = "https://" + domains[0]
            brands[key]["curated"] = True
    return [brands[k] for k in sorted(brands)]


def brand_by_key(key):
    return next((b for b in build_brands() if b["key"] == key), None)


if __name__ == "__main__":
    bs = build_brands()
    print("品牌总数:", len(bs))
    from collections import Counter
    print("类型分布:", dict(Counter(c for b in bs for c in b["categories"])))
    print("已配置官网域名:", sum(1 for b in bs if b["official_url"]))
