# -*- coding: utf-8 -*-
"""Generate the explanation-guide page guide.html (English notes + MathJax + sidebar TOC)."""
import os
import re
from _common import (BASE, CONTENT, TOPICS, GROUP_TITLE, CSS, md_to_html,
                     parse_topic, slug, inline, MJAX_HEAD, verify_mathjax)

SOL_RE = re.compile(r'^\*\*Solution\*\*\s*:?\s*(.*)$')


def split_solution(body):
    """把例题正文在 **解** 处切开：题干 + 可折叠解答。"""
    lines = body.split('\n')
    for i, ln in enumerate(lines):
        m = SOL_RE.match(ln.strip())
        if m:
            stem = '\n'.join(lines[:i])
            sol_lines = [m.group(1)] if m.group(1) else []
            sol_lines += lines[i + 1:]
            sol = ('<details open><summary>Solution (click to expand/collapse)</summary>'
                   '<div class="sol">%s</div></details>' % md_to_html('\n'.join(sol_lines)))
            return stem, sol
    return body, ''


def build():
    data = []
    for fn, grp, _ in TOPICS:
        p = os.path.join(CONTENT, fn)
        d = parse_topic(p)
        d['group'] = grp
        d['key'] = slug(fn.replace('.md', ''))
        data.append(d)

    # 侧栏
    side = ['<h1>Cambridge IGCSE Physics<br>Study Guide</h1>',
            '<div class="sub">Syllabus 0625 · 6 topics</div>']
    last = None
    for d in data:
        if d['group'] != last:
            side.append('<div class="grp">%s</div>' % GROUP_TITLE[d['group']])
            last = d['group']
        side.append('<a class="item" href="#%s">%s</a>' % (d['key'], d['title']))
        side.append('<a class="mini" href="#%s-ex">↳ Examples</a>' % d['key'])
    side.append('<div class="grp" style="margin-top:16px">Other pages</div>')
    side.append('<a class="item" href="index.html">&larr; Home</a>')
    side.append('<a class="item" href="slides.html">Class slides</a>')
    side.append('<a class="item" href="formula.html">Formula book</a>')
    side.append('<a class="item" href="practice.html">Practice</a>')
    side_html = '\n'.join(side)

    total_ex = sum(len(d['examples']) for d in data)
    total_q = sum(len(d['questions']) for d in data)

    main = []
    main.append(f"""<div class="hero">
<h1>Cambridge IGCSE Physics 0625 &middot; Study Guide</h1>
<div class="meta">
Cambridge IGCSE Physics (0625) &middot; six syllabus topics<br>
{len(data)} topics &middot; {total_ex} worked examples (with full solutions) &middot;
see the <a href="practice.html">Practice</a> page for {total_q} self-test questions<br>
Explanations written in English; equations rendered with MathJax.
</div></div>
<div class="toolbar">
<button class="btn" onclick="toggleAll(false)">Collapse all solutions</button>
<button class="btn" onclick="toggleAll(true)">Expand all solutions</button>
<a class="btn" href="formula.html">Formula book</a>
<a class="btn" href="practice.html">Practice</a>
</div>""")

    for d in data:
        main.append('<h2 id="%s">%s</h2>' % (d['key'], d['title']))
        if d['note']:
            main.append('<p class="note">%s</p>' % inline(d['note']))

        for name, raw in d['sections']:
            if name == 'Specification':
                items = [l[2:].strip() for l in raw.split('\n') if l.strip().startswith('- ')]
                lis = ''.join('<li>%s</li>' % md_to_html(x).strip() for x in items)
                main.append('<h3>Specification &middot; What students need to learn</h3>')
                main.append('<ul class="chk">%s</ul>' % lis)
            elif name == 'Notes':
                main.append('<h3>Notes</h3>')
                main.append(md_to_html(raw))
            elif name == 'Examples':
                main.append('<h3 id="%s-ex">Examples (%d)</h3>' % (d['key'], len(d['examples'])))
                for num, body in d['examples']:
                    stem, sol = split_solution(body)
                    main.append('<div class="ex"><h4>Example %s</h4>%s%s</div>'
                                % (num, md_to_html(stem), sol))
            elif name == 'Exercises':
                main.append('<h3>Exercises</h3>')
                main.append('<p>This topic''s %d practice questions are on the '
                            '<a href="practice.html#%s">Practice page</a>, '
                            'with answers hidden for self-testing.</p>'
                            % (len(d['questions']), d['key']))

    main.append('<div class="footer">Explanations are original write-ups following the Cambridge '
                'IGCSE Physics (0625) syllabus; all worked examples and '
                'exercises are original, written to accompany the notes.</div>')

    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cambridge IGCSE Physics 0625 &middot; Study Guide</title>
{MJAX_HEAD}
<link rel="stylesheet" href="_theme.css">
<style>
.ex .sol{{border-left:3px solid var(--acc2);padding-left:12px;margin-top:6px}}
</style></head>
<body>
<div class="wrap">
<div class="side">{side_html}</div>
<div class="main">{''.join(main)}</div>
</div>
<script>
function toggleAll(open){{
  document.querySelectorAll('details').forEach(function(d){{ d.open = open; }});
}}
</script>
</body></html>"""

    out = os.path.join(BASE, 'guide.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print('written', out, len(html), 'bytes;', len(data), 'topics,', total_ex, 'examples')
    verify_mathjax(out)


if __name__ == '__main__':
    build()
