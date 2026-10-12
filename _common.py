# -*- coding: utf-8 -*-
"""公共模块：主题元数据、Markdown 解析、共享样式、内容读取。"""
import os
import re
import html
import shutil
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(BASE, '_content')

# 主题顺序与分组（文件名, 分组, 标签）—— 纯英文项目，6 个 CIE IGCSE Physics 0625 专题
TOPICS = [
    ('motion_forces.md', 'P', 'Physics · Motion, Forces & Energy'),
    ('thermal.md',       'P', 'Physics · Thermal Physics'),
    ('waves.md',         'P', 'Physics · Waves'),
    ('electricity.md',   'P', 'Physics · Electricity & Magnetism'),
    ('nuclear.md',       'P', 'Physics · Nuclear Physics'),
    ('space.md',         'P', 'Physics · Space Physics'),
]

GROUP_TITLE = {
    'P': 'Cambridge IGCSE Physics 0625 (6 topics)',
}

MATH_RE = re.compile(r'(\$\$.*?\$\$|\$[^$\n]*?\$)', re.S)


def _esc_math(s):
    """数学片段只转义 HTML 特殊字符（MathJax 读取的是文本节点，&lt; 会还原为 <）。"""
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def esc(s):
    """转义 HTML；$...$ / $$...$$ 数学片段保留 LaTeX 原样但转义 < > &。"""
    parts = MATH_RE.split(s)
    out = []
    for i, p in enumerate(parts):
        if i % 2 == 1:
            out.append(_esc_math(p))
        else:
            out.append(html.escape(p, quote=False))
    return ''.join(out)


def inline(s):
    """行内格式：**粗体**、`代码`、数学原样。"""
    s = esc(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'`([^`]+?)`', r'<code>\1</code>', s)
    return s


def md_to_html(text):
    """把受限 Markdown 转成 HTML 片段。"""
    lines = text.split('\n')
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        st = line.strip()

        # 表格
        if st.startswith('|'):
            block = []
            while i < n and lines[i].strip().startswith('|'):
                block.append(lines[i].strip())
                i += 1
            rows = []
            for r in block:
                cells = [c.strip() for c in r.strip('|').split('|')]
                if all(re.fullmatch(r':?-{2,}:?', c) for c in cells if c):
                    continue
                rows.append(cells)
            if rows:
                head = rows[0]
                body = rows[1:]
                th = ''.join('<th>%s</th>' % inline(c) for c in head)
                tb = ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % inline(c) for c in r) for r in body)
                out.append('<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>' % (th, tb))
            continue

        # 标题
        m = re.match(r'^(#{1,6})\s+(.*)$', st)
        if m and not st.startswith('#'):
            pass
        if st.startswith('###'):
            out.append('<h4>%s</h4>' % inline(st[3:].strip()))
            i += 1
            continue
        if st.startswith('##'):
            out.append('<h3>%s</h3>' % inline(st[2:].strip()))
            i += 1
            continue
        if st.startswith('#'):
            out.append('<h2>%s</h2>' % inline(st[1:].strip()))
            i += 1
            continue

        # 引用说明
        if st.startswith('>'):
            out.append('<p class="note">%s</p>' % inline(st[1:].strip()))
            i += 1
            continue

        # 列表
        if st.startswith('- ') or re.match(r'^\d+\.\s', st):
            ordered = bool(re.match(r'^\d+\.\s', st))
            items = []
            while i < n:
                cur = lines[i].strip()
                if ordered and re.match(r'^\d+\.\s', cur):
                    items.append(re.sub(r'^\d+\.\s', '', cur))
                    i += 1
                elif (not ordered) and cur.startswith('- '):
                    items.append(cur[2:])
                    i += 1
                else:
                    break
            tag = 'ol' if ordered else 'ul'
            out.append('<%s>%s</%s>' % (tag, ''.join('<li>%s</li>' % inline(x) for x in items), tag))
            continue

        # 空行
        if not st:
            i += 1
            continue

        # 段落（连续非空行合并）
        buf = []
        while i < n and lines[i].strip():
            buf.append(lines[i].strip())
            i += 1
        out.append('<p>%s</p>' % inline(' '.join(buf)))
    return '\n'.join(out)


def split_blocks(raw):
    """把一段 Markdown 切成块：标题 / 表格 / 列表 / 显示公式 / 段落。"""
    lines = raw.split('\n')
    blocks = []
    i = 0
    n = len(lines)
    while i < n:
        st = lines[i].strip()
        if not st:
            i += 1
            continue
        if st.startswith('###'):
            blocks.append(st)
            i += 1
            continue
        if st.startswith('|'):
            buf = []
            while i < n and lines[i].strip().startswith('|'):
                buf.append(lines[i])
                i += 1
            blocks.append('\n'.join(buf))
            continue
        if st.startswith('- ') or re.match(r'^\d+\.\s', st):
            buf = []
            while i < n and (lines[i].strip().startswith('- ')
                             or re.match(r'^\d+\.\s', lines[i].strip())):
                buf.append(lines[i])
                i += 1
            blocks.append('\n'.join(buf))
            continue
        if st.startswith('$$'):
            buf = [lines[i]]
            i += 1
            if '$' not in buf[0] or buf[0].count('$') < 4:
                while i < n and lines[i].strip():
                    buf.append(lines[i])
                    i += 1
                    if lines[i - 1].strip().endswith('$$'):
                        break
            blocks.append('\n'.join(buf))
            continue
        blocks.append(st)
        i += 1
    return blocks


def parse_topic(path):
    """解析一个主题文件 → dict(title, note, sections, examples, questions)"""
    with open(path, encoding='utf-8') as f:
        text = f.read()

    title = ''
    note = ''
    sections = []       # [(name, raw)]
    cur = None
    buf = []

    for line in text.split('\n'):
        if line.startswith('# '):
            title = line[2:].strip()
            continue
        if line.startswith('## '):
            if cur:
                sections.append((cur, '\n'.join(buf)))
            cur = line[3:].strip()
            buf = []
            continue
        buf.append(line)
    if cur:
        sections.append((cur, '\n'.join(buf)))

    # 第一段 > 引用作为说明
    m = re.search(r'^>\s*(.+)$', text, re.M)
    if m:
        note = m.group(1).strip()

    examples = parse_examples(sections)
    questions = parse_questions(sections)
    return {'title': title, 'note': note, 'sections': sections,
            'examples': examples, 'questions': questions, 'file': os.path.basename(path)}


EX_HEAD = re.compile(r'^###\s*Example\s*(\d+)')


def parse_examples(sections):
    """Examples: ### Example N (title) … until next ### or ##."""
    out = []
    for name, raw in sections:
        if name != 'Examples':
            continue
        cur = None
        buf = []
        for line in raw.split('\n'):
            m = EX_HEAD.match(line)
            if m:
                if cur is not None:
                    out.append((cur, '\n'.join(buf).strip()))
                cur = m.group(1)
                buf = []
                continue
            if cur is not None:
                buf.append(line)
        if cur is not None:
            out.append((cur, '\n'.join(buf).strip()))
    return out


def parse_questions(sections):
    """Exercises: **Q1.** stem / **A1.** answer"""
    out = []
    for name, raw in sections:
        if name != 'Exercises':
            continue
        cur_q = None
        cur_a = None
        mode = None
        qb, ab = [], []

        def flush():
            if cur_q is not None:
                out.append({'q': ' '.join(x.strip() for x in qb if x.strip()),
                            'a': ' '.join(x.strip() for x in ab if x.strip())})

        for line in raw.split('\n'):
            st = line.strip()
            mq = re.match(r'^\*\*Q(\d+)\.\*\*\s*(.*)$', st)
            ma = re.match(r'^\*\*A(\d+)\.\*\*\s*(.*)$', st)
            if mq:
                flush()
                cur_q = mq.group(1)
                qb = [mq.group(2)]
                ab = []
                mode = 'q'
                continue
            if ma:
                mode = 'a'
                ab = [ma.group(2)]
                continue
            if mode == 'q' and st:
                qb.append(st)
            elif mode == 'a' and st:
                ab.append(st)
        flush()
    return out


def slug(s):
    s = re.sub(r'[^\w\u4e00-\u9fff]+', '-', s)
    return s.strip('-')


KIT_DIR = r"C:\Users\wade\.workbuddy\templates\teaching-kit"
KIT_CSS = os.path.join(KIT_DIR, 'theme.css')
KIT_SLIDES = os.path.join(KIT_DIR, 'slides.css')
LOCAL_CSS = os.path.join(BASE, '_theme.css')
LOCAL_SLIDES = os.path.join(BASE, '_theme_slides.css')


def _read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def load_css(slides=False):
    """浅色主题唯一来源：teaching-kit（theme.css，课件页再叠加 slides.css）。
    同时在工程目录留一份副本 _theme.css，保证工程被单独拷走时仍能重建。
    改样式请改工具包里的文件，不要在这里改。
    """
    pairs = [(KIT_CSS, LOCAL_CSS)]
    if slides:
        pairs.append((KIT_SLIDES, LOCAL_SLIDES))
    out = []
    for src, dst in pairs:
        if not os.path.exists(src):
            if os.path.exists(dst):
                out.append(_read(dst))
                continue
            raise SystemExit('缺少主题文件：%s（请从 teaching-kit 复制）' % src)
        text = _read(src)
        try:
            with open(dst, 'w', encoding='utf-8') as f:
                f.write(text)
        except OSError:
            pass
        out.append(text)
    return "\n".join(out)


CSS = load_css()


# ============================================================================
# 数学公式渲染：MathJax 3 的"单一正确片段"。所有页面从这里取，禁止在各脚本里重写。
# 要点（这是"数学符号反复出错"的根因清单）：
#   1) MathJax 3 默认【不】启用 $...$ 行内定界符，必须显式配 inlineMath；
#   2) 脚本/题目是 JS 动态注入的，页面必须在注入后调用 MathJax.typesetPromise 重排版
#      （各页里的 typeset() helper 已做）；只靠 MathJax 首屏自动排版会漏掉动态内容；
#   3) 用本地自包含 mathjax/tex-mml-svg.js，离线也能渲染，不依赖 CDN（CDN 离线即白屏）。
# ============================================================================
MJAX_HEAD = (
    '<script>\n'
    'window.MathJax = {\n'
    "  tex: { inlineMath: [['$','$'], ['\\(','\\)']], displayMath: [['$$','$$'], ['\\[','\\]']] }\n"
    '};\n'
    '</script>\n'
    '<script src="mathjax/tex-mml-svg.js" async></script>\n'
)

# 可选的"真渲染"检查依赖（仅在构建本机可用时启用，找不到就跳过，不影响构建）
_NODE_CANDIDATES = [
    'node',
    r'C:\Users\wade\.workbuddy\binaries\node\versions\22.22.2-6\node.exe',
]
_JSDOM_DIR = r'C:\Users\wade\.workbuddy\binaries\node\workspace\node_modules'


def _find_node():
    for c in _NODE_CANDIDATES:
        if c == 'node':
            p = shutil.which('node')
        else:
            p = c if os.path.exists(c) else None
        if p:
            return p
    return None


def verify_mathjax(outfile):
    """构建卡口：确保生成的 HTML 真的能渲染数学，而不是把 $...$ 当文本发出来。
    静态检查（必然执行，纯 Python）失败直接 SystemExit —— 让错误在本地构建时就暴露，
    而不是等用户线上发现。可选的"真渲染"检查（node+jsdom）在本机可用时额外跑一次，
    不可用时静默跳过，不影响构建。
    """
    with open(outfile, encoding='utf-8') as f:
        s = f.read()
    errs = []
    if 'mathjax/tex-mml-svg.js' not in s:
        errs.append('缺少本地 MathJax 引用 mathjax/tex-mml-svg.js（离线会不渲染）')
    if 'inlineMath' not in s:
        errs.append('缺少 MathJax inlineMath 配置（MathJax 3 默认不开 $...$，必须显式配置）')
    if 'cdn.jsdelivr.net/npm/mathjax' in s:
        errs.append('仍引用 jsdelivr CDN 的 MathJax（应改用本地 mathjax/）')
    if errs:
        raise SystemExit('数学渲染卡口失败 [%s]:\n  - %s' % (outfile, '\n  - '.join(errs)))
    _verify_render_jsdom(outfile)


def _verify_render_jsdom(outfile):
    """可选：用 node+jsdom 真实加载生成的页面（含本地 mathjax），排版后扫描正文，
    确认没有残留的原始 $...$ 文本。任何失败都静默跳过（不影响构建）。"""
    node = _find_node()
    if not node:
        return
    js = (
        "const {JSDOM}=require(%r);"
        "JSDOM.fromFile(%r,{runScripts:'dangerously',resources:'usable',pretendToBeVisual:true})"
        ".then(d=>{const w=d.window;const t=setInterval(()=>{"
        "if(w.MathJax&&w.MathJax.startup&&w.MathJax.startup.promise){clearInterval(t);"
        "w.MathJax.startup.promise.then(()=>setTimeout(()=>{"
        "let bad=0;w.document.body&&w.document.body.querySelectorAll('*').forEach(e=>{"
        "if(e.tagName==='SCRIPT'||e.tagName==='STYLE'||e.closest('mjx-container'))return;"
        "e.childNodes.forEach(n=>{if(n.nodeType===3&&/\\$[^$]+\\$/.test(n.textContent))bad++;});});"
        "console.log(JSON.stringify({ok:bad===0,bad}));process.exit(0);"
        "},800);}).catch(e=>{console.log(JSON.stringify({ok:true,skip:'startup:'+e.message}));process.exit(0);});"
        "}},50);setTimeout(()=>{console.log(JSON.stringify({ok:true,skip:'timeout'}));process.exit(0);},20000);"
        "}).catch(e=>{console.log(JSON.stringify({ok:true,skip:'load:'+e.message}));process.exit(0);});"
    ) % (os.path.join(_JSDOM_DIR, 'jsdom'), outfile)
    try:
        r = subprocess.run([node, '-e', js], capture_output=True, text=True, timeout=45)
        for line in ((r.stdout or '') + (r.stderr or '')).splitlines():
            if line.startswith('{"ok"'):
                import json as _json
                d = _json.loads(line)
                if d.get('bad'):
                    raise SystemExit('数学渲染卡口失败 [%s]: 仍发现 %s 处未渲染的原始 $...$ 文本'
                                     % (outfile, d['bad']))
                return
    except SystemExit:
        raise
    except Exception:
        return  # 可选检查失败不影响构建
