# -*- coding: utf-8 -*-
"""enrich.py · 自动补全数据信息
================================
对缺描述或未分类的新产品，自动抓取品牌官网产品页的 <title> 与 meta description，
回填描述并重新分类——对应「自动补充填充数据信息」环节。
"""
import re
import time

from . import classify, utils

_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_DESC_RE = re.compile(
    r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', re.I | re.S
)


def extract_page_meta(url, cfg, timeout=12):
    """抓取产品页标题与描述。失败返回 None。"""
    status, html = utils.http_get(url, cfg, timeout=timeout)
    if not html:
        return None
    t = _TITLE_RE.search(html)
    d = _DESC_RE.search(html)
    return {
        "title": re.sub(r"\s+", " ", t.group(1)).strip() if t else "",
        "description": re.sub(r"\s+", " ", d.group(1)).strip() if d else "",
    }


def enrich_unverified(data, cfg, limit=30):
    """为缺描述/未分类的产品补全官方页信息。返回 (补全数, 重新分类数)。"""
    http_cfg = cfg.get("http", {})
    products = data["products"]
    targets = [
        p for p in products
        if (not (p.get("description") or "").strip() or p.get("category") == "unclassified")
        and (p.get("links") or {}).get("official")
    ]
    enriched = 0
    reclassified = 0
    for p in targets[:limit]:
        info = extract_page_meta(p["links"]["official"], cfg, timeout=http_cfg.get("timeout", 12))
        if not info or not info.get("title"):
            continue
        if not (p.get("description") or "").strip():
            p["description"] = (info.get("description") or info["title"])[:300]
        old = p.get("category")
        classify.classify_product(p)
        if p.get("category") != old:
            reclassified += 1
        enriched += 1
        time.sleep(0.4)
    return enriched, reclassified
