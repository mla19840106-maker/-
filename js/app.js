(function () {
  const $ = (id) => document.getElementById(id);

  const SAMPLES = [
    "我在公司立过大功，老板最近客气却疏远，期权还没兑现，要不要走？",
    "两个团队都在抢我，一个资源多但价值观不对，一个志同道合却很弱。",
    "我掌握关键事实，说出来会得罪权位，不说会害了集体。",
    "机会只有一次，信息不完整，失败可能没有退路。",
    "旧东家待我有恩，新局面明显更有前途，改投算不算背义？",
    "合伙人开始防我，要不要先发制人？",
    "我把内部管得又稳又得人心，老板在前线却反复「关心」我在干什么。",
    "账面上人多钱多，有人鼓动一次性拿下对手，老人劝我先消化。"
  ];

  const state = {
    kernels: null,
    cases: [],
    selected: [],
    result: null,
    activeId: null
  };

  function hanNum(i) {
    return ["一", "二", "三", "四", "五"][i] || String(i + 1);
  }

  function setStatus(t) {
    $("status").textContent = t || "";
  }

  function renderChips() {
    const box = $("chips");
    box.innerHTML = "";
    SAMPLES.forEach((s) => {
      const b = document.createElement("button");
      b.className = "chip";
      b.type = "button";
      b.textContent = s.length > 22 ? s.slice(0, 22) + "…" : s;
      b.title = s;
      b.addEventListener("click", () => {
        $("q").value = s;
        $("q").focus();
      });
      box.appendChild(b);
    });
  }

  function renderGrainPick() {
    const box = $("grains");
    box.innerHTML = "";
    state.kernels.grains.forEach((g) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "grain" + (state.selected.indexOf(g.id) >= 0 ? " on" : "");
      b.textContent = g.id;
      b.title = g.desc;
      b.addEventListener("click", () => {
        const i = state.selected.indexOf(g.id);
        if (i >= 0) state.selected.splice(i, 1);
        else state.selected.push(g.id);
        renderGrainPick();
      });
      box.appendChild(b);
    });
  }

  function ask() {
    const q = $("q").value.trim();
    if (!q) {
      setStatus("先把处境写在笺上。");
      $("q").focus();
      return;
    }
    setStatus("按纹理取砾…");
    const result = LjianEngine.retrieve(q, state.cases, state.kernels, {
      selected: state.selected,
      topN: 3
    });
    state.result = result;
    state.activeId = result.matches[0] ? result.matches[0].case.id : null;
    renderResult();
    $("result").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function renderResult() {
    const r = state.result;
    $("result").classList.remove("hidden");
    if (!r.matches.length) {
      setStatus("库中暂无足够相似的砾石。可改写处境，或点选上方纹理。");
      $("kernels").innerHTML = "";
      $("pebbles").innerHTML = "";
      $("detail").classList.remove("show");
      $("counsel").innerHTML = "";
      return;
    }
    setStatus(r.weak ? "内核不明，已按字面近似检索。点选纹理会更准。" : "已按场景内核取三砾。点石可读判断、结果与原文。");

    $("weak").classList.toggle("hidden", !r.weak);

    const kbox = $("kernels");
    kbox.innerHTML = "";
    (r.grains.length ? r.grains : []).forEach((g) => {
      const d = document.createElement("div");
      d.className = "kernel-stone";
      const meta = state.kernels.grains.find((x) => x.id === g.id);
      d.innerHTML = "<b>" + g.id + "</b><span>" + (meta ? meta.desc : "") + "</span>";
      kbox.appendChild(d);
    });

    const pbox = $("pebbles");
    pbox.innerHTML = "";
    r.matches.forEach((m, i) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "pebble";
      b.innerHTML =
        '<span class="n">第' + hanNum(i) + "砾</span>" +
        '<span class="score">纹理 ' + Math.round(m.score * 100) + "</span>" +
        '<div class="inner">' +
        "<h3>" + m.case.title + "</h3>" +
        '<p class="sub2">' + m.case.subtitle + "</p>" +
        '<div class="cite">' + m.case.citation + " · " + m.case.year_label + "</div>" +
        '<p class="kernel">' + m.case.scene_kernel + "</p>" +
        '<div class="hits">' +
        m.hits.slice(0, 4).map((h) => '<span class="hit">' + h.id + "</span>").join("") +
        "</div></div>";
      b.addEventListener("click", () => {
        state.activeId = m.case.id;
        renderDetail();
        $("detail").scrollIntoView({ behavior: "smooth", block: "start" });
      });
      pbox.appendChild(b);
    });

    renderDetail();
    renderCounsel();
  }

  function renderDetail() {
    const r = state.result;
    const m = r.matches.find((x) => x.case.id === state.activeId) || r.matches[0];
    if (!m) return;
    const c = m.case;
    const el = $("detail");
    el.classList.add("show");
    const opts = (c.options || [])
      .map((o) => "<li><b>" + o.label + "</b>　利：" + o.tempting + "　隐：" + o.hidden + "</li>")
      .join("");
    const judges = (c.choice.judgment || []).map((j) => "<li>" + j + "</li>").join("");
    el.innerHTML =
      '<article class="sheet">' +
      '<div class="eyebrow">' + c.work + " · " + c.chapter + "</div>" +
      "<h2>" + c.title + "</h2>" +
      '<p class="sub2" style="color:var(--gold);margin:0 0 8px">' + c.subtitle + "</p>" +
      '<div class="cite" style="color:var(--muted)">' + c.citation + "　" + c.era + "　" + (c.figures || []).join("、") + "</div>" +
      '<div class="grid-2">' +
      '<div class="block"><h3>处境</h3><p>' + c.situation + "</p></div>" +
      '<div class="block"><h3>场景内核</h3><p>' + c.scene_kernel + "</p></div>" +
      '<div class="block"><h3>当时可见的选项</h3><ul>' + opts + "</ul></div>" +
      '<div class="block"><h3>选择与判断</h3><p><b>' + c.choice.actor + "</b>：" + c.choice.decision + "</p><ol>" + judges + "</ol></div>" +
      '<div class="block"><h3>结果</h3><p>近：' + c.result.near + "</p><p>远：" + c.result.far + "</p><p>对照 " + (c.result.contrast_figure || "") + "：" + c.result.contrast + "</p></div>" +
      '<div class="block"><h3>规律</h3><p>' + c.insight + "</p></div>" +
      "</div>" +
      '<div class="original"><div class="from">原文 · ' + c.citation + "</div>" + c.original +
      '<div class="vern">' + c.vernacular + "</div></div>" +
      '<div class="grid-2" style="margin-top:18px">' +
      '<div class="block map"><h3>映射到当下</h3><p>' + c.life_mapping + "</p></div>" +
      '<div class="block warn"><h3>此砾不可妄用</h3><p>' + c.misuse + "</p></div>" +
      "</div></article>";
  }

  function renderCounsel() {
    const c = LjianEngine.counsel(state.result);
    const box = $("counsel");
    box.innerHTML =
      '<div class="counsel-box">' +
      "<h2>鉴语</h2>" +
      "<h3>规律启发</h3>" +
      "<ul>" + c.insights.map((x) => "<li>" + x.text + "</li>").join("") + "</ul>" +
      "<h3>风险提醒</h3>" +
      "<ul>" + c.risks.map((x) => "<li>" + x.text + "</li>").join("") + "</ul>" +
      "</div>";
  }

  async function boot() {
    renderChips();
    setStatus("载入《史记》《资治通鉴》砾石库…");
    try {
      const [kernels, shiji, tongjian] = await Promise.all([
        fetch("data/kernels.json").then((r) => r.json()),
        fetch("data/cases-shiji.json").then((r) => r.json()),
        fetch("data/cases-tongjian.json").then((r) => r.json())
      ]);
      state.kernels = kernels;
      state.cases = [].concat(shiji, tongjian);
      renderGrainPick();
      setStatus("库中 " + state.cases.length + " 粒砾石。写下处境，或点一条现成的问。");
    } catch (err) {
      setStatus("数据未载入。请用本地服务器打开本页，例如 python3 -m http.server 8080");
      console.error(err);
    }

    $("go").addEventListener("click", ask);
    $("q").addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") ask();
    });
  }

  boot();
})();
