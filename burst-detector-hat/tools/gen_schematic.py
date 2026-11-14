"""Generate burst_detector_hat.kicad_sch from design.py.

Every connected pin gets a short wire stub ending in a net label, so the
schematic reads as a net list rather than a wiring diagram. Unused pins get a
no-connect flag so ERC stays clean.
"""
import os
import pathlib
import re
import uuid

from design import NETS, NO_CONNECT, PARTS, PROJECT

HERE = pathlib.Path(__file__).resolve().parent.parent
SYMDIR = pathlib.Path(os.environ.get("KICAD9_SYMBOL_DIR", "/usr/share/kicad/symbols"))
ROOT = str(uuid.uuid5(uuid.NAMESPACE_URL, "sturgeon/burst-detector-hat/root"))


def uid(*parts):
    # Stable UUIDs keep regenerated files diff-friendly.
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "sturgeon/burst-detector-hat/" + "/".join(parts)))


# ------------------------------------------------------- tiny s-expr parser --

TOKEN = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')


def parse(text):
    stack, cur = [], []
    for m in TOKEN.finditer(text):
        t = m.group(0)
        if t == "(":
            stack.append(cur)
            cur = []
        elif t == ")":
            done, cur = cur, stack.pop()
            cur.append(done)
        else:
            cur.append(t)
    return cur[0]


def dump(node, indent=0):
    if not isinstance(node, list):
        return node
    pad = "  " * indent
    simple = all(not isinstance(c, list) for c in node)
    if simple:
        return "(" + " ".join(node) + ")"
    parts = [c for c in node if not isinstance(c, list)]
    kids = [c for c in node if isinstance(c, list)]
    s = "(" + " ".join(parts)
    for k in kids:
        s += "\n" + pad + "  " + dump(k, indent + 1)
    return s + ")"


def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def unq(s):
    return s[1:-1] if s.startswith('"') else s


_libs = {}


def lib_symbol(lib_id):
    lib, name = lib_id.split(":")
    if lib not in _libs:
        path = HERE / f"{lib}.kicad_sym" if lib == PROJECT else SYMDIR / f"{lib}.kicad_sym"
        _libs[lib] = {unq(s[1]): s for s in find(parse(path.read_text()), "symbol")}
    sym = [list(x) if isinstance(x, list) else x for x in _libs[lib][name]]
    if find(sym, "extends"):
        raise SystemExit(f"{lib_id} uses extends; pick a base symbol")
    sym[1] = f'"{lib_id}"'
    return sym


def pins_of(sym):
    """{number: (x, y, angle)} in symbol coordinates (y up)."""
    out = {}

    def walk(n):
        for c in n:
            if isinstance(c, list):
                if c and c[0] == "pin":
                    at = find(c, "at")[0]
                    num = unq(find(c, "number")[0][1])
                    out[num] = (float(at[1]), float(at[2]), int(float(at[3])))
                else:
                    walk(c)
    walk(sym)
    return out


# ---------------------------------------------------------------- emitters --

def prop(name, value, x, y, hide=False, justify=None):
    h = " (hide yes)" if hide else ""
    j = f" (justify {justify})" if justify else ""
    return (f'    (property "{name}" "{value}" (at {x:.2f} {y:.2f} 0)\n'
            f'      (effects (font (size 1.27 1.27)){j}{h}))\n')


def symbol_instance(ref, part, pins):
    x, y = part["sch"]
    s = [f'  (symbol (lib_id "{part["sym"]}") (at {x:.2f} {y:.2f} 0) (unit 1)\n'
         f'    (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)\n'
         f'    (uuid "{uid("sym", ref)}")\n']
    top = max([p[1] for p in pins.values()] + [2.54])
    s.append(prop("Reference", ref, x + 2.54, y - top - 3.81, justify="left"))
    s.append(prop("Value", part["value"], x + 2.54, y - top - 1.27, justify="left"))
    s.append(prop("Footprint", part["fp"], x, y, hide=True))
    s.append(prop("Datasheet", "", x, y, hide=True))
    if part.get("lcsc"):
        s.append(prop("LCSC", part["lcsc"], x, y, hide=True))
    for num in sorted(pins):
        s.append(f'    (pin "{num}" (uuid "{uid("pin", ref, num)}"))\n')
    s.append(f'    (instances (project "{PROJECT}" (path "/{ROOT}" '
             f'(reference "{ref}") (unit 1))))\n  )\n')
    return "".join(s)


def main():
    pad_net = {(r, p): n for n, members in NETS.items() for r, p in members}
    nc = set(NO_CONNECT)
    lib_syms, body = {}, []

    for ref, part in PARTS.items():
        sym = lib_symbol(part["sym"])
        lib_syms[part["sym"]] = sym
        pins = pins_of(sym)
        body.append(symbol_instance(ref, part, pins))
        sx, sy = part["sch"]
        for num, (px, py, ang) in pins.items():
            x, y = sx + px, sy - py               # schematic y points down
            if (ref, num) in nc:
                body.append(f'  (no_connect (at {x:.2f} {y:.2f}) (uuid "{uid("nc", ref, num)}"))\n')
                continue
            net = pad_net.get((ref, num))
            if net is None:
                raise SystemExit(f"{ref}.{num} is neither on a net nor marked no-connect")
            # Stub runs away from the body: opposite to the pin's direction.
            dx, dy = {0: (-1, 0), 90: (0, 1), 180: (1, 0), 270: (0, -1)}[ang]
            ex, ey = x + dx * 5.08, y + dy * 5.08
            body.append(f'  (wire (pts (xy {x:.2f} {y:.2f}) (xy {ex:.2f} {ey:.2f}))\n'
                        f'    (stroke (width 0) (type default)) (uuid "{uid("w", ref, num)}"))\n')
            angle, just = {(-1, 0): (180, "right"), (1, 0): (0, "left"),
                           (0, -1): (90, "left"), (0, 1): (270, "right")}[(dx, dy)]
            body.append(f'  (label "{net}" (at {ex:.2f} {ey:.2f} {angle})\n'
                        f'    (effects (font (size 1.27 1.27)) (justify {just}))\n'
                        f'    (uuid "{uid("lbl", ref, num)}"))\n')

    notes = [
        (20.32, 20.32, "Burst-detector HAT v0 (lap counter): loop -> splitter -> SDR + 3-8 MHz band-pass -> AD8307 RSSI -> LM393 -> GPIO17"),
        (20.32, 25.4, "J1 takes the loop's 1:9 balun coax. Resistive splitter (3x 16.5R) sends -6 dB to J2 (RTL-SDR) and -6 dB to the detector."),
        (20.32, 30.48, "Filter: 3 MHz T high-pass (1n/1.5u/1n) + 8 MHz pi low-pass (390p/2.2u/390p), 50 ohm; 52.3R terminates into the AD8307."),
        (20.32, 35.56, "RSSI = AD8307 OUT (25 mV/dB). RV1 sets THRESH (0-3.3 V). BURST is open-collector, pulled to 3.3 V: safe for Pi GPIO."),
        (20.32, 40.64, "ADS1115 at I2C 0x48 (ADDR=GND): AIN0 = RSSI, AIN1 = THRESH, ALERT/RDY -> GPIO27. J4 = PoE pins, pass-through only."),
    ]
    for i, (x, y, t) in enumerate(notes):
        body.append(f'  (text "{t}" (exclude_from_sim no) (at {x:.2f} {y:.2f} 0)\n'
                    f'    (effects (font (size 1.524 1.524)) (justify left))\n'
                    f'    (uuid "{uid("note", str(i))}"))\n')

    libs = "\n".join("    " + dump(s, 2) for s in lib_syms.values())
    out = (f'(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0")\n'
           f'  (uuid "{ROOT}")\n  (paper "A4")\n'
           f'  (title_block (title "Lap counter burst-detector HAT") (rev "1.0") '
           f'(company "Sturgeon Technologies") (comment 1 "Generated by tools/gen_schematic.py"))\n'
           f'  (lib_symbols\n{libs}\n  )\n'
           + "".join(body) +
           '  (sheet_instances (path "/" (page "1")))\n  (embedded_fonts no)\n)\n')
    (HERE / f"{PROJECT}.kicad_sch").write_text(out)
    print("schematic written")


if __name__ == "__main__":
    main()
