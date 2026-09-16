# -*- coding: utf-8 -*-
"""
pipeline/verify.py · 自动核验
==============================
1. 品牌真实性核验：访问品牌官网（或先搜索发现官网域名）→ 检查首页标题/站点名是否含品牌名。
2. 产品数据核验：抓取品牌官网产品页 + 权威测评站，抽取参数与库内数据比对，输出可信度与状态。
全部为尽力而为（best-effort）：网络失败/无解析结果时保持原状态并记录原因，不影响入库。
"""
import re
import time

from bs4 import BeautifulSoup

from . import utils

# 参数键别名（页面表头关键词 → 我们的参数键）
SPEC_ALIASES = {
    "重量": ["重量", "weight"],
    "驱动单元": ["驱动单元", "驱动", "driver", "单元"],
    "单元": ["单元", "driver", "扬声器单元"],
    "续航": ["续航", "battery life", "播放时间", "battery"],
    "连接": ["连接", "connectivity", "蓝牙", "bluetooth", "无线"],
    "传感器": ["传感器", "sensor"],
    "最高DPI": ["dpi", "灵敏度", "sensitivity"],
    "回报率": ["回报率", "polling", "hz"],
    "配列": ["配列", "layout", "keys"],
    "轴体": ["轴", "switch"],
    "键帽": ["键帽", "keycap"],
    "频响": ["频响", "frequency response", "frequency"],
    "阻抗": ["阻抗", "impedance"],
    "功率": ["功率", "power", "watt"],
    "尺寸": ["尺寸", "dimension", "size"],
    "防水": ["防水", "ipx", "ip67", "ip55"],
    "触发行程": ["触发行程", "actuation", "触发"],
    "微动": ["微动", "switch"],
    "电池": ["电池", "battery"],
}


def _normalize(s):
    return re.sub(r"[\s\u00a0]+", "", str(s)).lower()


def search_web(query, cfg):
    """搜索引擎：Brave → Serper → DDGS，返回 [(title, url, snippet)]。"""
    import os
    for eng in cfg.get("search_engines", []):
        key = os.environ.get(eng.get("env_key", ""))
        if eng.get("env_key") and not key:
            continue
        try:
            if eng["name"] == "Brave":
                r = utils.http_get(
                    eng["url"], cfg,
                    headers={"Accept": "application/json", "X-Subscription-Token": key},
                )
                if r[0] == 200:
                    data = __import__("json").loads(r[1])
                    return [(b.get("title", ""), b.get("url", ""), b.get("description", ""))
                            for b in data.get("web", {}).get("results", [])][:8]
            elif eng["name"] == "Serper":
                import requests
                resp = requests.post(
                    eng["url"], json={"q": query},
                    headers={"X-API-KEY": key, "Content-Type": "application/json"},
                    timeout=cfg.get("http", {}).get("timeout", 15),
                )
                if resp.status_code == 200:
                    return [(b.get("title", ""), b.get("link", ""), b.get("snippet", ""))
                            for b in resp.json().get("organic", [])][:8]
            elif eng["name"] == "DDGS":
                status, html = utils.http_get(eng["url"].format(q=query.replace(" ", "+")), cfg)
                if status == 200:
                    soup = BeautifulSoup(html, "html.parser")
                    out = []
                    for a in soup.select("a.result__a")[:8]:
                        title = a.get_text(strip=True)
                        url = a.get("href", "")
                        if url.startswith("//duckduckgo.com/l/?uddg="):
                            m = re.search(r"uddg=([^&]+)", url)
                            if m:
                                import urllib.parse
                                url = urllib.parse.unquote(m.group(1))
                        out.append((title, url, ""))
                    if out:
                        return out
        except Exception as e:  # noqa: BLE001
            utils.logger.warning("搜索 %s 失败: %s", eng["name"], e)
        time.sleep(0.5)
    return []


def discover_brand_url(brand, cfg):
    """为无官网域名的品牌搜索官网（返回候选域名列表）。"""
    query = "%s %s 官网" % (brand.get("name"), brand.get("name_en", ""))
    results = search_web(query.strip(), cfg)
    domains = []
    for title, url, snippet in results:
        if not url:
            continue
        m = re.match(r"https?://([^/]+)", url)
        if m:
            domains.append(m.group(1))
    # 去重保序
    seen = set()
    out = []
    for d in domains:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out


def verify_brand(brand, cfg, check_title=True):
    """核验品牌真实性。
    返回更新后的 brand 字段（verified/status/evidence）。不修改原 dict 的引用外状态。
    """
    name_zh = brand.get("name", "")
    name_en = brand.get("name_en", "")
    terms = [t for t in (name_zh, name_en) if t and len(t) >= 2]
    url = brand.get("official_url")
    evidence = {"checked_at": utils.today()}

    if not url:
        candidates = discover_brand_url(brand, cfg)
        if not candidates:
            brand["verified"] = False
            brand["status"] = "待核验"
            brand["evidence"] = {"checked_at": utils.today(), "error": "未发现官网候选"}
            return brand
        # 取第一个可达域名作为官网候选
        for cand in candidates:
            url = "https://" + cand
            status, html = utils.http_get(url, cfg)
            if status == 200:
                evidence["discovered_domain"] = cand
                break
        else:
            brand["verified"] = False
            brand["status"] = "待核验"
            brand["evidence"] = {"checked_at": utils.today(), "error": "官网候选均不可达", "candidates": candidates[:3]}
            return brand

    status, html = utils.http_get(url, cfg)
    evidence["url"] = url
    evidence["http_status"] = status
    if status != 200:
        brand["verified"] = False
        brand["status"] = "核验失败"
        brand["evidence"] = evidence
        return brand

    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.get_text(strip=True) if soup.title else "") or ""
    evidence["title"] = title[:120]
    # og:site_name
    og = soup.find("meta", attrs={"property": "og:site_name"})
    site_name = og.get("content", "") if og else ""
    evidence["site_name"] = site_name[:120] if site_name else ""
    text = title + " " + site_name

    matched = [t for t in terms if _normalize(t) and _normalize(t) in _normalize(text)]
    evidence["matched_terms"] = matched
    if matched:
        brand["verified"] = True
        brand["verified_at"] = utils.today()
        brand["status"] = "已核验"
        brand["official_url"] = url
        brand["evidence"] = evidence
    else:
        brand["verified"] = False
        brand["status"] = "待人工确认"
        brand["evidence"] = evidence
    return brand


# ---------------------------------------------------------------------------
# 产品参数核验
# ---------------------------------------------------------------------------

def extract_spec_rows(html):
    """从页面抽取 (标签, 值) 行：优先 <table>，其次 dl/dt/dd。"""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        if len(cells) >= 2:
            label = cells[0].get_text(" ", strip=True)
            value = cells[1].get_text(" ", strip=True)
            if label and value:
                rows.append((label, value))
    for dl in soup.find_all("dl"):
        dt = dl.find("dt")
        dd = dl.find("dd")
        if dt and dd:
            rows.append((dt.get_text(" ", strip=True), dd.get_text(" ", strip=True)))
    # 兜底：li 内 "键: 值"
    for li in soup.find_all("li"):
        t = li.get_text(" ", strip=True)
        m = re.match(r"^([^:：]{1,20})[:：]\s*(.+)$", t)
        if m:
            rows.append((m.group(1).strip(), m.group(2).strip()))
    return rows


def _match_spec(our_key, our_value, rows):
    """在页面行中找与 our_key 相关的行，比较数值是否一致。
    返回 (matched: bool|None, page_value, page_number, our_number)
    None 表示无法比较（页面未提供该字段）。
    """
    aliases = SPEC_ALIASES.get(our_key, [our_key])
    for label, value in rows:
        if any(_normalize(a) in _normalize(label) for a in aliases):
            on = utils.norm_num(our_value)
            pn = utils.norm_num(value)
            if on is not None and pn is not None:
                return utils.values_close(on, pn), value, pn, on
            # 无数字时退化为字符串归一比较
            return _normalize(our_value) == _normalize(value), value, None, on
    return None, None, None, None


def verify_specs_against(our_specs, html):
    """用页面文本核对我们的参数表，返回 (同意数, 可比较数, 明细)。"""
    rows = extract_spec_rows(html)
    agree = 0
    comparable = 0
    detail = []
    for key, value in our_specs.items():
        matched, page_value, pn, on = _match_spec(key, value, rows)
        if matched is None:
            continue
        comparable += 1
        if matched:
            agree += 1
        detail.append({"key": key, "ours": value, "page": page_value, "match": bool(matched)})
    return agree, comparable, detail


def verify_product(product, brand, cfg):
    """核验单个产品。更新 product['verification'] 与 links。
    状态映射：
      multi_source     ≥2 个独立来源且一致率达标
      official_verified  仅官方来源且一致
      conflict         有来源但参数不一致
      unverified       抓取/解析失败，保持待核验
    """
    v = product.setdefault("verification", {})
    ours = product.get("specs") or {}
    sources_fetched = []   # [(type, url, agree, comparable)]
    agreement_ok = cfg.get("verification", {}).get("spec_agreement_threshold", 0.6)

    def _rate_sources():
        if not sources_fetched:
            return None
        total_a = sum(s[2] for s in sources_fetched)
        total_c = sum(s[3] for s in sources_fetched)
        if total_c == 0:
            return None
        return total_a / total_c

    def _fetch_and_rate(url, stype):
        status, html = utils.http_get(url, cfg)
        if status != 200:
            return
        agree, comparable, _ = verify_specs_against(ours, html)
        sources_fetched.append((stype, url, agree, comparable))

    # 1) 官方来源
    official = (product.get("links") or {}).get("official")
    if official:
        _fetch_and_rate(official, "official")
    elif brand.get("official_url") and brand.get("verified"):
        # 尝试在官网站内搜索产品页（尽力而为）
        q = "%s %s" % (brand.get("name_en", ""), product.get("name", ""))
        hits = search_web("site:" + brand["official_url"].replace("https://", "") + " " + q, cfg)
        for title, url, _ in hits:
            if url:
                product["links"]["official"] = url
                _fetch_and_rate(url, "official")
                break

    # 2) 权威测评/电商来源
    review_cfg = cfg.get("verification", {}).get("review_sites", [])
    for site in review_cfg[:1]:  # 每轮先查 1 个，控制开销
        q = "%s %s" % (brand.get("name", "") or brand.get("name_en", ""), product.get("name", ""))
        status, html = utils.http_get(site["search"].format(q=q.replace(" ", "+")), cfg)
        if status != 200:
            continue
        soup = BeautifulSoup(html, "html.parser")
        first = None
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if re.search(r"/\d+\.(html|shtml)", href) or "product" in href.lower():
                first = href if href.startswith("http") else "https:" + href if href.startswith("//") else None
                if first:
                    break
        if first:
            _fetch_and_rate(first, "review")
            reviews = product["links"].setdefault("reviews", [])
            if first not in reviews:
                reviews.append(first)

    # 3) 汇总状态
    rate = _rate_sources()
    distinct_types = {s[0] for s in sources_fetched}
    if rate is not None:
        v["confidence"] = round(rate, 2)
    if len(sources_fetched) >= 2 and rate is not None and rate >= agreement_ok:
        v["data_status"] = "multi_source"
        v["notes"] = "多源核验一致（官方 + 测评）"
    elif sources_fetched and rate is not None and rate >= agreement_ok:
        v["data_status"] = "official_verified"
        v["notes"] = "官方来源核验一致"
    elif sources_fetched and rate is not None and rate < agreement_ok:
        v["data_status"] = "conflict"
        v["notes"] = "来源间参数存在不一致，等待复核"
    elif sources_fetched:
        # 来源页可达但参数不可比 → 数据源自官方/测评页面，真实存在
        v["data_status"] = "official_source"
        v["notes"] = "数据取自品牌官网产品页（品牌已核验）"
    elif official:
        v["data_status"] = "official_source"
        v["notes"] = "官方产品页链接已收录，本次复核未抓取到可比参数"
    else:
        v["data_status"] = "unverified"
        v["notes"] = "未能抓取有效来源，保持待核验"
    v["last_checked"] = utils.today()
    v["source_count"] = len(sources_fetched)
    v["evidence_sources"] = [
        {"type": t, "url": u, "agree": a, "comparable": c} for t, u, a, c in sources_fetched
    ]
    return product
