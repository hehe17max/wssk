/* 外设水库 · 关于页统计 */
(() => {
  const { $, escapeHtml } = Util;
  function fill() {
    const m = Data.state.meta;
    if (!m) return;
    $("#statBrands").textContent = m.brands?.total || 0;
    $("#statVerified").textContent = m.brands?.verified || 0;
    $("#statPending").textContent = m.brands?.pending || 0;
    $("#statProducts").textContent = m.products?.total || 0;
    $("#statSync").textContent = m.last_sync || "—";
    $("#statPipe").textContent = (m.pipeline && m.pipeline.status) || "待运行";

    const byCat = m.products?.by_category || {};
    const total = m.products?.total || 1;
    const rows = Object.entries(byCat).map(([k, v]) => `
      <div style="margin:8px 0">
        <div style="display:flex;justify-content:space-between;font-size:13px;color:var(--muted)">
          <span>${escapeHtml(k)}</span><span>${v} 款</span>
        </div>
        <div style="height:8px;background:var(--card2);border-radius:4px;margin-top:4px">
          <div style="width:${Math.max(2, (v / total) * 100)}%;height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2));border-radius:4px"></div>
        </div>
      </div>`).join("");
    $("#catDist").innerHTML = rows || "暂无数据";
  }
  Data.loadAll().then(fill).catch(() => {});
})();
