#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Reuben A. Popp
# SPDX-License-Identifier: CERN-OHL-W-2.0

"""The notice on each board's back silkscreen: the author, CERN-OHL-W v2 and its Source Location (§4.1).

post_route.py adds it to every routed board. `python3 notice.py <board>` adds it to a routed board
without routing it again.
"""
import sys
import pcbnew

MM = pcbnew.FromMM
URL = 'github.com/driador/antenna-tuner'
TEXT = f'R. A. Popp, KF0OWR\nCERN-OHL-W-2.0\n{URL}'
# text center (board mm) along the bottom edge, where no pad, hole or via comes within 11 mm
AT = {'control': (124.0, 86.6), 'measurement': (66.0, 69.6)}


def add(b, board):
    for d in list(b.GetDrawings()):         # an earlier notice is replaced, never doubled
        if d.Type() == pcbnew.PCB_TEXT_T and URL in d.GetText():
            b.Remove(d)
    t = pcbnew.PCB_TEXT(b)
    t.SetText(TEXT)
    t.SetLayer(pcbnew.B_SilkS)
    t.SetMirrored(True)                     # reads the right way round from the back
    t.SetTextSize(pcbnew.VECTOR2I(MM(1.0), MM(1.0)))
    t.SetTextThickness(MM(0.15))
    t.SetPosition(pcbnew.VECTOR2I(MM(AT[board][0]), MM(AT[board][1])))
    b.Add(t)


if __name__ == '__main__':
    B = sys.argv[1]
    brd = pcbnew.LoadBoard(f'{B}.kicad_pcb')
    add(brd, B)
    pcbnew.SaveBoard(f'{B}.kicad_pcb', brd)
