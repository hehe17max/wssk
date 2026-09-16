/* 外设水库 · 筛选状态与逻辑
   筛选模型：
     category  类型（单选）
     subtypes  子类型（多选 AND）
     brands    品牌（多选 OR）
     chips     关键词快捷筛选（多选 OR，可选/不可选）
     struct    结构化参数（字段 + 运算符 + 数值，单条 AND）
     q         搜索词（品牌中英文 + 产品名，AND 全文）
     sort      排序
*/
const Filters = (() => {
  const state = {
    category: null,        // earphone | mouse | keyboard | gamepad | speaker | mousepad
    subtypes: new Set(),
    brands: new Set(),
    chips: new Set(),
    struct: null,          // {field, op, val}
    q: "",
    sort: "default",
  };

  const CATEGORIES = {
    earphone: { label: "耳机", subtypes: ["TWS", "头戴", "游戏", "HiFi", "骨传导", "监听·麦克风", "未分类"] },
    mouse: { label: "鼠标", subtypes: ["电竞", "办公", "未分类"] },
    keyboard: { label: "键盘", subtypes: ["磁轴", "机械", "静电容", "薄膜", "未分类"] },
    gamepad: { label: "手柄", subtypes: ["主机", "第三方", "精英", "便携", "未分类"] },
    speaker: { label: "音响", subtypes: ["智能音箱", "桌面音箱", "HiFi", "便携蓝牙", "回音壁", "监听", "未分类"] },
    mousepad: { label: "鼠标垫", subtypes: ["速度垫", "控制垫", "混合垫", "未分类"] },
  };

  /* 快捷筛选词汇（可选/不可选 chips） */
  const CHIPS = [
    { k: "wireless", label: "无线", kw: ["无线", "wireless", "蓝牙", "bluetooth", "2.4g", "2.4ghz", "三模", "双模", "lightspeed", "hyperspeed", "hyperpolling"] },
    { k: "wired", label: "有线", kw: ["有线", "wired", "usb", "usb-c", "type-c", "3.5mm", "6.3mm"] },
    { k: "24g", label: "2.4G", kw: ["2.4g", "2.4ghz", "lightspeed", "hyperspeed"] },
    { k: "bt", label: "蓝牙", kw: ["蓝牙", "bluetooth"] },
    { k: "tri", label: "三模", kw: ["三模"] },
    { k: "8k", label: "8K 回报率", kw: ["8000hz", "8k", "8khz", "8k 回报率"] },
    { k: "4k", label: "4K 回报率", kw: ["4000hz", "4k", "4khz"] },
    { k: "l60", label: "≤60g", spec: { field: "重量", op: "<=", val: 60 } },
    { k: "l80", label: "≤80g", spec: { field: "重量", op: "<=", val: 80 } },
    { k: "b100", label: "≥100h 续航", spec: { field: "续航", op: ">=", val: 100 } },
    { k: "dpi26", label: "≥26000 DPI", spec: { field: "最高DPI", op: ">=", val: 26000 } },
    { k: "anc", label: "ANC 降噪", kw: ["anc", "主动降噪", "降噪", "消噪"] },
    { k: "ldac", label: "LDAC", kw: ["ldac"] },
    { k: "bone", label: "骨传导", kw: ["骨传导", "bone conduction"] },
    { k: "mag", label: "磁轴", kw: ["磁轴", "磁力", "霍尔", "hall", "omni point", "模拟光轴", "he "] },
    { k: "rt", label: "Rapid Trigger", kw: ["rapid trigger", "rt"] },
    { k: "hs", label: "热插拔", kw: ["热插拔", "hot-swap", "hotswap"] },
    { k: "gasket", label: "Gasket", kw: ["gasket"] },
    { k: "pbt", label: "PBT 键帽", kw: ["pbt"] },
    { k: "opt", label: "光微动", kw: ["光微动", "光学微动", "optical"] },
    { k: "hall", label: "霍尔摇杆", kw: ["霍尔"] },
    { k: "game", label: "电竞/游戏", kw: ["电竞", "游戏", "gaming"] },
    { k: "office", label: "办公", kw: ["办公", "office"] },
    { k: "hifi", label: "HiFi", kw: ["hifi", "高保真"] },
    { k: "rgb", label: "RGB", kw: ["rgb"] },
    { k: "new7", label: "新品 7 天", time: { days: 7 } },
    { k: "new30", label: "新品 30 天", time: { days: 30 } },
  ];

  function productText(p) {
    const b = Data.brandOf(p.brand);
    return [
      p.name || "", p.description || "", p.subtype || "", p.category || "",
      b.name, b.name_en, (p.tags || []).join(" "),
      ...Object.entries(p.specs || {}).map(([k, v]) => k + " " + v),
    ].join(" ").toLowerCase();
  }

  function chipMatches(chip, p) {
    if (chip.kw) {
      const t = productText(p);
      return chip.kw.some(k => t.includes(k));
    }
    if (chip.spec) {
      const { field, op, val } = chip.spec;
      const n = Util.specNumber(p.specs || {}, field);
      if (n == null) return false;
      return op === "<=" ? n <= val : n >= val;
    }
    if (chip.time) {
      const d = p.discovered_at ? new Date(p.discovered_at) : null;
      if (!d) return false;
      const days = (Date.now() - d.getTime()) / 86400000;
      return days <= chip.time.days;
    }
    return false;
  }

  function apply(products) {
    let list = products;
    if (state.category) {
      list = list.filter(p => p.category === state.category);
      if (state.subtypes.size) {
        list = list.filter(p => state.subtypes.has(p.subtype));
      }
    }
    if (state.brands.size) {
      list = list.filter(p => state.brands.has(p.brand));
    }
    if (state.chips.size) {
      const chips = CHIPS.filter(c => state.chips.has(c.k));
      list = list.filter(p => chips.some(c => chipMatches(c, p)));
    }
    if (state.struct) {
      const { field, op, val } = state.struct;
      list = list.filter(p => {
        const n = Util.specNumber(p.specs || {}, field);
        if (n == null) return false;
        return op === "<=" ? n <= val : n >= val;
      });
    }
    const q = state.q.trim().toLowerCase();
    if (q) {
      list = list.filter(p => productText(p).includes(q));
    }
    // 排序
    const sort = state.sort;
    list = list.slice();
    if (sort === "new") {
      list.sort((a, b) => String(b.discovered_at || "").localeCompare(String(a.discovered_at || "")));
    } else if (sort === "brand") {
      list.sort((a, b) => {
        const ba = Data.brandOf(a.brand).name;
        const bb = Data.brandOf(b.brand).name;
        return ba.localeCompare(bb, "zh") || a.name.localeCompare(b.name, "zh");
      });
    } else if (sort === "name") {
      list.sort((a, b) => a.name.localeCompare(b.name, "zh"));
    }
    return list;
  }

  function clearAll() {
    state.category = null;
    state.subtypes.clear();
    state.brands.clear();
    state.chips.clear();
    state.struct = null;
    state.q = "";
    state.sort = "default";
  }

  return { state, CATEGORIES, CHIPS, apply, clearAll };
})();
