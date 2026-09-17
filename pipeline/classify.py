# -*- coding: utf-8 -*-
"""
pipeline/classify.py · 产品自动分类
====================================
把任意新产品自动划分到 6 大外设类型，并细分到子类型（TWS/头戴/磁轴/机械…）。
规则基于 名称 + 描述 + 标签 + 参数键值 + URL 类型线索 的关键词匹配，幂等可重复执行。
"""
import re

from . import utils

CATEGORIES = {
    "earphone": "耳机",
    "mouse": "鼠标",
    "keyboard": "键盘",
    "gamepad": "手柄",
    "speaker": "音响",
    "mousepad": "鼠标垫",
}

# 类型关键词（命中即归属，长度代表特异度）
CATEGORY_KEYWORDS = {
    "earphone": [
        "耳机", "耳塞", "耳麦", "头戴", "tws", "入耳", "耳挂", "骨传导", "earphone",
        "headphone", "earbuds", "iems", "头戴式", "真无线", "headset", "earcups",
        "casque", "écouteurs", "auriculares", "kopfhörer", "in-ear", "over-ear",
        "on-ear", "anc", "noise cancelling", "noise-cancelling", "earphones",
        "buds", "airpods", "earbud", "wireless earbuds", "bluetooth earphone",
        "circumaural", "supra-aural",
    ],
    "mouse": [
        "鼠标", "mouse", "gaming mouse", "mice", "trackball", "轨迹球", "souris",
        "ratón", "ergonomic mouse", "wireless mouse", "gaming-mice", "wired mouse",
        "mmo mouse", "fps mouse", "esports mouse", "ultralight mouse", "superlight",
        "deathadder", "viper", "naga", "basilisk", "g pro", "g502", "g304", "g305",
        "g403", "g703", "g903", "g102", "g203", "mx master", "mx anywhere", "lift",
        "model o", "model d", "g-wolves", "lamzu", "atlantis", "mchose", "vgn",
        "atk", "vxe", "pulsar", "zowie", "vaxee", "ec1", "ec2", "fk1", "s2", "xm1",
        "xm2", "finalmouse", "starlight", "a4tech", "bloody", "dareu", "rapoo",
        "gaming mice", "wireless mice", "pro x superlight", "mamba", "cobra",
    ],
    "keyboard": [
        "键盘", "keyboard", "磁轴", "机械键盘", "静电容", "客制化", "keys",
        "mechanical", "clavier", "teclado", "tastatur", "keycaps", "keycap",
        "hotswap", "hot-swap", "gasket", "switches", "tkl", "75%", "65%", "60%",
        "magnetic switch", "hall effect", "rapid trigger", "omni point",
        "apex pro", "huntsman", "blackwidow", "k70", "k95", "k100", "g915",
        "g815", "g913", "ducky", "varmilo", "akko", "keychron", "ikbc", "ganss",
        "rk ", "lofree", "kzzi", "nj80", "nj81", "wooting", "drunkdeer",
        "keyboard switches", "keyboard kit", "barebone", "qwerty", "macropad",
        "wob", "unikorn", "alice", "split keyboard", "ortholinear", "keyboard case",
    ],
    "gamepad": [
        "手柄", "gamepad", "controller", "摇杆", "手把", "manette", "mando",
        "dualsense", "dualshock", "playstation", "xbox wireless controller",
        "elite series", "pro controller", "joy-con", "8bitdo", "sn30", "ultimate",
        "gulikit", "flydigi", "apex 3", "bacon", "scuf", "victrix", "wolverine",
        "kishi", "gamesir", "x2 pro", "nacon", "thrustmaster", "eswap",
        "racing wheel", "arcade stick", "fight stick", "gamepad wireless",
        "wireless controller", "game controller", "mobile controller",
        "backbone", "powera", "pdp ", "horipad", "pad pro",
    ],
    "speaker": [
        "音箱", "音响", "扬声器", "回音壁", "解码", "耳放", "功放", "speaker",
        "soundbar", "dac", "书架箱", "监听音箱", "enceinte", "altavoz", "subwoofer",
        "bookshelf", "tower speaker", "floorstanding", "smart speaker", "echo",
        "nest", "homepod", "sonos", "flip", "charge", "boom", "mega", "xb",
        "srs-", "zeppelin", "stanmore", "woburn", "kef ls50", "genelec", "hs5",
        "hs7", "dali", "dynaudio", "party speaker", "bluetooth speaker",
        "wireless speaker", "soundcore motion", "tronsmart", "anker soundcore",
        "soundbar with", "home theater", "boombox", "computer speaker",
        "multimedia speaker", "portable speaker", "speakers", "woofer",
        "desktop speaker", "bookshelf speaker", "active speaker", "passive speaker",
        "high-fidelity speaker", "hifi speaker",
    ],
    "mousepad": [
        "鼠标垫", "桌垫", "布垫", "树脂垫", "玻璃垫", "mousepad", "mousemat",
        "pads", "tapis", "desk mat", "deskmat", "mouse pad", "mouse mat",
        "g640", "qck", "g-sr", "gigantus", "saturn", "hayate", "otsu", "hien",
        "raiden", "skypad", "artisan", "padsmith", "cloth pad", "glass pad",
        "speed pad", "control pad", "hybrid pad", "mousepad premium", "hard pad",
        "soft pad", "mousepad xl", "extended mousepad",
    ],
}

# 品牌产品族名称关键词（补足 URL 线索缺失时的判定；名称命中即强信号）
BRAND_HINTS = {
    "earphone": [
        "airpods", "quietcomfort", "qc35", "qc45", "qc ultra", "wh-1000", "wf-1000",
        "galaxy buds", "freebuds", "soundcore", "liberty", "space q45", "moondrop",
        "momentum", "hd600", "hd650", "hd660", "hd800", "dt 770", "dt 880",
        "dt 990", "ath-m50", "ath-m40", "shure se", "westone", "campfire",
        "audeze", "lcd-", "hifiman", "sundara", "arya", "ananda", "he400",
        "he1000", "deva", "edifier w", "soundpeats", "baseus", "qcy", "haylou",
        "sabbat", "edifier tws", "taotronics", "tribit", "marshall major",
        "bose quiet", "sony xm", "jbl tune", "jbl live", "jbl reflect",
        "soundcore p30", "soundcore aero", "soundcore liberty", "1more",
        "moondrop chu", "moondrop aria", "kz ", "trn ", "cca ", "tinhifi",
        "simgot", "fiio fd", "fiio fa", "shuoer", "tangzu", "hidisz", "letshuoer",
        "kiwi ears", "thieaudio", "64 audio", "focal bathys", "focal clear",
        "focal utopia", "meze", "audeze lcd", "hifiman edition",
    ],
    "mouse": [
        "g pro", "g502", "g102", "g203", "g304", "g305", "g403", "g703", "g903",
        "g604", "g402", "g400s", "g300s", "mx master", "mx anywhere", "mx ergo",
        "lift", "m331", "m330", "m590", "m650", "m720", "m185", "m190", "m90",
        "m100", "m110", "marathon", "gaming mouse", "razer viper", "deathadder",
        "naga", "basilisk", "mamba", "cobra", "lancehead", "razer orochi",
        "razer atheris", "corsair scimitar", "corsair m65", "corsair glaive",
        "corsair dark core", "corsair harpoon", "corsair ironclaw", "corsair katar",
        "steelseries rival", "steelseries aerox", "steelseries prime",
        "steelseries sensei", "steelseries rival 3", "rival 5", "rival 600",
        "zowie", "ec1", "ec2", "fk1", "fk2", "s1", "s2", "za11", "za12", "za13",
        "vaxee", "np-01", "outset ax", "xe", "pulsar", "x2", "x2h", "xlite",
        "xm1", "xm2", "xm2w", "g-wolves", "hati", "skoll", "model o", "model d",
        "model o-", "glorious model", "finalmouse", "starlight", "ultralight",
        "air58", "gpw", "superlight", "g pro x superlight", "atk", "vxe",
        "mchose", "vgn", "ajazz", "darmoshark", "vancer", "lamzu", "atlantis",
        "maya", "thorn", "eggs", "xtrfy", "m42", "m4", "mz1", "endgame gear",
        "op1", "op18k", "razer dav3", "deathadder v3", "viper v2", "viper v3",
        "basilisk v3", "naga v2",
    ],
    "keyboard": [
        "g915", "g815", "g913", "g413", "g512", "g513", "g610", "g710", "mx keys",
        "mx mechanical", "k70", "k95", "k100", "k63", "k65", "k68", "k70 rgb",
        "apex pro", "apex 7", "apex 5", "apex 3", "blackwidow", "huntsman",
        "razer ornata", "razer cynosa", "razer tartarus", "ducky one", "ducky shine",
        "varmilo", "va87", "va108", "akko", "3087", "3098", "3108", "keychron",
        "k2", "k4", "k6", "k8", "q1", "q2", "q3", "v1", "v2", "ikbc", "c87",
        "f87", "w200", "ganss", "gs87", "alt71", "gk87", "rk ", "royal kludge",
        "lofree", "flow", "kzzi", "k75", "k68", "nj80", "nj81", "nj68", "womier",
        "wooting", "60he", "80he", "drunkdeer", "a75", "g60", "mchose", "vgn",
        "atk", "qk", "zoom65", "zoom75", "mode65", "sonnet", "unikorn", "owlab",
        "gmk", "keycaps", "switches", "gasket", "tkl", "60%", "65%", "75%",
        "mechanical keyboard", "magnetic keyboard", "hall effect keyboard",
        "thock", "hotswap", "hot-swap", "wob", "lynx", "neo65", "neo75",
    ],
    "gamepad": [
        "dualsense", "dualshock", "xbox wireless controller", "xbox series",
        "elite series 2", "elite series 3", "pro controller", "joy-con",
        "switch pro", "8bitdo", "sn30", "sn30 pro", "ultimate", "pro 2",
        "gulikit", "kingkong", "zen pro", "flydigi", "apex 3", "apex 4", "vader",
        "direwolf", "beacon", "bacon", "gamesir", "t4", "t3", "x2", "g7",
        "nova lite", "scuf", "reflex", "instinct", "victrix", "gambit", "pro bfg",
        "wolverine", "v2 chroma", "kishi", "razer raiju", "backbone", "powera",
        "enhanced", "fusion", "spectra", "pdp", "afterglow", "recon", "nacon",
        "revolution", "pro controller", "hori", "split pad", "fighting commander",
        "thrustmaster", "eswap", "racing wheel", "t248", "t300", "t150", "g29",
        "g920", "g923", "wheel", "pedals", "arcade stick", "fight stick", "mayflash",
        "f500", "f300", "betop", "beitong", "北通", "莱仕达", "飞智", "魔派", "谷粒",
        "盖世小鸡", "墨将",
    ],
    "speaker": [
        "echo", "echo dot", "echo studio", "nest audio", "nest hub", "homepod",
        "sonos", "one sl", "era 100", "era 300", "beam", "arc", "ray", "sub",
        "jbl flip", "jbl charge", "jbl xtreme", "jbl boombox", "jbl pulse",
        "jbl go", "jbl clip", "sony srs", "srs-xb", "srs-xg", "srs-xe", "xb",
        "marshall", "stanmore", "acton", "woburn", "kilburn", "emerton", "willen",
        "b&o", "beosound", "beoplay", "kef ls50", "kef lsx", "kef q", "genelec",
        "hs5", "hs7", "hs8", "adam audio", "yamaha hs", "krk", "jbl 305", "dali",
        "oberon", "spektor", "opticon", "dynaudio", "emit", "special forty",
        "elac", "debut", "unifi", "bowers", "formation", "zeppelin", "宝华韦健",
        "sony xg", "xiaomi sound", "huawei sound", "soundcore motion", "motion+",
        "motion boom", "anker", "tronsmart", "soundbar", "bookshelf", "floorstanding",
        "subwoofer", "home theater", "party speaker", "boombox", "smart speaker",
        "edifier r", "edifier m", "edifier s", "edifier g", "惠威", "漫步者",
        "microlab", "麦博", "creative pebble", "creative stage", "logitech z",
        "z333", "z407", "z623", "z625", "z906",
    ],
    "mousepad": [
        "g640", "qck", "qck heavy", "g-sr", "g-sr-se", "gigantus", "gigantus v2",
        "saturn", "saturn pro", "hayate", "otsu", "hien", "raiden", "shidenkai",
        "skypad", "glass pad", "artisan", "zero", "xsoft", "mid", "padsmith",
        "empress", "temple of dreams", "esptiger", "tang dao", "razer strider",
        "vaxee pa", "vaxee pb", "vaxee pd", "lgg", "lethal gaming gear",
        "saturn pro", "venus pro", "jupiter pro", "puretrak", "tiger", "icy",
        "gt-r", "xtrfy gp4", "gp4", "gpx", "coolermaster mp511", "mp510",
        "mp511", "mpc450", "corsair mm", "mm300", "mm350", "mm700", "steelseries",
        "hyperx fury", "fury s", "fury xl", "desk mat", "deskmat", "mouse pad",
        "mousepad", "桌垫", "鼠标垫", "凌沃克", "虎符", "臻火", "铃鹿千羽",
    ],
}

FALLBACK_SUBTYPE = "未分类"

# 子类型关键词（按类型细分）
SUBTYPE_RULES = {
    "earphone": [
        ("TWS", ["tws", "真无线", "蓝牙耳机", "入耳式无线", "耳塞式", "earbuds", "buds", "airpods", "freebuds", "galaxy buds", "soundcore liberty", "qcy t", "pro 2", "pro 3", "anc"]),
        ("骨传导", ["骨传导", "bone conduction", "openrun", "openswim", "openear", "openfit"]),
        ("游戏", ["游戏", "电竞", "gaming", "耳麦", "7.1", "g pro x", "blackshark", "kraken", "barracuda", "arctic", "cloud "]),
        ("监听·麦克风", ["监听", "麦克风", "monitor", "studio", "pro x", "dt ", "ath-m", "sr840", "tak55", "hd600", "hd650", "hd800", "sr-", "reference"]),
        ("头戴", ["头戴", "罩耳", "over-ear", "on-ear", "包耳", "quietcomfort", "wh-1000", "momentum", "hd ", "dt ", "ath-m", "marshall major", "airpods max"]),
        ("HiFi", ["hifi", "高保真", "动圈", "动铁", "平板", "静电", "入耳", "iem", "开放式", "封闭式", "mmcx", "2pin", "moondrop", "simgot", "shuoer", "fiio", "tin", "trn", "cca", "kz ", "campfire", "audeze", "hifiman", "64 audio", "thieaudio", "letshuoer", "tangzu", "hidisz"]),
    ],
    "mouse": [
        ("办公", ["办公", "静音", "蓝牙鼠标", "m系列", "mx master", "anywhere", "magic mouse", "office", "ergo", "lift", "m330", "m331", "m590", "m650", "m720", "m185", "m190", "m90", "m100", "marathon"]),
        ("电竞", ["电竞", "游戏", "gaming", "g pro", "viper", "deathadder", "naga", "basilisk", "dpi", "回报率", "微动", "传感器", "superlight", "model o", "zowie", "vaxee", "pulsar", "xm1", "xm2", "finalmouse", "g-wolves", "mchose", "vgn", "atk", "vxe", "lamzu", "endgame", "razer", "steelseries", "corsair", "hyperx", "logitech g", "gpw", "superlight", "dav3", "viper v"]),
    ],
    "keyboard": [
        ("磁轴", ["磁轴", "磁力", "霍尔", "he", "hall effect", "rapid trigger", "omni point", "模拟光轴", "60he", "80he", "apex pro", "huntsman", "wooting", "drunkdeer", "a75", "magnetic", "magnet"]),
        ("静电容", ["静电容", "静电容量", "hhkb", "realforce", "燃风", "topre"]),
        ("薄膜", ["薄膜", "membrane"]),
        ("机械", ["机械", "机械键盘", "轴", "cherry", "热插拔", "gasket", "客制化", "keyboard", "keycap", "switches", "tkl", "75%", "65%", "60%", "hotswap", "ducky", "varmilo", "akko", "keychron", "ikbc", "ganss", "lofree", "kzzi", "nj80", "womier"]),
    ],
    "gamepad": [
        ("主机", ["ps5", "xbox", "switch", "playstation", "dualsense", "xbox 无线", "pro 手柄", "xbox series", "elite series", "pro controller", "joy-con"]),
        ("精英", ["精英", "elite", "edge", "八爪鱼", "宙斯", "wolverine", "eswap", "scuf", "victrix", "apex 3", "apex 4", "vader", "kingkong", "zen pro"]),
        ("便携", ["便携", "拉伸", "手机", "hori", "split pad", "mobile", "kishi", "backbone", "x2", "g7"]),
        ("第三方", ["第三方", "多平台", "无线手柄", "蓝牙手柄", "2.4g", "gamepad", "8bitdo", "sn30", "ultimate", "gamesir", "nacon", "thrustmaster", "powera", "pdp", "beitong", "北通", "莱仕达", "飞智", "盖世小鸡", "魔派", "谷粒", "墨将"]),
    ],
    "speaker": [
        ("智能音箱", ["智能", "语音", "小爱", "小度", "天猫精灵", "叮咚", "echo", "nest", "assistant", "homepod"]),
        ("监听", ["监听", "monitor", "genelec", "hs5", "hs7", "hs8", "真力", "studio", "adam", "krk", "yamaha hs"]),
        ("回音壁", ["回音壁", "soundbar", "影院", "beam", "arc", "ray", "sonos"]),
        ("便携蓝牙", ["便携", "蓝牙音箱", "防水", "party", "srs-", "xb", "flip", "charge", "boombox", "pulse", "go", "clip", "xtreme", "beosound a1", "m230", "sound joy", "motion", "tronsmart"]),
        ("桌面音箱", ["桌面", "桌面音箱", "多媒体", "蓝牙音箱", "zeppelin", "stanmore", "woburn", "acton", "edifier r", "edifier m", "creative", "logitech z", "z333", "z407", "z623", "z625", "z906"]),
        ("HiFi", ["hifi", "书架", "有源", "无源", "解码", "耳放", "dac", "同轴", "落地", "高保真", "kef", "dali", "dynaudio", "elac", "bowers", "focal", "sonus", "floorstanding", "bookshelf"]),
    ],
    "mousepad": [
        ("速度垫", ["速度", "speed", "zero", "g640", "滑", "hayate", "raiden", "skypad", "glide"]),
        ("控制垫", ["控制", "control", "qck", "g-sr", "gigantus", "saturn", "vaxee", "pa ", "gigantus v2", "empress", "temple"]),
        ("混合垫", ["混合", "hybrid", "strider", "hien", "平衡", "otsu", "jupiter", "venus"]),
    ],
}


def _text_of(product):
    parts = [
        product.get("name", ""),
        product.get("description", ""),
        " ".join(product.get("tags", [])),
    ]
    for k, v in (product.get("specs") or {}).items():
        parts.append(k)
        parts.append(str(v))
    for k, v in (product.get("extra") or {}).items():
        parts.append(str(v))
    return " ".join(parts)


def _match_kw(text, kw):
    """关键词匹配：短词/数字词用词边界，避免误命中（k2、s2、60% 等）。"""
    k = kw.strip()
    if not k:
        return False
    if len(k) <= 2 or k[-1].isdigit() or "%" in k or any(c in k for c in "-+."):
        return bool(re.search(r"(?<![0-9a-z])" + re.escape(k) + r"(?![0-9a-z])", text))
    return k in text


def classify_category(product, current=None):
    """判定 6 大类型。
    评分 = (命中关键词数, 最长命中关键词长度, 名称品牌提示加分)：
    名称品牌提示（BRAND_HINTS）命中视为强信号（+3 次命中、长度按提示词计）。
    """
    text = _text_of(product).lower()
    name = (product.get("name") or "").lower()
    scores = {}
    for cat, kws in CATEGORY_KEYWORDS.items():
        s = 0
        mx = 0
        for k in kws:
            if _match_kw(text, k):
                s += 1
                mx = max(mx, len(k))
        for k in BRAND_HINTS.get(cat, []):
            if _match_kw(name, k):
                s += 3
                mx = max(mx, len(k) + 3)
        if s:
            scores[cat] = (s, mx)
    if not scores:
        return current or "unclassified"
    best = max(scores, key=lambda c: (scores[c][0], scores[c][1]))
    # 已有合法类型且得分不低于新判定时保持稳定（幂等）
    if current in CATEGORIES and scores.get(current, (0, 0)) >= scores[best]:
        return current
    return best


def classify_subtype(product, category):
    text = _text_of(product).lower()
    rules = SUBTYPE_RULES.get(category, [])
    for subtype, kws in rules:
        if any(k.lower() in text for k in kws):
            return subtype
    return FALLBACK_SUBTYPE


def classify_product(product, force=False):
    """对单个产品执行分类，原地写入 category/subtype，返回 (category, subtype)。"""
    category = classify_category(product, product.get("category"))
    subtype = classify_subtype(product, category)
    product["category"] = category
    product["subtype"] = subtype
    return category, subtype


def classify_all(products):
    """批量分类，返回变更数。"""
    changed = 0
    for p in products:
        before = (p.get("category"), p.get("subtype"))
        classify_product(p)
        after = (p.get("category"), p.get("subtype"))
        if before != after:
            changed += 1
    return changed


if __name__ == "__main__":
    utils.setup_logging()
    data = utils.load_json(utils.data_path("products.json"), {"products": []})
    n = classify_all(data["products"])
    print("已分类产品:", len(data["products"]), "变更:", n)
    from collections import Counter
    print("类型分布:", dict(Counter(p["category"] for p in data["products"])))
