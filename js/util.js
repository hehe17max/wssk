/* 外设水库 · 通用工具 */
const Util = (() => {
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  function debounce(fn, ms = 200) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
  }

  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function slug(s) {
    return String(s).toLowerCase().replace(/[^0-9a-z\u4e00-\u9fff]+/g, "-").replace(/^-|-$/g, "");
  }

  function parseNumber(text) {
    const m = String(text == null ? "" : text).match(/(\d+(?:\.\d+)?)/);
    return m ? parseFloat(m[1]) : null;
  }

  function specNumber(specs, field) {
    const v = specs[field];
    return v == null ? null : parseNumber(v);
  }

  function getParam(name) {
    return new URLSearchParams(location.search).get(name);
  }

  function fmtDate(s) {
    if (!s) return "—";
    return String(s).slice(0, 10);
  }

  return { $, $$, debounce, escapeHtml, slug, parseNumber, specNumber, getParam, fmtDate };
})();
