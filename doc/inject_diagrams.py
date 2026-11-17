#!/usr/bin/env python3
"""Replace specific ASCII-art <pre> blocks with rendered SVG diagrams.

Matching is by a signature string unique to each block, so the markdown source
keeps its plain-text diagrams (useful in a terminal or a diff) while the PDF
gets proper figures. A signature that stops matching is reported rather than
silently skipped -- otherwise an edit upstream would quietly drop a figure.
"""
import io, re, sys, os

FIGS = [
    # (signature in the <pre> text, svg file, caption, max width in mm)
    ('16.00&quot; WIDTH',        'floorplan.svg',     'Enclosure floorplan, drawn to the Section 3 dimensions.', 150),
    ('SELF-TEST',               'state_machine.svg', 'Firmware state machine. Red transitions reach FAULT; dashed are retries.', 132),
    ('interlock asserts INHIBIT','boot.svg',     'Boot sequence. Latched faults are re-asserted, never cleared by a power cycle.', 120),
    ('AT THE TUNER',            'interlock.svg', 'Amplifier interlock. The permissive is a hardware AND carried on its own fiber strand.', 160),
    ('fwd port',                'counter.svg',   'Frequency counter chain. The ÷1024 prescaler is what lets the count cross the bulkhead.', 170),
    ('single-shaft stepper',    'coupling.svg',  'Stepper coupling train. The encoder reads the G10 shaft by belt; only a shaft crosses the shelf.', 170),
    ('admin changes a setting', 'mirror.svg',    'Write-through mirroring. Internal flash is authoritative; the card is a backup.', 150),
    ('rig PTT out',             'estop.svg',     'Bench emergency stop. It breaks the keying line locally and needs no link to the tuner.', 150),
    ('Teensy 4.1 ]',            'link.svg',      'Bench link. Data over Ethernet; the interlock permissive on its own fiber strand.', 155),
    ('entry panel ]',           'strain.svg',    'Balanced output strain relief. Mechanical load is taken before the ceramic.', 170),
    ('coupler -&gt; pads',      'crossing.svg',  'Only filtered DC crosses the Sampler/Control bulkhead.', 165),
]

def main(path, diagdir='diagrams'):
    h = io.open(path, encoding='utf-8').read()
    hit = miss = 0
    for sig, svg, cap, wmm in FIGS:
        src = os.path.join(diagdir, svg)
        if not os.path.exists(src):
            alt = os.path.join(diagdir, svg.replace('.dot.svg', '.svg'))
            if os.path.exists(alt):
                src = alt
            else:
                print(f'  MISSING {svg}'); miss += 1; continue
        pat = re.compile(r'<pre[^>]*>(?:(?!</pre>).)*?' + re.escape(sig) + r'(?:(?!</pre>).)*?</pre>', re.S)
        fig = (f'<figure class="diagram"><img src="{src}" style="max-width:{wmm}mm"/>'
               f'<figcaption>{cap}</figcaption></figure>')
        h, n = pat.subn(fig, h, count=1)
        if n: hit += 1
        else:
            print(f'  SIGNATURE NOT FOUND: {sig!r} -- figure not inserted'); miss += 1
    io.open(path, 'w', encoding='utf-8').write(h)
    print(f'  diagrams: {hit} inserted, {miss} missed')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'diagrams')
