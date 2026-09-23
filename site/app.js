(function () {
  'use strict';

  var KERNELS = ['忍辱蓄势', '进退去留', '站队择主', '关键决断', '用人识人', '高风险押注',
    '信息采信', '过度自信', '纳谏倾听', '顾全大局', '变革树敌', '功高震主', '利益与底线'];
  var CASES = CASE_DATA.cases;

  function norm(s) { return (s || '').toLowerCase().replace(/\s+/g, ''); }
  function esc(s) {
    return (s || '').replace(/[&<>"]/g, function (ch) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch];
    });
  }
  function byId(id) {
    for (var i = 0; i < CASES.length; i++) if (CASES[i].id === id) return CASES[i];
    return null;
  }

  CASES.forEach(function (c) {
    c._h = norm([c.title, c.actors.join(' '), c.era, c.source.book, c.source.chapter,
      c.kernel.join(' '), c.situation, (c.keywords || []).join(' '),
      (c.modern_scenarios || []).join(' ')].join(' '));
    c._tk = norm(c.title + c.actors.join('') + (c.keywords || []).join(''));
  });

  var state = { q: '', kernel: '', book: '', id: '' };

  /* ---------------- URL hash（可分享链接） ---------------- */
  function fromHash() {
    var h = location.hash.replace(/^#/, '');
    var m = {};
    h.split('&').forEach(function (kv) {
      if (!kv) return;
      var p = kv.split('=');
      m[p[0]] = decodeURIComponent(p[1] || '');
    });
    state.q = m.q || ''; state.kernel = m.kernel || '';
    state.book = m.book || ''; state.id = m.id || '';
  }
  function toHash() {
    var parts = [];
    if (state.q) parts.push('q=' + encodeURIComponent(state.q));
    if (state.kernel) parts.push('kernel=' + encodeURIComponent(state.kernel));
    if (state.book) parts.push('book=' + encodeURIComponent(state.book));
    if (state.id) parts.push('id=' + encodeURIComponent(state.id));
    var h = parts.join('&');
    if (('#' + h) !== location.hash) history.replaceState(null, '', h ? '#' + h : '#');
  }

  /* ---------------- 过滤与排序 ---------------- */
  function filtered() {
    var terms = state.q ? state.q.toLowerCase().split(/\s+/).map(norm).filter(Boolean) : [];
    var out = CASES.filter(function (c) {
      if (state.book && c.source.book !== state.book) return false;
      if (state.kernel && c.kernel.indexOf(state.kernel) < 0) return false;
      for (var i = 0; i < terms.length; i++) if (c._h.indexOf(terms[i]) < 0) return false;
      return true;
    });
    if (terms.length) {
      var qn = norm(state.q);
      out.sort(function (a, b) {
        var ra = a._tk.indexOf(qn) >= 0 ? 0 : 1;
        var rb = b._tk.indexOf(qn) >= 0 ? 0 : 1;
        return ra - rb;
      });
    }
    return out;
  }

  /* ---------------- 渲染 ---------------- */
  function renderStats() {
    document.getElementById('stats').textContent =
      CASE_DATA.count + ' 案 · 13 类场景内核 · 2 部底本 · 数据生成于 ' + CASE_DATA.generated;
  }

  function renderChips() {
    var counts = {};
    CASES.forEach(function (c) {
      (c.kernel || []).forEach(function (k) { counts[k] = (counts[k] || 0) + 1; });
    });
    var el = document.getElementById('kernels');
    el.innerHTML = '';
    KERNELS.forEach(function (k) {
      var b = document.createElement('button');
      b.className = 'chip' + (state.kernel === k ? ' on' : '');
      b.innerHTML = esc(k) + ' <span class="n">' + (counts[k] || 0) + '</span>';
      b.onclick = function () { state.kernel = (state.kernel === k ? '' : k); toHash(); render(); };
      el.appendChild(b);
    });
  }

  function renderBookSeg() {
    var btns = document.querySelectorAll('#bookSeg button');
    for (var i = 0; i < btns.length; i++) {
      btns[i].classList.toggle('on', btns[i].getAttribute('data-book') === state.book);
    }
  }

  function renderCards() {
    var list = filtered();
    document.getElementById('count').textContent =
      list.length ? '共 ' + list.length + ' 案' : '';
    var grid = document.getElementById('grid');
    if (!list.length) {
      grid.innerHTML = '<div class="empty">没有匹配的案例——换个说法，或清除筛选试试。</div>';
      return;
    }
    grid.innerHTML = list.map(function (c) {
      var sit = c.situation.length > 92 ? c.situation.slice(0, 92) + '……' : c.situation;
      return '<article class="card" data-id="' + esc(c.id) + '">' +
        '<div class="head"><span class="book ' + (c.source.book === '史记' ? 's' : 't') + '">' +
        c.source.book + '</span><span class="era">' + esc(c.era) + '</span></div>' +
        '<h3>' + esc(c.title) + '</h3>' +
        '<p class="meta">' + esc(c.actors.join(' / ')) + ' ·《' + esc(c.source.book) + '·' +
        esc(c.source.chapter) + '》</p>' +
        '<p class="sit">' + esc(sit) + '</p>' +
        '<div class="tags">' + c.kernel.map(function (k) {
          return '<span>' + esc(k) + '</span>';
        }).join('') + '</div></article>';
    }).join('');
  }

  /* ---------------- 详情浮层 ---------------- */
  function section(t, body) { return '<section><h4>' + t + '</h4>' + body + '</section>'; }

  function caseMd(c) {
    var L = [];
    L.push('### ' + c.title + '（' + c.actors.join('、') + '，《' + c.source.book + '·' + c.source.chapter + '》）');
    L.push('场景内核：' + c.kernel.join(' / '));
    L.push('**① 当时局面**\n' + c.situation);
    L.push('**② 当时真实拥有的选项**\n' + c.options.map(function (o) {
      return '- ' + o.option + ' — ' + o.assessment; }).join('\n'));
    L.push('**③ 实际选择**\n' + c.choice);
    L.push('**④ 判断依据**\n' + c.reasoning);
    L.push('**⑤ 结果**\n- 短期：' + c.outcome.short_term + '\n- 终局：' + c.outcome.long_term);
    L.push('**⑥ 原文出处**\n' + c.original_text.map(function (t) {
      return '> ' + t.quote + '\n>\n> ——《' + t.citation + '》'; }).join('\n\n'));
    L.push('**⑦ 规律启发**\n' + c.insight.map(function (x) { return '- ' + x; }).join('\n'));
    L.push('**⑧ 风险提醒**\n' + c.risks.map(function (x) { return '- ' + x; }).join('\n'));
    if ((c.modern_scenarios || []).length) L.push('**现代对应场景**：' + c.modern_scenarios.join('；'));
    return L.join('\n\n');
  }

  function fallbackCopy(text) {
    var ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); } catch (e) {}
    document.body.removeChild(ta);
  }

  function openModal(id) {
    var c = byId(id);
    if (!c) return;
    var quotes = c.original_text.map(function (t) {
      return '<blockquote>' + esc(t.quote) + '<footer>——《' + esc(t.citation) + '》</footer></blockquote>';
    }).join('');
    var paired = (c.paired_cases || []).map(function (pid) {
      var pc = byId(pid);
      return pc ? '<button class="pair" data-id="' + esc(pid) + '">' +
        esc(pc.title.split('：')[0]) + '</button>' : '';
    }).join('');

    document.getElementById('modalBody').innerHTML =
      '<div class="mhead">' +
      '<span class="book ' + (c.source.book === '史记' ? 's' : 't') + '">' + c.source.book + '</span>' +
      '<h2>' + esc(c.title) + '</h2>' +
      '<p class="meta">' + esc(c.actors.join(' / ')) + ' · ' + esc(c.era) +
      ' ·《' + esc(c.source.book) + '·' + esc(c.source.chapter) + '》</p>' +
      '<p class="meta2">场景内核：' + esc(c.kernel.join(' / ')) + '</p>' +
      '<button id="copyMd" class="ghost">复制为 Markdown</button></div>' +
      section('① 当时局面', '<p>' + esc(c.situation) + '</p>') +
      section('② 当时真实拥有的选项', '<ul class="opts">' + c.options.map(function (o) {
        return '<li><b>' + esc(o.option) + '</b><span>' + esc(o.assessment) + '</span></li>';
      }).join('') + '</ul>') +
      section('③ 实际选择', '<p>' + esc(c.choice) + '</p>') +
      section('④ 判断依据', '<p>' + esc(c.reasoning) + '</p>') +
      section('⑤ 结果', '<p><b>短期</b>：' + esc(c.outcome.short_term) + '</p>' +
        '<p><b>终局</b>：' + esc(c.outcome.long_term) + '</p>') +
      section('⑥ 原文出处', quotes) +
      section('⑦ 规律启发', '<ul>' + c.insight.map(function (x) {
        return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>') +
      section('⑧ 风险提醒（迁移边界）', '<ul>' + c.risks.map(function (x) {
        return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>') +
      ((c.modern_scenarios || []).length ?
        section('现代对应场景', '<div class="tags">' + c.modern_scenarios.map(function (x) {
          return '<span>' + esc(x) + '</span>'; }).join('') + '</div>') : '') +
      (paired ? section('成对 / 对照案例', '<div class="pairs">' + paired + '</div>') : '');

    document.getElementById('modal').classList.add('open');
    document.getElementById('modalCard').scrollTop = 0;

    var btn = document.getElementById('copyMd');
    btn.onclick = function () {
      var done = function () {
        btn.textContent = '已复制 ✓';
        setTimeout(function () { btn.textContent = '复制为 Markdown'; }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(caseMd(c)).then(done, function () { fallbackCopy(caseMd(c)); done(); });
      } else { fallbackCopy(caseMd(c)); done(); }
    };
    var pairs = document.querySelectorAll('#modalBody .pair');
    for (var i = 0; i < pairs.length; i++) {
      pairs[i].onclick = function () {
        state.id = this.getAttribute('data-id');
        toHash(); openModal(state.id);
      };
    }
  }

  function closeModal() {
    document.getElementById('modal').classList.remove('open');
    state.id = '';
    toHash();
  }

  function render() {
    renderChips();
    renderBookSeg();
    renderCards();
    document.getElementById('search').value = state.q;
    if (state.id) openModal(state.id);
  }

  /* ---------------- 事件 ---------------- */
  window.addEventListener('hashchange', function () { fromHash(); render(); });
  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && document.activeElement !== document.getElementById('search')) {
      e.preventDefault();
      document.getElementById('search').focus();
    }
    if (e.key === 'Escape') closeModal();
  });

  var deb;
  document.getElementById('search').addEventListener('input', function (e) {
    clearTimeout(deb);
    deb = setTimeout(function () { state.q = e.target.value.trim(); toHash(); render(); }, 120);
  });

  var segBtns = document.querySelectorAll('#bookSeg button');
  for (var i = 0; i < segBtns.length; i++) {
    segBtns[i].onclick = function () { state.book = this.getAttribute('data-book'); toHash(); render(); };
  }

  document.getElementById('grid').addEventListener('click', function (e) {
    var card = e.target.closest ? e.target.closest('.card') : null;
    if (card) { state.id = card.getAttribute('data-id'); toHash(); openModal(state.id); }
  });

  document.getElementById('modal').addEventListener('click', function (e) {
    if (e.target === document.getElementById('modal')) closeModal();
  });
  document.getElementById('modalClose').onclick = closeModal;

  fromHash();
  render();
})();
