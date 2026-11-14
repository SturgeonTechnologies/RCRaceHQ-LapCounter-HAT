"""Generate burst_detector_hat.kicad_pcb (unrouted) from design.py.

Places every footprint, assigns nets, draws the outline and a GND pour on both
layers, and sets JLCPCB-safe design rules. Routing is done afterwards by
route.sh (Freerouting via Specctra DSN/SES).

Run with KiCad's Python (see README for the env), from this directory:
    python3 tools/gen_pcb.py
"""
import os
import pathlib

import pcbnew

from design import (BOARD_H, BOARD_W, CORNER_R, NETS, PARTS, POE_KEEPOUT,
                    POWER_NETS, PRE_ROUTES, PROJECT)

HERE = pathlib.Path(__file__).resolve().parent.parent
FPDIR = pathlib.Path(os.environ.get("KICAD9_FOOTPRINT_DIR", "/usr/share/kicad/footprints"))
OUT = HERE / f"{PROJECT}.kicad_pcb"
MM = pcbnew.FromMM

POWER = POWER_NETS

FINE_PITCH = {"U3"}

# Front silkscreen labels: (text, x, y).
SILK_LABELS = [
    ("LOOP IN", 7.5, 27.6),
    ("TO SDR", 7.5, 46.6),
    ("THRESHOLD", 38.0, 51.6),
    ("BURST", 51.0, 53.6),
    ("RSSI THR BRST GND", 23.0, 52.4),
    ("PoE", 61.5, 14.4),
]


def lib_path(lib):
    return str(FPDIR / f"{lib}.pretty")


def outline(board, w, h, r=2.0):
    """Rounded-rectangle outline on Edge.Cuts."""
    def seg(a, b):
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
        s.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(MM(0.1))
        board.Add(s)

    def arc(c, start, angle):
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
        s.SetCenter(pcbnew.VECTOR2I(MM(c[0]), MM(c[1])))
        s.SetStart(pcbnew.VECTOR2I(MM(start[0]), MM(start[1])))
        s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(MM(0.1))
        board.Add(s)

    seg((r, 0), (w - r, 0))
    seg((w, r), (w, h - r))
    seg((w - r, h), (r, h))
    seg((0, h - r), (0, r))
    arc((w - r, r), (w - r, 0), 90)
    arc((w - r, h - r), (w, h - r), 90)
    arc((r, h - r), (r, h), 90)
    arc((r, r), (0, r), 90)


def gnd_zone(board, net, layer):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(net)
    z.SetLocalClearance(MM(0.3))
    z.SetMinThickness(MM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.3))
    z.SetThermalReliefSpokeWidth(MM(0.5))
    poly = z.Outline()
    poly.NewOutline()
    for x, y in [(0, 0), (BOARD_W, 0), (BOARD_W, BOARD_H), (0, BOARD_H)]:
        poly.Append(MM(x), MM(y))
    board.Add(z)


def edge_keepouts(board, margin=0.8):
    """Track/via keepout strips along each edge.

    Freerouting doesn't apply KiCad's copper-to-edge clearance, so without
    these it happily runs tracks 0.36 mm from the outline.
    """
    w, h, m = BOARD_W, BOARD_H, margin
    for x0, y0, x1, y1 in [(0, 0, w, m), (0, h - m, w, h), (0, 0, m, h), (w - m, 0, w, h)]:
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowCopperPour(False)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        z.SetLayerSet(pcbnew.LSET.AllCuMask())
        poly = z.Outline()
        poly.NewOutline()
        for x, y in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
            poly.Append(MM(x), MM(y))
        board.Add(z)


def poe_keepout(board):
    """No copper near the Pi's PoE pins: they carry the raw ~48 V PoE pairs."""
    x0, y0, x1, y1 = POE_KEEPOUT
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowCopperPour(True)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    z.SetLayerSet(pcbnew.LSET.AllCuMask())
    poly = z.Outline()
    poly.NewOutline()
    for x, y in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
        poly.Append(MM(x), MM(y))
    board.Add(z)


def rules(board):
    ds = board.GetDesignSettings()
    # JLCPCB 2-layer standard capability, with margin.
    ds.m_MinClearance = MM(0.13)   # floor for the MSOP pads; netclasses keep 0.2+
    ds.m_TrackMinWidth = MM(0.15)
    ds.m_ViasMinSize = MM(0.6)
    ds.m_MinThroughDrill = MM(0.3)
    ds.m_CopperEdgeClearance = MM(0.4)
    ds.SetBoardThickness(MM(1.6))
    # Every GND pad is also tied in with a routed track, so one thermal spoke
    # into the pour is enough (the header rows near the edge can't fit two).
    ds.m_MinResolvedSpokes = 1

    nc = ds.m_NetSettings
    default = nc.GetDefaultNetclass()
    default.SetClearance(MM(0.2))
    default.SetTrackWidth(MM(0.25))
    default.SetViaDiameter(MM(0.8))
    default.SetViaDrill(MM(0.4))

    power = pcbnew.NETCLASS("Power")
    power.SetClearance(MM(0.25))
    power.SetTrackWidth(MM(0.4))
    power.SetViaDiameter(MM(0.9))
    power.SetViaDrill(MM(0.5))
    nc.SetNetclass("Power", power)
    for name in POWER:
        nc.SetNetclassPatternAssignment(name, "Power")


def main():
    board = pcbnew.NewBoard(str(OUT))
    rules(board)

    nets = {}
    for name in NETS:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
        nets[name] = n
    pad_net = {(ref, pad): name for name, pins in NETS.items() for ref, pad in pins}

    for ref, p in PARTS.items():
        lib, name = p["fp"].split(":")
        fp = pcbnew.FootprintLoad(lib_path(lib), name)
        if fp is None:
            raise SystemExit(f"footprint {p['fp']} not found")
        fp.SetReference(ref)
        fp.SetValue(p["value"])
        x, y, rot = p["pcb"]
        fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        fp.SetOrientationDegrees(rot)
        if ref.startswith("H"):
            fp.Reference().SetVisible(False)
        if ref in FINE_PITCH:
            # 0.5 mm pitch MSOP: pads sit 0.15 mm apart (JLCPCB minimum is 0.1 mm).
            fp.SetLocalClearance(MM(0.1))
        board.Add(fp)
        for pad in fp.Pads():
            net = pad_net.get((ref, pad.GetNumber()))
            if net:
                pad.SetNet(nets[net])

    for net, layer, pts in PRE_ROUTES:
        for a, b in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
            t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
            t.SetWidth(MM(0.25))
            t.SetLayer(board.GetLayerID(layer))
            t.SetNet(nets[net])
            board.Add(t)

    outline(board, BOARD_W, BOARD_H, CORNER_R)
    edge_keepouts(board)
    poe_keepout(board)
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        gnd_zone(board, nets["GND"], layer)

    txt = pcbnew.PCB_TEXT(board)
    txt.SetText("RC Race HQ lap counter - burst detector HAT v0")
    txt.SetLayer(pcbnew.B_SilkS)
    txt.SetMirrored(True)
    txt.SetTextSize(pcbnew.VECTOR2I(MM(1.0), MM(1.0)))
    txt.SetPosition(pcbnew.VECTOR2I(MM(BOARD_W / 2), MM(BOARD_H - 3.0)))
    board.Add(txt)

    for s, x, y in SILK_LABELS:
        lbl = pcbnew.PCB_TEXT(board)
        lbl.SetText(s)
        lbl.SetLayer(pcbnew.F_SilkS)
        lbl.SetTextSize(pcbnew.VECTOR2I(MM(1.0), MM(1.0)))
        lbl.SetTextThickness(MM(0.15))
        lbl.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        board.Add(lbl)

    board.Save(str(OUT))
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
