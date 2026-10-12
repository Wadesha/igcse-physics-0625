# -*- coding: utf-8 -*-
"""Generate the classroom-slides page slides.html (full-screen slides for teaching)."""
import os
import re
import json
from _common import (BASE, CONTENT, TOPICS, GROUP_TITLE, load_css, md_to_html,
                     parse_topic, split_blocks, slug, inline, MJAX_HEAD, verify_mathjax)

# 课件页：核心主题 + 幻灯片/打印样式（都来自 teaching-kit）
CSS = load_css(slides=True)

BUDGET_CHARS = 620     # 每张幻灯片正文预算
BUDGET_BLOCKS = 6


def chunk(blocks, budget_chars=BUDGET_CHARS, budget_blocks=BUDGET_BLOCKS):
    """把块序列切成若干页，每页尽量不超过预算。"""
    pages, cur, size = [], [], 0
    for b in blocks:
        blen = len(b)
        if cur and (size + blen > budget_chars or len(cur) >= budget_blocks):
            pages.append(cur)
            cur, size = [], 0
        cur.append(b)
        size += blen
    if cur:
        pages.append(cur)
    return pages


def build_deck(d):
    slides = []
    title_short = re.split(r'[·—]', d['title'])[-1].strip() if re.search(r'[·—]', d['title']) else d['title']

    # 封面
    slides.append({'k': 'cover', 't': d['title'],
                   'h': '<div class="cover"><h1>%s</h1><p class="sub">%s</p></div>'
                        % (inline(d['title']), inline(d['note']))})

    # 考纲要求
    for name, raw in d['sections']:
        if name != 'Specification':
            continue
        items = [l[2:].strip() for l in raw.split('\n') if l.strip().startswith('- ')]
        for gi in range(0, len(items), 4):
            part = items[gi:gi + 4]
            lis = ''.join('<li>%s</li>' % md_to_html(x).strip() for x in part)
            slides.append({'k': 'spec', 't': 'Specification',
                           'h': '<h2>Specification</h2><ul class="big">%s</ul>' % lis})

    # 知识点
    for name, raw in d['sections']:
        if name != 'Notes':
            continue
        blocks = split_blocks(raw)
        groups, cur = [], []
        for b in blocks:
            if b.startswith('###') and cur:
                groups.append(cur)
                cur = [b]
            else:
                cur.append(b)
        if cur:
            groups.append(cur)
        for g in groups:
            head = g[0][3:].strip() if g[0].startswith('###') else ''
            body = g[1:] if g[0].startswith('###') else g
            for gi, part in enumerate(chunk(body)):
                h = ('<h2>%s</h2>' % inline(head)) if gi == 0 else '<h2 class="cont">%s (continued)</h2>' % inline(head)
                slides.append({'k': 'note', 't': head or '知识点',
                               'h': h + md_to_html('\n\n'.join(part))})

    # 例题：题干一页，解答一页（或多页）
    for num, body in d['examples']:
        stem, sol_html = split_example(body)
        slides.append({'k': 'ex', 't': 'Example %s' % num,
                       'h': '<h2>Example %s</h2><div class="stem">%s</div>' % (num, md_to_html(stem))})
        sol_blocks = [b for b in split_blocks(sol_body(body))]
        for gi, part in enumerate(chunk(sol_blocks, 700, 7)):
            slides.append({'k': 'sol', 't': 'Example %s solution' % num,
                           'h': '<h2 class="sol">Example %s &middot; Solution%s</h2>%s'
                                % (num, ' (cont.)' if gi else '', md_to_html('\n\n'.join(part)))})

    # 练习：题目一页 + 答案一页
    for i, qa in enumerate(d['questions'], 1):
        slides.append({'k': 'q', 't': 'Exercise %d' % i,
                       'h': '<h2>Exercise %d</h2><div class="stem">%s</div>'
                            % (i, md_to_html(qa['q']))})
        slides.append({'k': 'a', 't': 'Exercise %d answer' % i,
                       'h': '<h2 class="sol">Exercise %d &middot; Answer</h2><div class="ans">%s</div>'
                            % (i, md_to_html(qa['a']))})

    return {'key': d['key'], 'title': d['title'], 'short': title_short,
            'group': d['group'], 'slides': slides}


SOL_RE = re.compile(r'^\*\*Solution\*\*\s*:?\s*(.*)$')


def _split_at(body):
    lines = body.split('\n')
    for i, ln in enumerate(lines):
        if SOL_RE.match(ln.strip()):
            return lines[:i], lines[i:]
    return lines, []


def split_example(body):
    stem_lines, _ = _split_at(body)
    return '\n'.join(stem_lines), ''


def sol_body(body):
    _, sol = _split_at(body)
    if not sol:
        return ''
    m = SOL_RE.match(sol[0].strip())
    rest = ([m.group(1)] if m.group(1) else []) + sol[1:]
    return '\n'.join(rest)


def main():
    decks = []
    gmeta = {}
    grank = []
    for fn, grp, label in TOPICS:
        d = parse_topic(os.path.join(CONTENT, fn))
        d['group'] = grp
        d['key'] = slug(fn.replace('.md', ''))
        decks.append(build_deck(d))
        gmeta[grp] = {'title': GROUP_TITLE[grp], 'label': label}
        if grp not in grank:
            grank.append(grp)

    data_js = json.dumps({'decks': decks, 'gmeta': gmeta, 'grank': grank},
                         ensure_ascii=False)
    total = sum(len(d['slides']) for d in decks)

    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cambridge IGCSE Physics 0625 &middot; Class Slides</title>
{MJAX_HEAD}
<link rel="stylesheet" href="_theme.css">
<link rel="stylesheet" href="_theme_slides.css">
</head>
<body>
<div class="wrap">
<div class="side">
  <h1>Cambridge IGCSE Physics<br>Class Slides</h1>
  <div class="sub">{len(decks)} topics &middot; {total} slides</div>
  <div class="grp">Controls</div>
  <a class="item" href="#" onclick="backMenu();return false;">&larr; Topic menu</a>
  <a class="item" href="#" onclick="toggleIdx();return false;">This topic''s index</a>
  <div class="idx" id="idx"></div>
  <div class="grp" style="margin-top:16px">Other pages</div>
  <a class="item" href="index.html">&larr; Home</a>
  <a class="item" href="guide.html">Study guide</a>
  <a class="item" href="formula.html">Formula book</a>
  <a class="item" href="practice.html">Practice</a>
</div>
<div class="main">

<div class="menu on" id="menu">
  <div class="hero">
  <h1>Class Slides</h1>
  <div class="meta">Pick a topic to enter full-screen slides: concept &rarr; examples (question first, then solution) &rarr;
  in-class exercises (question first, then answer). Good for projecting in class;
  <b>F</b> full-screen, <b>&larr;/&rarr;</b> flip, <b>Esc</b> back to this menu, browser Ctrl+P prints to PDF.</div>
  </div>
  <div id="groups"></div>
</div>

<div class="stage" id="stage">
  <div class="toolbar">
    <button class="btn" onclick="backMenu()">&larr; Menu</button>
    <button class="btn" onclick="prev()">Previous</button>
    <button class="btn" onclick="next_()">Next</button>
    <button class="btn" onclick="full()">Full screen (F)</button>
    <button class="btn" onclick="window.print()">Print / Export PDF</button>
    <span class="btn" id="pos">—</span>
  </div>
  <div class="bar"><i id="prog"></i></div>
  <div class="slide" id="slide"></div>
  <div class="nav">
    <button class="btn" onclick="prev()">&larr; Previous</button>
    <button class="btn" onclick="next_()">Next &rarr;</button>
    <span class="btn" id="topic"></span>
  </div>
  <div class="hint">Shortcuts: <b>&rarr;</b>/<b>Space</b> next &middot; <b>&larr;</b> previous &middot; <b>Home/End</b> first/last &middot; <b>F</b> full screen &middot; <b>Esc</b> back to menu</div>
</div>

</div></div>
<script>
const DATA = {data_js};
let cur = null, idx = 0;

function renderMenu(){{
  let h = '';
  DATA.grank.forEach(function(g){{
    h += '<h3>' + DATA.gmeta[g].title + '</h3><div class="grid">';
    DATA.decks.filter(function(d){{return d.group===g;}}).forEach(function(d){{
      h += '<div class="card" onclick="openDeck(\\'' + d.key + '\\')"><div class="t">' +
           d.title + '</div><div class="c">' + d.slides.length + ' slides</div></div>';
    }});
    h += '</div>';
  }});
  document.getElementById('groups').innerHTML = h;
  typeset('groups');
}}
/* MathJax loads asynchronously: after dynamically inserting content we must
   re-typeset. A single Promise chain serialises all typeset calls so fast
   slide changes don't trigger MathJax "Typeset already in progress"; retry
   by polling until MathJax has finished loading. */
let _tp = Promise.resolve();
function typeset(id){{
  const run = function() {{
    const el = id ? [document.getElementById(id)] : undefined;
    return window.MathJax.typesetPromise(el);
  }};
  if (window.MathJax && window.MathJax.typesetPromise) {{
    _tp = _tp.then(run).catch(function(e){{ /* ignore a local typeset error and continue */ }});
  }} else {{
    setTimeout(function(){{ typeset(id); }}, 120);
  }}
}}
function renderIdx(){{
  if(!cur) return;
  let h = '';
  cur.slides.forEach(function(s,i){{
    h += '<a href="#" class="' + (i===idx?'on':'') + '" onclick="go(' + i + ');return false;">' +
         (i+1) + '. ' + s.t + '</a>';
  }});
  document.getElementById('idx').innerHTML = h;
  typeset('idx');
}}
function toggleIdx(){{
  const el = document.getElementById('idx');
  el.classList.toggle('on');
  if(el.classList.contains('on')) renderIdx();
}}
function openDeck(key){{
  cur = DATA.decks.find(function(d){{return d.key===key;}});
  idx = 0;
  document.getElementById('menu').classList.remove('on');
  document.getElementById('stage').classList.add('on');
  render();
}}
function backMenu(){{
  document.getElementById('stage').classList.remove('on');
  document.getElementById('menu').classList.add('on');
}}
function go(i){{ idx = i; render(); if(document.getElementById('idx').classList.contains('on')) renderIdx(); }}
function render(){{
  const s = cur.slides[idx];
  const kind = {{cover:'Cover',spec:'Specification',note:'Notes',ex:'Example',sol:'Example solution',q:'Exercise',a:'Exercise answer'}}[s.k] || '';
  document.getElementById('slide').innerHTML =
    '<div class="kind">' + kind + '　|　' + cur.title + '</div>' + s.h;
  document.getElementById('pos').textContent = (idx+1) + ' / ' + cur.slides.length;
  document.getElementById('topic').textContent = cur.title;
  document.getElementById('prog').style.width = ((idx+1)/cur.slides.length*100) + '%';
  typeset('slide');
}}
function prev(){{ if(!cur) return; idx = Math.max(0, idx-1); render();
  if(document.getElementById('idx').classList.contains('on')) renderIdx(); }}
function next_(){{ if(!cur) return; idx = Math.min(cur.slides.length-1, idx+1); render();
  if(document.getElementById('idx').classList.contains('on')) renderIdx(); }}
function full(){{
  const el = document.documentElement;
  if(!document.fullscreenElement){{ el.requestFullscreen && el.requestFullscreen(); }}
  else {{ document.exitFullscreen && document.exitFullscreen(); }}
}}
document.addEventListener('keydown', function(e){{
  if(!cur) return;
  if(e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown'){{ e.preventDefault(); next_(); }}
  else if(e.key === 'ArrowLeft' || e.key === 'PageUp'){{ e.preventDefault(); prev(); }}
  else if(e.key === 'Home'){{ go(0); }}
  else if(e.key === 'End'){{ go(cur.slides.length-1); }}
  else if(e.key === 'f' || e.key === 'F'){{ full(); }}
  else if(e.key === 'Escape'){{ backMenu(); }}
}});
renderMenu();
// Allow deep-linking straight into a topic from the index / other pages via URL params
(function(){{
  const want = sessionStorage.getItem('deck');
  const hash = decodeURIComponent((location.hash || '').replace('#',''));
  const key = want || hash;
  if (key && DATA.decks.some(function(d){{return d.key === key;}})) {{
    sessionStorage.removeItem('deck');
    openDeck(key);
  }}
}})();
</script>
</body></html>"""

    out = os.path.join(BASE, 'slides.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print('written', out, len(html), 'bytes;', len(decks), 'decks,', total, 'slides')
    verify_mathjax(out)


if __name__ == '__main__':
    main()
