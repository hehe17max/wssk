/* 外设水库 · 数据层 */
const Data = (() => {
  const state = {
    products: [],
    brands: [],
    brandMap: new Map(),
    meta: null,
    ready: false,
  };

  async function loadProducts() {
    // 优先 gzip（体积减约 80%）；不支持 DecompressionStream 时回退原始 JSON
    try {
      if (typeof DecompressionStream !== "undefined") {
        const resp = await fetch("data/products.json.gz");
        if (resp.ok) {
          const buf = await resp.arrayBuffer();
          const ds = new DecompressionStream("gzip");
          const stream = new Response(buf).body.pipeThrough(ds);
          return await new Response(stream).json();
        }
      }
    } catch (e) { /* 回退原始 JSON */ }
    return await fetch("data/products.json").then(r => r.json());
  }

  async function loadAll() {
    const [p, b, m] = await Promise.all([
      loadProducts(),
      fetch("data/brands.json").then(r => r.json()),
      fetch("data/meta.json").then(r => r.json()).catch(() => null),
    ]);
    state.products = p.products || [];
    state.brands = b.brands || [];
    state.meta = m;
    for (const br of state.brands) state.brandMap.set(br.key, br);
    state.ready = true;
    return state;
  }

  function brandOf(key) {
    return state.brandMap.get(key) || { key, name: key, name_en: key, verified: false, status: "未知" };
  }

  /* 每类产品的参数展示优先级（用于卡片预览与对比表排序） */
  const SPEC_PRIORITY = {
    earphone: ["驱动单元", "降噪", "续航", "连接", "编码", "重量", "阻抗", "频响"],
    mouse: ["传感器", "最高DPI", "回报率", "重量", "连接", "续航", "微动"],
    keyboard: ["配列", "轴体", "连接", "结构", "键帽", "回报率", "续航"],
    gamepad: ["平台", "连接", "特性", "续航", "重量"],
    speaker: ["类型", "单元", "功率", "连接", "频响", "阻抗"],
    mousepad: ["材质", "表面", "尺寸", "底部", "厚度"],
  };

  const COMMON_FIELDS = ["品牌", "型号", "类型", "子类型", "上市时间", "核验状态"];

  function specFieldOrder(category) {
    return SPEC_PRIORITY[category] || [];
  }

  /* 对比表字段顺序：通用字段 + 该类别优先字段 + 其余参数键（按字母序） */
  function compareFields(products) {
    const common = COMMON_FIELDS.filter(f => f !== "型号"); // 型号单独作为表头
    const ordered = [];
    const seen = new Set(common);
    for (const p of products) {
      for (const k of specFieldOrder(p.category)) {
        if (!seen.has(k)) { seen.add(k); ordered.push(k); }
      }
    }
    for (const p of products) {
      for (const k of Object.keys(p.specs || {})) {
        if (!seen.has(k)) { seen.add(k); ordered.push(k); }
      }
    }
    return [...common.filter(f => f !== "品牌" && f !== "类型"), ...ordered];
  }

  const STATUS_LABEL = {
    multi_source: { text: "多源核验一致", cls: "ok" },
    official_verified: { text: "官方来源确认", cls: "ok" },
    official_source: { text: "官方来源", cls: "ok" },
    auto_verified: { text: "自动核验通过", cls: "ok" },
    conflict: { text: "来源冲突待复核", cls: "warn" },
    seed: { text: "种子数据待核验", cls: "mid" },
    unverified: { text: "待核验", cls: "off" },
    discovered: { text: "自动发现", cls: "mid" },
  };

  function statusInfo(product) {
    const s = (product.verification || {}).data_status;
    return STATUS_LABEL[s] || { text: "待核验", cls: "off" };
  }

  return { state, loadAll, brandOf, specFieldOrder, compareFields, statusInfo, STATUS_LABEL };
})();
