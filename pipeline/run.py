# -*- coding: utf-8 -*-
"""
pipeline/run.py · 流水线 CLI 编排
==================================
用法：
    python -m pipeline.run seed                      重新生成种子数据
    python -m pipeline.run classify                  全库分类
    python -m pipeline.run verify --limit-brands 6   品牌真实性核验（前 6 个）
    python -m pipeline.run verify-products --limit 5 产品参数多源核验（前 5 个）
    python -m pipeline.run discover --brands logitech,sony   指定品牌新品发现
    python -m pipeline.run enrich --limit 500              官方页信息/图片/参数补全
    python -m pipeline.run mass                            全量模式（全部品牌）
    python -m pipeline.run ingest                             合并入库
    python -m pipeline.run full --limit-brands 6 --limit 5   全链路
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from . import classify, discover, enrich, ingest, utils, verify  # noqa: E402


def cmd_seed():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
    import seed_data
    seed_data.main()


def cmd_classify():
    data, _, _ = ingest.load_all()
    n = classify.classify_all(data["products"])
    utils.save_json(utils.data_path("products.json"), data)
    print("分类完成：产品 %d，变更 %d" % (len(data["products"]), n))


def cmd_verify_brands(args):
    cfg = utils.load_config()
    _, brands_data, _ = ingest.load_all()
    brands = brands_data["brands"]
    if args.brands:
        keys = set(args.brands.split(","))
        brands = [b for b in brands if b["key"] in keys]
    elif args.limit_brands:
        # 优先核验「未核验」的品牌
        pending = [b for b in brands if not b.get("verified")]
        brands = pending[: args.limit_brands]
    updates = {}
    ok = 0
    for b in brands:
        utils.logger.info("核验品牌: %s (%s)", b["key"], b.get("official_url") or "未配置官网")
        before = b.get("verified")
        verify.verify_brand(b, cfg)
        updates[b["key"]] = b
        if b.get("verified"):
            ok += 1
        utils.logger.info("  -> %s %s", b["status"], b.get("evidence", {}).get("url", ""))
    report = ingest.run_ingest(brand_updates=updates, cfg=cfg)
    print("品牌核验完成：%d 个，其中确认 %d 个" % (len(updates), ok))
    print("报告:", report)


def cmd_verify_products(args):
    cfg = utils.load_config()
    data, brands_data, _ = ingest.load_all()
    brands_by_key = {b["key"]: b for b in brands_data["brands"]}
    products = data["products"]
    if args.brands:
        keys = set(args.brands.split(","))
        products = [p for p in products if p["brand"] in keys]
    if args.limit:
        products = products[: args.limit]
    for p in products:
        b = brands_by_key.get(p["brand"], {})
        utils.logger.info("核验产品: %s / %s", p["brand"], p["name"])
        verify.verify_product(p, b, cfg)
        v = p["verification"]
        utils.logger.info("  -> %s confidence=%s sources=%s",
                          v.get("data_status"), v.get("confidence"), v.get("source_count"))
    utils.save_json(utils.data_path("products.json"), data)
    report = ingest.run_ingest(cfg=cfg)
    print("产品核验完成：%d 个" % len(products))
    print("报告:", report)


def cmd_discover(args):
    cfg = utils.load_config()
    data, brands_data, _ = ingest.load_all()
    brands_by_key = {b["key"]: b for b in brands_data["brands"]}
    existing = {p["id"] for p in data["products"]}
    existing_names = set()
    for p in data["products"]:
        existing_names.add(utils.slug(p["brand"] + utils.canonical_name(p["name"])))

    targets = args.brands.split(",") if args.brands else None
    all_candidates = []
    for b in brands_data["brands"]:
        if targets and b["key"] not in targets:
            continue
        if not b.get("verified"):
            continue
        utils.logger.info("发现新品: %s", b["key"])
        cands = discover.discover_brand_products(b, cfg, existing_names=existing_names)
        all_candidates.extend(cands)
        if cands:
            utils.logger.info("  +%d 个候选", len(cands))
    report = ingest.run_ingest(candidates=all_candidates, cfg=cfg)
    print("新品发现：候选 %d 个，新增 %d 个" % (len(all_candidates), report["products_added"]))
    print("报告:", report)


def cmd_enrich(args):
    cfg = utils.load_config()
    data, brands_data, _ = ingest.load_all()
    done, reclassified, failed = enrich.enrich_unverified(data, brands_data, cfg, limit=args.limit or 500)
    utils.save_json(utils.data_path("products.json"), data)
    report = ingest.run_ingest(cfg=cfg)
    print("页面补全：完成 %d，重新分类 %d，失败 %d" % (done, reclassified, failed))
    print("报告:", report)


def _verify_brands_parallel(brands, cfg, workers=14):
    """并发核验品牌真实性。返回 (确认数, 总数)。"""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    ok = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(verify.verify_brand, b, cfg) for b in brands]
        for fut in as_completed(futs):
            b = fut.result()
            if b.get("verified"):
                ok += 1
    return ok, len(brands)


def cmd_mass(args):
    """全量模式：分类 → 核验全部品牌 → 全品牌新品发现 → 入库 → 页面/图片/参数补全 → 产品核验 → 审计。"""
    cfg = utils.load_config()
    data, brands_data, _ = ingest.load_all()
    brands = brands_data["brands"]

    print("== 1/7 全库分类 ==")
    n = classify.classify_all(data["products"])
    print("分类变更:", n)

    print("== 2/7 核验全部品牌（并发） ==")
    pending = [b for b in brands if not b.get("verified")]
    ok, total = _verify_brands_parallel(pending, cfg)
    utils.save_json(utils.data_path("brands.json"), brands_data)
    print("品牌核验：%d/%d 确认" % (ok, total))

    print("== 3/7 全品牌新品发现（并发） ==")
    verified = [b for b in brands_data["brands"] if b.get("verified")]
    existing = {p["id"] for p in data["products"]}
    existing_names = {utils.slug(p["brand"] + utils.canonical_name(p["name"])) for p in data["products"]}
    cap = cfg.get("discovery", {}).get("mass_total_cap", 5000)
    all_candidates = []

    def _discover_one(b):
        utils.logger.info("发现新品: %s", b["key"])
        cands = discover.discover_brand_products(b, cfg, existing_names=existing_names)
        return b["key"], cands

    from concurrent.futures import ThreadPoolExecutor, as_completed as _ac
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = {ex.submit(_discover_one, b): b for b in verified}
        for fut in _ac(futs):
            key, cands = fut.result()
            if cands:
                all_candidates.extend(cands)
                utils.logger.info("%s +%d 个候选（累计 %d）", key, len(cands), len(all_candidates))
            if len(all_candidates) >= cap:
                utils.logger.info("已达候选上限 %d，停止等待", cap)
                for f in list(futs):
                    f.cancel()
                break
    print("候选总数:", len(all_candidates))

    print("== 4/7 入库 ==")
    report = ingest.run_ingest(candidates=all_candidates, cfg=cfg)
    print("入库:", report)

    print("== 5/7 页面/图片/参数补全 ==")
    data, brands_data, _ = ingest.load_all()
    done, reclassified, failed = enrich.enrich_unverified(
        data, brands_data, cfg, limit=args.limit or 3000)
    utils.save_json(utils.data_path("products.json"), data)
    ingest.run_ingest(cfg=cfg)
    print("补全：完成 %d，重新分类 %d，失败 %d" % (done, reclassified, failed))

    print("== 6/7 产品数据多源核验（限量） ==")
    import argparse as _ap
    args2 = _ap.Namespace(**vars(args))
    args2.limit = min(args.limit or 150, 150)  # 多源核验仅抽样前 150 款
    cmd_verify_products(args2)

    print("== 7/7 数据审计 ==")
    import subprocess
    subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                 "scripts", "audit_data.py")], check=False)
    print("全量流程完成。")


def cmd_full(args):
    cfg = utils.load_config()
    print("== 1/5 全库分类 ==")
    data, brands_data, _ = ingest.load_all()
    n = classify.classify_all(data["products"])
    utils.save_json(utils.data_path("products.json"), data)
    print("分类变更:", n)

    print("== 2/5 品牌核验 ==")
    cmd_verify_brands(args)

    print("== 3/5 产品核验 ==")
    cmd_verify_products(args)

    print("== 4/5 新品发现 ==")
    cmd_discover(args)

    print("== 5/5 官方页信息补全 ==")
    cmd_enrich(args)

    print("全链路完成。")


def main():
    ap = argparse.ArgumentParser(description="外设水库自动化流水线")
    ap.add_argument("mode", choices=["seed", "classify", "verify", "verify-products", "discover", "enrich", "ingest", "full", "mass"])
    ap.add_argument("--limit-brands", type=int, default=6)
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--brands", type=str, default=None)
    args = ap.parse_args()

    utils.setup_logging()
    if args.mode == "seed":
        cmd_seed()
    elif args.mode == "classify":
        cmd_classify()
    elif args.mode == "verify":
        cmd_verify_brands(args)
    elif args.mode == "verify-products":
        cmd_verify_products(args)
    elif args.mode == "discover":
        cmd_discover(args)
    elif args.mode == "enrich":
        cmd_enrich(args)
    elif args.mode == "mass":
        cmd_mass(args)
    elif args.mode == "ingest":
        report = ingest.run_ingest()
        print("入库完成:", report)
    elif args.mode == "full":
        cmd_full(args)


if __name__ == "__main__":
    main()
