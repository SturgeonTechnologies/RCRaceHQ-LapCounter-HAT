#!/usr/bin/env bash
# Regenerate libraries, schematic and board from design.py, autoroute with
# Freerouting, run ERC/DRC, and write the JLCPCB fabrication files.
#
# Needs: KiCad 9 (kicad-cli + its Python `pcbnew` module) and Java 25+ with
# freerouting.jar. Override paths with JAVA=... FREEROUTING=... if needed.
set -euo pipefail
cd "$(dirname "$0")/.."

JAVA=${JAVA:-java}
FREEROUTING=${FREEROUTING:-freerouting.jar}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

NAME=burst_detector_hat
python3 tools/gen_libs.py
python3 tools/gen_schematic.py
python3 tools/gen_pcb.py

python3 - "$WORK/board.dsn" <<'EOF'
import sys, pcbnew
board = pcbnew.LoadBoard("burst_detector_hat.kicad_pcb")
# Hide the GND pours from Freerouting so it routes GND as real tracks too;
# the pours stay in the saved board and are refilled after import.
for z in list(board.Zones()):
    if not z.GetIsRuleArea():
        board.Remove(z)
assert pcbnew.ExportSpecctraDSN(board, sys.argv[1]), "DSN export failed"
EOF
"$JAVA" -Djava.awt.headless=true -jar "$FREEROUTING" \
  -de "$WORK/board.dsn" -do "$WORK/board.ses" -mp 100 --gui.enabled=false >fab/reports/freerouting.log 2>&1 \
  || { tail -20 fab/reports/freerouting.log; exit 1; }
python3 tools/finish_pcb.py "$WORK/board.ses"

mkdir -p fab/reports
kicad-cli sch erc --severity-error --exit-code-violations -o fab/reports/erc.rpt burst_detector_hat.kicad_sch
kicad-cli pcb drc --severity-error --schematic-parity --exit-code-violations \
  -o fab/reports/drc.rpt burst_detector_hat.kicad_pcb

rm -rf fab/gerbers && mkdir -p fab/gerbers
kicad-cli pcb export gerbers --no-protel-ext \
  --layers F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,Edge.Cuts \
  -o fab/gerbers/ burst_detector_hat.kicad_pcb
kicad-cli pcb export drill --format excellon --excellon-separate-th \
  --generate-map --map-format gerberx2 -o fab/gerbers/ burst_detector_hat.kicad_pcb
python3 - <<'EOF'
import pathlib, zipfile
src = pathlib.Path("fab/gerbers")
with zipfile.ZipFile("fab/burst_detector_hat_gerbers.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(src.iterdir()):
        z.write(f, f.name)
EOF

kicad-cli sch export pdf -o fab/burst_detector_hat_schematic.pdf burst_detector_hat.kicad_sch
kicad-cli pcb export pdf --mode-single --black-and-white \
  --layers Edge.Cuts,F.SilkS,F.Fab,F.Cu -o fab/burst_detector_hat_fitcheck_1to1.pdf burst_detector_hat.kicad_pcb
kicad-cli pcb export svg --mode-single --exclude-drawing-sheet --page-size-mode 2 \
  --layers Edge.Cuts,F.Cu,B.Cu,F.SilkS -o fab/burst_detector_hat_preview.svg burst_detector_hat.kicad_pcb
kicad-cli pcb export pos --format csv --units mm --side front --exclude-dnp \
  -o "$WORK/pos.csv" burst_detector_hat.kicad_pcb
python3 tools/gen_fab.py "$WORK/pos.csv"
echo "done: fab/burst_detector_hat_gerbers.zip + fab/bom_jlcpcb.csv + fab/cpl_jlcpcb.csv"
