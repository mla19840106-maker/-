#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鉴史决策 · 案例数据校验器
=========================
对 cases/ 下全部案例做结构、引用与一致性校验，零第三方依赖。
CI 中运行（见 .github/workflows/ci.yml）；新增/修改案例后请先本地运行：

    python3 scripts/validate.py

退出码：0 = 全部通过；1 = 存在硬性错误。
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
CASE_DIR = os.path.join(ROOT, "cases")
README = os.path.join(ROOT, "README.md")

KERNELS = [
    "忍辱蓄势", "进退去留", "站队择主", "关键决断", "用人识人", "高风险押注",
    "信息采信", "过度自信", "纳谏倾听", "顾全大局", "变革树敌", "功高震主", "利益与底线",
]

BOOKS = {"史记", "资治通鉴"}
BOOK_BY_PREFIX = {"shiji-": "史记", "tongjian-": "资治通鉴"}

REQUIRED = ["id", "title", "actors", "era", "source", "kernel", "situation",
            "options", "choice", "reasoning", "outcome", "original_text",
            "insight", "risks", "keywords"]

MIN_CHOICE_LEN = 40      # choice 字段最小长度
MIN_SITUATION_LEN = 50   # situation 字段最小长度
MIN_QUOTE_LEN = 6        # 引文最小长度


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def err(self, path, msg):
        self.errors.append("%s: %s" % (os.path.basename(path), msg))

    def warn(self, path, msg):
        self.warnings.append("%s: %s" % (os.path.basename(path), msg))


def is_nonempty_str(v):
    return isinstance(v, str) and v.strip() != ""


def validate_case(path, all_ids, report):
    fname = os.path.basename(path)
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        report.err(path, "JSON 无法解析: %s" % e)
        return None

    # ---- id 与文件名
    if "id" not in d:
        report.err(path, "缺少 id")
        return None
    if d["id"] != fname[:-5]:
        report.err(path, "id(%s) 与文件名(%s)不一致" % (d["id"], fname[:-5]))
    if d["id"] in all_ids:
        report.err(path, "id 重复: %s" % d["id"])
    all_ids.add(d["id"])

    # ---- 必填字段
    for k in REQUIRED:
        if k not in d:
            report.err(path, "缺少必填字段: %s" % k)

    # ---- id 前缀与底本对应
    for prefix, book in BOOK_BY_PREFIX.items():
        if d["id"].startswith(prefix):
            src = d.get("source", {})
            if src.get("book") != book:
                report.err(path, "source.book 应为「%s」(与 id 前缀 %s 对应)" % (book, prefix))
            break
    else:
        report.err(path, "id 必须以 shiji- 或 tongjian- 开头")

    # ---- source
    src = d.get("source", {})
    if src.get("book") not in BOOKS:
        report.err(path, "source.book 必须是 史记/资治通鉴")
    if not is_nonempty_str(src.get("chapter")):
        report.err(path, "source.chapter 缺失或为空")

    # ---- kernel
    ks = d.get("kernel", [])
    if not isinstance(ks, list) or not ks:
        report.err(path, "kernel 必须是非空数组")
    else:
        bad = [k for k in ks if k not in KERNELS]
        if bad:
            report.err(path, "kernel 含未定义内核: %s" % "、".join(bad))
        if ks[0] not in KERNELS:
            report.err(path, "kernel[0]（主内核）必须是 13 类内核之一")

    # ---- 基础文本字段
    if not is_nonempty_str(d.get("title")):
        report.err(path, "title 缺失或为空")
    if not isinstance(d.get("actors"), list) or not d.get("actors"):
        report.err(path, "actors 必须是非空数组")
    if not is_nonempty_str(d.get("era")):
        report.err(path, "era 缺失或为空")
    if len(d.get("situation", "")) < MIN_SITUATION_LEN:
        report.err(path, "situation 过短（<%d 字）" % MIN_SITUATION_LEN)
    if len(d.get("choice", "")) < MIN_CHOICE_LEN:
        report.err(path, "choice 过短（<%d 字）" % MIN_CHOICE_LEN)
    if not is_nonempty_str(d.get("reasoning")):
        report.err(path, "reasoning 缺失或为空")

    # ---- options
    opts = d.get("options", [])
    if not isinstance(opts, list) or len(opts) < 2:
        report.err(path, "options 至少 2 项")
    else:
        for i, o in enumerate(opts):
            if not is_nonempty_str(o.get("option")):
                report.err(path, "options[%d].option 缺失或为空" % i)
            if not is_nonempty_str(o.get("assessment")):
                report.err(path, "options[%d].assessment 缺失或为空" % i)

    # ---- outcome
    oc = d.get("outcome", {})
    if not is_nonempty_str(oc.get("short_term")) or not is_nonempty_str(oc.get("long_term")):
        report.err(path, "outcome.short_term / outcome.long_term 缺失或为空")

    # ---- original_text
    quotes = d.get("original_text", [])
    if not isinstance(quotes, list) or not quotes:
        report.err(path, "original_text 至少 1 条")
    else:
        for i, t in enumerate(quotes):
            if len(t.get("quote", "")) < MIN_QUOTE_LEN:
                report.err(path, "original_text[%d].quote 缺失或过短" % i)
            cit = t.get("citation", "")
            if not is_nonempty_str(cit):
                report.err(path, "original_text[%d].citation 缺失" % i)
            elif src.get("book") and src["book"] not in cit:
                report.warn(path, "original_text[%d].citation 未包含书名「%s」" % (i, src["book"]))

    # ---- insight / risks / keywords / modern_scenarios
    for field, minimum in (("insight", 1), ("risks", 1), ("keywords", 3)):
        v = d.get(field, [])
        if not isinstance(v, list) or len(v) < minimum or not all(is_nonempty_str(x) for x in v):
            report.err(path, "%s 必须是非空字符串数组（≥%d 项）" % (field, minimum))
    if len(d.get("keywords", [])) < 5:
        report.warn(path, "keywords 少于 5 个，检索召回可能不足")
    if not d.get("modern_scenarios"):
        report.warn(path, "缺少 modern_scenarios，影响语境匹配召回")

    # ---- paired_cases（悬空引用检查在主流程做，这里先收集）
    return d


def main():
    report = Report()
    paths = sorted(glob.glob(os.path.join(CASE_DIR, "*.json")))
    if not paths:
        print("错误：cases/ 下没有任何案例文件")
        return 1

    all_ids = set()
    cases = []
    for p in paths:
        d = validate_case(p, all_ids, report)
        if d is not None:
            cases.append(d)

    # ---- paired_cases 悬空引用
    id_set = {c["id"] for c in cases}
    for c in cases:
        for pid in c.get("paired_cases", []):
            if pid not in id_set:
                report.err(c["id"], "paired_cases 悬空引用: %s" % pid)
            if pid == c["id"]:
                report.err(c["id"], "paired_cases 引用了自身")

    # ---- 覆盖统计
    by_book = {}
    by_kernel = {k: {"史记": 0, "资治通鉴": 0} for k in KERNELS}
    for c in cases:
        book = c["source"]["book"]
        by_book[book] = by_book.get(book, 0) + 1
        primary = c["kernel"][0]
        if primary in by_kernel:
            by_kernel[primary][book] += 1

    # ---- README 收录表核对（警告级）
    try:
        with open(README, encoding="utf-8") as f:
            readme = f.read()
        for c in cases:
            short = c["title"].split("：")[0]
            if short not in readme:
                report.warn(c["id"], "README 收录表中未找到「%s」，请同步更新" % short)
        m = "## 收录案例（"
        if m in readme:
            tail = readme[readme.index(m) + len(m):].split("）")[0]
            if str(len(cases)) not in tail:
                report.warn("README", "标题中的案例总数与实际（%d）可能不符" % len(cases))
    except OSError:
        report.warn("README", "无法读取，跳过核对")

    # ---- 输出
    total = len(cases)
    print("案例总数：%d（%s）" % (total, " + ".join("%s %d 案" % (k, v) for k, v in sorted(by_book.items()))))
    print("")
    print("内核覆盖（按主内核统计）：")
    for k in KERNELS:
        s, t = by_kernel[k]["史记"], by_kernel[k]["资治通鉴"]
        flag = "" if (s + t) else "  ← 仍无案例"
        print("  %-6s 史记 %d | 通鉴 %d%s" % (k, s, t, flag))
    print("")
    for w in report.warnings:
        print("警告: %s" % w)
    if report.errors:
        print("")
        for e in report.errors:
            print("错误: %s" % e)
        print("")
        print("校验失败：%d 个错误" % len(report.errors))
        return 1
    print("校验通过 ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
