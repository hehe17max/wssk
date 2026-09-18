/* 外设水库 · 对比页（最多 20 款） */
(() => {
  const { $, $$, escapeHtml } = Util;

  const el = {
    wrap: $("#cmpWrap"),
    count: $("#cmpCount"),
    diff: $("#diffToggle"),
    exportBtn: $("#exportBtn"),
    back: $("#backBtn"),
  };

  function loadIds() {
    const params = new URLSearchParams(location.search).getAll("p");
    if (params.length) return params;
    try {
      const s = JSON.parse(sessionStorage.getItem("wsk-compare")) || [];
      return s;
    } catch { return []; }
  }

  function render() {
    let ids = loadIds();
    if (ids.length > 20) ids = ids.slice(0, 20);
    const products = ids.map(id => Data.state.products.find(p => p.id === id)).filter(Boolean);
    el.count.textContent = `对比中：${products.length} / 20`;

    if (!products.length) {
      el.wrap.innerHTML = `<div class="cmp-empty">尚未选择产品。<br><br><a href="index.html" class="primary-btn" style="display:inline-block;padding:10px 22px">← 返回去选择产品</a></div>`;
      return;
    }

    const fields = Data.compareFields(products);
    const highlight = el.diff.checked;

    // 表头
    let html = `<table class="cmp"><thead><tr><th class="fixed">参数</th>`;
    for (const p of products) {
      const b = Data.brandOf(p.brand);
      html += `<th>${p.image ? `<img src="${escapeHtml(p.image)}" class="cmp-thumb" alt="" onerror="this.style.display='none'">` : ""}<div style="font-weight:700;color:var(--accent2)">${escapeHtml(b.name)}</div>
        <div>${escapeHtml(p.name_zh || p.name)}${p.name_zh && p.name && p.name_zh !== p.name ? `<span class="en-sub">${escapeHtml(p.name)}</span>` : ""}</div>
        <div style="font-size:11px;color:var(--muted);margin-top:4px">${escapeHtml((Filters.CATEGORIES[p.category] || {}).label || "")} · ${escapeHtml(p.subtype || "")}</div>
        <button class="icon-btn col-rm" data-rm="${p.id}" style="margin-top:6px">移除</button></th>`;
    }
    html += `</tr></thead><tbody>`;

    // 通用行
    const rows = [
      { key: "品牌", get: p => Data.brandOf(p.brand).name },
      { key: "类型", get: p => (Filters.CATEGORIES[p.category] || {}).label || p.category },
      { key: "子类型", get: p => p.subtype || "—" },
      { key: "上市时间", get: p => p.release || "—" },
      { key: "核验状态", get: p => Data.statusInfo(p).text },
    ];
    for (const r of rows) {
      html += `<tr><td class="fixed">${r.key}</td>`;
      for (const p of products) {
        html += `<td>${escapeHtml(r.get(p))}</td>`;
      }
      html += `</tr>`;
    }
    // 参数行
    for (const f of fields) {
      const vals = products.map(p => (p.specs || {})[f]);
      const common = highlight ? modeValue(vals) : null;
      html += `<tr><td class="fixed">${escapeHtml(f)}</td>`;
      for (const p of products) {
        const v = (p.specs || {})[f];
        const cls = highlight && v != null && String(v) !== String(common) && common != null ? ' class="diff"' : "";
        html += `<td${cls}>${v != null ? escapeHtml(v) : "—"}</td>`;
      }
      html += `</tr>`;
    }
    html += `</tbody></table>`;
    el.wrap.innerHTML = html;

    $$(".col-rm", el.wrap).forEach(b => {
      b.onclick = () => {
        const ids2 = loadIds().filter(x => x !== b.dataset.rm);
        sessionStorage.setItem("wsk-compare", JSON.stringify(ids2));
        const qs = ids2.map(x => "p=" + encodeURIComponent(x)).join("&");
        history.replaceState(null, "", "compare.html?" + qs);
        render();
      };
    });
  }

  function modeValue(arr) {
    const valid = arr.filter(v => v != null);
    if (!valid.length) return null;
    const cnt = new Map();
    for (const v of valid) cnt.set(String(v), (cnt.get(String(v)) || 0) + 1);
    let best = null, bestN = 0;
    for (const [v, n] of cnt) if (n > bestN) { best = v; bestN = n; }
    return best;
  }

  function exportCsv() {
    const products = loadIds().map(id => Data.state.products.find(p => p.id === id)).filter(Boolean);
    if (!products.length) return;
    const fields = Data.compareFields(products);
    const commonRows = ["品牌", "类型", "子类型", "上市时间", "核验状态"];
    const all = [...commonRows, ...fields];
    const esc = s => `"${String(s == null ? "" : s).replace(/"/g, '""')}"`;
    let csv = "参数," + products.map(p => esc(Data.brandOf(p.brand).name + " " + (p.name_zh || p.name))).join(",") + "\n";
    for (const r of commonRows) {
      const get = r === "品牌" ? p => Data.brandOf(p.brand).name
        : r === "类型" ? p => (Filters.CATEGORIES[p.category] || {}).label
        : r === "子类型" ? p => p.subtype
        : r === "上市时间" ? p => p.release
        : p => Data.statusInfo(p).text;
      csv += esc(r) + "," + products.map(p => esc(get(p))).join(",") + "\n";
    }
    for (const f of fields) {
      csv += esc(f) + "," + products.map(p => esc((p.specs || {})[f])).join(",") + "\n";
    }
    const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "外设水库-对比-" + new Date().toISOString().slice(0, 10) + ".csv";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  function bind() {
    el.diff.addEventListener("change", render);
    el.exportBtn.addEventListener("click", exportCsv);
    el.back.addEventListener("click", () => { location.href = "index.html"; });
  }

  Data.loadAll().then(() => {
    bind();
    render();
  }).catch(err => {
    el.wrap.innerHTML = `<div class="cmp-empty">数据加载失败：${escapeHtml(err.message)}</div>`;
  });
})();
