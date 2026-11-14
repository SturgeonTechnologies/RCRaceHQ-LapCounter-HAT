"""Import a Freerouting session into the board and refill the GND pours.

Usage: python3 tools/finish_pcb.py <routed.ses>
"""
import pathlib
import sys

import pcbnew

from design import PROJECT

PCB = pathlib.Path(__file__).resolve().parent.parent / f"{PROJECT}.kicad_pcb"


def main(ses):
    board = pcbnew.LoadBoard(str(PCB))
    if not pcbnew.ImportSpecctraSES(board, ses):
        raise SystemExit(f"could not import {ses}")
    # Freerouting necks tracks down to 0.125 mm at fine-pitch pads; JLCPCB's
    # 2-layer minimum is 0.127 mm, so widen those stubs back to 0.15 mm.
    for t in board.GetTracks():
        if t.GetClass() == "PCB_TRACK" and t.GetWidth() < pcbnew.FromMM(0.15):
            t.SetWidth(pcbnew.FromMM(0.15))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(str(PCB))
    tracks = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"]
    vias = [t for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]
    print(f"imported {len(tracks)} tracks, {len(vias)} vias; zones filled")


if __name__ == "__main__":
    main(sys.argv[1])
