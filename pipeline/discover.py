# -*- coding: utf-8 -*-
"""
pipeline/discover.py · 新品发现
================================
从品牌官网自动发现新产品：
  1. sitemap.xml / sitemap_index.xml 中的产品 URL（跟随子 sitemap，宽松过滤）
  2. Shopify /products.json（名称+URL+真实图片+描述+标签，分页）
  3. 首页中符合产品 URL 模式的链接
发现的候选产品写入 ingest 流程，经分类后入库（状态 = 待核验）。
"""
import re
from urllib.parse import urljoin, urlparse

import requests

from . import utils

# 非产品栏目路径段（整段匹配，用于 sitemap/首页过滤）
NON_PRODUCT_SEGMENTS = {
    "support", "help", "about", "blog", "blogs", "news", "newsroom", "press",
    "media", "events", "company", "careers", "jobs", "legal", "privacy",
    "terms", "contact", "login", "cart", "account", "wishlist", "faq",
    "download", "downloads", "drivers", "driver", "software", "firmware",
    "warranty", "registration", "register", "search", "sitemap", "robots",
    "cdn-cgi", "wp-content", "wp-includes", "wp-json", "collections", "pages",
    "policies", "policy", "compare", "checkout", "gift-cards", "giftcard",
    "redeem", "rewards", "newsletter", "subscription", "investors", "investor",
    "sustainability", "environment", "security", "vulnerability", "developers",
    "developer", "partners", "partner", "resellers", "reseller", "where-to-buy",
    "stores", "store-locator", "pro-shops", "affiliates", "affiliate",
    "community", "forum", "forums", "player-support", "games", "game",
    "esports", "esports-team", "app", "mobile-app", "apps", "tools", "tool",
    "b2b", "enterprise", "business", "shop", "store", "servicesolutions",
    "solutions_latest", "katalog", "catalog", "categories", "category",
    "tags", "tag", "archive", "archives", "author", "feed", "rss", "tracking",
    "trailer", "wallpapers", "resources", "resource", "insights", "stories",
    "videos", "video", "webinars", "whitepapers", "case-studies", "showcase",
    "gallery", "reviews", "testimonials", "team", "management", "board",
    "corporate", "governance", "cookies", "cookie", "sitemap_index",
    "support-articles", "product-support", "questions", "topics", "articles",
    "article", "zte_certification", "product_index", "exa_details", "param",
    "detail", "car-audio", "marques", "smartphones", "nintendo-switch",
    "xbox-series-xs", "bmw", "gift", "gifts", "replacement", "spare-parts",
    "repair", "manuals", "knowledge", "kb", "academy", "learn", "guides",
    "guide", "tutorials", "tutorial", "education", "docs", "documentation",
    "api", "status", "maintenance", "promotions", "promo", "offers",
    "specials", "campaigns", "giveaway", "giveaways", "contests", "quiz",
    "quizzes", "lookbook", "magazine", "journal", "publications",
    "publication", "certifications", "awards", "grants", "research",
    "podcasts", "podcast", "brand-assets", "press-kit", "media-kit",
    "trade-shows", "exhibitions", "conferences", "summits", "meetups",
    "hackathons", "internships", "wholesale", "wholesaler", "procurement",
    "suppliers", "vendor", "vendors", "portals", "portal", "dashboard",
    "inbox", "messages", "newsletters", "unsubscribe", "gdpr", "ccpa",
    "cookie-policy", "terms-of-service", "terms-of-use", "license-agreement",
    "eula", "agreements", "invoices", "billing", "payments", "refunds",
    "exchange", "exchanges", "cancellation", "cancellations", "track-order",
    "order-tracking", "shipping-policy", "shipping-options", "customs",
    "duties", "marketplace", "integrations", "plugins", "extensions",
    "addons", "themes", "templates", "widgets", "components", "modules",
    "sdk", "apis", "webhooks", "changelog", "roadmap", "milestones",
    "releases", "examples", "demos", "contributing", "code-of-conduct",
    "funding", "kickstarter", "patreon", "indiegogo",
}
# 产品名中的非产品词（用于判断名称是否只是栏目/类别词）
NON_PRODUCT_NAME_WORDS = {
    "products", "product", "mice", "mouse", "keyboards", "keyboard", "headsets",
    "headset", "speakers", "speaker", "accessories", "accessory", "support",
    "contact", "about", "search", "cart", "login", "account", "wishlist", "faq",
    "blog", "blogs", "news", "newsroom", "deals", "gaming", "creators",
    "business", "home", "index", "catalog", "catalogue", "categories",
    "category", "shop", "store", "buy", "compare", "help", "new", "featured",
    "all", "collection", "collections", "gear", "audio", "wireless", "wired",
    "official", "site", "us", "global", "en", "zh", "de", "fr", "jp", "uk",
    "series", "line", "family", "overview", "explore", "discover", "chairs",
    "chair", "mats", "mat", "pads", "pad", "customize", "custom", "configure",
    "configurator", "specs", "specifications", "reviews", "gallery", "bundles",
    "bundle", "kits", "kit", "parts", "part", "stands", "stand", "arms", "arm",
    "mounts", "mount", "cases", "case", "bags", "bag", "caps", "cap",
    "clothing", "apparel", "merch", "merchandise", "swag", "gift", "pc",
    "streaming", "smart", "mobile", "laptop", "desktop", "console", "tablet",
    "monitor", "tv", "television", "video", "cameras", "camera", "projectors",
    "projector", "printers", "printer", "servers", "server", "storage",
    "networking", "service", "services", "solutions", "solution", "press",
    "media", "videos", "video", "wallpapers", "resources", "downloads",
}
# 非外设品类词（含则跳过该候选，保持数据库聚焦外设）
NON_PERIPHERAL_WORDS = {
    "chair", "chairs", "apparel", "hoodie", "hoodies", "t-shirt", "tshirt",
    "shirt", "shirts", "jacket", "jackets", "backpack", "backpacks", "cap",
    "caps", "socks", "pants", "shoes", "shorts", "beanie", "beanies", "mask",
    "masks", "towel", "towels", "bottle", "bottles", "mug", "mugs", "sticker",
    "stickers", "keychain", "keychains", "lanyard", "lanyards", "poster",
    "posters", "puzzle", "puzzles", "sleeve", "sleeves", "glove", "gloves",
    "sweatshirt", "sweatshirts", "tank", "tanks", "underwear", "plushie",
    "plushies", "toy", "toys", "figurine", "figurines", "statuette",
}
# 忽略的静态/非页面扩展名
SKIP_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".avif", ".ico", ".css",
    ".js", ".json", ".pdf", ".zip", ".rar", ".7z", ".xml", ".txt", ".mp4",
    ".webm", ".mp3", ".wav", ".woff", ".woff2", ".ttf", ".eot", ".xls", ".xlsx",
    ".doc", ".docx", ".csv", ".gz", ".map", ".ts",
}


def _is_product_url(url, patterns):
    u = url.lower()
    return any(p in u for p in patterns)


def _has_non_product_segment(path):
    segs = [s for s in path.split("/") if s]
    for s in segs:
        s = s.lower().strip()
        if s in NON_PRODUCT_SEGMENTS:
            return True
        if s.startswith("page-") or s.startswith("?page") or s.startswith("search"):
            return True
    return False


def _has_skip_extension(url):
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in SKIP_EXTENSIONS)


def _looks_like_product_url(url, patterns, min_segments=3):
    """宽松产品 URL 判定：命中严格模式，或路径≥3段且无栏目段/静态扩展。"""
    if _is_product_url(url, patterns):
        return True
    if _has_skip_extension(url):
        return False
    if _has_non_product_segment(urlparse(url).path):
        return False
    segs = [s for s in urlparse(url).path.split("/") if s]
    segs = [s for s in segs if s.lower() not in ("en", "us", "zh", "de", "fr", "jp", "uk", "intl", "global")]
    return len(segs) >= min_segments


def discover_from_sitemap(brand, cfg):
    """解析 sitemap（含索引→子 sitemap），返回产品 URL 列表（宽松过滤）。"""
    base = brand.get("official_url", "")
    if not base:
        return []
    sitemap_candidates = [
        urljoin(base, "sitemap.xml"),
        urljoin(base, "sitemap_index.xml"),
        urljoin(base, "sitemap-index.xml"),
        urljoin(base, "sitemap/sitemap.xml"),
        urljoin(base, "sitemap/sitemap-index.xml"),
    ]
    patterns = cfg.get("discovery", {}).get("product_url_patterns", [])
    max_children = cfg.get("discovery", {}).get("max_sitemap_children", 25)
    found = []

    def _collect(html):
        urls = re.findall(r"<loc>\s*([^<]+?)\s*</loc>", html)
        return [u.strip() for u in urls if u.strip().lower().startswith("http")]

    for sm in sitemap_candidates:
        status, html = utils.http_get(sm, cfg)
        if status != 200:
            continue
        locs = _collect(html)
        if not locs:
            continue
        # 判断是否为 sitemap 索引（子项为 .xml）
        child_xml = [u for u in locs if re.search(r"\.xml($|\?)", u, re.I)]
        if child_xml:
            # 优先英文版子 sitemap
            child_xml.sort(key=lambda u: (0 if re.search(r"/(en|en-us|en-gb|us-en|english)/", u, re.I) else 1, u))
            for sub in child_xml[:max_children]:
                s2, h2 = utils.http_get(sub, cfg)
                if s2 == 200:
                    for u in _collect(h2):
                        if _looks_like_product_url(u, patterns):
                            found.append(u)
        else:
            for u in locs:
                if _looks_like_product_url(u, patterns):
                    found.append(u)
        # 去重保序
        seen = set()
        found = [u for u in found if not (u in seen or seen.add(u))]
        if found:
            utils.logger.info("%s sitemap 发现产品 URL %d 个", brand.get("key"), len(found))
            return found
    return found


def discover_from_shopify(brand, cfg):
    """Shopify /products.json：直接拿名称+URL+图片+描述+标签（分页最多 2 页）。"""
    base = brand.get("official_url", "")
    if not base:
        return []
    results = []
    for page in range(1, 3):
        url = urljoin(base, "/products.json?limit=250&page=%d" % page)
        try:
            r = requests.get(
                url, headers={"User-Agent": cfg.get("http", {}).get("user_agent", "")},
                timeout=cfg.get("http", {}).get("timeout", 15),
            )
            if r.status_code != 200:
                break
            data = r.json()
            prods = data.get("products", [])
            if not prods:
                break
            for p in prods:
                images = p.get("images") or []
                img = images[0].get("src") if images else None
                results.append({
                    "name": p.get("title", ""),
                    "url": urljoin(base, "/products/" + p.get("handle", "")),
                    "title": p.get("title", ""),
                    "image": img,
                    "description": (p.get("body_html") or "")[:400],
                    "price_cny": None,
                    "tags": (p.get("tags") or "").split(",")[:8],
                    "product_type": p.get("product_type") or "",
                })
        except Exception as e:  # noqa: BLE001
            utils.logger.debug("shopify 失败: %s", e)
            break
    if results:
        utils.logger.info("%s Shopify 发现产品 %d 个", brand.get("key"), len(results))
    return results


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
        if full in seen:
            continue
        seen.add(full)
        # 首页链接：命中严格模式 或 宽松判定（≥3 段）都可作为候选
        if not (_is_product_url(full, patterns) or _looks_like_product_url(full, patterns)):
            continue
        out.append(full)
    return out


def _segment_is_category(seg):
    """判断 URL 段是否仅为栏目/类别词（如 gaming-mice）。"""
    words = [w for w in re.split(r"[\s\-_]+", seg.lower()) if w]
    return bool(words) and all(w in NON_PRODUCT_NAME_WORDS for w in words)


def name_from_url(url):
    """从 URL 提取产品名（跳过栏目/语言段，取最后 1-2 个产品段）。"""
    path = urlparse(url).path
    segs = [s for s in path.split("/") if s and not s.lower().startswith(("product", "p", "item", "goods", "id"))]
    if not segs:
        return ""
    words = []
    for seg in reversed(segs):
        w = re.sub(r"\.(html|shtml|php)$", "", seg, flags=re.I)
        w = w.replace("-", " ").replace("_", " ").replace("+", " ").strip()
        if not w or _segment_is_category(w):
            if words:
                break
            continue
        words.insert(0, w)
        if len(words) >= 2:
            break
    return " ".join(words) if words else ""


# URL 路径段 → 类型线索（官网栏目通常比产品名更可靠）
URL_HINT_MAP = {
    "mice": "mouse", "mouse": "mouse", "gaming-mice": "mouse", "wireless-mice": "mouse",
    "wired-mice": "mouse", "ergonomic-mice": "mouse", "mouse-accessories": "mouse",
    "keyboards": "keyboard", "keyboard": "keyboard", "keyboard-accessories": "keyboard",
    "gaming-keyboards": "keyboard", "wireless-keyboards": "keyboard",
    "mechanical-keyboards": "keyboard", "keycaps": "keyboard", "switches": "keyboard",
    "headsets": "earphone", "headset": "earphone", "headphones": "earphone",
    "headphone": "earphone", "audio": "earphone", "gaming-headsets": "earphone",
    "wireless-headsets": "earphone", "bluetooth-headsets": "earphone",
    "noise-cancelling-headphones": "earphone", "earbuds": "earphone",
    "true-wireless": "earphone", "tws": "earphone", "in-ear": "earphone",
    "over-ear": "earphone", "on-ear": "earphone", "speakers": "speaker",
    "speaker": "speaker", "speaker-systems": "speaker", "soundbars": "speaker",
    "smart-speakers": "speaker", "computer-speakers": "speaker",
    "gaming-speakers": "speaker", "wireless-speakers": "speaker",
    "bluetooth-speakers": "speaker", "bookshelf-speakers": "speaker",
    "gamepads": "gamepad", "controllers": "gamepad", "gaming-controllers": "gamepad",
    "game-controllers": "gamepad", "joysticks": "gamepad", "arcade-sticks": "gamepad",
    "fight-sticks": "gamepad", "racing-wheels": "gamepad", "wheels": "gamepad",
    "mousepads": "mousepad", "desk-mats": "mousepad", "mouse-pads": "mousepad",
    "mouse-mats": "mousepad", "desk-pads": "mousepad", "gaming-mouse-mats": "mousepad",
}


def url_hints(url):
    """从产品 URL 提取类型线索列表。"""
    segs = urlparse(url).path.lower().split("/")
    return [URL_HINT_MAP[s] for s in segs if s in URL_HINT_MAP]


def discover_brand_products(brand, cfg, existing_names=None):
    """对一个品牌执行全部发现渠道，返回候选产品 [{name,url,title,source,...}]。"""
    existing_names = existing_names or set()
    candidates = []
    seen = set()

    def _add(name, url, title, source, extra=None):
        n = re.sub(r"\s+", " ", (name or "").strip())
        if not n or len(n) < 2:
            return
        low = n.lower()
        words = [w for w in re.split(r"[\s\-_/]+", low) if w]
        # 名称全部由非产品词组成 → 栏目页而非产品
        if words and all(w in NON_PRODUCT_NAME_WORDS for w in words):
            return
        # 含非外设品类词 → 跳过（椅子/服饰/周边等）
        if any(w in NON_PERIPHERAL_WORDS for w in words):
            return
        key = utils.slug(brand.get("key", "") + utils.canonical_name(n))
        if key in seen or key in existing_names:
            return
        seen.add(key)
        item = {
            "brand": brand.get("key"),
            "name": n,
            "url": url,
            "title": (title or "").strip(),
            "source": source,
            "hints": url_hints(url),
        }
        if extra:
            item.update({k: v for k, v in extra.items() if v not in (None, "")})
        candidates.append(item)

    if brand.get("verified"):
        for url in discover_from_sitemap(brand, cfg):
            _add(name_from_url(url), url, "", "sitemap")
        for p in discover_from_shopify(brand, cfg):
            _add(p.get("name"), p.get("url"), p.get("title"), "shopify", {
                "image": p.get("image"),
                "description": p.get("description"),
                "price_cny": p.get("price_cny"),
                "tags": p.get("tags"),
            })
        for url in discover_from_homepage(brand, cfg)[:300]:
            _add(name_from_url(url), url, "", "homepage")

    max_new = cfg.get("discovery", {}).get("max_new_products_per_run", 200)
    return candidates[:max_new]
