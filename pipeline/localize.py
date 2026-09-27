# -*- coding: utf-8 -*-
"""localize.py · 产品数据中文化
================================
离线术语词典翻译：为每个产品生成 name_zh（中文名），
并尽可能把描述/标签中的常见术语替换为中文。
保留原始 name（英文）作为对照；品牌名替换为注册表中文名。
"""
import re

from . import utils

# 品牌中文名（由 brand_registry 提供，运行时注入）
# 品牌名 → 中文（用于名称里的品牌词替换）
BRAND_ZH = {
    "razer": "雷蛇", "logitech": "罗技", "logitech g": "罗技G", "steelseries": "赛睿",
    "corsair": "海盗船", "hyperx": "HyperX", "sony": "索尼", "bose": "Bose",
    "jbl": "JBL", "sennheiser": "森海塞尔", "beyerdynamic": "拜亚动力", "akg": "AKG",
    "audio-technica": "铁三角", "panasonic": "松下", "jvc": "JVC", "pioneer": "先锋",
    "yamaha": "雅马哈", "shure": "舒尔", "grado": "歌德", "audeze": "Audeze",
    "edifier": "漫步者", "soundcore": "声阔", "ankor": "安克", "1more": "万魔",
    "qcy": "QCY", "baseus": "倍思", "ugreen": "绿联", "pisen": "品胜",
    "nank": "南卡", "haylou": "嘿喽", "moondrop": "水月雨", "simgot": "兴戈",
    "dunu": "达音科", "fiiO": "飞傲", "shanling": "山灵", "cayin": "凯音",
    "shokz": "韶音", "rapoo": "雷柏", "dareu": "达尔优", "a4tech": "双飞燕",
    "bloody": "血手幽灵", "ajazz": "黑爵", "varmilo": "阿米洛", "ganss": "高斯",
    "durgod": "杜伽", "lofree": "洛斐", "vgn": "VGN", "mchose": "迈从",
    "atk": "ATK", "vxe": "VXE", "g-wolves": "游狼", "lamzu": "兰族",
    "keychron": "Keychron", "leopold": "Leopold", "filco": "斐尔可", "hhkb": "HHKB",
    "realforce": "燃风", "wooting": "Wooting", "8bitdo": "八位堂", "8bitdo": "八位堂",
    "8bitdo": "八位堂", "gamesir": "盖世小鸡", "gulikit": "谷粒", "mobapad": "魔派",
    "powera": "PowerA", "scuf": "SCUF", "thrustmaster": "图马思特", "nacon": "Nacon",
    "hori": "HORI", "nintendo": "任天堂", "microsoft": "微软", "apple": "苹果",
    "beats": "Beats", "huawei": "华为", "xiaomi": "小米", "redmi": "红米",
    "oppo": "OPPO", "vivo": "vivo", "honor": "荣耀", "meizu": "魅族",
    "lenovo": "联想", "zte": "中兴", "nubia": "努比亚", "asus": "华硕",
    "msi": "微星", "gigabyte": "技嘉", "zowie": "卓威", "vaxee": "VAXEE",
    "turtle beach": "乌龟海岸", "pulsar": "Pulsar", "finalmouse": "Finalmouse",
    "g pro": "G Pro", "glorious": "Glorious", "ninjutso": "Ninjutso",
}

# 外设术语词典：长词在前（避免子串误替换）
DESC_TERM_ZH = [
    # —— 描述/卖点高频词（用于整句描述中文化） ——
    ("immersive", "沉浸式"), ("crystal clear", "清澈通透"), ("premium", "旗舰级"),
    ("high-quality", "高品质"), ("high quality", "高品质"), ("exceptional", "出色"),
    ("superior", "卓越"), ("ultimate", "极致"), ("flagship", "旗舰"), ("compact", "小巧"),
    ("portable", "便携"), ("durable", "耐用"), ("sturdy", "坚固"), ("precise", "精准"),
    ("responsive", "响应灵敏"), ("low latency", "低延迟"), ("ultra-low latency", "超低延迟"),
    ("lag-free", "无延迟"), ("seamless", "无缝"), ("versatile", "多用途"),
    ("customizable", "可自定义"), ("adjustable", "可调节"), ("removable", "可拆卸"),
    ("detachable", "可拆卸"), ("swappable", "可更换"), ("replaceable", "可更换"),
    ("built-in", "内置"), ("integrated", "集成"), ("enhanced", "增强"),
    ("improved", "改进"), ("upgraded", "升级"), ("next-generation", "新一代"),
    ("next gen", "新一代"), ("cutting-edge", "前沿"), ("innovative", "创新"),
    ("intuitive", "直观易用"), ("user-friendly", "用户友好"), ("easy-to-use", "易用"),
    ("comfortable", "舒适"), ("all-day comfort", "全天舒适"), ("breathable", "透气"),
    ("soft", "柔软"), ("plush", "柔软"), ("cushioned", "加厚缓震"), ("memory foam", "记忆棉"),
    ("long battery life", "超长续航"), ("battery life", "续航"), ("up to 30 hours", "续航长达30小时"),
    ("fast charging", "快充"), ("quick charge", "快充"), ("usb-c", "USB-C"),
    ("type-c", "Type-C"), ("bluetooth 5.3", "蓝牙5.3"), ("bluetooth 5.2", "蓝牙5.2"),
    ("bluetooth 5.0", "蓝牙5.0"), ("multi-point", "多点连接"), ("multipoint", "多点连接"),
    ("dual device", "双设备"), ("dual-connect", "双连接"), ("auto-pairing", "自动配对"),
    ("water resistant", "防水"), ("ipx4", "IPX4防水"), ("ipx5", "IPX5防水"), ("ipx6", "IPX6防水"),
    ("ip67", "IP67防护"), ("ip68", "IP68防护"), ("dust-proof", "防尘"),
    ("app support", "App支持"), ("companion app", "配套App"), ("eq tuning", "EQ调音"),
    ("custom eq", "自定义EQ"), ("sound profile", "声音风格"), ("sound signature", "声音风格"),
    ("spatial audio", "空间音频"), ("360 audio", "360度音频"), ("dolby atmos", "杜比全景声"),
    ("hi-res audio", "高解析音频"), ("lossless", "无损"), ("aptx", "aptX"),
    ("ldac", "LDAC"), ("multi-driver", "多单元"), ("dual driver", "双单元"),
    ("dynamic driver", "动圈单元"), ("planar magnetic", "平板振膜"), ("electrostatic", "静电"),
    ("titanium driver", "钛膜单元"), ("beryllium", "铍振膜"), ("diaphragm", "振膜"),
    ("frequency response", "频响"), ("impedance", "阻抗"), ("sensitivity", "灵敏度"),
    ("pivoting", "可旋转"), ("swivel", "可旋转"), ("folding", "可折叠"), ("foldable", "可折叠"),
    ("360-degree", "360度"), ("rotating", "旋转"), ("telescopic", "伸缩"),
    ("rgb lighting", "RGB灯效"), ("rgb", "RGB"), ("led indicators", "LED指示灯"),
    ("haptic feedback", "触觉反馈"), ("vibration feedback", "震动反馈"), ("rumble", "震动"),
    ("gyroscope", "陀螺仪"), ("6-axis", "六轴"), ("motion control", "体感控制"),
    ("programmable buttons", "可编程按键"), ("remappable", "可自定义映射"),
    ("onboard memory", "板载存储"), ("macro", "宏"), ("polling rate", "回报率"),
    ("1000hz", "1000Hz"), ("8000hz", "8000Hz"), ("dpi", "DPI"), ("cpi", "CPI"),
    ("optical switches", "光轴"), ("tactile", "段落感"), ("linear", "线性"),
    ("clicky", "清脆"), ("silent", "静音"), ("quiet", "静音"), ("thocky", "闷厚"),
    ("pbt keycaps", "PBT键帽"), ("double-shot", "双色注塑"), ("doubleshot", "双色注塑"),
    ("cherry profile", "Cherry高度"), ("oem profile", "OEM高度"), ("sa profile", "SA高度"),
    ("north-facing", "上灯位"), ("south-facing", "下灯位"), ("screw-in stabilizers", "螺丝卫星轴"),
    ("plate-mounted", "钢板卫星轴"), ("pcb-mounted", "PCB卫星轴"), ("gasket mounted", "Gasket结构"),
    ("poron", "Poron棉"), ("foam", "消音棉"), ("case foam", "底棉"),
    ("multi-layout", "多配列"), ("wireless mode", "无线模式"), ("bluetooth mode", "蓝牙模式"),
    ("2.4g", "2.4G"), ("2.4ghz", "2.4GHz"), ("wired mode", "有线模式"),
    ("usb wired", "USB有线"), ("detachable cable", "可拆卸线缆"), ("braided cable", "编织线"),
    ("coiled cable", "弹簧线"), ("aviation connector", "航插头"),
    ("wireless gaming", "无线游戏"), ("esports", "电竞"), ("e-sports", "电竞"),
    ("competitive gaming", "竞技游戏"), ("professional gaming", "专业电竞"),
    ("streaming", "直播"), ("content creation", "内容创作"), ("studio", "录音棚"),
    ("podcast", "播客"), ("vocal", "人声"), ("voice", "人声"), ("vocals", "人声"),
    ("music production", "音乐制作"), ("audio editing", "音频编辑"),
    ("noise isolation", "物理隔音"), ("passive noise", "物理降噪"),
    ("transparency mode", "通透模式"), ("ambient mode", "环境声模式"),
    ("hear-through", "通透"), ("wind noise", "风噪"), ("echo cancellation", "回声消除"),
    ("dsp", "DSP"), ("dac chip", "解码芯片"), ("amplifier", "功放"), ("headphone amp", "耳放"),
    ("balanced", "平衡"), ("unbalanced", "单端"), ("4.4mm", "4.4mm平衡"),
    ("3.5mm", "3.5mm"), ("6.35mm", "6.35mm"), ("xlr", "XLR"),
    ("simultaneous", "同步"), ("pairing", "配对"), ("connection", "连接"),
    ("connectivity", "连接性"), ("interface", "接口"), ("ports", "接口"),
    ("output", "输出"), ("input", "输入"), ("volume control", "音量控制"),
    ("touch controls", "触控"), ("touch control", "触控"), ("physical buttons", "实体按键"),
    ("wear detection", "佩戴检测"), ("auto pause", "自动暂停"), ("voice assistant", "语音助手"),
    ("siri", "Siri"), ("alexa", "Alexa"), ("google assistant", "谷歌助手"),
    ("calls", "通话"), ("call quality", "通话质量"), ("microphone array", "麦克风阵列"),
    ("beamforming", "波束成形"), ("mute", "静音"), ("unmute", "取消静音"),
    ("game mode", "游戏模式"), ("low-latency mode", "低延迟模式"), ("console", "主机"),
    ("pc gaming", "PC游戏"), ("mobile gaming", "手游"), ("cloud gaming", "云游戏"),
    ("battery", "电池"), ("battery capacity", "电池容量"), ("mah", "毫安时"),
    ("rechargeable", "可充电"), ("charging case", "充电仓"), ("wireless charging case", "无线充电仓"),
    ("charging time", "充电时间"), ("playback time", "播放时间"), ("standby time", "待机时间"),
    ("talk time", "通话时间"), ("weight", "重量"), ("grams", "克"), ("dimensions", "尺寸"),
    ("sensor", "传感器"), ("pixel", "像素"), ("resolution", "分辨率"), ("frame rate", "帧率"),
    ("fps", "帧率"), ("latency", "延迟"), ("ms", "毫秒"), ("hz", "Hz"),
    ("sample rate", "采样率"), ("bit depth", "位深"),
    ("companion", "配套"), ("software", "软件"), ("firmware", "固件"), ("driver", "驱动"),
    ("compatible with", "兼容"), ("compatibility", "兼容性"), ("works with", "兼容"),
    ("designed for", "专为"), ("engineered for", "专为"), ("built for", "专为"),
    ("suitable for", "适用于"), ("ideal for", "适合"), ("perfect for", "适合"),
    ("great for", "适合"), ("best for", "适合"), ("everyday use", "日常使用"),
    ("daily use", "日常使用"), ("long sessions", "长时间使用"), ("marathon", "马拉松式"),
    ("endurance", "续航"), ("performance", "性能"), ("precision", "精准度"),
    ("accuracy", "准确度"), ("speed", "速度"), ("powerful", "强劲"), ("robust", "强健"),
    ("reliable", "可靠"), ("consistent", "稳定"), ("smooth", "顺滑"),
    ("effortless", "轻松"), ("simplicity", "简洁"), ("elegant", "优雅"),
    ("sleek", "流线"), ("modern", "现代"), ("classic", "经典"), ("retro", "复古"),
    ("minimalist", "极简"), ("stylish", "时尚"), ("aesthetic", "美学"),
    ("silicone", "硅胶"), ("rubber", "橡胶"), ("leather", "皮革"), ("fabric", "织物"),
    ("metal", "金属"), ("plastic", "塑料"), ("carbon fiber", "碳纤维"),
    ("magnetic", "磁吸"), ("mag-safe", "磁吸"), ("snap", "磁吸"),
    ("cradle", "底座"), ("stand", "支架"), ("holder", "支架"), ("mount", "支架"),
    ("case", "外壳"), ("shell", "外壳"), ("housing", "外壳"),
    ("glossy", "亮面"), ("matte", "磨砂"), ("textured", "纹理"), ("grip", "防滑"),
    ("anti-slip", "防滑"), ("non-slip", "防滑"), ("rubberized", "橡胶涂层"),
    ("coating", "涂层"), ("finish", "工艺"), ("surface", "表面"),
    ("wrist support", "腕托"), ("palm rest", "手托"), ("hand rest", "手托"),
    ("adjustable height", "可调高度"), ("tilt", "倾斜"), ("angle", "角度"),
    ("fold", "折叠"), ("unfold", "展开"), ("stretch", "拉伸"), ("elastic", "弹力"),
    ("velcro", "魔术贴"), ("zipper", "拉链"), ("pocket", "口袋"),
    ("genuine", "正品"), ("original", "原装"), ("official", "官方"),
    ("authentic", "正品"), ("refurbished", "翻新"), ("renewed", "翻新"),
    ("certified", "认证"), ("warranty", "质保"), ("1-year warranty", "一年质保"),
    ("2-year warranty", "两年质保"), ("lifetime warranty", "终身质保"),
    ("included", "随附"), ("includes", "包含"), ("package includes", "包装内含"),
    ("box contains", "包装内含"), ("what's in the box", "包装内含"),
    ("user manual", "说明书"), ("quick start guide", "快速入门指南"),
    ("download", "下载"), ("update", "更新"), ("installation", "安装"),
    ("setup", "设置"), ("configuration", "配置"), ("factory reset", "恢复出厂设置"),
    ("firmware update", "固件更新"), ("ota", "OTA升级"),
    ("full charge", "充满电"), ("power on", "开机"), ("power off", "关机"),
    ("standby", "待机"), ("sleep mode", "休眠模式"), ("auto-off", "自动关机"),
    ("led", "LED"), ("light", "灯光"), ("backlight", "背光"),
    ("indicator", "指示灯"), ("status", "状态"), ("notification", "通知"),
    ("alerts", "提醒"), ("customization", "自定义"), ("personalization", "个性化"),
    ("tuning", "调校"), ("calibration", "校准"), ("profile", "配置文件"),
    ("preset", "预设"), ("scene", "场景"), ("mode", "模式"), ("modes", "模式"),
    ("feature", "功能"), ("features", "功能"), ("specifications", "规格参数"),
    ("specs", "规格"), ("technical", "技术"), ("dimension", "尺寸"),
    ("color options", "配色"), ("colours", "配色"), ("colors", "配色"),
    ("available in", "提供"), ("finishes", "配色"), ("black", "黑色"),
    ("white", "白色"), ("grey", "灰色"), ("gray", "灰色"), ("silver", "银色"),
    ("gold", "金色"), ("blue", "蓝色"), ("red", "红色"), ("green", "绿色"),
    ("purple", "紫色"), ("pink", "粉色"), ("orange", "橙色"), ("transparent", "透明"),
    ("clear", "透明"), ("frosted", "磨砂"), ("camo", "迷彩"),
    ("standard", "标准"), ("deluxe", "豪华"), ("premium edition", "旗舰版"),
    ("special edition", "特别版"), ("limited edition", "限量版"), ("collector", "收藏版"),
    ("starter kit", "入门套装"), ("bundle", "套装"), ("combo", "组合"),
    ("accessory", "配件"), ("accessories", "配件"), ("spare", "备用"),
    ("replacement parts", "替换件"), ("kit", "套件"), ("set", "套装"),
    ("series", "系列"), ("generation", "代"), ("gen", "代"),
    ("new", "新款"), ("latest", "最新"), ("2024", "2024款"), ("2025", "2025款"), ("2026", "2026款"),
    ("discontinued", "已停产"), ("limited", "限量"),
]
TERM_ZH = [
    # —— 通用 ——
    ("true wireless earbuds", "真无线耳塞"), ("true wireless earphones", "真无线耳机"),
    ("wireless gaming mouse", "无线游戏鼠标"), ("wireless gaming keyboard", "无线游戏键盘"),
    ("wireless gaming headset", "无线游戏耳机"), ("bluetooth speaker", "蓝牙音箱"),
    ("bluetooth headphones", "蓝牙耳机"), ("bluetooth headset", "蓝牙耳机"),
    ("noise cancelling", "主动降噪"), ("noise-cancelling", "主动降噪"),
    ("active noise cancellation", "主动降噪"), ("anc", "降噪"),
    ("bone conduction", "骨传导"), ("open-ear", "开放式"),
    ("over-ear", "头戴式"), ("on-ear", "压耳式"), ("in-ear", "入耳式"),
    ("earbuds", "耳塞"), ("earbud", "耳塞"), ("earphones", "耳机"), ("earphone", "耳机"),
    ("headphones", "耳机"), ("headphone", "耳机"), ("headset", "耳机"),
    ("gaming headset", "游戏耳机"), ("hi-fi", "高保真"), ("hifi", "高保真"),
    ("studio monitor", "监听"), ("monitor headphones", "监听耳机"),
    ("microphone", "麦克风"), ("gaming microphone", "游戏麦克风"),
    ("condenser microphone", "电容麦克风"), ("dynamic microphone", "动圈麦克风"),
    ("usb microphone", "USB麦克风"), ("lavalier", "领夹式"),
    ("wireless microphone", "无线麦克风"),
    # —— 鼠标 ——
    ("gaming mouse", "游戏鼠标"), ("wireless mouse", "无线鼠标"),
    ("wired mouse", "有线鼠标"), ("ergonomic mouse", "人体工学鼠标"),
    ("vertical mouse", "垂直鼠标"), ("trackball", "轨迹球"),
    ("optical mouse", "光学鼠标"), ("mouse", "鼠标"),
    ("ergonomic", "人体工学"), ("lightweight", "轻量化"),
    ("ambidextrous", "左右手通用"), ("left-handed", "左手"),
    ("optical sensor", "光学传感器"), ("high-performance sensor", "高性能传感器"),
    ("wireless charging", "无线充电"), ("charging dock", "充电底座"),
    ("receiver", "接收器"), ("dongle", "接收器"),
    # —— 键盘 ——
    ("mechanical keyboard", "机械键盘"), ("gaming keyboard", "游戏键盘"),
    ("magnetic keyboard", "磁轴键盘"), ("hall effect", "霍尔效应"),
    ("hall-effect", "霍尔效应"), ("magnetic switch", "磁轴"),
    ("keyboard switch", "键盘轴"), ("switches", "轴体"), ("switch", "轴"),
    ("keycap set", "键帽套装"), ("keycaps", "键帽"), ("keycap", "键帽"),
    ("hot-swappable", "热插拔"), ("hot swap", "热插拔"), ("gasket", "Gasket结构"),
    ("aluminum", "铝合金"), ("aluminium", "铝合金"),
    ("rgb backlit", "RGB背光"), ("rgb backlight", "RGB背光"), ("backlit", "背光"),
    ("wireless keyboard", "无线键盘"), ("wired keyboard", "有线键盘"),
    ("low profile", "矮轴"), ("low-profile", "矮轴"),
    ("membrane keyboard", "薄膜键盘"), ("wireless mechanical keyboard", "无线机械键盘"),
    ("custom keyboard", "客制化键盘"), ("gasket mount", "Gasket结构"),
    ("tri-mode", "三模"), ("dual-mode", "双模"), ("triple mode", "三模"),
    ("75%", "75配列"), ("65%", "65配列"), ("80%", "80配列"), ("98%", "98配列"),
    ("full size", "全尺寸"), ("tenkeyless", "87键"), ("tkl", "87键"),
    # —— 手柄 ——
    ("game controller", "游戏手柄"), ("gamepad", "手柄"), ("controller", "手柄"),
    ("wireless controller", "无线手柄"), ("pro controller", "专业手柄"),
    ("elite controller", "精英手柄"), ("arcade stick", "摇杆"),
    ("fight stick", "格斗摇杆"), ("racing wheel", "方向盘"),
    ("gaming wheel", "游戏方向盘"), ("pedals", "踏板"), ("hall effect joystick", "霍尔摇杆"),
    ("adaptive trigger", "自适应扳机"), ("trigger", "扳机"),
    ("game console", "游戏主机"), ("for nintendo switch", "任天堂Switch"),
    ("for switch", "Switch"), ("for xbox", "Xbox"), ("for playstation", "PlayStation"),
    ("xbox series", "Xbox Series"), ("playstation 5", "PS5"), ("ps5", "PS5"),
    ("switch lite", "Switch Lite"), ("oled", "OLED"),
    # —— 音响 ——
    ("bookshelf speaker", "书架音箱"), ("floorstanding speaker", "落地音箱"),
    ("floor-standing", "落地式"), ("active speaker", "有源音箱"),
    ("passive speaker", "无源音箱"), ("smart speaker", "智能音箱"),
    ("smart display", "智能屏"), ("soundbar", "回音壁"),
    ("sound bar", "回音壁"), ("subwoofer", "低音炮"),
    ("portable speaker", "便携音箱"), ("wireless speaker", "无线音箱"),
    ("computer speaker", "电脑音箱"), ("pc speaker", "电脑音箱"),
    ("gaming speaker", "游戏音箱"), ("studio monitor speaker", "监听音箱"),
    ("monitor speaker", "监听音箱"), ("dac", "解码器"),
    ("headphone amplifier", "耳机放大器"), ("amplifier", "功放"),
    ("speaker system", "音箱系统"), ("speakers", "音箱"), ("speaker", "音箱"),
    ("home theater", "家庭影院"), ("hi-fi speaker", "高保真音箱"),
    ("tower speaker", "落地音箱"), ("center channel", "中置音箱"),
    ("surround speaker", "环绕音箱"), ("outdoor speaker", "户外音箱"),
    ("party speaker", "派对音箱"), ("karaoke", "卡拉OK"),
    # —— 鼠标垫 ——
    ("mousepad", "鼠标垫"), ("mouse pad", "鼠标垫"),
    ("desk mat", "桌垫"), ("deskmat", "桌垫"), ("desk pad", "桌垫"),
    ("gaming mouse pad", "游戏鼠标垫"), ("gaming mousepad", "游戏鼠标垫"),
    ("control pad", "控制面鼠标垫"), ("speed pad", "速度面鼠标垫"),
    ("cloth mousepad", "布面鼠标垫"), ("hard mousepad", "硬质鼠标垫"),
    ("glass mousepad", "玻璃鼠标垫"), ("xxl", "超大号"),
    # —— 属性/通用 ——
    ("wireless", "无线"), ("wired", "有线"), ("bluetooth", "蓝牙"),
    ("rechargeable", "可充电"), ("recharge", "充电"), ("battery", "电池"),
    ("charging case", "充电仓"), ("charging", "充电"), ("rgb", "RGB"),
    ("gaming", "游戏"), ("gamer", "游戏"), ("esports", "电竞"),
    ("competitive", "竞技"), ("tournament", "赛事"),
    ("professional", "专业"), ("pro", "专业版"), ("ultimate", "旗舰"),
    ("premium", "旗舰"), ("limited edition", "限量版"), ("special edition", "特别版"),
    ("collector's edition", "典藏版"), ("anniversary", "周年纪念"),
    ("refurbished", "官翻"), ("renewed", "官翻"),
    ("white", "白色"), ("black", "黑色"), ("pink", "粉色"), ("blue", "蓝色"),
    ("red", "红色"), ("gray", "灰色"), ("grey", "灰色"), ("green", "绿色"),
    ("silver", "银色"), ("gold", "金色"), ("purple", "紫色"), ("yellow", "黄色"),
    ("orange", "橙色"), ("brown", "棕色"), ("cream", "奶油色"),
    ("clear", "透明"), ("transparent", "透明"), ("midnight", "午夜蓝"),
    ("space gray", "深空灰"), ("graphite", "石墨色"), ("titanium", "钛金属"),
    ("mini", "迷你"), ("compact", "紧凑"), ("slim", "纤薄"),
    ("lite", "青春版"),     ("edition", "版本"), ("version", "版本"), ("series", "系列"),
    ("generation", "代"), ("gen 2", "第二代"), ("gen 3", "第三代"),
    ("gen 4", "第四代"), ("new", "新款"), ("2023", "2023款"),
    ("2024", "2024款"), ("2025", "2025款"), ("2026", "2026款"),
    ("kit", "套装"), ("bundle", "套装"), ("set", "套装"),
    ("stand", "支架"), ("cradle", "底座"), ("dock", "底座"),
    ("case", "保护壳"), ("cover", "保护套"), ("sleeve", "保护套"),
    ("cable", "线缆"), ("usb-c", "Type-C"), ("usb c", "Type-C"),
    ("type-c", "Type-C"), ("usb", "USB"), ("hdmi", "HDMI"),
    ("adapter", "转接头"), ("hub", "扩展坞"), ("cradle", "底座"),
    ("combo", "套装"), ("duo", "双件套"), ("plus version", "增强版"),
]

# 品牌产品系列词（型号词，不翻译，但常用中文官方译名可映射）
MODEL_ZH = {
    "viper": "蝰蛇", "deathadder": "炼狱蝰蛇", "basilisk": "巴塞利斯蛇", "naga": "那伽梵蛇",
    "cobra": "眼镜蛇", "lancehead": "曼巴", "mamba": "曼巴", "g502": "G502",
    "g pro x": "G Pro X", "gpw": "GPW", "gpx": "GPX", "superlight": "Superlight",
    "glorious model o": "Model O", "model d": "Model D", "air58": "Air58",
    "starlight": "Starlight", "xm1": "XM1", "xm2": "XM2", "op1": "OP1",
    "zowie ec": "EC", "zowie za": "ZA", "zowie fk": "FK", "zowie s": "S系列",
    "ducky one": "One", "ducky shine": "Shine", "keychron k": "K系列",
    "keychron q": "Q系列", "keychron v": "V系列", "k2": "K2", "k3": "K3",
    "k6": "K6", "k8": "K8", "k12": "K12", "q1": "Q1", "q2": "Q2", "q3": "Q3",
    "v1": "V1", "v2": "V2", "v3": "V3", "v4": "V4", "v5": "V5", "v6": "V6",
    "airpods": "AirPods", "airpods pro": "AirPods Pro", "airpods max": "AirPods Max",
    "wh-1000xm": "WH-1000XM", "wh-1000xm4": "WH-1000XM4", "wh-1000xm5": "WH-1000XM5",
    "wf-1000xm": "WF-1000XM", "xm4": "XM4", "xm5": "XM5", "xm6": "XM6",
    "qc45": "QC45", "qc ultra": "QC Ultra", "quietcomfort": "QuietComfort",
    "quietcomfort ultra": "QuietComfort Ultra", "soundsport": "SoundSport",
    "liberty": "Liberty", "liberty 4": "Liberty 4", "liberty 3": "Liberty 3",
    "space q45": "Space Q45", "space one": "Space One", "life q30": "Life Q30",
    "life p3": "Life P3", "soundcore motion": "Motion", "soundcore flare": "Flare",
    "sony inzone": "InZone", "pulse": "Pulse", "arctis": "Arctis",
    "arctis nova": "Arctis Nova", "aerox": "Aerox", "rival": "Rival",
    "sensei": "Sensei", "prime": "Prime", "kana": "Kana", "kinzu": "Kinzu",
    "gaming k": "K系列", "razer kraken": "北海巨妖", "kraken": "北海巨妖",
    "blackshark": "黑鲨", "barracuda": "梭鱼", "hammerhead": "锤头鲨",
    "dareu a": "A系列", "vgn 87": "VGN 87", "s99": "S99", "n75": "N75", "v98": "V98",
    "ajazz ak": "AK系列", "ajazz ac": "AC系列", "mchose g": "G系列", "mchose a": "A系列",
    "ganss gs": "GS系列", "ganss alt": "Alt", "durgod k": "K系列", "durgod gk": "GK系列",
    "durgod fusion": "Fusion", "lofree flow": "Flow", "lofree keyboard": "洛斐键盘",
    "i8": "i8", "i61": "i61", "h81": "H81", "wob": "WOB", "wobkey": "WOB",
    "angrymiao": "怒喵", "cyberboard": "Cyberboard", "8bitdo ultimate": "Ultimate",
    "8bitdo pro": "Pro", "sn30": "SN30", "sn30 pro": "SN30 Pro", "zero 2": "Zero 2",
    "gamesir t4": "T4", "gamesir g7": "G7", "gamesir x2": "X2",
    "gulikit kingkong": "金刚", "kingkong": "金刚", "kk3": "KK3", "kk2": "KK2",
    "flydigi apex": "Apex", "apex 4": "Apex 4", "direwolf": "直狼", "wee": "Wee",
    "mobapad": "魔派", "hd2": "HD2", "hd2s": "HD2S", "dualsense": "DualSense",
    "dualshock": "DualShock", "elite series": "精英系列", "xbox wireless": "Xbox无线",
    "pro controller": "专业手柄", "joy-con": "Joy-Con", "switch pro": "Switch Pro",
    "scuf reflex": "Reflex", "scuf instinct": "Instinct", "victrix pro": "Victrix Pro",
    "thrustmaster t": "T系列", "t248": "T248", "t300": "T300", "t598": "T598",
    "t-flight": "T-Flight", "hori pad": "HORI手柄", "fighting commander": "格斗手柄",
    "edifier r": "R系列", "edifier s": "S系列", "edifier m": "M系列",
    "edifier g": "G系列", "edifier w": "W系列", "s880": "S880", "s1000": "S1000",
    "s2000": "S2000", "r1280": "R1280", "r1700": "R1700", "r2000": "R2000",
    "m360": "M360", "m80": "M80", "m100": "M100", "m201": "M201",
    "swans": "惠威", "d1080": "D1080", "d200": "D200", "m200": "M200", "m300": "M300",
    "hivi": "惠威", "t200": "T200", "t300": "T300", "x5": "X5", "x8": "X8",
    "mk200": "MK200", "mk300": "MK300", "go play": "Go Play", "harman kardon": "哈曼卡顿",
    "soundsticks": "SoundSticks", "aura": "Aura", "jbl charge": "Charge", "charge 5": "Charge 5",
    "jbl flip": "Flip", "flip 6": "Flip 6", "jbl pulse": "Pulse", "jbl xtreme": "Xtreme",
    "jbl boombox": "Boombox", "jbl partybox": "PartyBox", "jbl go": "Go", "jbl clip": "Clip",
    "marshall stanmore": "Stanmore", "stanmore ii": "Stanmore II", "stanmore iii": "Stanmore III",
    "acton": "Acton", "woburn": "Woburn", "kilburn": "Kilburn", "tufton": "Tufton",
    "emberton": "Emberton", "marshall willen": "Willen", "sonos": "Sonos",
    "one sl": "One SL", "beam": "Beam", "arc": "Arc", "era": "Era", "roam": "Roam",
    "move": "Move", "sub": "Sub", "dali": "达尼", "spektor": "Spektor", "oberon": "Oberon",
    "opticon": "Opticon", "rubicon": "Rubicon", "epicon": "Epicon", "katch": "Katch",
    "dynaudio": "丹拿", "emits": "Emit", "evoke": "Evoke", "focus": "Focus",
    "confidence": "Confidence", "kef": "KEF", "ls50": "LS50", "ls60": "LS60",
    "q series": "Q系列", "r series": "R系列", "reference": "Reference",
    "b&o": "B&O", "beoplay": "Beoplay", "beosound": "Beosound", "beolit": "Beolit",
    "a1": "A1", "a2": "A2", "a5": "A5", "a9": "A9", "explore": "Explore",
    "bose soundlink": "SoundLink", "soundlink": "SoundLink", "sonos roam": "Roam",
    "focal": "劲浪", "bathys": "Bathys", "utopia": "乌托邦", "stelia": "Stelia",
    "clear": "Clear", "elegia": "Elegia", "arche": "Arche", "listen": "Listen",
    "celestee": "Celestee", "radiance": "Radiance", "hd600": "HD600", "hd650": "HD650",
    "hd660s": "HD660S", "hd800": "HD800", "hd800s": "HD800S", "hd560s": "HD560S",
    "hd599": "HD599", "momentum": "Momentum", "momentum 4": "Momentum 4",
    "ie 600": "IE 600", "ie 900": "IE 900", "ie200": "IE200", "ie300": "IE300",
    "hd25": "HD25", "dt 770": "DT 770", "dt 880": "DT 880", "dt 990": "DT 990",
    "dt 1990": "DT 1990", "dt 900": "DT 900", "dt 700": "DT 700", "t1": "T1",
    "t5": "T5", "t90": "T90", "t70": "T70", "t5p": "T5p", "amiron": "Amiron",
    "avento": "Avento", "lagoon": "Lagoon", "tago": "Tago", "verio": "Verio",
    "k701": "K701", "k702": "K702", "k712": "K712", "k240": "K240", "k271": "K271",
    "k371": "K371", "k361": "K361", "k612": "K612", "n700": "N700", "n90": "N90",
    "y50": "Y50", "k872": "K872", "k872": "K872", "se846": "SE846", "se215": "SE215",
    "se535": "SE535", "shure sm7b": "SM7B", "sm7b": "SM7B", "sm58": "SM58",
    "mv7": "MV7", "mv88": "MV88", "mv51": "MV51", "beta": "Beta", "pga": "PGA",
    "rode": "罗德", "nt1": "NT1", "nt-usb": "NT-USB", "podmic": "PodMic",
    "ps4": "PS4", "xbox one": "Xbox One", "nintendo switch": "任天堂Switch",
    "nintendo switch oled": "Switch OLED",
}

# 构造按长度降序的正则（长词优先，避免 "gaming mouse" 被 "mouse" 提前替换）
_TERM_PAIRS = sorted(TERM_ZH + DESC_TERM_ZH + [(k, v) for k, v in MODEL_ZH.items()], key=lambda kv: -len(kv[0]))


def _term_pat(k):
    """短纯字母数字词加词边界，防止 Products→专业版ducts、reduces→红色uces 类误伤。"""
    if re.fullmatch(r"[A-Za-z0-9]+", k) and len(k) <= 5:
        return r"(?<![A-Za-z0-9])" + re.escape(k) + r"(?![A-Za-z0-9])"
    return re.escape(k)


_TERM_RE = re.compile("|".join(_term_pat(k) for k, _ in _TERM_PAIRS), re.I)
_TERM_MAP = {k.lower(): v for k, v in _TERM_PAIRS}

_BRAND_RE = re.compile("|".join(re.escape(k) for k in BRAND_ZH), re.I)
_BRAND_MAP = {k.lower(): v for k, v in BRAND_ZH.items()}


def _replace_terms(text):
    def _rep(m):
        return _TERM_MAP.get(m.group(0).lower(), m.group(0))
    return _TERM_RE.sub(_rep, text)


def _replace_brands(text, brand_keys):
    """品牌名替换（仅在名称开头/独立出现时替换，避免误伤型号词）。"""
    def _rep(m):
        return _BRAND_MAP.get(m.group(0).lower(), m.group(0))
    out = _BRAND_RE.sub(_rep, text)
    # 若品牌名在名称中部出现且前后是词边界，也替换（如 "Razer Viper" → "雷蛇 Viper"）
    return out


_ACCENT_RE = re.compile(r"[àâäáåæçèéêëîïíìñôöòóøùûúüÿ]", re.I)
# 非英文高频词（法/西/德/意/葡）：描述含 >=2 个即判定非英文
_NON_EN_WORDS_RE = re.compile(
    r"\b(la|le|les|des|dans|avec|pour|sur|une|un|est|et|que|qui|acheter|achetez|profitez|"
    r"para|con|por|el|los|las|del|una|este|esta|nuevo|más|mas|sin|como|tambien|também|"
    r"das|der|die|und|mit|ist|von|für|fur|ein|eine|auf|auch|nicht|"
    r"il|lo|la|del|della|per|con|una|non|piu|anche|molto|"
    r"um|uma|para|com|não|nao|muito|mais|como)\b", re.I)


def _looks_english(text):
    """检测文本是否为英文：重音字符出现或含 >=2 个非英文高频词 → 非英文。"""
    if not text:
        return False
    if _ACCENT_RE.search(text):
        return False
    if len(_NON_EN_WORDS_RE.findall(text)) >= 2:
        return False
    return True


def _clean_zh(s):
    s = re.sub(r"\s+", " ", s or "").strip()
    return s


def localize_product(p, brand_zh=None):
    """为单个产品生成中文名 name_zh，并尝试中文化描述/标签。返回是否新增/变更 name_zh。"""
    brand_zh = brand_zh or {}
    name = (p.get("name") or "").strip()
    if not name:
        return False
    old_zh = p.get("name_zh")
    # 已含中文 → 视为已中文化
    if old_zh and re.search(r"[\u4e00-\u9fff]", old_zh):
        return False
    zh = name
    bkey = p.get("brand") or ""
    if bkey in brand_zh:
        # 名称以品牌名开头时，去掉英文品牌词避免重复（"Razer Viper" → "Viper"）
        low = name.lower()
        for en in (brand_zh[bkey].get("name_en") or []):
            if low.startswith(en.lower() + " "):
                zh = name[len(en):].strip()
                break
        zh = brand_zh[bkey].get("name") + " " + zh
    else:
        zh = _replace_brands(zh, [])
    zh = _replace_terms(zh)
    zh = _clean_zh(zh)
    if not zh:
        return False
    # 去重空格与可能残留的英文重复品牌（"雷蛇 Viper 蝰蛇" 等情况不处理，保留）
    if zh == name:
        return False
    p["name_zh"] = zh
    # 描述中文化：术语替换（保原文）
    desc = p.get("description") or ""
    if desc and re.search(r"[A-Za-z]{4,}", desc) and not re.search(r"[\u4e00-\u9fff]", desc) and _looks_english(desc):
        d = _replace_terms(desc)
        if d != desc:
            p["description_zh"] = d
    # 标签中文化
    tags = p.get("tags") or []
    if tags and any(isinstance(t, str) and re.search(r"[A-Za-z]{3,}", t) and _looks_english(t) for t in tags):
        p["tags_zh"] = [_replace_terms(t) for t in tags]
    return True


def localize_all(data, brands_data):
    """全库中文化。返回新增 name_zh 数量。"""
    brand_zh = {}
    for b in brands_data.get("brands", []):
        key = b.get("key")
        if not key:
            continue
        nm = b.get("name") or ""
        nms = b.get("name_en") or []
        brand_zh[key] = {"name": nm, "name_en": nms if isinstance(nms, list) else [nms]}
    n = 0
    cleaned = 0
    for p in data.get("products", []):
        # 清理历史垃圾 desc_zh：原文非英文（法/西/德等重音字符）时，删除 desc_zh 防误导
        desc = p.get("description") or ""
        if p.get("description_zh") and desc and not re.search(r"[\u4e00-\u9fff]", desc) and not _looks_english(desc):
            p["description_zh"] = ""
            cleaned += 1
        if localize_product(p, brand_zh):
            n += 1
    if cleaned:
        utils.logger.info("中文化：清除 %d 条非英文描述的旧垃圾 desc_zh", cleaned)
    return n
