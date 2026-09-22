#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import ljian  # noqa: E402


def test_json_loads():
    kernels, cases = ljian.load_library()
    assert kernels["grains"]
    assert len(cases) >= 20
    required = {
        "id",
        "title",
        "subtitle",
        "work",
        "chapter",
        "citation",
        "grains",
        "scene_kernel",
        "situation",
        "options",
        "choice",
        "result",
        "original",
        "vernacular",
        "insight",
        "risks",
        "misuse",
        "life_mapping",
    }
    for c in cases:
        missing = required - set(c)
        assert not missing, (c.get("id"), missing)
        assert c["original"].strip()
        assert c["citation"].strip()
        assert len(c["options"]) >= 2
        json.dumps(c, ensure_ascii=False)


def _ids(query, n=3):
    kernels, cases = ljian.load_library()
    r = ljian.retrieve(query, cases, kernels, top_n=n)
    return [m["case"]["id"] for m in r["matches"]]


def test_功成身退_hits_fanli_or_zhangliang():
    ids = _ids("我在公司立过大功，老板最近客气却疏远，期权还没兑现，要不要走？")
    assert any(x in ids for x in ("fanli-wuhu", "zhangliang-chisong", "hanxin-kuitong", "xiaohe-ziwu", "guoziyi-kaimen")), ids


def test_择主():
    ids = _ids("两个团队都在抢我，一个资源多但价值观不对，一个志同道合却很弱。")
    assert any(x in ids for x in ("chenping-guihan", "guanzhong-baoshu", "hanxin-kuitong")), ids


def test_直谏():
    ids = _ids("我掌握关键事实，说出来会得罪权位，不说会害了集体。")
    assert any(x in ids for x in ("weizheng-jianting", "quyuan-yufu")), ids


def test_孤注():
    ids = _ids("账面上人多钱多，有人鼓动一次性拿下对手，老人劝我先消化，失败可能没有退路。")
    assert any(x in ids for x in ("fuqian-feishui", "guandu-xuyou", "zhaokuo-changping")), ids


if __name__ == "__main__":
    tests = [
        test_json_loads,
        test_功成身退_hits_fanli_or_zhangliang,
        test_择主,
        test_直谏,
        test_孤注,
    ]
    for fn in tests:
        fn()
        print("ok", fn.__name__)
    print("all passed")
