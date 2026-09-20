# -*- coding: utf-8 -*-
"""enrich.py · 自动补全数据信息（并行版）
========================================
对缺描述/未分类/缺图片/缺参数的产品，自动抓取品牌官网产品页：
  - <title> 与 meta description → 回填描述
  - og:image / 首张产品图 → 回填 image（真实产品图 URL）
  - 页面规格表 → 抽取真实参数写入 specs（仅当原 specs 为空时）
无官方链接且品牌已核验的产品，先经搜索引擎发现产品页再抓取。
"""
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from . import classify, utils, verify

_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_DESC_RE = re.compile(
    r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', re.I | re.S
)
_OG_IMAGE_RE = re.compile(
    r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](.*?)["\']', re.I | re.S
)
_OG_IMAGE_RE2 = re.compile(
    r'<meta[^>]+content=["\'](.*?)["\'][^>]+property=["\']og:image["\']', re.I | re.S
)
_OG_SECURE_RE = re.compile(
    r'<meta[^>]+property=["\']og:image:secure_url["\'][^>]+content=["\'](.*?)["\']', re.I | re.S
)
_OG_SECURE_RE2 = re.compile(
    r'<meta[^>]+content=["\'](.*?)["\'][^>]+property=["\']og:image:secure_url["\']', re.I | re.S
)
_TWITTER_IMG_RE = re.compile(
    r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\'](.*?)["\']', re.I | re.S
)
_TWITTER_IMG_RE2 = re.compile(
    r'<meta[^>]+content=["\'](.*?)["\'][^>]+name=["\']twitter:image["\']', re.I | re.S
)

# 页面图片候选（产品图常见选择器，按优先级）
_IMG_SELECTORS = [
    "img.product-image", "img[data-src*='product']", "img[src*='product']",
    "img[src*='prod']", ".product img", "main img", "#content img",
    "img[data-src]", "img.lazyload", "img[loading='lazy']",
]
_IMG_SKIP = ("logo", "icon", "banner", "sprite", "avatar", "loading", "placeholder",
             "tracking", "pixel", "transparent", "blank", "loader", "spinner",
             "badge", "flag", "share", "social", "favicon", "paypal", "visa",
             "mastercard", "shipping", "returns", "guarantee")


def _clean(s):
    return re.sub(r"\s+", " ", s or "").strip()


def extract_page_meta(url, cfg, timeout=20):
    """抓取产品页标题/描述/产品图/规格行。失败返回 None。"""
    status, html = utils.http_get(url, cfg, timeout=timeout)
    if not html:
        return None
    t = _TITLE_RE.search(html)
    d = _DESC_RE.search(html)
    og = (_OG_IMAGE_RE.search(html) or _OG_IMAGE_RE2.search(html)
          or _OG_SECURE_RE.search(html) or _OG_SECURE_RE2.search(html)
          or _TWITTER_IMG_RE.search(html) or _TWITTER_IMG_RE2.search(html))
    image = ""
    if og:
        image = _clean(og.group(1))
    if image and image.startswith("//"):
        image = "https:" + image
    elif image:
        image = urljoin(url, image)
    if not image:
        soup = BeautifulSoup(html, "html.parser")
        best = None
        best_w = 0
        # 先试精确选择器
        for sel in _IMG_SELECTORS:
            img = soup.select_one(sel)
            if img:
                src = img.get("src") or img.get("data-src") or img.get("data-original") or ""
                if src and not any(k in src.lower() for k in _IMG_SKIP):
                    if not src.startswith("data:"):
                        best = urljoin(url, src) if not src.startswith(("http", "//")) else ("https:" + src if src.startswith("//") else src)
                        break
        if not best:
            # 兜底：遍历所有 img，取宽度最大的产品图
            for img in soup.find_all("img"):
                src = img.get("src") or img.get("data-src") or img.get("data-original") or img.get("data-lazy-src") or ""
                low = src.lower()
                if not src or src.startswith("data:") or any(k in low for k in _IMG_SKIP):
                    continue
                w = 0
                for wk in ("width", "data-width"):
                    try:
                        w = max(w, int(float(str(img.get(wk) or 0))))
                    except (TypeError, ValueError):
                        pass
                if not w:
                    # 无显式宽度时，取 URL 中含 product/prod/media/cdn 的大图
                    if any(k in low for k in ("product", "/prod", "media", "cdn", "images")):
                        w = 800
                if w > best_w:
                    best_w = w
                    best = urljoin(url, src) if not src.startswith(("http", "//")) else ("https:" + src if src.startswith("//") else src)
        if best:
            image = best
    rows = verify.extract_spec_rows(html)
    return {
        "title": _clean(t.group(1)) if t else "",
        "description": _clean(d.group(1)) if d else "",
        "image": _clean(image),
        "rows": rows,
    }


def _fill_specs_from_rows(product, rows):
    """把页面规格行映射为我们的参数键（仅填 specs 为空的产品）。"""
    if product.get("specs"):
        return False
    # 页签 → 参数键 反向匹配（SPEC_ALIASES 值命中页签则归属该键）
    filled = {}
    for label, value in rows:
        for our_key, aliases in verify.SPEC_ALIASES.items():
            if our_key in filled:
                continue
            if any(utils.norm_num(a) is not None or a.lower() in label.lower() for a in aliases):
                if any(a.lower() in label.lower() for a in aliases):
                    filled[our_key] = value
                    break
    if filled:
        product["specs"] = filled
        return True
    return False


def _discover_page_url(product, brand, cfg):
    """无官方链接时经搜索引擎找产品页。返回 URL 或 None。"""
    q = "%s %s" % (brand.get("name_en") or brand.get("name"), product.get("name", ""))
    results = verify.search_web(q, cfg)
    for _t, url, _s in results:
        if url and "http" in url:
            return url
    return None


# 国内站优先：国内 CDN 图对国内用户加载快，且有中文参数
CN_HOSTS = ("zol.com.cn", "pconline.com.cn", "jd.com", "tmall.com", "smzdm.com", "pchome.net", "sohu.com", "pcpop.com", "yesky.com")


def _host_of(url):
    try:
        return (url.split("//", 1)[1].split("/", 1)[0]).lower()
    except Exception:
        return ""


def _find_cn_page(product, brand, cfg):
    """优先从国内站找产品页（中关村在线/太平洋/京东等）。"""
    q = (product.get("name_zh") or product.get("name") or "").strip()
    if not q or len(q) < 3:
        return None
    try:
        results = verify.search_web(q + " 参数", cfg)
    except Exception:
        return None
    for _t, url, _s in results:
        if not url or "http" not in url:
            continue
        host = _host_of(url)
        # 去掉 www. 后匹配国内站
        bare = host.split("www.", 1)[-1]
        if any(cn in bare for cn in CN_HOSTS):
            return url
    return None


def _enrich_one(product, brands_by_key, cfg):
    """补全单个产品。返回 (product_id, 变更标记, 分类变更标记)。"""
    changed = False
    cat_changed = False
    url = (product.get("links") or {}).get("official")
    brand = brands_by_key.get(product.get("brand"), {})
    if not url and brand.get("verified"):
        url = _discover_page_url(product, brand, cfg)
        if url and product.get("links") is None:
            product["links"] = {}
        if url:
            product["links"]["official"] = url
    if not url:
        return product.get("id"), changed, cat_changed
    # 优先抓国内站（图在国内 CDN、描述为中文），再用官方页补缺
    need_cn = (not product.get("image")) or not (product.get("description") or "").strip()
    cn_url = _find_cn_page(product, brand, cfg) if need_cn else None
    if cn_url:
        info = extract_page_meta(cn_url, cfg)
        if info and info.get("title"):
            if not (product.get("description") or "").strip():
                product["description"] = (info.get("description") or info["title"])[:300]
                changed = True
            if info.get("image") and not product.get("image"):
                product["image"] = info["image"]
                changed = True
            if _fill_specs_from_rows(product, info.get("rows") or []):
                changed = True
    # 官方页兜底补全
    info = extract_page_meta(url, cfg)
    if not info or not info.get("title"):
        return product.get("id"), changed, cat_changed
    if not (product.get("description") or "").strip():
        product["description"] = (info.get("description") or info["title"])[:300]
        changed = True
    if info.get("image") and not product.get("image"):
        product["image"] = info["image"]
        changed = True
    if _fill_specs_from_rows(product, info.get("rows") or []):
        changed = True
    old = product.get("category")
    classify.classify_product(product)
    if product.get("category") != old:
        changed = True
        cat_changed = True
    return product.get("id"), changed, cat_changed


def enrich_unverified(data, brands_data, cfg, limit=None, workers=None):
    """批量补全：优先缺图片/描述/参数的产品。返回 (补全数, 新分类数, 失败数)。"""
    brands_by_key = {b["key"]: b for b in brands_data["brands"]}
    products = data["products"]
    limit = limit or cfg.get("enrich", {}).get("per_run_limit", 3000)
    workers = workers or cfg.get("enrich", {}).get("workers", 14)
    targets = [
        p for p in products
        if (not p.get("image") or not (p.get("description") or "").strip() or not p.get("specs"))
        and ((p.get("links") or {}).get("official") or brands_by_key.get(p.get("brand"), {}).get("verified"))
    ][:limit]
    done = 0
    reclassified = 0
    failed = 0
    start = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_enrich_one, p, brands_by_key, cfg): p for p in targets}
        for fut in as_completed(futs):
            try:
                _pid, changed, cat_changed = fut.result()
                if changed:
                    done += 1
                if cat_changed:
                    reclassified += 1
            except Exception:  # noqa: BLE001
                failed += 1
    utils.logger.info("补全: 目标 %d, 完成 %d, 重新分类 %d, 失败 %d, 耗时 %.0fs",
                      len(targets), done, reclassified, failed, time.time() - start)
    return done, reclassified, failed
