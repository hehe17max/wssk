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
    from concurrent.futures import ThreadPoolExecutor, as_completed as _ac2

    def _vp(p):
        b = brands_by_key.get(p["brand"], {})
        try:
            verify.verify_product(p, b, cfg)
        except Exception:  # noqa: BLE001
            pass
        v = p["verification"]
        return p["id"], v.get("data_status"), v.get("confidence"), v.get("source_count")

    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(_vp, p) for p in products]
        for fut in _ac2(futs):
            try:
                _pid, ds, conf, sc = fut.result()
                utils.logger.info("  -> %s confidence=%s sources=%s", ds, conf, sc)
            except Exception:  # noqa: BLE001
                pass
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


def cmd_prune(args):
    """清洗垃圾条目（博客/服务/栏目页）并重新分类去重，返回清洗统计。"""
    cfg = utils.load_config()
    data, brands_data, _ = ingest.load_all()
    removed, _ = ingest.prune_junk(data)
    n = classify.classify_all(data["products"])
    utils.save_json(utils.data_path("products.json"), data)
    report = ingest.run_ingest(cfg=cfg)
    print("清洗完成：移除 %d 条垃圾，分类变更 %d，剩余产品 %d" % (removed, n, len(data["products"])))
    print("报告:", report)


def cmd_localize(args):
    """全库数据中文化：生成 name_zh（中文名），描述/标签术语中文化。"""
    from . import localize
    cfg = utils.load_config()
    data, brands_data, _ = ingest.load_all()
    n = localize.localize_all(data, brands_data)
    utils.save_json(utils.data_path("products.json"), data)
    print("中文化完成：%d 条产品新增中文名（全库 %d 条）" % (n, len(data["products"])))
    try:
        ingest.run_ingest(cfg=cfg)
    except Exception as e:
        print("meta 更新跳过:", e)


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
    """全量模式：分类 → 核验全部品牌 → 全品牌新品发现 → 入库 → 页面/图片/参数补全 → 产品核验 → 审计。
    每步独立容错：单步失败记录后继续，最后统一保存（保证部分结果可提交）。"""
    import traceback
    import json as _json

    cfg = utils.load_config()
    data, brands_data, _ = ingest.load_all()
    brands = brands_data["brands"]
    step_errors = []

    def _step(name, fn):
        print("== %s ==" % name)
        try:
            fn()
        except Exception:  # noqa: BLE001
            msg = traceback.format_exc(limit=3)
            print("[步骤失败] %s: %s" % (name, msg))
            step_errors.append((name, msg))
        finally:
            utils.save_json(utils.data_path("products.json"), data)
            utils.save_json(utils.data_path("brands.json"), brands_data)

    def _s1():
        removed, _ = ingest.prune_junk(data)
        n = classify.classify_all(data["products"])
        print("清洗垃圾:", removed, "| 分类变更:", n)

    def _s2():
        pending = [b for b in brands if not b.get("verified")]
        ok, total = _verify_brands_parallel(pending, cfg)
        print("品牌核验：%d/%d 确认" % (ok, total))

    def _s3():
        verified = [b for b in brands_data["brands"] if b.get("verified")]
        existing_names = {utils.slug(p["brand"] + utils.canonical_name(p["name"])) for p in data["products"]}
        cap = cfg.get("discovery", {}).get("mass_total_cap", 5000)
        cands_all = []

        def _discover_one(b):
            utils.logger.info("发现新品: %s", b["key"])
            return b["key"], discover.discover_brand_products(b, cfg, existing_names=existing_names)

        from concurrent.futures import ThreadPoolExecutor, as_completed as _ac
        with ThreadPoolExecutor(max_workers=16) as ex:
            futs = {ex.submit(_discover_one, b): b for b in verified}
            for fut in _ac(futs):
                key, cands = fut.result()
                if cands:
                    cands_all.extend(cands)
                    utils.logger.info("%s +%d（累计 %d）", key, len(cands), len(cands_all))
                if len(cands_all) >= cap:
                    for f in list(futs):
                        f.cancel()
                    break
        print("候选总数:", len(cands_all))
        data["_mass_candidates"] = cands_all

    def _s4():
        cands_all = data.pop("_mass_candidates", [])
        report = ingest.run_ingest(candidates=cands_all, cfg=cfg)
        print("入库:", report)

    def _s5():
        d, bd, _ = ingest.load_all()
        removed2, _ = ingest.prune_junk(d)
        if removed2:
            classify.classify_all(d["products"])
        utils.save_json(utils.data_path("products.json"), d)
        print("二次清洗移除:", removed2)
        done, reclassified, failed = enrich.enrich_unverified(d, bd, cfg, limit=args.limit or 3000)
        utils.save_json(utils.data_path("products.json"), d)
        ingest.run_ingest(cfg=cfg)
        print("补全：完成 %d，重新分类 %d，失败 %d" % (done, reclassified, failed))

    def _s6():
        import argparse as _ap
        args2 = _ap.Namespace(**vars(args))
        args2.limit = min(args.limit or 150, 150)
        cmd_verify_products(args2)

    def _s7():
        import subprocess
        subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                     "scripts", "audit_data.py")], check=False)

    _step("1/7 全库分类", _s1)
    _step("2/7 核验全部品牌（并发）", _s2)
    _step("3/7 全品牌新品发现（并发）", _s3)
    _step("4/7 入库", _s4)
    _step("5/7 页面/图片/参数补全", _s5)
    _step("5.5/7 数据中文化", lambda: cmd_localize(args))
    _step("6/7 产品数据多源核验（限量）", _s6)
    _step("7/7 数据审计", _s7)

    # 收尾：统一保存 + 状态记录
    utils.save_json(utils.data_path("products.json"), data)
    utils.save_json(utils.data_path("brands.json"), brands_data)
    try:
        ingest.run_ingest(cfg=cfg)
    except Exception:  # noqa: BLE001
        step_errors.append(("final-ingest", traceback.format_exc(limit=3)))
    _json.dump({"mode": "mass", "finished_at": utils.today(), "step_errors": step_errors},
               open(utils.data_path("pipeline_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if step_errors:
        print("全量流程完成，但有 %d 个步骤报错：%s" % (len(step_errors), [e[0] for e in step_errors]))
    else:
        print("全量流程完成，无步骤报错。")



def cmd_full(args):
    cfg = utils.load_config()
    print("== 0/5 清洗垃圾 ==")
    data, brands_data, _ = ingest.load_all()
    removed, _ = ingest.prune_junk(data)
    print("清洗垃圾:", removed)
    print("== 1/5 全库分类 ==")
    n = classify.classify_all(data["products"])
    utils.save_json(utils.data_path("products.json"), data)
    print("分类变更:", n)

    print("== 2/5 品牌核验 ==")
    cmd_verify_brands(args)

    print("== 3/5 产品核验 ==")
    cmd_verify_products(args)

    print("== 4/5 新品发现 ==")
    cmd_discover(args)

    print("== 4.5/5 二次清洗（防垃圾回灌）==")
    data, brands_data, _ = ingest.load_all()
    removed2, _ = ingest.prune_junk(data)
    if removed2:
        classify.classify_all(data["products"])
        utils.save_json(utils.data_path("products.json"), data)
    print("二次清洗移除:", removed2)

    print("== 5/5 官方页信息补全 ==")
    args2 = argparse.Namespace(**vars(args))
    args2.limit = getattr(args, "enrich_limit", 0) or 1500
    cmd_enrich(args2)

    print("== 6/6 数据中文化 ==")
    cmd_localize(args)

    print("全链路完成。")


def main():
    ap = argparse.ArgumentParser(description="外设水库自动化流水线")
    ap.add_argument("mode", choices=["seed", "classify", "verify", "verify-products", "discover", "enrich", "ingest", "full", "mass", "prune", "localize"])
    ap.add_argument("--limit-brands", type=int, default=6)
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--enrich-limit", type=int, default=0)
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
    elif args.mode == "prune":
        cmd_prune(args)
    elif args.mode == "localize":
        cmd_localize(args)
    elif args.mode == "full":
        cmd_full(args)


if __name__ == "__main__":
    main()

# MASS_RUN_V3_MARKER
