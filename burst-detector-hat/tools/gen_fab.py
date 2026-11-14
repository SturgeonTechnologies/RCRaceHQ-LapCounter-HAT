"""Write the JLCPCB assembly BOM and placement (CPL) files.

Usage: python3 tools/gen_fab.py <kicad-pos.csv>

Only parts with an LCSC number in design.py are assembled. Headers, test
points and mounting holes are left out (hand-soldered / not parts).
"""
import collections
import csv
import pathlib
import sys

from design import PARTS

FAB = pathlib.Path(__file__).resolve().parent.parent / "fab"


def main(pos_csv):
    assembled = {ref: p for ref, p in PARTS.items() if p.get("lcsc")}

    groups = collections.OrderedDict()
    for ref, p in assembled.items():
        key = (p["value"], p["fp"].split(":")[1], p["lcsc"])
        groups.setdefault(key, []).append(ref)
    with open(FAB / "bom_jlcpcb.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for (value, fp, lcsc), refs in groups.items():
            w.writerow([value, ",".join(refs), fp, lcsc])

    rows = []
    with open(pos_csv) as f:
        for r in csv.DictReader(f):
            if r["Ref"] in assembled:
                rows.append([r["Ref"], f'{float(r["PosX"]):.3f}mm', f'{float(r["PosY"]):.3f}mm',
                             "Top", f'{float(r["Rot"]) % 360:.0f}'])
    missing = set(assembled) - {r[0] for r in rows}
    if missing:
        raise SystemExit(f"no placement for {sorted(missing)}")
    with open(FAB / "cpl_jlcpcb.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        w.writerows(sorted(rows, key=lambda r: r[0]))
    print(f"BOM: {len(groups)} lines, CPL: {len(rows)} parts")


if __name__ == "__main__":
    main(sys.argv[1])
