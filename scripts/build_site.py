#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鉴史决策 · 网页版案例浏览器生成器
=================================
把 cases/ 下全部案例打包为 site/data.js（window.CASE_DATA），
供 site/index.html 零构建加载（file:// 或任意静态服务器均可）。

零第三方依赖。新增/修改案例后请运行：

    python3 scripts/build_site.py
"""
import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
CASE_DIR = os.path.join(ROOT, "cases")
SITE_DIR = os.path.join(ROOT, "site")

REQUIRED = ["id", "title", "actors", "era", "source", "kernel", "situation",
            "options", "choice", "reasoning", "outcome", "original_text",
            "insight", "risks", "keywords"]


def main():
    cases = []
    for path in sorted(glob.glob(os.path.join(CASE_DIR, "*.json"))):
        with open(path, encoding="utf-8") as f:
            c = json.load(f)
        missing = [k for k in REQUIRED if k not in c]
        if missing:
            print("错误：%s 缺少字段 %s（请先运行 scripts/validate.py）" % (path, missing))
            return 1
        cases.append(c)

    os.makedirs(SITE_DIR, exist_ok=True)
    payload = {
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "count": len(cases),
        "cases": cases,
    }
    out = os.path.join(SITE_DIR, "data.js")
    with open(out, "w", encoding="utf-8") as f:
        f.write("/* 由 scripts/build_site.py 自动生成，请勿手编 */\n")
        f.write("window.CASE_DATA = ")
        f.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        f.write(";\n")

    size = os.path.getsize(out) / 1024.0
    print("已生成 %s：%d 案，%.0f KB" % (os.path.relpath(out, ROOT), len(cases), size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
