# -*- coding: utf-8 -*-
"""生成入口页 index.html。"""
import os
from _common import BASE, CONTENT, TOPICS, GROUP_TITLE, CSS, md_to_html, parse_topic, slug, MJAX_HEAD, verify_mathjax
from _build_slides import build_deck


def build():
    data = []
    for fn, grp, label in TOPICS:
        d = parse_topic(os.path.join(CONTENT, fn))
        d['group'] = grp
        d['key'] = slug(fn.replace('.md', ''))
        d['n_ex'] = len(d['examples'])
        d['n_q'] = len(d['questions'])
        data.append(d)

    tot_ex = sum(d['n_ex'] for d in data)
    tot_q = sum(d['n_q'] for d in data)
    tot_sl = sum(len(build_deck(d)['slides']) for d in data)

    groups = []
    present = list(dict.fromkeys(d['group'] for d in data))
    for g in present:
        rows = ''.join(
            '<tr><td><a href="guide.html#%s">%s</a></td><td>%d</td>'
            '<td><a href="practice.html" onclick="sessionStorage.setItem(\'deck\',\'%s\')">%d Qs</a></td>'
            '<td><a href="slides.html" onclick="sessionStorage.setItem(\'deck\',\'%s\')">Slides</a></td></tr>'
            % (d['key'], d['title'], d['n_ex'], d['key'], d['n_q'], d['key'])
            for d in data if d['group'] == g)
        groups.append('<h3>%s</h3><table><thead><tr><th>Topic</th><th>Examples</th><th>Exercises</th><th>Slides</th></tr></thead>'
                      '<tbody>%s</tbody></table>' % (GROUP_TITLE[g], rows))

    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cambridge IGCSE Physics 0625 &middot; Study Kit</title>
{MJAX_HEAD}
<link rel="stylesheet" href="_theme.css">
<style>
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;margin:18px 0}}
.card{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px 20px}}
.card:hover{{border-color:var(--acc)}}
.card h3{{margin:0 0 6px;color:var(--acc);font-size:17px}}
.card p{{color:var(--dim);font-size:13.5px;margin:4px 0 0}}
.stat{{display:flex;gap:22px;flex-wrap:wrap;margin:12px 0}}
.stat div{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 16px}}
.stat b{{display:block;font-size:22px;color:var(--acc2)}}
.stat span{{font-size:12.5px;color:var(--dim)}}
</style></head>
<body>
<div class="wrap">
<div class="side">
  <h1>Cambridge IGCSE<br>Physics 0625</h1>
  <div class="sub">Syllabus 0625 &middot; 6 topics</div>
  <div class="grp">Four pages</div>
  <a class="item" href="slides.html">① Class slides</a>
  <a class="item" href="guide.html">② Study guide</a>
  <a class="item" href="formula.html">③ Formula book</a>
  <a class="item" href="practice.html">④ Practice</a>
  <div class="grp" style="margin-top:16px">Topic index</div>
  {''.join('<a class="item" href="guide.html#%s">%s</a>' % (d['key'], d['title']) for d in data)}
</div>
<div class="main">
<div class="hero">
<h1>Cambridge IGCSE Physics 0625 &middot; Study Kit</h1>
<div class="meta">Cambridge IGCSE Physics (0625) &middot; six syllabus topics<br>
Motion, forces and energy &middot; Thermal physics &middot; Waves &middot; Electricity and magnetism &middot; Nuclear physics &middot; Space physics.<br>
Notes in English; equations rendered with MathJax, fully offline.</div>
</div>

<div class="stat">
<div><b>{len(data)}</b><span>Topics</span></div>
<div><b>{tot_ex}</b><span>Worked examples</span></div>
<div><b>{tot_q}</b><span>Practice questions</span></div>
<div><b>{tot_sl}</b><span>Slides</span></div>
<div><b>0625</b><span>Syllabus</span></div>
</div>

<div class="cards">
<a class="card" href="slides.html" style="color:inherit">
  <h3>① Class slides</h3>
  <p>{tot_sl} slides (6 topics): concept &rarr; examples (question first, then solution) &rarr; in-class exercises. Full-screen projection, keyboard navigation, Ctrl+P to print a PDF handout.</p>
</a>
<a class="card" href="guide.html" style="color:inherit">
  <h3>② Study guide</h3>
  <p>Six topics explained: specification checklist + worked notes + example solutions. Sidebar TOC; example solutions collapse/expand with one click.</p>
</a>
<a class="card" href="formula.html" style="color:inherit">
  <h3>③ Formula book</h3>
  <p>Every equation the 0625 exam expects you to recall, grouped by topic, plus units, prefixes, constants and the standard practical methods.</p>
</a>
<a class="card" href="practice.html" style="color:inherit">
  <h3>④ Practice</h3>
  <p>Play questions topic by topic; answers hidden by default; &larr; &rarr; to flip, Space for answer, Esc to return. For class projection and self-test.</p>
</a>
</div>

<h2>Where these topics sit</h2>
<table>
<thead><tr><th>Paper</th><th>What it covers</th><th>Notes</th></tr></thead>
<tbody>
<tr><td>Papers 1 &amp; 2 &mdash; Multiple choice</td><td>Core (1) and Extended (2)</td><td>40 multiple-choice questions in 45 minutes.</td></tr>
<tr><td>Papers 3 &amp; 4 &mdash; Theory</td><td>Core (3) and Extended (4)</td><td>Structured and free-response questions, 1 hour 15 minutes.</td></tr>
<tr><td>Papers 5 &amp; 6 &mdash; Practical</td><td>Practical test (5) / Alternative to practical (6)</td><td>1 hour 15 minutes; Paper 6 is the written alternative where no laboratory is available.</td></tr>
</tbody></table>
<p class="note">Candidates take either the Core papers (1, 3 and 5/6) or the Extended papers (2, 4 and 5/6). No formula booklet is provided, so every equation on the Equations page must be recalled. These six topics cover the whole 0625 theory content.</p>

<h2>Topic index</h2>
{''.join(groups)}

<div class="footer">
Source: Cambridge IGCSE Physics (0625) syllabus for examination from 2026. The explanations, worked examples and exercises on this site are original study write-ups and are not affiliated with or endorsed by Cambridge University Press &amp; Assessment.
</div>
</div></div>
</body></html>"""

    out = os.path.join(BASE, 'index.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print('written', out, len(html))
    verify_mathjax(out)


if __name__ == '__main__':
    build()
