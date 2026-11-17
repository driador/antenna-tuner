#!/usr/bin/env python3
"""Post-process the review log HTML.

Two jobs the stylesheet cannot do alone, because WeasyPrint has no :has():
  1. tag each attribution paragraph (and the block that follows it) by author
  2. turn the `STATUS` codes into semantically coloured chips
"""
import io, re, sys, datetime

html_path, src_path = sys.argv[1], sys.argv[2]
h   = io.open(html_path, encoding='utf-8').read()
src = io.open(src_path, encoding='utf-8').read()

# ---- 1. attribution ----
def tag(m):
    body, who = m.group(0), m.group(1).upper()
    cls = 'claude-block' if who.startswith('CLAUDE') else 'gemini-block'
    return body.replace('<p>', f'<p class="{cls}">', 1)
h = re.sub(r'<p><strong>((?:CLAUDE|GEMINI|Gemini)[^<]*)</strong>.*?</p>', tag, h, flags=re.S)

# ---- 2. status chips ----
def classify(t):
    u = t.upper()
    bad   = any(k in u for k in ('DISPUTED', 'NOT RESOLVED', 'STILL OPEN', 'UNMATCHABLE'))
    openish = 'OPEN' in u
    good  = any(k in u for k in ('RESOLVED', 'CLOSED', 'CONCUR', 'VERIFIED', 'CONFIRMED'))
    mixed = any(k in u for k in ('PARTIAL', 'EXCEPTION', 'BLOCKED', 'PENDING'))
    if bad:                      return 'chip-bad'
    if mixed or (good and openish): return 'chip-mixed'
    if openish:                  return 'chip-bad'
    if good:                     return 'chip-ok'
    return 'chip-neutral'

def chip(m):
    t = m.group(1)
    # HTML-escaped ampersands appear as &amp; -- normalise before matching
    probe = t.replace('&amp;', '&')
    if not re.fullmatch(r'[A-Z0-9][A-Z0-9 &;—/,.\-]{2,60}', probe):
        return m.group(0)                     # leave ordinary inline code alone
    return f'<span class="chip {classify(probe)}">{t}</span>'
h = re.sub(r'<code>([^<]+)</code>', chip, h)

# ---- 3. TeX that --math-method=plain could not flatten ----
# Fractions and roots have no plain-text form, so pandoc emits raw TeX. Convert
# the constructs actually present into readable ASCII. The source markdown is
# left untouched -- this is a rendering concern, not a content change.
TEX = [
    (r'\\frac\{([^{}]*)\}\{([^{}]*)\}', r'(\1)/(\2)'),
    (r'\\sqrt\{([^{}]*)\}',               r'sqrt(\1)'),
    (r'\\text\{\s*([^{}]*?)\s*\}',      r'\1'),
    (r'\\left\(|\\right\)',             ''),
    (r'\\times', ' x '), (r'\\approx', ' ~= '), (r'\\le\b', ' <= '),
    (r'\\ge\b', ' >= '), (r'\\cdot', '*'), (r'\\quad', '   '),
    (r'\\pm', '+/-'), (r'\\ln', 'ln'), (r'\\Omega', ' ohm'),
    (r'\\epsilon', 'eps'), (r'\\theta', 'theta'), (r'\\pi\b', 'pi'),
    (r'\\mathbf\{([^{}]*)\}', r'\1'), (r'\\circ', ' deg'),
    (r'\\[,;!]', ' '), (r'[{}]', ''), (r'\\\\', ' '),
]
def detex(m):
    body = m.group(2)
    for _ in range(3):                        # nested braces need a few passes
        for pat, rep in TEX:
            body = re.sub(pat, rep, body)
    body = re.sub(r'\s{2,}', ' ', body).strip()
    return f'<span class="{m.group(1)}">{body}</span>'
h = re.sub(r'<span class="(math (?:inline|display))">(.*?)</span>', detex, h, flags=re.S)

# Some display math survives as literal $$...$$ because pandoc did not wrap it.
# Catch those too, then run the same conversion.
def detex_raw(m):
    body = m.group(1)
    for _ in range(3):
        for pat, rep in TEX:
            body = re.sub(pat, rep, body)
    body = re.sub(r'\s{2,}', ' ', body).strip()
    return f'<code>{body}</code>'
h = re.sub(r'\$\$(.+?)\$\$', detex_raw, h, flags=re.S)

# ---- 4. cover ----
rounds  = len(set(re.findall(r'ROUND-(\d)', src))) + 1
findings= len(re.findall(r'^### \d+\.', src, re.M))
disputed= len(re.findall(r'`DISPUTED', src))
stamp   = datetime.date.today().isoformat()
cover = f"""<div class="coverpage">
  <div class="cover-eyebrow">Design Review &middot; Peer Resolution</div>
  <h1 class="cover-title">1500W Doublet Tuner<br>Design Review</h1>
  <div class="cover-sub">Four rounds of review between two reviewers, with every
  finding tracked to resolution or dispute.</div>
  <div class="cover-rule"></div>
  <table class="cover-meta">
    <tr><td>Rounds</td><td>{rounds}</td></tr>
    <tr><td>Numbered findings</td><td>{findings}</td></tr>
    <tr><td>Disputed at some point</td><td>{disputed}</td></tr>
    <tr><td>Generated</td><td>{stamp}</td></tr>
    <tr><td>Outcome</td><td>All findings carried into Rev&nbsp;3.4 of the design log</td></tr>
  </table>
  <div class="cover-legend">
    <span class="chip chip-ok">RESOLVED</span>
    <span class="chip chip-mixed">PARTIAL</span>
    <span class="chip chip-bad">DISPUTED</span>
    &nbsp;&nbsp;<span style="border-left:3pt solid #0C6B7A;padding-left:5pt">Claude</span>
    &nbsp;<span style="border-left:3pt solid #4F5B93;padding-left:5pt">Gemini</span>
  </div>
</div>"""
h = h.replace('<h1 class="title">Design Review</h1>', cover, 1)
h = re.sub(r'<h1 (id="[^"]*design-review[^"]*")>.*?</h1>', r'<span \1 class="anchor-only"></span>',
           h, flags=re.S)
io.open(html_path, 'w', encoding='utf-8').write(h)
print(f'  cover: {rounds} rounds, {findings} findings, {disputed} disputed')
