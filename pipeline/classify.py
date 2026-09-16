# -*- coding: utf-8 -*-
"""
pipeline/classify.py · 产品自动分类
====================================
把任意新产品自动划分到 6 大外设类型，并细分到子类型（TWS/头戴/磁轴/机械…）。
规则基于 名称 + 描述 + 标签 + 参数键值 的关键词匹配，幂等可重复执行。
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

# 类型关键词（命中即归属）
CATEGORY_KEYWORDS = {
    "earphone": ["耳机", "耳塞", "耳麦", "头戴", "tws", "入耳", "耳挂", "骨传导", "earphone", "headphone", "earbuds", "iems", "头戴式", "真无线", "headset", "earcups", "casque", "écouteurs", "auriculares", "kopfhörer"],
    "mouse": ["鼠标", "mouse", "gaming mouse", "mice", "trackball", "轨迹球", "souris", "ratón"],
    "keyboard": ["键盘", "keyboard", "磁轴", "机械键盘", "静电容", "客制化", "keys", "mechanical", "clavier", "teclado", "tastatur"],
    "gamepad": ["手柄", "gamepad", "controller", "摇杆", "手把", "manette", "mando"],
    "speaker": ["音箱", "音响", "扬声器", "回音壁", "解码", "耳放", "功放", "speaker", "soundbar", "dac", "书架箱", "监听音箱", "enceinte", "altavoz"],
    "mousepad": ["鼠标垫", "桌垫", "布垫", "树脂垫", "玻璃垫", "mousepad", "mousemat", "pads", "tapis"],
}

# 子类型关键词（按类型细分）
SUBTYPE_RULES = {
    "earphone": [
        ("TWS", ["tws", "真无线", "蓝牙耳机", "入耳式无线", "耳塞式"]),
        ("骨传导", ["骨传导", "bone conduction", "openrun", "openswim"]),
        ("游戏", ["游戏", "电竞", "gaming", "耳麦", "7.1"]),
        ("监听·麦克风", ["监听", "麦克风", "monitor", "studio", "pro x", "dt ", "ath-m", "sr840", "tak55"]),
        ("头戴", ["头戴", "罩耳", "over-ear", "on-ear", "包耳"]),
        ("HiFi", ["hifi", "高保真", "动圈", "动铁", "平板", "静电", "入耳", "iem", "开放式", "封闭式", "mmcx", "2pin"]),
    ],
    "mouse": [
        ("办公", ["办公", "静音", "蓝牙鼠标", "m系列", "mx master", "anywhere", "magic mouse", "office"]),
        ("电竞", ["电竞", "游戏", "gaming", "g pro", "viper", "deathadder", "dpi", "回报率", "微动", "传感器"]),
    ],
    "keyboard": [
        ("磁轴", ["磁轴", "磁力", "霍尔", "he", "hall effect", "rapid trigger", "omni point", "模拟光轴", "60he", "80he", "apex pro", "huntsman"]),
        ("静电容", ["静电容", "静电容量", "hhkb", "realforce", "燃风", "topre"]),
        ("薄膜", ["薄膜", "membrane"]),
        ("机械", ["机械", "机械键盘", "轴", "cherry", "热插拔", "gasket", "客制化", "keyboard"]),
    ],
    "gamepad": [
        ("主机", ["ps5", "xbox", "switch", "playstation", "dualsense", "xbox 无线", "pro 手柄"]),
        ("精英", ["精英", "elite", "edge", "八爪鱼", "宙斯", "wolverine", "eswap", "scuf", "victrix"]),
        ("便携", ["便携", "拉伸", "手机", "hori", "split pad", "mobile"]),
        ("第三方", ["第三方", "多平台", "无线手柄", "蓝牙手柄", "2.4g", "gamepad"]),
    ],
    "speaker": [
        ("智能音箱", ["智能", "语音", "小爱", "小度", "天猫精灵", "叮咚", "echo", "nest", "assistant"]),
        ("监听", ["监听", "monitor", "genelec", "hs5", "hs7", "真力", "studio"]),
        ("回音壁", ["回音壁", "soundbar", "影院"]),
        ("便携蓝牙", ["便携", "蓝牙音箱", "防水", "party", "srs-", "xb", "flip", "charge", "beosound a1", "m230", "sound joy"]),
        ("桌面音箱", ["桌面", "桌面音箱", "多媒体", "蓝牙音箱", "zeppelin", "stanmore", "woburn"]),
        ("HiFi", ["hifi", "书架", "有源", "无源", "解码", "耳放", "dac", "同轴", "落地", "高保真"]),
    ],
    "mousepad": [
        ("速度垫", ["速度", "speed", "zero", "g640", "滑"]),
        ("控制垫", ["控制", "control", "qck", "g-sr", "gigantus", "saturn", "vaxee", "pa "]),
        ("混合垫", ["混合", "hybrid", "strider", "hien", "平衡"]),
    ],
}

FALLBACK_SUBTYPE = "未分类"


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


def classify_category(product, current=None):
    """判定 6 大类型。
    评分 = (命中关键词数, 最长命中关键词长度)：长度代表特异度，
    解决「鼠标垫」与「鼠标」同时命中时的误判。
    """
    text = _text_of(product).lower()
    scores = {}
    for cat, kws in CATEGORY_KEYWORDS.items():
        s = 0
        mx = 0
        for k in kws:
            if k.lower() in text:
                s += 1
                mx = max(mx, len(k))
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
