# -*- coding: utf-8 -*-
"""
scripts/audit_data.py · 数据核算审计
====================================
核算全库数据：品牌覆盖、产品分布、图片/描述/参数覆盖率、核验状态分布、
重复检测、引用完整性。结果写入 data/audit_report.json 并在控制台摘要。
用法：python scripts/audit_data.py
"""
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    return json.load(open(os.path.join(ROOT, "data", name), encoding="utf-8"))


def main():
    brands = load("brands.json")["brands"]
    products = load("products.json")["products"]
    by_key = {b["key"]: b for b in brands}
    cat_labels = {"earphone": "耳机", "mouse": "鼠标", "keyboard": "键盘",
                  "gamepad": "手柄", "speaker": "音响", "mousepad": "鼠标垫", "unclassified": "未分类"}

    ids = [p["id"] for p in products]
    dup_ids = [i for i, c in Counter(ids).items() if c > 1]

    canon = [p["brand"] + "|" + p["name"].lower().replace(" ", "") for p in products]
    dup_canon = [c for c, n in Counter(canon).items() if n > 1]

    brand_products = Counter(p["brand"] for p in products)
    no_product_brands = [b["key"] for b in brands if brand_products.get(b["key"], 0) == 0]
    verified_no_product = [k for k in no_product_brands if by_key[k].get("verified")]

    with_image = sum(1 for p in products if p.get("image"))
    with_desc = sum(1 for p in products if (p.get("description") or "").strip())
    with_specs = sum(1 for p in products if p.get("specs"))
    with_official_link = sum(1 for p in products if (p.get("links") or {}).get("official"))
    orphan = [p["id"] for p in products if p["brand"] not in by_key]

    cat_dist = Counter(p.get("category", "unclassified") for p in products)
    data_status = Counter((p.get("verification") or {}).get("data_status", "none") for p in products)
    brand_status = Counter(b.get("status", "待核验") for b in brands)
    verified_brands = sum(1 for b in brands if b.get("verified"))

    report = {
        "site": "外设水库",
        "generated_at": json.load(open(os.path.join(ROOT, "data", "meta.json"), encoding="utf-8")).get("generated_at"),
        "brands": {"total": len(brands), "verified": verified_brands,
                   "by_status": dict(brand_status),
                   "with_products": len(brands) - len(no_product_brands),
                   "no_products": len(no_product_brands),
                   "verified_no_products": len(verified_no_product)},
        "products": {"total": len(products), "by_category": {cat_labels.get(k, k): v for k, v in sorted(cat_dist.items(), key=lambda x: -x[1])},
                     "data_status": dict(data_status),
                     "with_image": with_image, "with_description": with_desc,
                     "with_specs": with_specs, "with_official_link": with_official_link,
                     "image_coverage": round(with_image / max(len(products), 1) * 100, 1),
                     "spec_coverage": round(with_specs / max(len(products), 1) * 100, 1)},
        "integrity": {"dup_ids": len(dup_ids), "dup_canonical_names": len(dup_canon),
                      "orphan_products": len(orphan)},
        "brands_no_products_sample": no_product_brands[:20],
    }
    out = os.path.join(ROOT, "data", "audit_report.json")
    json.dump(report, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("=== 外设水库数据审计 ===")
    print("品牌 %d（已核验 %d / 有产品 %d） | 产品 %d" % (
        len(brands), verified_brands, report["brands"]["with_products"], len(products)))
    print("类型分布:", report["products"]["by_category"])
    print("数据核验:", dict(data_status))
    print("图片 %d (%.1f%%) | 描述 %d | 参数 %d (%.1f%%) | 官网链接 %d" % (
        with_image, report["products"]["image_coverage"], with_desc,
        with_specs, report["products"]["spec_coverage"], with_official_link))
    print("重复 id %d | 疑似重复名称 %d | 孤儿产品 %d" % (
        len(dup_ids), len(dup_canon), len(orphan)))
    if no_product_brands:
        print("无产品品牌 %d 个（样例）: %s" % (len(no_product_brands), ",".join(no_product_brands[:15])))
    if len(dup_ids) or len(dup_canon) or orphan:
        print("⚠ 存在完整性问题，见 audit_report.json")
    else:
        print("完整性：通过 ✓")
    print("审计报告: data/audit_report.json")


if __name__ == "__main__":
    main()
