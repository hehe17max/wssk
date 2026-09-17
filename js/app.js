/* 外设水库 · 首页主控制器 */
(() => {
  const { $, $$, debounce, escapeHtml } = Util;
  const SKEY = "wsk-compare";   // 对比选择（sessionStorage）

  const el = {
    searchInput: $("#searchInput"),
    chipsRow: $("#chipsRow"),
    catTabs: $("#catTabs"),
    subtypeRow: $("#subtypeRow"),
    brandList: $("#brandList"),
    brandSearch: $("#brandSearch"),
    brandAll: $("#brandAll"),
    structField: $("#structField"),
    structOp: $("#structOp"),
    structVal: $("#structVal"),
    structApply: $("#structApply"),
    structReset: $("#structReset"),
    grid: $("#grid"),
    count: $("#count"),
    sort: $("#sort"),
    clearAll: $("#clearAll"),
    compareBar: $("#compareBar"),
    compareNames: $("#compareNames"),
    compareGo: $("#compareGo"),
    compareClear: $("#compareClear"),
    modalMask: $("#modalMask"),
    modalBody: $("#modalBody"),
    footerMeta: $("#footerMeta"),
    navCompare: $("#navCompare"),
  };

  /* ---------- 对比选择 ---------- */
  function getSelected() {
    try { return JSON.parse(sessionStorage.getItem(SKEY)) || []; } catch { return []; }
  }
  function setSelected(ids) { sessionStorage.setItem(SKEY, JSON.stringify(ids.slice(0, 20))); }
  function toggleCompare(id) {
    let ids = getSelected();
    ids = ids.includes(id) ? ids.filter(x => x !== id) : [...ids, id];
    setSelected(ids);
    renderCompareBar();
    renderGrid();
  }
  function renderCompareBar() {
    const ids = getSelected();
    const names = ids.map(id => {
      const p = Data.state.products.find(x => x.id === id);
      return p ? `<span class="nm">${escapeHtml(p.name)}<span class="rm" data-rm="${id}">✕</span></span>` : "";
    }).join("");
    el.compareNames.innerHTML = names;
    el.compareBar.classList.toggle("show", ids.length > 0);
    el.compareGo.disabled = ids.length < 2;
    el.navCompare.textContent = `对比 (${ids.length}/20)`;
    $$(".rm", el.compareNames).forEach(b => b.onclick = () => { toggleCompare(b.dataset.rm); });
  }
  function compareUrl() {
    const ids = getSelected();
    return "compare.html?" + ids.map(id => "p=" + encodeURIComponent(id)).join("&");
  }

  /* ---------- 侧栏渲染 ---------- */
  function renderCategoryTabs() {
    const cats = [{ k: null, label: "全部" }, ...Object.entries(Filters.CATEGORIES).map(([k, v]) => ({ k, label: v.label }))];
    el.catTabs.innerHTML = cats.map(c =>
      `<button class="cat-tab ${Filters.state.category === c.k ? "on" : ""}" data-cat="${c.k || ""}">${c.label}</button>`
    ).join("");
    $$(".cat-tab", el.catTabs).forEach(b => {
      b.onclick = () => {
        Filters.state.category = b.dataset.cat || null;
        Filters.state.subtypes.clear();
        Filters.state.brands.clear();
        renderSidebar();
        renderGrid();
      };
    });
  }

  function renderSubtypes() {
    const cat = Filters.state.category;
    const list = cat ? (Filters.CATEGORIES[cat] || {}).subtypes : [];
    el.subtypeRow.innerHTML = list.map(s =>
      `<button class="subtype ${Filters.state.subtypes.has(s) ? "on" : ""}" data-s="${escapeHtml(s)}">${escapeHtml(s)}</button>`
    ).join("");
    $$(".subtype", el.subtypeRow).forEach(b => {
      b.onclick = () => {
        const s = b.dataset.s;
        Filters.state.subtypes.has(s) ? Filters.state.subtypes.delete(s) : Filters.state.subtypes.add(s);
        renderSubtypes();
        renderGrid();
      };
    });
  }

  function renderBrandList() {
    const cat = Filters.state.category;
    const brands = Data.state.brands.filter(b => !cat || b.categories.includes(cat));
    const kw = (el.brandSearch.value || "").trim().toLowerCase();
    const filtered = brands.filter(b =>
      !kw || b.name.toLowerCase().includes(kw) || (b.name_en || "").toLowerCase().includes(kw));
    // 分组：选中类型→按该类型分组标签；全部→按类型再按分组
    const groups = new Map();
    for (const b of filtered) {
      let g;
      if (cat) {
        g = b.groups[cat] || "其他";
      } else {
        const cats = (b.categories || []).map(c => Filters.CATEGORIES[c]?.label).join("/") || "其他";
        g = cats;
      }
      if (!groups.has(g)) groups.set(g, []);
      groups.get(g).push(b);
    }
    const html = [];
    for (const [g, list] of [...groups.entries()].sort((a, b) => a[0].localeCompare(b[0], "zh"))) {
      html.push(`<div class="brand-group-title">${escapeHtml(g)} · ${list.length}</div>`);
      for (const b of list) {
        const on = Filters.state.brands.has(b.key);
        html.push(`<label class="brand-item ${on ? "on" : ""}">
          <input type="checkbox" data-key="${b.key}" ${on ? "checked" : ""}>
          <span>${escapeHtml(b.name)}</span>
          <span class="en">${escapeHtml(b.name_en || "")}</span>
          <span class="dot ${b.verified ? "verified" : "pending"}" title="${b.verified ? "品牌已核验" : "待核验"}"></span>
        </label>`);
      }
    }
    el.brandList.innerHTML = html.join("") || `<div class="empty">无匹配品牌</div>`;
    $$("input[data-key]", el.brandList).forEach(cb => {
      cb.onchange = () => {
        const k = cb.dataset.key;
        Filters.state.brands.has(k) ? Filters.state.brands.delete(k) : Filters.state.brands.add(k);
        renderBrandList();
        renderGrid();
      };
    });
  }

  function renderSidebar() {
    renderSubtypes();
    renderBrandList();
  }

  /* ---------- 快捷筛选 chips ---------- */
  function renderChips() {
    el.chipsRow.innerHTML = Filters.CHIPS.map(c =>
      `<button class="chip ${Filters.state.chips.has(c.k) ? "on" : ""}" data-chip="${c.k}">${c.label}${Filters.state.chips.has(c.k) ? '<span class="x">✕</span>' : ""}</button>`
    ).join("");
    $$(".chip", el.chipsRow).forEach(b => {
      b.onclick = () => {
        const k = b.dataset.chip;
        Filters.state.chips.has(k) ? Filters.state.chips.delete(k) : Filters.state.chips.add(k);
        renderChips();
        renderGrid();
      };
    });
  }

  /* ---------- 产品卡片 ---------- */
  // 分页渲染：默认每页 60 张卡片，「加载更多」增量追加，避免全量 DOM 卡顿
  let PAGE = 60;
  let lastSig = "";
  function filterSig() {
    const s = Filters.state;
    return [s.q, s.category, [...s.subtypes].sort().join(","), [...s.brands].sort().join(","),
      [...s.chips].sort().join(","), s.sort, JSON.stringify(s.struct)].join("|");
  }
  function specPreview(p) {
    const order = Data.specFieldOrder(p.category);
    const keys = [];
    for (const k of order) if ((p.specs || {})[k] != null && keys.length < 3) keys.push(k);
    if (keys.length < 3) {
      for (const k of Object.keys(p.specs || {})) if (!keys.includes(k) && keys.length < 3) keys.push(k);
    }
    return keys.map(k => `<span>${escapeHtml(k)}：<b>${escapeHtml(p.specs[k])}</b></span>`).join("");
  }

  function cardHtml(p) {
    const b = Data.brandOf(p.brand);
    const si = Data.statusInfo(p);
    const catLabel = (Filters.CATEGORIES[p.category] || {}).label || (p.category === "unclassified" ? "未分类" : p.category);
    const isNew = p.discovered_at && (Date.now() - new Date(p.discovered_at).getTime()) / 86400000 <= 7;
    const added = getSelected().includes(p.id);
    return `<div class="card" data-id="${p.id}">
      ${p.image ? `<div class="card-img"><img src="${escapeHtml(p.image)}" alt="${escapeHtml(p.name)}" loading="lazy" onerror="this.closest('.card-img').classList.add('noimg')"><span class="img-ph">${escapeHtml(b.name)}</span></div>` : ""}
      <div class="card-top">
        <span class="brand-badge">${escapeHtml(b.name)}</span>
        <span class="type-badge">${escapeHtml(catLabel)}</span>
        ${p.subtype && p.subtype !== "未分类" ? `<span class="type-badge">${escapeHtml(p.subtype)}</span>` : ""}
      </div>
      <h4>${escapeHtml(p.name)}${isNew ? '<span class="new">新品</span>' : ""}</h4>
      <p class="desc">${escapeHtml(p.description || "")}</p>
      <div class="spec-preview">${specPreview(p)}</div>
      <div class="card-bottom">
        <span class="vbadge ${si.cls}">${si.text}</span>
        <div class="card-actions">
          <button class="icon-btn" data-act="detail">详情</button>
          <button class="icon-btn ${added ? "added" : ""}" data-act="cmp">${added ? "已加入" : "对比"}</button>
        </div>
      </div>
    </div>`;
  }

  function renderGrid() {
    const sig = filterSig();
    if (sig !== lastSig) { PAGE = 60; lastSig = sig; }
    const list = Filters.apply(Data.state.products);
    el.count.innerHTML = `共 <b>${list.length}</b> 款产品`;
    if (!list.length) {
      el.grid.innerHTML = `<div class="empty"><div class="big">💧</div>没有匹配的产品<br>试试放宽筛选条件</div>`;
      return;
    }
    const visible = list.slice(0, PAGE);
    const moreHtml = list.length > PAGE
      ? `<button class="load-more" id="loadMore">加载更多（还剩 ${list.length - PAGE} 款）</button>` : "";
    el.grid.innerHTML = visible.map(cardHtml).join("") + moreHtml;
    $$(".card", el.grid).forEach(card => {
      const id = card.dataset.id;
      $$("button[data-act=detail]", card)[0].onclick = () => openModal(id);
      $$("button[data-act=cmp]", card)[0].onclick = () => toggleCompare(id);
    });
    const lm = document.getElementById("loadMore");
    if (lm) lm.onclick = () => { PAGE += 60; renderGrid(); };
  }

  /* ---------- 详情弹窗 ---------- */
  function openModal(id) {
    const p = Data.state.products.find(x => x.id === id);
    if (!p) return;
    const b = Data.brandOf(p.brand);
    const si = Data.statusInfo(p);
    const v = p.verification || {};
    const order = Data.specFieldOrder(p.category);
    const keys = [...order.filter(k => (p.specs || {})[k] != null),
      ...Object.keys(p.specs || {}).filter(k => !order.includes(k))];
    const specRows = keys.map(k => `<tr><th>${escapeHtml(k)}</th><td>${escapeHtml(p.specs[k])}</td></tr>`).join("");
    const links = [];
    if (p.links && p.links.official) links.push(`<a href="${escapeHtml(p.links.official)}" target="_blank" rel="noopener">品牌官网产品页 ↗</a>`);
    if (b.official_url) links.push(`<a href="${escapeHtml(b.official_url)}" target="_blank" rel="noopener">品牌官网 ↗</a>`);
    if (v.evidence_sources) v.evidence_sources.forEach(s => {
      if (s.url) links.push(`<a href="${escapeHtml(s.url)}" target="_blank" rel="noopener">${s.type === "official" ? "官方来源" : "测评来源"} ↗</a>`);
    });
    if (p.links && p.links.reviews) p.links.reviews.forEach(u => links.push(`<a href="${escapeHtml(u)}" target="_blank" rel="noopener">测评来源 ↗</a>`));
    el.modalBody.innerHTML = `
      <button class="close">✕</button>
      ${p.image ? `<div class="modal-img"><img src="${escapeHtml(p.image)}" alt="${escapeHtml(p.name)}" onerror="this.style.display='none'"></div>` : ""}
      <div class="brand-line">${escapeHtml(b.name)} <span class="type-badge">${escapeHtml((Filters.CATEGORIES[p.category] || {}).label || "")}</span> <span class="type-badge">${escapeHtml(p.subtype || "")}</span></div>
      <h2>${escapeHtml(p.name)}</h2>
      <p class="desc">${escapeHtml(p.description || "暂无描述")}</p>
      ${p.release ? `<p style="color:var(--muted);font-size:12.5px">上市时间：${escapeHtml(p.release)}</p>` : ""}
      <table class="spec-table">${specRows || "<tr><td>参数待补充</td></tr>"}</table>
      <h3 style="margin:0 0 8px;font-size:14px;color:var(--muted)">信息源</h3>
      <div class="links-list">${links.length ? links.join("") : '<span style="color:var(--muted)">暂无来源链接，等待流水线自动定位</span>'}</div>
      <div class="veri-box">
        <div class="row"><span>品牌核验：<b>${b.verified ? "已确认" : (b.status || "待核验")}</b></span>
        <span>数据核验：<b>${si.text}</b></span>
        <span>可信度：<b>${v.confidence != null ? (v.confidence * 100).toFixed(0) + "%" : "—"}</b></span>
        <span>来源数：<b>${v.source_count != null ? v.source_count : 0}</b></span>
        <span>最近核验：<b>${escapeHtml(v.last_checked || "—")}</b></span></div>
        ${v.notes ? `<div class="row">说明：${escapeHtml(v.notes)}</div>` : ""}
      </div>`;
    el.modalMask.classList.add("show");
    $(".close", el.modalBody).onclick = closeModal;
  }
  function closeModal() { el.modalMask.classList.remove("show"); }

  /* ---------- 结构化筛选 ---------- */
  function renderStructFields() {
    const fields = Filters.state.category === "mouse" || Filters.state.category === null
      ? ["重量", "最高DPI", "续航", "回报率"]
      : Filters.state.category === "keyboard" ? ["配列", "回报率", "续航", "重量"]
      : Filters.state.category === "earphone" ? ["重量", "续航", "阻抗", "频响"]
      : Filters.state.category === "gamepad" ? ["续航", "重量"] : ["尺寸", "厚度"];
    el.structField.innerHTML = fields.map(f => `<option value="${f}">${f}</option>`).join("");
  }

  /* ---------- 页脚元信息 ---------- */
  function renderFooter() {
    const m = Data.state.meta;
    if (!m) return;
    const b = m.brands || {};
    const p = m.products || {};
    el.footerMeta.innerHTML = `
      <span>品牌 ${b.total || 0}（已核验 ${b.verified || 0}）</span>
      <span>产品 ${p.total || 0}</span>
      <span>最近同步 ${escapeHtml(m.last_sync || "—")}</span>
      <span>流水线 ${escapeHtml((m.pipeline || {}).status || "待运行")}</span>`;
  }

  /* ---------- 事件绑定 ---------- */
  function bind() {
    el.searchInput.addEventListener("input", debounce(() => {
      Filters.state.q = el.searchInput.value;
      renderGrid();
    }, 200));

    el.sort.addEventListener("change", () => {
      Filters.state.sort = el.sort.value;
      renderGrid();
    });

    el.clearAll.onclick = () => {
      Filters.clearAll();
      el.searchInput.value = "";
      el.brandSearch.value = "";
      renderCategoryTabs();
      renderSidebar();
      renderChips();
      renderStructFields();
      renderGrid();
    };

    el.brandSearch.addEventListener("input", debounce(renderBrandList, 150));
    el.brandAll.onclick = () => {
      const cat = Filters.state.category;
      Data.state.brands.filter(b => !cat || b.categories.includes(cat)).forEach(b => Filters.state.brands.add(b.key));
      renderBrandList();
      renderGrid();
    };

    el.structApply.onclick = () => {
      const field = el.structField.value;
      const op = el.structOp.value;
      const val = parseFloat(el.structVal.value);
      if (!field || isNaN(val)) return;
      Filters.state.struct = { field, op, val };
      renderGrid();
    };
    el.structReset.onclick = () => {
      Filters.state.struct = null;
      el.structVal.value = "";
      renderGrid();
    };

    el.compareGo.onclick = () => { location.href = compareUrl(); };
    el.compareClear.onclick = () => { setSelected([]); renderCompareBar(); renderGrid(); };
    el.modalMask.addEventListener("click", e => { if (e.target === el.modalMask) closeModal(); });
    document.addEventListener("keydown", e => { if (e.key === "Escape") closeModal(); });
  }

  /* ---------- 初始化 ---------- */
  function init() {
    // 支持 URL 参数：?cat=earphone&q=sony&brand=sony
    const cat = Util.getParam("cat");
    if (cat && Filters.CATEGORIES[cat]) Filters.state.category = cat;
    const q = Util.getParam("q");
    if (q) { Filters.state.q = q; el.searchInput.value = q; }
    const brand = Util.getParam("brand");
    if (brand) brand.split(",").filter(Boolean).forEach(k => Filters.state.brands.add(k));

    renderCategoryTabs();
    renderSidebar();
    renderChips();
    renderStructFields();
    renderCompareBar();
    renderGrid();
    renderFooter();
    bind();
  }

  Data.loadAll().then(() => {
    el.grid.innerHTML = "";
    init();
  }).catch(err => {
    document.body.innerHTML = `<div class="empty"><div class="big">⚠</div>数据加载失败：${escapeHtml(err.message)}<br><span style="font-size:12px">请确认 data/ 目录下存在 brands.json 与 products.json，并通过本地服务器访问（不要直接双击打开）</span></div>`;
  });
})();
