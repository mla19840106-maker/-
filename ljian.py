#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""砾鉴 CLI：从《史记》《资治通鉴》取场景内核相似的抉择砾石。"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

GRAIN_COUNSEL = {
    "功高震主": (
        "功劳大到无法被忽视时，封赏与猜忌会同时到达。对方需要的是你的清单，不一定需要你这个活人。",
        "用更多成绩去解释猜忌，等于把威胁写得更大。成绩不是安神药。",
    ),
    "进退时机": (
        "能走的时候不像必须走，必须走的时候往往已经不能走。窗口只在「尚可走」的短暂重叠里。",
        "把恋栈说成负责，把逃说成身退。真正的退，要在结构翻转之前完成剥离。",
    ),
    "择主而事": (
        "择主不是谁更道德，是谁的评价函数用得上你的才能。选错尺子，才能会变成祸。",
        "反复改投会耗尽被相信一次的信用。新局必须交出结果。",
    ),
    "隐忍待机": (
        "隐忍不是性格温和，是把可见的牙收起来。等的是对方离开根据地的空间窗口。",
        "忍而无备，是真病。窗口来了接不住，等于把时间白白送给对方。",
    ),
    "孤注一掷": (
        "孤注只在退则势屈、且一击打在对方结构心脏时才像官渡。",
        "没有「败了如何收」的设计，就是苻坚。人数和声量都不是结构。",
    ),
    "忠义自保": (
        "旧恩只能证明过去。当对方开始设计你，还用旧恩禁止自己谈判，是把道德变成对方的时间。",
        "不是有能力就该背主。要在被需要时把关系写成结构，或把威胁降下来。",
    ),
    "直言犯上": (
        "镜子能在，是因为主怕被蒙甚于怕被顶。进言前先看对方的损失函数。",
        "对只怕羞、不怕暗的人当众直谏，是错误入局。",
    ),
    "名实不符": (
        "把事说得流畅，是危险信号。真懂的人说难、说条件、说不能。",
        "头衔与光环都是书传。败了谁填坑，比他说得多漂亮更重要。",
    ),
    "信息不对称": (
        "信一条关键情报，看三件事：来人是否已无退路、是否打在结构心脏、你是否已无更好的牌。",
        "希望不是证据。来奔者的收益函数若与你不完全重合，先问他不能回去的原因。",
    ),
    "联盟背弃": (
        "连续向盟友索取，短期得地，长期训练出一个以你为公约数的反对同盟。",
        "去年的忠诚不能预测今年的刀向。",
    ),
    "自污求全": (
        "给权力一个关于你的、他能睡着的故事。解释忠心没有用，要减少威胁的落点。",
        "自污只解疑，不解必杀。专业底线不能拿去自污。",
    ),
    "骨肉权争": (
        "情感账户支付不了结构账单时，还在讲亲情的人，会被用结构思考的人结算。",
        "能用分家、股权、程序拆开零和，就不要学宫门。",
    ),
    "和战抉择": (
        "打不打，先数队伍里意志是否同一。新附者的鼓掌，可能是他的窗口。",
        "看起来最强、刚可以不听劝的时刻，往往最危。",
    ),
    "人才任用": (
        "战时问能，治时问行。用错尺子，会滤掉奇谋，或把纸上谈兵放上举国之兵。",
        "老人用道德攻击新人，常是在争夺评价权。",
    ),
    "不可逆局": (
        "「何面目」会否决还存在的船。优化被讲述，还是优化下一局，是两种人生。",
        "用体面关掉选项之前，先确认船是否真的不在。",
    ),
    "道德洁癖": (
        "渔父与屈原争的不是智愚，是目标函数：要在场，还是要白。",
        "既要洁又要权，会把日常意气写成汨罗。",
    ),
    "强弱转化": (
        "弱而整，可以等强而散自己裂开。强而杂，投鞭也断不了流。",
        "示弱若无下一手，就是投降预告。",
    ),
    "危机脱身": (
        "刀俎之席，目标函数只有一项：离开时还活着。",
        "能不入局则不入。逃回去第一件事是堵内部泄漏。",
    ),
}


def load_library():
    kernels = json.loads((DATA / "kernels.json").read_text(encoding="utf-8"))
    cases = json.loads((DATA / "cases-shiji.json").read_text(encoding="utf-8"))
    cases += json.loads((DATA / "cases-tongjian.json").read_text(encoding="utf-8"))
    return kernels, cases


def extract_grains(query: str, kernels: dict, selected=None):
    selected = selected or []
    scores = {}
    for g in kernels.get("grains", []):
        s = 0.0
        for word in g.get("lexicon", []):
            if word and word in query:
                s += max(1.2, len(word) * 0.55)
        if g["id"] in selected:
            s += 4
        if s > 0:
            scores[g["id"]] = s
    boosts = [
        (r"两个.*(团队|老板|offer|东家|局)", "择主而事", 3),
        (r"一个.*一个", "择主而事", 2),
        (r"(要不要走|该不该走|抽身|离职)", "进退时机", 2.5),
        (r"(先发|动手|内斗|接班)", "骨肉权争", 2),
        (r"(得罪|说真话|不敢说)", "直言犯上", 2),
    ]
    for pat, gid, w in boosts:
        if re.search(pat, query):
            scores[gid] = scores.get(gid, 0) + w
    return scores


def _bigrams(s: str):
    t = re.sub(r"\s+", "", s or "")
    return {t[i : i + 2] for i in range(max(0, len(t) - 1))}


def _overlap(a: str, b: str) -> float:
    A, B = _bigrams(a), _bigrams(b)
    if not A or not B:
        return 0.0
    return len(A & B) / max(len(A), len(B))


def score_case(item, grain_scores, query):
    kernel = 0.0
    hits = []
    for g, w in (item.get("grains") or {}).items():
        if g in grain_scores:
            kernel += grain_scores[g] * float(w)
            hits.append((g, w, grain_scores[g]))
    hits.sort(key=lambda x: x[1] * x[2], reverse=True)
    kw = 0.0
    for k in item.get("keywords") or []:
        if k and k in query:
            kw += 1
    for t in item.get("tags") or []:
        if t and t in query:
            kw += 0.8
    blob = "。".join(
        [
            item.get("scene_kernel") or "",
            item.get("situation") or "",
            item.get("life_mapping") or "",
            item.get("subtitle") or "",
            item.get("title") or "",
        ]
    )
    text = _overlap(query, blob)
    kernel_norm = kernel / (1 + kernel)
    kw_norm = kw / (1 + kw)
    score = 0.5 * kernel_norm + 0.28 * kw_norm + 0.22 * min(1.0, text * 8)
    return score, hits, kw, text


def retrieve(query, cases, kernels, selected=None, top_n=3):
    grain_scores = extract_grains(query, kernels, selected)
    ranked = []
    for item in cases:
        score, hits, kw, text = score_case(item, grain_scores, query)
        ranked.append(
            {"case": item, "score": score, "hits": hits, "kw": kw, "text": text}
        )
    ranked.sort(key=lambda x: x["score"], reverse=True)
    grains = sorted(grain_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    return {
        "query": query,
        "grains": grains,
        "matches": ranked[:top_n],
        "weak": not grain_scores,
    }


def render_markdown(result) -> str:
    lines = ["# 砾鉴问策", "", f"> {result['query']}", ""]
    if result["weak"]:
        lines += ["*内核信号弱，下列为字面近似。*", ""]
    if result["grains"]:
        lines += ["## 场景内核", ""]
        for gid, _ in result["grains"]:
            lines.append(f"- **{gid}**")
        lines.append("")
    for i, m in enumerate(result["matches"], 1):
        c = m["case"]
        lines += [
            f"## 第{'一二三四五'[i-1] if i <= 5 else i}砾　{c['title']}",
            "",
            f"**{c['subtitle']}**",
            "",
            f"出处：{c['citation']}　{c.get('year_label','')}",
            "",
            f"**场景内核**　{c['scene_kernel']}",
            "",
            f"**处境**　{c['situation']}",
            "",
            "**当时选项**",
            "",
        ]
        for o in c.get("options") or []:
            lines.append(f"- {o['label']}。利：{o['tempting']} 隐：{o['hidden']}")
        lines += [
            "",
            f"**选择**　{c['choice']['actor']}：{c['choice']['decision']}",
            "",
            "**判断**",
            "",
        ]
        for j in c["choice"].get("judgment") or []:
            lines.append(f"- {j}")
        r = c["result"]
        lines += [
            "",
            f"**结果**　近：{r['near']}",
            f"远：{r['far']}",
            f"对照 {r.get('contrast_figure') or ''}：{r.get('contrast') or ''}",
            "",
            f"**原文**（{c['citation']}）",
            "",
            c["original"],
            "",
            f"**今译**　{c['vernacular']}",
            "",
            f"**规律**　{c['insight']}",
            "",
            f"**映射**　{c['life_mapping']}",
            "",
            f"**此砾不可妄用**　{c['misuse']}",
            "",
        ]
    lines += ["## 鉴语", "", "### 规律启发", ""]
    seen = set()
    for gid, _ in result["grains"]:
        if gid in GRAIN_COUNSEL and gid not in seen:
            seen.add(gid)
            lines.append(f"- {GRAIN_COUNSEL[gid][0]}")
    lines += ["", "### 风险提醒", ""]
    for gid, _ in result["grains"]:
        if gid in GRAIN_COUNSEL:
            lines.append(f"- {GRAIN_COUNSEL[gid][1]}")
    for m in result["matches"]:
        risks = m["case"].get("risks") or []
        if risks:
            lines.append(f"- {risks[0]}")
    lines += [
        "",
        "---",
        "",
        "史为镜，非卜筮。砾石打磨抉择，并不代替抉择。",
        "",
    ]
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description="砾鉴：历史抉择推演")
    p.add_argument("query", nargs="?", help="你的处境与两难")
    p.add_argument("-n", "--top", type=int, default=3, help="取砾数量，默认 3")
    p.add_argument("-g", "--grain", action="append", default=[], help="强制纹理，可重复")
    p.add_argument("--list", action="store_true", help="列出全部砾石")
    p.add_argument("--json", action="store_true", help="输出 JSON")
    args = p.parse_args(argv)
    kernels, cases = load_library()
    if args.list:
        for c in cases:
            print(f"{c['id']}\t{c['work']}\t{c['title']}\t{c['citation']}")
        return 0
    if not args.query:
        p.print_help()
        print("\n例：python3 ljian.py \"我立了大功，老板开始疏远，要不要走\"")
        return 1
    result = retrieve(args.query, cases, kernels, selected=args.grain, top_n=args.top)
    if args.json:
        slim = {
            "query": result["query"],
            "grains": result["grains"],
            "weak": result["weak"],
            "matches": [
                {
                    "id": m["case"]["id"],
                    "title": m["case"]["title"],
                    "score": round(m["score"], 4),
                    "hits": [h[0] for h in m["hits"]],
                    "citation": m["case"]["citation"],
                }
                for m in result["matches"]
            ],
        }
        json.dump(slim, sys.stdout, ensure_ascii=False, indent=2)
        print()
        return 0
    sys.stdout.write(render_markdown(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
