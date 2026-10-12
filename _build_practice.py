# -*- coding: utf-8 -*-
"""生成练习题互动页 as_math_practice.html（逐题播放、可隐藏答案、键盘操作）。"""
import os
import json
from _common import (BASE, CONTENT, TOPICS, GROUP_TITLE, load_css, parse_topic,
                     slug, md_to_html, MJAX_HEAD, verify_mathjax)

# 菜单/卡片网格/进度条/导航等组件样式与课件页共用，统一取自 teaching-kit
# 工具包（load_css(slides=True) = theme.css + slides.css），禁止在脚本里重抄。
CSS = load_css(slides=True)


def build():
    decks = []
    gmeta = {}
    order = []
    for fn, grp, label in TOPICS:
        d = parse_topic(os.path.join(CONTENT, fn))
        key = slug(fn.replace('.md', ''))
        qs = []
        for i, qa in enumerate(d['questions'], 1):
            qs.append({
                'n': i,
                'q': md_to_html(qa['q']).strip(),
                'a': md_to_html(qa['a']).strip(),
            })
        decks.append({'key': key, 'title': d['title'], 'group': grp, 'qs': qs})
        gmeta[grp] = {'title': GROUP_TITLE[grp], 'label': label}
        order.append(grp)
    grank = []
    for g in order:
        if g not in grank:
            grank.append(g)

    total = sum(len(d['qs']) for d in decks)
    data_js = json.dumps({'decks': decks, 'gmeta': gmeta, 'grank': grank},
                         ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cambridge IGCSE Physics 0625 &middot; Practice</title>
{MJAX_HEAD}
<link rel="stylesheet" href="_theme.css">
<link rel="stylesheet" href="_theme_slides.css">
<style>
/* Layout unique to the practice page; menu/card grid/progress/nav come from teaching-kit */
.grid{{margin-top:8px}}
.qbox{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:26px 28px;min-height:230px}}
.qhead{{color:var(--dim);font-size:13px;margin-bottom:8px}}
.qtext{{font-size:18px;line-height:1.85}}
.abox{{margin-top:18px;border-left:3px solid var(--acc2);padding:12px 16px;display:none}}
.abox.on{{display:block}}
.kbd{{color:var(--dim);font-size:12.5px;margin-top:10px}}
.kbd b{{background:var(--panel2);border:1px solid var(--line);border-radius:4px;padding:1px 6px}}
</style></head>
<body>
<div class="wrap">
<div class="side">
  <h1>Cambridge IGCSE Physics<br>Practice</h1>
  <div class="sub">{len(decks)} topics &middot; {total} questions</div>
  <div class="grp">Controls</div>
  <a class="item" href="#" onclick="backMenu();return false;">&larr; Back to topic menu</a>
  <div class="grp" style="margin-top:16px">Other pages</div>
  <a class="item" href="index.html">&larr; Home</a>
  <a class="item" href="slides.html">Class slides</a>
  <a class="item" href="guide.html">Study guide</a>
  <a class="item" href="formula.html">Formula book</a>
</div>
<div class="main">

<div class="menu on" id="menu">
  <div class="hero">
  <h1>Practice</h1>
  <div class="meta">Pick a topic to play its questions one by one. Answers are hidden by default;
  press <b>Space</b> to show/hide, <b>&larr; &rarr;</b> to flip, <b>Esc</b> back to this menu.</div>
  </div>
  <div id="groups"></div>
</div>

<div class="stage" id="stage">
  <div class="toolbar">
    <button class="btn" onclick="backMenu()">&larr; Menu</button>
    <button class="btn" onclick="toggleAns()">Show/Hide answer</button>
    <button class="btn" onclick="prev()">Previous</button>
    <button class="btn" onclick="next_()">Next</button>
    <span class="btn" id="pos">—</span>
  </div>
  <div class="bar"><i id="prog"></i></div>
  <div class="qbox">
    <div class="qhead" id="qhead">—</div>
    <div class="qtext" id="qtext">—</div>
    <div class="abox" id="abox"><b style="color:var(--acc2)">Answer</b>
      <div id="atext" style="margin-top:6px"></div></div>
  </div>
  <div class="nav">
    <button class="btn" onclick="prev()">&larr; Previous</button>
    <button class="btn" onclick="toggleAns()">Space: answer</button>
    <button class="btn" onclick="next_()">Next &rarr;</button>
  </div>
  <div class="kbd">Shortcuts: <b>&larr;</b> previous &middot; <b>&rarr;</b> next &middot; <b>Space</b> answer &middot; <b>Esc</b> back to menu</div>
</div>

</div></div>
<script>
const DATA = {data_js};
let cur = null, idx = 0, showAns = false;

/* MathJax loads asynchronously: after dynamically inserting content we must
   re-typeset. A single Promise chain serialises all typeset calls so fast
   question changes don't trigger MathJax "Typeset already in progress"; retry
   by polling until MathJax has finished loading. */
let _tp = Promise.resolve();
function typeset(id){{
  const run = function() {{
    const el = id ? [document.getElementById(id)] : undefined;
    return window.MathJax.typesetPromise(el);
  }};
  if (window.MathJax && window.MathJax.typesetPromise) {{
    _tp = _tp.then(run).catch(function(e){{ /* ignore a local typeset error */ }});
  }} else {{
    setTimeout(function(){{ typeset(id); }}, 120);
  }}
}}

function renderMenu(){{
  const box = document.getElementById('groups');
  let h = '';
  DATA.grank.forEach(function(g){{
    h += '<h3>' + DATA.gmeta[g].title + '</h3><div class="grid">';
    DATA.decks.filter(function(d){{return d.group===g;}}).forEach(function(d){{
      h += '<div class="card" onclick="openDeck(\\'' + d.key + '\\')"><div class="t">' +
           d.title + '</div><div class="c">' + d.qs.length + ' questions</div></div>';
    }});
    h += '</div>';
  }});
  box.innerHTML = h;
  typeset('groups');
}}

function openDeck(key){{
  cur = DATA.decks.find(function(d){{return d.key===key;}});
  idx = 0; showAns = false;
  document.getElementById('menu').classList.remove('on');
  document.getElementById('stage').classList.add('on');
  render();
}}
function backMenu(){{
  document.getElementById('stage').classList.remove('on');
  document.getElementById('menu').classList.add('on');
}}
function render(){{
  const q = cur.qs[idx];
  document.getElementById('qhead').textContent = cur.title + '  ·  Question ' + q.n + ' / ' + cur.qs.length;
  document.getElementById('qtext').innerHTML = q.q;
  document.getElementById('atext').innerHTML = q.a;
  document.getElementById('abox').classList.toggle('on', showAns);
  document.getElementById('pos').textContent = (idx+1) + ' / ' + cur.qs.length;
  document.getElementById('prog').style.width = ((idx+1)/cur.qs.length*100) + '%';
  typeset('qbox');
}}
function toggleAns(){{ showAns = !showAns; document.getElementById('abox').classList.toggle('on', showAns);
  if (showAns) typeset('atext'); }}
function prev(){{ if(!cur) return; idx = (idx - 1 + cur.qs.length) % cur.qs.length; showAns=false; render(); }}
function next_(){{ if(!cur) return; idx = (idx + 1) % cur.qs.length; showAns=false; render(); }}
document.addEventListener('keydown', function(e){{
  if(!cur) return;
  if(e.key === 'ArrowRight'){{ next_(); }}
  else if(e.key === 'ArrowLeft'){{ prev(); }}
  else if(e.key === ' '){{ e.preventDefault(); toggleAns(); }}
  else if(e.key === 'Escape'){{ backMenu(); }}
}});
renderMenu();
</script>
</body></html>"""

    out = os.path.join(BASE, 'practice.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print('written', out, len(html), 'bytes;', len(decks), 'decks,', total, 'questions')
    verify_mathjax(out)


if __name__ == '__main__':
    build()
