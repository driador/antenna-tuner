#!/usr/bin/env python3
"""Insert a title page ahead of the TOC and suppress the duplicated body H1."""
import io, re, sys, datetime, os

html_path, src_path = sys.argv[1], sys.argv[2]
h = io.open(html_path, encoding='utf-8').read()
src = io.open(src_path, encoding='utf-8').read()

# figures lifted from the document so the cover cannot drift from the content
def grab(pat, default='—'):
    m = re.search(pat, src, re.M)
    return m.group(1) if m else default
rev   = grab(r'^### Revision ([0-9.]+[a-z]?)', 'Rev')
stamp = datetime.date.today().isoformat()
secs  = len(re.findall(r'^## Section', src, re.M))
words = len(src.split())
open_items = len(re.findall(r'\|\s*\*\*OPEN', src))

cover = f"""<div class="coverpage">
  <div class="cover-eyebrow">Design Log</div>
  <h1 class="cover-title">1500W Automated<br>Antenna Tuner</h1>
  <div class="cover-sub">170&nbsp;ft doublet &middot; 600&nbsp;&#937; ladder line &middot; inverted-V, NVIS</div>
  <div class="cover-rule"></div>
  <table class="cover-meta">
    <tr><td>Revision</td><td>{rev}</td></tr>
    <tr><td>Generated</td><td>{stamp}</td></tr>
    <tr><td>Sections</td><td>{secs}</td></tr>
    <tr><td>Open items</td><td>{open_items}</td></tr>
    <tr><td>Stress basis</td><td>Real NEC-2 simulation, 1200 segments, 27 band-edge points</td></tr>
    <tr><td>Design envelope</td><td>4,191&nbsp;V peak &middot; ~14&nbsp;A RMS &middot; both limits on 160&nbsp;m</td></tr>
  </table>
</div>
"""
h = h.replace('<h1 class="title">1500W Automated Antenna Tuner</h1>', cover, 1)
# The markdown's own H1 repeats the cover. Replace it with an empty anchor
# rather than deleting it -- the TOC still targets that id for its page number.
h = re.sub(r'<h1 (id="1500w-automated-antenna-tuner--design-log")>.*?</h1>',
           r'<span \1 class="anchor-only"></span>', h, flags=re.S)
io.open(html_path, 'w', encoding='utf-8').write(h)
print(f'  cover inserted: {rev}, {secs} sections, {open_items} open items')
