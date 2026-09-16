# -*- coding: utf-8 -*-
"""
pipeline/utils.py · 通用工具
HTTP 抓取（UA/超时/重试）、JSON 读写、数字归一化、日志。
"""
import json
import logging
import os
import re
import sys
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger("waishui")


def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def load_config():
    path = os.path.join(ROOT, "config", "pipeline.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def data_path(name):
    return os.path.join(ROOT, "data", name)


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def http_get(url, cfg, timeout=None, headers=None):
    """带重试与 UA 的 GET，返回 (status, text) 或 (None, 错误信息)。"""
    http = cfg.get("http", {})
    ua = http.get("user_agent", "Mozilla/5.0 (compatible; waishui-bot/1.0)")
    timeout = timeout or http.get("timeout", 15)
    retries = http.get("retries", 2)
    delay = http.get("delay_seconds", 1.0)
    hdrs = {"User-Agent": ua}
    if headers:
        hdrs.update(headers)
    last_err = None
    for i in range(retries + 1):
        try:
            r = requests.get(url, headers=hdrs, timeout=timeout)
            if r.status_code == 200:
                r.encoding = r.apparent_encoding or r.encoding
                return r.status_code, r.text
            last_err = "HTTP %s" % r.status_code
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
        if i < retries:
            time.sleep(delay * (i + 1))
    return None, last_err


def slug(s):
    s = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", str(s)).strip("-").lower()
    return s


def extract_number(text):
    """从文本提取第一个数字（含小数）。"""
    m = re.search(r"(\d+(?:\.\d+)?)", str(text))
    return float(m.group(1)) if m else None


def norm_num(text):
    """归一化数值，用于跨来源比对。"""
    n = extract_number(text)
    if n is None:
        return None
    # 常见单位换算：英寸→mm、小时→分钟 不做自动换算，仅比较原始数字
    return n


def values_close(a, b, tol=0.05):
    """两个数字是否视为一致（±5% 容差，处理 50 vs 49.9 等）。"""
    if a is None or b is None:
        return False
    if a == 0 and b == 0:
        return True
    return abs(a - b) / max(abs(a), abs(b), 1e-9) <= tol


def split_kw(text):
    """把文本切为小写词元，用于匹配。"""
    return re.findall(r"[0-9a-z\u4e00-\u9fff]+", str(text).lower())


def contains_any(text, keywords):
    t = str(text).lower()
    return any(k.lower() in t for k in keywords)


def today():
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d")


def utc_now():
    import datetime
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
