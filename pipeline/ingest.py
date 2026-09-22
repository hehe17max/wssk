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
            "tags": list(c.get("tags") or []),
            "specs": {},
            "description": (c.get("description") or c.get("title") or "")[:500],
            "release": None,
            "price_cny": c.get("price_cny"),
            "image": c.get("image"),
            "extra": {"hints": " ".join(hints)} if hints else {},
            "links": {"official": c.get("url"), "reviews": []},
            "verification": {
                "brand_status": "待核验",
                "data_status": "official" if (c.get("image") or c.get("description")) else "unverified",
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


def prune_junk(data):
    """清洗垃圾条目：栏目/博客/服务页 URL、栏目类名称；返回移除数。"""
    import re as _re
    from urllib.parse import urlparse as _up
    junk_path_parts = (
        "/blogs/", "/blog/", "/news/", "/newsroom/", "/press/", "/media/",
        "/servicesolutions/", "/solutions_latest/", "/katalog/", "/collections/",
        "/pages/", "/tags/", "/search", "/about/", "/support/", "/help/",
        "/company/", "/careers/", "/jobs/", "/legal/", "/privacy/", "/terms/",
        "/faq/", "/account/", "/login/", "/cart/", "/wishlist/", "/compare",
        "/contact/", "/videos/", "/video/", "/wallpapers/", "/resources/",
        "/insights/", "/stories/", "/webinars/", "/whitepapers/", "/case-studies/",
        "/testimonials/", "/team/", "/management/", "/corporate/", "/governance/",
        "/cookie", "/sitemap", "/tracking", "/app/", "/store-locator/",
        "/where-to-buy/", "/catalog/", "/category/", "/categories/", "/archive/",
        "/author/", "/feed", "/rss", "/forums/", "/forum/", "/community/",
        "/support-articles/", "/product-support/", "/questions/", "/topics/",
        "/articles/", "/article/", "/zte_certification", "/product_index",
        "/exa_details", "/param/", "/detail/", "/car-audio/", "/marques/",
        "/smartphones/", "/nintendo-switch/", "/xbox-series-xs/", "/bmw/",
        "/gift/", "/gifts/", "/replacement/", "/spare-parts/", "/repair/",
        "/manuals/", "/knowledge/", "/kb/", "/academy/", "/learn/", "/guides/",
        "/guide/", "/tutorials/", "/tutorial/", "/education/", "/docs/",
        "/documentation/", "/api/", "/developers/", "/status/", "/maintenance/",
        "/promotions/", "/promo/", "/offers/", "/specials/", "/campaigns/",
        "/giveaway/", "/giveaways/", "/contests/", "/quiz/", "/quizzes/",
        "/lookbook/", "/magazine/", "/journal/", "/publications/",
        "/publication/", "/certifications/", "/awards/", "/grants/",
        "/research/", "/podcasts/", "/podcast/", "/brand-assets/", "/press-kit/",
        "/media-kit/", "/trade-shows/", "/exhibitions/", "/conferences/",
        "/summits/", "/meetups/", "/hackathons/", "/internships/",
        "/wholesale/", "/wholesaler/", "/distributors/", "/distributor/",
        "/procurement/", "/suppliers/", "/vendor/", "/vendors/", "/portals/",
        "/portal/", "/dashboard/", "/inbox/", "/messages/", "/newsletters/",
        "/unsubscribe/", "/confirm/", "/activation/", "/otp/", "/captcha/",
        "/gdpr/", "/ccpa/", "/cookie-policy/", "/terms-of-service/",
        "/terms-of-use/", "/license-agreement/", "/eula/", "/agreements/",
        "/invoices/", "/billing/", "/payments/", "/refunds/", "/exchange/",
        "/exchanges/", "/cancellation/", "/cancellations/", "/track-order/",
        "/order-tracking/", "/shipping-policy/", "/shipping-options/",
        "/customs/", "/duties/", "/tax/", "/taxes/", "/vat/", "/marketplace/",
        "/integrations/", "/plugins/", "/extensions/", "/addons/", "/themes/",
        "/templates/", "/widgets/", "/components/", "/modules/", "/sdk/",
        "/apis/", "/webhooks/", "/changelog/", "/roadmap/", "/milestones/",
        "/releases/", "/examples/", "/demos/", "/sample/", "/samples/",
        "/contributing/", "/code-of-conduct/", "/funding/", "/donate/",
        "/donation/", "/kickstarter/", "/patreon/", "/indiegogo/",
        "/assets/", "/cdn/", "/files/", "/s/files/", "/cdn-cgi/", "/checkout/",
    )
    # 名称级垃圾：西语站前缀、资源名、乱码、配件/耗材、SEO 堆砌
    _ACC = _re.compile(r"(storage bag|carry (case|pouch)|carrying case|protective (case|cover)|protection box|dust (cover|plug)|charging cable|data cable|power cord|ear tips?|comply foam|replacement (earpads?|pads?|cushions?|tips?)|screen (protector|guard)|wrist rest|mouse (feet|skates))", _re.I)
    _MAIN = _re.compile(r"(earbud|earphone|headphone|speaker|soundbar|subwoofer|mouse|keyboard|gamepad|controller|console|power ?bank|charger|charging station|hub|dock|adapter|amplifier|\bamp\b|dac|streamer|microphone|\bmic\b|webcam|monitor|tablet|phone|laptop|\btv\b|receiver|headunit)", _re.I)
    _GEN = _re.compile(r"\b(wireless|bluetooth|headphones?|earphones?|earbuds?|speakers?|with|and|for|noise|cancelling|charging|compatible|headset|cable|type|usb|portable|mini|new|upgrade|pro|max|plus)\b", _re.I)
    _RESOURCE_NAMES = ("assets", "css", "js", "images", "files", "img", "static")
    def _name_extra_junk(nl, raw):
        if nl.startswith("es "):
            return True
        if nl in _RESOURCE_NAMES:
            return True
        if _re.search(r"(.)\1{6,}", raw):
            return True
        if len(nl) > 45 and len(set(nl)) < 9:
            return True
        if _ACC.search(raw) and not _MAIN.search(raw):
            return True
        g = len(_GEN.findall(raw))
        if g >= 4 or len(nl.split()) >= 18:
            return True
        return False
    junk_name_words = (
        "blog", "blogs", "news", "newsroom", "press", "media", "videos",
        "wallpapers", "resources", "insights", "stories", "webinars",
        "whitepapers", "case study", "case studies", "testimonial",
        "servicesolutions", "solutions", "aggregation", "katalog", "category",
        "catalogue", "services", "service level", "corporate", "governance",
        "sustainability", "careers", "investor", "cookies", "privacy policy",
        "terms of", "faq", "help center", "support center", "about us",
        "community", "forum", "shop all", "view all", "shop the", "collection",
        "apparel", "merchandise", "gift card", "giftcard", "gift cards",
        "plushie", "plushies", "sticker", "stickers", "keychain", "lanyard",
        "poster", "posters", "mug", "mugs", "t-shirt", "tshirt", "hoodie",
        "socks", "beanie", "backpack", "water bottle", "towel", "tote bag",
    )
    before = len(data["products"])
    kept = []
    removed = 0
    for p in data["products"]:
        url = ((p.get("links") or {}).get("official") or "").lower()
        name = (p.get("name") or "").lower()
        path = _up(url).path if url else ""
        junk = False
        if url:
            if any(jp in path for jp in junk_path_parts):
                junk = True
        if not junk:
            if any(w in name for w in junk_name_words):
                junk = True
        if not junk:
            if _name_extra_junk(name, p.get("name") or ""):
                junk = True
        if junk:
            removed += 1
        else:
            kept.append(p)
    data["products"] = kept
    return removed, before - len(kept)


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
    import gzip as _gz
    utils.save_json(utils.data_path("products.json"), data)
    # 站点提速：预压缩 products.json.gz（前端 DecompressionStream 解压，体积约减 80%）
    try:
        p = utils.data_path("products.json")
        with open(p, "rb") as _f:
            raw = _f.read()
        with open(p + ".gz", "wb") as _f:
            _f.write(_gz.compress(raw, 6))
    except Exception:
        pass
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
