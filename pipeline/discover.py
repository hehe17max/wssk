# -*- coding: utf-8 -*-
"""
pipeline/discover.py · 新品发现
================================
从品牌官网自动发现新产品：
  1. sitemap.xml / sitemap_index.xml 中的产品 URL
  2. Shopify /products.json
  3. 首页中符合产品 URL 模式的链接
发现的候选产品写入 ingest 流程，经分类后入库（状态 = 待核验）。
"""
import re
from urllib.parse import urljoin, urlparse

import requests

from . import utils


def _is_product_url(url, patterns):
    u = url.lower()
    return any(p in u for p in patterns)


def discover_from_sitemap(brand, cfg):
    """解析 sitemap，返回产品 URL 列表。"""
    base = brand.get("official_url", "")
    if not base:
        return []
    sitemap_candidates = [
        urljoin(base, "sitemap.xml"),
        urljoin(base, "sitemap_index.xml"),
        urljoin(base, "sitemap/sitemap.xml"),
    ]
    found = []
    patterns = cfg.get("discovery", {}).get("product_url_patterns", [])
    for sm in sitemap_candidates:
        status, html = utils.http_get(sm, cfg)
        if status != 200:
            continue
        urls = re.findall(r"<loc>\s*([^<]+?)\s*</loc>", html)
        if urls and _is_product_url(urls[0], patterns):
            found = [u for u in urls if _is_product_url(u, patterns)]
            utils.logger.info("%s sitemap 发现产品 URL %d 个", brand.get("key"), len(found))
            return found
        # 子 sitemap：优先英文版（避免多语言重复）
        subs = re.findall(r"<loc>\s*([^<]+?\.xml)\s*</loc>", html)
        subs.sort(key=lambda u: (0 if re.search(r"/(en-us|en-gb|en|us-en)/", u) else 1, u))
        for sub in subs[:5]:
            s2, h2 = utils.http_get(sub, cfg)
            if s2 == 200:
                u2 = re.findall(r"<loc>\s*([^<]+?)\s*</loc>", h2)
                found.extend(u for u in u2 if _is_product_url(u, patterns))
        if found:
            return found
    return found


def discover_from_shopify(brand, cfg):
    base = brand.get("official_url", "")
    if not base:
        return []
    url = urljoin(base, "/products.json")
    try:
        r = requests.get(
            url, headers={"User-Agent": cfg.get("http", {}).get("user_agent", "")},
            timeout=cfg.get("http", {}).get("timeout", 15),
        )
        if r.status_code == 200:
            data = r.json()
            handles = data.get("products", [])
            utils.logger.info("%s Shopify 发现产品 %d 个", brand.get("key"), len(handles))
            return [
                {
                    "name": p.get("title", ""),
                    "url": urljoin(base, "/products/" + p.get("handle", "")),
                    "title": p.get("title", ""),
                }
                for p in handles
            ]
    except Exception as e:  # noqa: BLE001
        utils.logger.debug("shopify 失败: %s", e)
    return []


def discover_from_homepage(brand, cfg):
    base = brand.get("official_url", "")
    if not base:
        return []
    status, html = utils.http_get(base, cfg)
    if status != 200:
        return []
    patterns = cfg.get("discovery", {}).get("product_url_patterns", [])
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', html)
    out = []
    seen = set()
    for h in hrefs:
        if h.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        full = urljoin(base, h)
        if not _is_product_url(full, patterns):
            continue
        if full in seen:
            continue
        seen.add(full)
        out.append(full)
    return out


def name_from_url(url):
    """从 URL 提取产品名（slugs 合并）。"""
    path = urlparse(url).path
    segs = [s for s in path.split("/") if s and not s.lower().startswith(("product", "p", "item", "goods", "id"))]
    if not segs:
        return ""
    last = segs[-1]
    last = re.sub(r"\.(html|shtml|php)$", "", last, flags=re.I)
    return last.replace("-", " ").replace("_", " ").strip()


# 非产品页关键词（整体匹配 / 子串匹配）
STOPWORDS = {
    "products", "product", "mice", "keyboards", "keyboard", "headsets", "headset",
    "speakers", "speaker", "accessories", "support", "contact", "about", "search",
    "cart", "login", "account", "wishlist", "faq", "blog", "news", "deals", "gaming",
    "creators", "business", "home", "index", "catalog", "categories", "category",
    "shop", "store", "buy", "compare", "help",
}
STOPWORD_PARTS = {"/support", "/help", "/warranty", "/download", "/driver", "/software",
                  "/privacy", "/terms", "/legal", "collection-", "/collections/", "?page=",
                  "buy-", "/buy/", "/shop/", "shop-", "store-"}

# URL 路径段 → 类型线索（官网栏目通常比产品名更可靠）
URL_HINT_MAP = {
    "mice": "mouse", "mouse": "mouse", "gaming-mice": "mouse", "wireless-mice": "mouse",
    "keyboards": "keyboard", "keyboard": "keyboard", "keyboard-accessories": "keyboard",
    "headsets": "earphone", "headset": "earphone", "headphones": "earphone",
    "headphone": "earphone", "audio": "earphone", "gaming-headsets": "earphone",
    "speakers": "speaker", "speaker": "speaker", "speaker-systems": "speaker",
    "gamepads": "gamepad", "controllers": "gamepad", "gaming-controllers": "gamepad",
    "mousepads": "mousepad", "desk-mats": "mousepad", "mouse-pads": "mousepad",
}


def url_hints(url):
    """从产品 URL 提取类型线索列表。"""
    segs = urlparse(url).path.lower().split("/")
    return [URL_HINT_MAP[s] for s in segs if s in URL_HINT_MAP]


def discover_brand_products(brand, cfg, existing_names=None):
    """对一个品牌执行全部发现渠道，返回候选产品 [{name,url,title,source}]。"""
    existing_names = existing_names or set()
    candidates = []
    seen = set()

    def _add(name, url, title, source):
        n = re.sub(r"\s+", " ", (name or "").strip())
        if not n or len(n) < 2:
            return
        # 排除非产品页（栏目/支持/账号等）
        low = n.lower()
        if low in STOPWORDS or any(w in low for w in STOPWORD_PARTS):
            return
        key = utils.slug(brand.get("key", "") + utils.canonical_name(n))
        if key in seen or key in existing_names:
            return
        seen.add(key)
        candidates.append({
            "brand": brand.get("key"),
            "name": n,
            "url": url,
            "title": (title or "").strip(),
            "source": source,
            "hints": url_hints(url),
        })

    if brand.get("verified"):
        for url in discover_from_sitemap(brand, cfg):
            _add(name_from_url(url), url, "", "sitemap")
        for p in discover_from_shopify(brand, cfg):
            _add(p.get("name"), p.get("url"), p.get("title"), "shopify")
        for url in discover_from_homepage(brand, cfg)[:200]:
            _add(name_from_url(url), url, "", "homepage")

    max_new = cfg.get("discovery", {}).get("max_new_products_per_run", 200)
    return candidates[:max_new]
