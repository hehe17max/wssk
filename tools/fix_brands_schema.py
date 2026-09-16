# -*- coding: utf-8 -*-
"""
tools/fix_brands_schema.py · 品牌数据重建（修正字段 schema）
============================================================
品牌条目规范字段：key/name/name_en/categories/groups/region/official_url/
curated/verified/verified_at/status/evidence。
从 brand_registry 重建，并按 key 保留既有核验证据（云端跑出的真实证据不丢弃）。
用法：python tools/fix_brands_schema.py
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from config import brand_registry as BR


def main():
    data_dir = os.path.join(ROOT, "data")
    old_path = os.path.join(data_dir, "brands.json")
    old = {b["key"]: b for b in json.load(open(old_path, encoding="utf-8"))["brands"]}

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    brands = []
    for b in BR.build_brands():
        rec = {
            "key": b["key"],
            "name": b["zh"],
            "name_en": b["en"],
            "categories": b["categories"],
            "groups": b["groups"],
            "region": b["region"],
            "official_url": b["official_url"],
            "curated": bool(b.get("curated")),
            "verified": False,
            "verified_at": None,
            "status": "待核验",
            "evidence": None,
        }
        o = old.get(b["key"])
        if o:
            for f in ("verified", "verified_at", "status", "evidence"):
                if o.get(f) is not None:
                    rec[f] = o[f]
            if o.get("official_url"):
                rec["official_url"] = o["official_url"]
        brands.append(rec)

    with open(old_path, "w", encoding="utf-8") as f:
        json.dump({"schema_version": 1, "generated_at": now, "brands": brands}, f, ensure_ascii=False, indent=1)

    from collections import Counter
    st = Counter(b["status"] for b in brands)
    print("品牌重建完成: %d | 状态分布 %s" % (len(brands), dict(st)))
    print("字段样例:", sorted(brands[0].keys()))


if __name__ == "__main__":
    main()
