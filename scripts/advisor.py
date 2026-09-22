#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鉴史决策 · 人生抉择推演引擎
============================
从《史记》《资治通鉴》结构化案例库中检索与用户处境「场景内核」相似的
历史抉择案例，输出：局面拆解 → 选项 → 选择与判断 → 结果 → 原文出处
→ 跨案例规律启发 → 风险提醒。

零第三方依赖，Python 3.7+。

用法:
  python3 scripts/advisor.py "公司被收购，新老板让我表态站队"
  python3 scripts/advisor.py --kernel 进退去留
  python3 scripts/advisor.py --list
  python3 scripts/advisor.py "要不要全部积蓄创业" -o report.md -n 4
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
CASE_DIR = os.path.join(HERE, "..", "cases")

# ---------------------------------------------------------------- 内核词典
# 现代语汇 -> 场景内核 的映射（检索时用于内核判定）
KERNEL_LEXICON = {
    "忍辱蓄势": ["忍", "受辱", "羞辱", "打压", "憋屈", "咽下", "面子", "尊严", "挑衅",
               "欺负", "隐忍", "低头", "委屈", "报复", "冲动", "硬碰"],
    "进退去留": ["离职", "辞职", "退出", "去留", "走还是留", "套现", "退休", "隐退",
               "功成", "上市", "退场", "离开", "撤", "抽身", "淡出", "躺平"],
    "站队择主": ["站队", "跳槽", "offer", "选老板", "择主", "阵营", "跟谁", "投靠",
               "平台", "表态", "选边", "新领导", "旧领导", "派系", "投降", "收购", "并购"],
    "关键决断": ["犹豫", "窗口", "错过", "决断", "摊牌", "先发制人", "下手", "时机",
               "当断", "拖延", "机会", "一击", "抢先", "架空", "夺权"],
    "用人识人": ["招聘", "用人", "识人", "换将", "接班", "候选人", "面试", "背调",
               "提拔", "任命", "托付", "合伙人选", "纸上谈兵", "看人"],
    "高风险押注": ["创业", "押注", "梭哈", "全部积蓄", "重仓", "豪赌", "赌", "投资",
                "身家", "杠杆", "赔率", "回报", "低估", "抄底"],
    "信息采信": ["情报", "爆料", "消息", "信不信", "验证", "内幕", "告密", "线报",
               "传闻", "尽调", "真假", "采信", "内部消息"],
    "过度自信": ["连胜", "膨胀", "盲目", "乐观", "扩张", "都反对", "听不进", "自信",
               "碾压", "稳赢", "轻敌", "上头"],
    "纳谏倾听": ["纳谏", "反对意见", "唱反调", "真话", "坏消息", "直言", "劝",
               "听劝", "谏言", "反馈", "一言堂"],
    "顾全大局": ["同事矛盾", "内斗", "退让", "大局", "让步", "抢功", "叫板", "内耗",
               "和解", "以退为进", "争一口气"],
    "变革树敌": ["改革", "变革", "得罪", "树敌", "动奶酪", "空降", "整顿", "新官上任",
               "靠山", "利益集团", "阻力"],
    "功高震主": ["功高", "震主", "猜忌", "被防", "光芒", "威胁", "老臣", "功劳太大",
               "被忌惮", "鸟尽弓藏", "清算", "边缘化"],
    "利益与底线": ["底线", "造假", "违规", "灰色", "假账", "隐瞒", "同流合污", "把柄",
                "良心", "职业道德", "违法", "越线", "潜规则"],
}


# ---------------------------------------------------------------- 数据加载
def load_cases(case_dir=CASE_DIR):
    cases = []
    if not os.path.isdir(case_dir):
        sys.exit("案例目录不存在: %s" % case_dir)
    for name in sorted(os.listdir(case_dir)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(case_dir, name)
        try:
            with open(path, encoding="utf-8") as f:
                case = json.load(f)
            cases.append(case)
        except (json.JSONDecodeError, OSError) as e:
            print("警告: 跳过无法解析的案例 %s (%s)" % (name, e), file=sys.stderr)
    return cases


# ---------------------------------------------------------------- 检索
def _bigrams(text):
    text = re.sub(r"[\s，。、；：？！「」『』（）,.;:?!()\"'-]", "", text)
    return {text[i:i + 2] for i in range(len(text) - 1)}


def detect_kernels(query):
    """根据内核词典判定查询命中的场景内核，返回 [(内核, 分数)]。"""
    scores = defaultdict(float)
    for kernel, words in KERNEL_LEXICON.items():
        for w in words:
            if w.lower() in query.lower():
                scores[kernel] += 1.0 + 0.1 * len(w)  # 长词更可信
    return sorted(scores.items(), key=lambda kv: -kv[1])


def score_case(case, query, query_kernels):
    """案例综合得分 = 内核匹配 + 关键词命中 + 文本 bigram 重合。"""
    score = 0.0
    hits = []

    kmap = dict(query_kernels)
    for i, k in enumerate(case.get("kernel", [])):
        if k in kmap:
            w = 6.0 if i == 0 else 3.5          # 主内核权重更高
            score += w * min(kmap[k], 3.0)
            hits.append("内核:%s" % k)

    ql = query.lower()
    for kw in case.get("keywords", []):
        if kw.lower() in ql:
            score += 4.0
            hits.append("词:%s" % kw)

    qb = _bigrams(query)
    if qb:
        corpus = case.get("situation", "") + "".join(case.get("modern_scenarios", []))
        overlap = len(qb & _bigrams(corpus))
        score += 0.6 * overlap
        if overlap >= 3:
            hits.append("语境相合")

    return score, hits


def retrieve(cases, query, top_n=3):
    query_kernels = detect_kernels(query)
    scored = []
    for c in cases:
        s, hits = score_case(c, query, query_kernels)
        if s > 0:
            scored.append((s, c, hits))
    scored.sort(key=lambda x: -x[0])

    picked = scored[:top_n]
    # 补充对照案例（结果相反的成对案例价值最高）
    picked_ids = {c["id"] for _, c, _ in picked}
    by_id = {c["id"]: c for c in cases}
    for _, c, _ in list(picked):
        for pid in c.get("paired_cases", []):
            if pid not in picked_ids and pid in by_id and len(picked) < top_n + 1:
                picked.append((0.1, by_id[pid], ["对照案例:与「%s」成对" % c["title"].split("：")[0]]))
                picked_ids.add(pid)
    return query_kernels, picked


# ---------------------------------------------------------------- 报告渲染
def render_case(case, hits, idx):
    src = case["source"]
    lines = []
    lines.append("### 镜鉴 %d ｜ %s" % (idx, case["title"]))
    lines.append("")
    lines.append("- **人物**：%s　**时代**：%s　**出处**：《%s·%s》"
                 % ("、".join(case["actors"]), case["era"], src["book"], src["chapter"]))
    lines.append("- **场景内核**：%s　（匹配依据：%s）"
                 % (" / ".join(case["kernel"]), "，".join(hits) if hits else "—"))
    lines.append("")
    lines.append("**① 当时局面**")
    lines.append("")
    lines.append(case["situation"])
    lines.append("")
    lines.append("**② 当时真实拥有的选项**")
    lines.append("")
    for opt in case["options"]:
        lines.append("- **%s** — %s" % (opt["option"], opt["assessment"]))
    lines.append("")
    lines.append("**③ 实际选择**")
    lines.append("")
    lines.append(case["choice"])
    lines.append("")
    lines.append("**④ 判断依据**")
    lines.append("")
    lines.append(case["reasoning"])
    lines.append("")
    lines.append("**⑤ 结果**")
    lines.append("")
    lines.append("- 短期：%s" % case["outcome"]["short_term"])
    lines.append("- 终局：%s" % case["outcome"]["long_term"])
    lines.append("")
    lines.append("**⑥ 原文出处**")
    lines.append("")
    for t in case["original_text"]:
        lines.append("> %s" % t["quote"])
        lines.append(">")
        lines.append("> ——《%s》" % t["citation"])
        lines.append("")
    return "\n".join(lines)


def render_report(query, query_kernels, picked):
    lines = []
    lines.append("# 抉择推演报告")
    lines.append("")
    lines.append("**你的处境**：%s" % query)
    lines.append("")
    lines.append("## 一、场景内核判定")
    lines.append("")
    if query_kernels:
        for k, s in query_kernels[:3]:
            lines.append("- **%s**（贴合度 %.1f）" % (k, s))
        lines.append("")
        lines.append("> 内核判定基于决策结构的同构性（筹码、张力、可逆性），而非表面情节相似。")
    else:
        lines.append("未能从描述中判定明确内核，以下按全文相关度检索。"
                     "建议补充：这个决定可逆吗？时间窗口多长？你最怕失去什么？")
    lines.append("")
    lines.append("## 二、历史镜鉴")
    lines.append("")
    if not picked:
        lines.append("案例库中暂无足够贴合的案例。请换一种描述，或运行 `--list` 浏览全部内核。")
        return "\n".join(lines)

    for i, (score, case, hits) in enumerate(picked, 1):
        lines.append(render_case(case, hits, i))
        lines.append("---")
        lines.append("")

    lines.append("## 三、规律启发（跨案例）")
    lines.append("")
    seen = set()
    for _, case, _ in picked:
        for ins in case["insight"]:
            if ins not in seen:
                seen.add(ins)
                lines.append("- %s ｜ *来自：%s*" % (ins, case["title"].split("：")[0]))
    lines.append("")
    lines.append("## 四、风险提醒")
    lines.append("")
    seen = set()
    for _, case, _ in picked:
        for r in case["risks"]:
            if r not in seen:
                seen.add(r)
                lines.append("- %s" % r)
    lines.append("")
    lines.append("### 通用边界声明")
    lines.append("")
    lines.append("- 历史案例是**参照系而非答案**：古今的制度环境、退出机制、风险结构差异巨大。")
    lines.append("- 史书详载的多为极端样本，存在**幸存者偏差**；同策略而无闻者不见于史。")
    lines.append("- 涉及法律、重大财务、健康的决定，请咨询专业人士。最终判断权在你。")
    return "\n".join(lines)


# ---------------------------------------------------------------- CLI
def cmd_list(cases):
    by_kernel = defaultdict(list)
    for c in cases:
        by_kernel[c["kernel"][0]].append(c)
    print("案例库共 %d 案：\n" % len(cases))
    for kernel in KERNEL_LEXICON:
        items = by_kernel.get(kernel, [])
        if not items:
            continue
        print("■ %s" % kernel)
        for c in items:
            print("   - [%s] %s（%s，《%s·%s》）"
                  % (c["id"], c["title"], "、".join(c["actors"][:2]),
                     c["source"]["book"], c["source"]["chapter"]))
        print()


def cmd_kernel(cases, kernel):
    hits = [c for c in cases if kernel in c.get("kernel", [])]
    if not hits:
        sys.exit("没有内核为「%s」的案例。可用内核：%s" % (kernel, "、".join(KERNEL_LEXICON)))
    picked = [(1.0, c, ["内核:%s" % kernel]) for c in hits]
    print(render_report("浏览内核「%s」下的全部案例" % kernel, [(kernel, 1.0)], picked))


def main():
    ap = argparse.ArgumentParser(description="鉴史决策 · 人生抉择推演引擎")
    ap.add_argument("query", nargs="?", help="描述你的处境/抉择")
    ap.add_argument("--kernel", help="按场景内核浏览案例")
    ap.add_argument("--list", action="store_true", help="列出全部案例")
    ap.add_argument("-n", "--top", type=int, default=3, help="返回案例数（默认 3）")
    ap.add_argument("-o", "--output", help="将报告写入 markdown 文件")
    args = ap.parse_args()

    cases = load_cases()

    if args.list:
        cmd_list(cases)
        return
    if args.kernel:
        cmd_kernel(cases, args.kernel)
        return
    if not args.query:
        ap.print_help()
        return

    query_kernels, picked = retrieve(cases, args.query, top_n=args.top)
    report = render_report(args.query, query_kernels, picked)
    if args.output:
        out_dir = os.path.dirname(os.path.abspath(args.output))
        os.makedirs(out_dir, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print("报告已写入 %s" % args.output)
    else:
        print(report)


if __name__ == "__main__":
    main()
