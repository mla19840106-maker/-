/**
 * 砾鉴检索引擎
 * 不比故事外形，只比抉择纹理。
 */
(function (root) {
  const GRAIN_COUNSEL = {
    功高震主: {
      insight: "功劳大到无法被忽视时，封赏与猜忌会同时到达。对方需要的是你的清单，不一定需要你这个活人。",
      risk: "用更多成绩去解释猜忌，等于把威胁写得更大。成绩不是安神药。"
    },
    进退时机: {
      insight: "能走的时候不像必须走，必须走的时候往往已经不能走。窗口只在「尚可走」的短暂重叠里。",
      risk: "把恋栈说成负责，把逃说成身退。真正的退，要在结构翻转之前完成剥离。"
    },
    择主而事: {
      insight: "择主不是谁更道德，是谁的评价函数用得上你的才能。选错尺子，才能会变成祸。",
      risk: "反复改投会耗尽被相信一次的信用。新局必须交出结果，战时被用，不保证治时被信。"
    },
    隐忍待机: {
      insight: "隐忍不是性格温和，是把可见的牙收起来。等的是对方离开根据地的空间窗口，不是自己心情平复。",
      risk: "忍而无备，是真病。窗口来了接不住，等于把时间白白送给对方。"
    },
    孤注一掷: {
      insight: "孤注只在退则势屈、且一击打在对方结构心脏时才像官渡。其余的孤注，是把焦虑一次性花掉。",
      risk: "没有「败了如何收」的设计，就是苻坚。人数、声量、自我感觉都不是结构。"
    },
    忠义自保: {
      insight: "旧恩只能证明过去。当对方开始设计你，还用旧恩禁止自己谈判，是把道德变成对方的时间。",
      risk: "不是有能力就该背主。要在被需要时把关系写成结构，或把威胁降下来——默认既不是叛，也不是殉。"
    },
    直言犯上: {
      insight: "镜子能在，是因为主怕被蒙甚于怕被顶。进言前先看对方的损失函数，再决定当不当魏征。",
      risk: "对只怕羞、不怕暗的人当众直谏，是错误入局。没有第二信息源的勇敢，是殉。"
    },
    名实不符: {
      insight: "把事说得流畅，是危险信号。真懂的人说难、说条件、说不能。相持中途用「好听」换将，是用焦虑破坏正确的慢。",
      risk: "头衔、二代、名校、前东家光环都是书传。败了谁填坑，比他说得多漂亮更重要。"
    },
    信息不对称: {
      insight: "信一条关键情报，看三件事：来人是否已无退路、是否打在结构心脏、你是否已无更好的牌。",
      risk: "希望不是证据。来奔者的收益函数若与你不完全重合，出迎之前先问他不能回去的原因。"
    },
    联盟背弃: {
      insight: "连续向盟友索取，短期得地，长期训练出一个以你为公约数的反对同盟。强不是法律。",
      risk: "去年的忠诚不能预测今年的刀向。把对手逼到死地，也常把盟友逼到必须选边。"
    },
    自污求全: {
      insight: "给权力一个关于你的、他能睡着的故事：欲望停在田宅，到不了龙椅。解释忠心没有用，要减少威胁的落点。",
      risk: "自污只解疑，不解必杀。假隐真干会被看穿。专业底线不能拿去自污。"
    },
    骨肉权争: {
      insight: "情感账户支付不了结构账单时，还在讲亲情的人，会被用结构思考的人结算。拖延只是把先手交给对方。",
      risk: "先发不可逆。没有迫急证据的「先下手」是开启地狱。能用分家、股权、程序拆开零和，就不要学宫门。"
    },
    和战抉择: {
      insight: "打不打，先数队伍里意志是否同一，再数鞭子有多少。新附者的鼓掌，可能是他的窗口。",
      risk: "空国而战是把所有裂缝带到前线去裂。看起来最强、刚可以不听劝的时刻，往往最危。"
    },
    人才任用: {
      insight: "战时问能，治时问行。用错尺子，会把奇谋之士滤掉，或把纸上谈兵的人放上举国之兵。",
      risk: "老人用道德攻击新人，常是在争夺评价权。主事者被带节奏，等于把将将之权交出去。"
    },
    不可逆局: {
      insight: "「何面目」会否决还存在的船。优化被讲述，还是优化下一局，是两种人生。",
      risk: "用体面关掉选项之前，先确认船是否真的不在。大多数现代情境里，亭长还在等。"
    },
    道德洁癖: {
      insight: "渔父与屈原争的不是智愚，是目标函数：要在场，还是要白。两者都贵，混着要最贵。",
      risk: "清高一旦成为身份，选择集会收窄。既要洁又要权，会把日常意气写成汨罗。"
    },
    强弱转化: {
      insight: "弱而整，可以等强而散自己裂开。强而杂，投鞭也断不了流。",
      risk: "示弱若无下一手，就是投降预告。由弱转强需要时间，时间要买得起。"
    },
    危机脱身: {
      insight: "刀俎之席，目标函数只有一项：离开时还活着。礼仪、面子、解释权都可以丢。",
      risk: "能不入局则不入。逃回去第一件事是堵内部泄漏，不是解释自己为什么受辱。"
    }
  };

  function bigrams(s) {
    const t = String(s || "").replace(/\s+/g, "");
    const out = [];
    for (let i = 0; i < t.length - 1; i++) out.push(t.slice(i, i + 2));
    return out;
  }

  function overlap(a, b) {
    const A = new Set(bigrams(a));
    const B = new Set(bigrams(b));
    if (!A.size || !B.size) return 0;
    let n = 0;
    A.forEach((x) => {
      if (B.has(x)) n += 1;
    });
    return n / Math.max(A.size, B.size);
  }

  function extractGrains(query, kernels, selected) {
    const q = query || "";
    const scores = {};
    (kernels.grains || []).forEach((g) => {
      let s = 0;
      (g.lexicon || []).forEach((word) => {
        if (word && q.includes(word)) s += Math.max(1.2, word.length * 0.55);
      });
      if (selected && selected.indexOf(g.id) >= 0) s += 4;
      if (s > 0) scores[g.id] = s;
    });
    const boosts = [
      [/两个.*(团队|老板|offer|东家|局)/, "择主而事", 3],
      [/一个.*一个/, "择主而事", 2],
      [/(要不要走|该不该走|抽身|离职)/, "进退时机", 2.5],
      [/(先发|动手|内斗|接班)/, "骨肉权争", 2],
      [/(得罪|说真话|不敢说)/, "直言犯上", 2]
    ];
    boosts.forEach((row) => {
      if (row[0].test(q)) scores[row[1]] = (scores[row[1]] || 0) + row[2];
    });
    return scores;
  }

  function scoreCase(item, grainScores, query) {
    let kernel = 0;
    const hits = [];
    const grains = item.grains || {};
    Object.keys(grains).forEach((g) => {
      const w = grains[g];
      if (grainScores[g]) {
        kernel += grainScores[g] * w;
        hits.push({ id: g, weight: w, user: grainScores[g] });
      }
    });
    hits.sort((a, b) => b.weight * b.user - a.weight * a.user);

    let kw = 0;
    (item.keywords || []).forEach((k) => {
      if (k && query.includes(k)) kw += 1;
    });
    (item.tags || []).forEach((t) => {
      if (t && query.includes(t)) kw += 0.8;
    });

    const blob = [
      item.scene_kernel,
      item.situation,
      item.life_mapping,
      item.subtitle,
      item.title
    ].join("。");
    const text = overlap(query, blob);

    const kernelNorm = kernel / (1 + kernel);
    const kwNorm = kw / (1 + kw);
    const score = 0.5 * kernelNorm + 0.28 * kwNorm + 0.22 * Math.min(1, text * 8);

    return { score, hits, kw, text };
  }

  function retrieve(query, cases, kernels, opts) {
    opts = opts || {};
    const selected = opts.selected || [];
    const topN = opts.topN || 3;
    const q = String(query || "").trim();
    const grainScores = extractGrains(q, kernels, selected);
    const grainCount = Object.keys(grainScores).length;

    const ranked = cases
      .map((item) => {
        const r = scoreCase(item, grainScores, q);
        return { case: item, ...r };
      })
      .filter((x) => x.score > 0.02 || grainCount === 0)
      .sort((a, b) => b.score - a.score);

    const top = ranked.slice(0, topN);

    const grainRank = Object.keys(grainScores)
      .map((id) => ({ id, score: grainScores[id] }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 5);

    return {
      query: q,
      grains: grainRank,
      grainScores,
      matches: top,
      weak: grainCount === 0
    };
  }

  function counsel(result) {
    const seen = [];
    const insights = [];
    const risks = [];
    (result.grains || []).forEach((g) => {
      const c = GRAIN_COUNSEL[g.id];
      if (c && seen.indexOf(g.id) < 0) {
        seen.push(g.id);
        insights.push({ grain: g.id, text: c.insight });
        risks.push({ grain: g.id, text: c.risk });
      }
    });
    (result.matches || []).forEach((m) => {
      if (m.case && m.case.risks) {
        m.case.risks.slice(0, 1).forEach((t) => {
          if (risks.length < 6) risks.push({ grain: m.case.title, text: t });
        });
      }
    });
    return { insights: insights.slice(0, 4), risks: risks.slice(0, 5) };
  }

  root.LjianEngine = {
    GRAIN_COUNSEL,
    extractGrains,
    retrieve,
    counsel
  };
})(typeof window !== "undefined" ? window : globalThis);
