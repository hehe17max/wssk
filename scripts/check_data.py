# -*- coding: utf-8 -*-
"""
scripts/check_data.py · 数据质量检查
====================================
校验 data/ 三个 JSON 的结构、计数、重复与引用完整性，供交付前与 CI 使用。
用法：python scripts/check_data.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def main():
    errors = []
    data = json.load(open(os.path.join(ROOT, "data", "products.json"), encoding="utf-8"))
    brands = json.load(open(os.path.join(ROOT, "data", "brands.json"), encoding="utf-8"))
    meta = json.load(open(os.path.join(ROOT, "data", "meta.json"), encoding="utf-8"))

    products = data["products"]
    brand_list = brands["brands"]
    keys = {b["key"] for b in brand_list}
    ids = set()
    cat_set = {"earphone", "mouse", "keyboard", "gamepad", "speaker", "mousepad", "unclassified"}

    for p in products:
        if not p.get("id"):
            errors.append("产品缺少 id")
        if p["id"] in ids:
            errors.append("重复产品 id: %s" % p["id"])
        ids.add(p["id"])
        if p.get("category") not in cat_set:
            errors.append("%s 类型非法: %s" % (p.get("id"), p.get("category")))
        if not p.get("subtype"):
            errors.append("%s 缺少子类型" % p.get("id"))
        if p.get("brand") not in keys:
            errors.append("%s 引用未知品牌: %s" % (p.get("id"), p.get("brand")))

    # meta 一致性
    if meta["products"]["total"] != len(products):
        errors.append("meta 产品总数不一致: %s vs %s" % (meta["products"]["total"], len(products)))
    if meta["brands"]["total"] != len(brand_list):
        errors.append("meta 品牌总数不一致")

    print("产品:", len(products), "| 品牌:", len(brand_list))
    print("meta:", json.dumps(meta["products"]["by_category"], ensure_ascii=False))
    if errors:
        print("发现问题 %d 个:" % len(errors))
        for e in errors[:20]:
            print(" -", e)
        sys.exit(1)
    print("校验通过：结构完整、无重复、引用一致 ✓")


if __name__ == "__main__":
    main()
