# -*- coding: utf-8 -*-
"""
pipeline/ingest.py · 数据入库与发布
====================================
把「发现 → 分类 → 核验」的结果合并进 data/products.json / data/brands.json，
并重算 data/meta.json 与 data/pipeline_report.json。
幂等：按 (brand, name) 去重，重复运行不会产生重复产品。
"""
from . import classify, discover, utils


def load_all():
    data = utils.load_json(utils.data_path("products.json"), {"schema_version": 1, "products": []})
    brands_data = utils.load_json(utils.data_path("brands.json"), {"schema_version": 1, "brands": []})
    meta = utils.load_json(utils.data_path("meta.json"), {})
    return data, brands_data, meta


def merge_candidates(data, candidates, cfg):
    """把发现的新产品并入产品库（先分类，标记待核验）。"""
    products = data.setdefault("products", [])
    by_id = {p["id"]: p for p in products}
    existing_canon = {utils.canonical_name(p["brand"] + p["name"]) for p in products}
    added = 0
    enriched = 0
    for c in candidates:
        canon = utils.canonical_name(c["brand"] + c["name"])
        pid = utils.slug(c["brand"]) + "-" + utils.slug(c["name"])
        hints = c.get("hints") or []
        if pid in by_id:
            # 已存在：仅补充缺失的类型线索，便于分类修正
            extra = by_id[pid].setdefault("extra", {})
            cur = set((extra.get("hints") or "").split())
            new = [h for h in hints if h not in cur]
            if new:
                extra["hints"] = " ".join(cur | set(hints))
                enriched += 1
            continue
        if canon in existing_canon:
            # 规范化名称已存在（跨语言/修饰词变体）→ 视为重复跳过
            continue
        product = {
            "id": pid,
            "brand": c["brand"],
            "name": c["name"],
            "category": None,
            "subtype": None,
            "tags": [],
            "specs": {},
            "description": (c.get("title") or "")[:300],
            "release": None,
            "price_cny": None,
            "extra": {"hints": " ".join(hints)} if hints else {},
            "links": {"official": c.get("url"), "reviews": []},
            "verification": {
                "brand_status": "待核验",
                "data_status": "unverified",
                "confidence": None,
                "last_checked": None,
                "notes": "自动发现（%s），待核验" % c.get("source", ""),
            },
            "discovered_at": utils.today(),
            "status": "published",
        }
        classify.classify_product(product)
        products.append(product)
        by_id[pid] = product
        existing_canon.add(canon)
        added += 1
    return added, enriched


def backfill_url_hints(data):
    """从已入库产品的官方 URL 回填类型线索（幂等，用于分类修正）。"""
    n = 0
    for p in data["products"]:
        url = (p.get("links") or {}).get("official")
        if not url:
            continue
        hints = discover.url_hints(url)
        if not hints:
            continue
        extra = p.setdefault("extra", {})
        cur = set((extra.get("hints") or "").split())
        new = [h for h in hints if h not in cur]
        if new:
            extra["hints"] = " ".join(cur | set(hints))
            n += 1
    return n


def apply_brand_verification(brands_data, brand_updates):
    """把品牌核验结果写回。"""
    by_key = {b["key"]: b for b in brands_data["brands"]}
    updated = 0
    for key, upd in brand_updates.items():
        b = by_key.get(key)
        if not b:
            continue
        if b.get("verified") != upd.get("verified"):
            updated += 1
        b["verified"] = upd.get("verified", b.get("verified"))
        b["verified_at"] = upd.get("verified_at", b.get("verified_at"))
        b["status"] = upd.get("status", b.get("status"))
        b["evidence"] = upd.get("evidence", b.get("evidence"))
        if upd.get("official_url"):
            b["official_url"] = upd["official_url"]
    return updated


def build_meta(data, brands_data, meta):
    from collections import Counter
    products = data["products"]
    by_cat = Counter(p.get("category", "unclassified") for p in products)
    by_status = Counter((p.get("verification") or {}).get("data_status", "unverified") for p in products)
    meta.update({
        "schema_version": 1,
        "generated_at": utils.utc_now(),
        "brands": {
            "total": len(brands_data["brands"]),
            "verified": sum(1 for b in brands_data["brands"] if b.get("verified")),
            "pending": sum(1 for b in brands_data["brands"] if not b.get("verified")),
        },
        "products": {
            "total": len(products),
            "by_category": {classify.CATEGORIES.get(k, k): v for k, v in sorted(by_cat.items(), key=lambda x: -x[1])},
            "by_status": dict(by_status),
        },
        "last_sync": utils.today(),
        "pipeline": meta.get("pipeline", {}),
    })
    return meta


def save_all(data, brands_data, meta, report):
    utils.save_json(utils.data_path("products.json"), data)
    utils.save_json(utils.data_path("brands.json"), brands_data)
    meta["pipeline"] = report
    utils.save_json(utils.data_path("meta.json"), meta)
    utils.save_json(utils.data_path("pipeline_report.json"), report)


def run_ingest(candidates=None, brand_updates=None, cfg=None):
    """入口：合并候选产品 + 品牌核验结果 → 分类 → 重算元数据 → 保存。"""
    cfg = cfg or utils.load_config()
    data, brands_data, meta = load_all()

    classify_changed = classify.classify_all(data["products"])
    hint_backfilled = backfill_url_hints(data)
    if hint_backfilled:
        classify.classify_all(data["products"])

    added = 0
    enriched = 0
    if candidates:
        added, enriched = merge_candidates(data, candidates, cfg)
        classify.classify_all(data["products"])

    brand_updated = 0
    if brand_updates:
        brand_updated = apply_brand_verification(brands_data, brand_updates)

    meta = build_meta(data, brands_data, meta)
    report = {
        "ran_at": utils.utc_now(),
        "products_total": len(data["products"]),
        "products_added": added,
        "products_enriched": enriched,
        "hint_backfilled": hint_backfilled,
        "classify_changed": classify_changed,
        "brands_updated": brand_updated,
        "brands_verified_total": meta["brands"]["verified"],
    }
    save_all(data, brands_data, meta, report)
    return report
