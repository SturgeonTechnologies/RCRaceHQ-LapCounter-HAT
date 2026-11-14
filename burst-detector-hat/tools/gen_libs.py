"""Write the project-local symbol library (the three ICs as simple boxes).

Every footprint comes from KiCad's stock libraries, so there is no
project-local footprint library.
"""
import pathlib
import uuid

HERE = pathlib.Path(__file__).resolve().parent.parent
PITCH = 2.54


def u():
    return str(uuid.uuid4())


# ---------------------------------------------------------------- symbols ---

def sym_pin(num, name, x, y, angle):
    return (f'      (pin passive line (at {x:.2f} {y:.2f} {angle}) (length 2.54)\n'
            f'        (name "{name}" (effects (font (size 1.27 1.27))))\n'
            f'        (number "{num}" (effects (font (size 1.27 1.27)))))\n')


def box_symbol(name, ref, left, right, width=15.24, desc=""):
    """left/right: lists of (number, name) top to bottom."""
    rows = max(len(left), len(right))
    top = (rows - 1) * PITCH / 2
    h2 = top + PITCH
    w2 = width / 2
    out = [f'  (symbol "{name}" (exclude_from_sim no) (in_bom yes) (on_board yes)\n',
           f'    (property "Reference" "{ref}" (at 0 {h2 + 1.27:.2f} 0) (effects (font (size 1.27 1.27))))\n',
           f'    (property "Value" "{name}" (at 0 {-h2 - 1.27:.2f} 0) (effects (font (size 1.27 1.27))))\n',
           '    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))\n',
           '    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))\n',
           f'    (property "Description" "{desc}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))\n',
           f'    (symbol "{name}_0_1"\n',
           f'      (rectangle (start {-w2:.2f} {h2:.2f}) (end {w2:.2f} {-h2:.2f})\n',
           '        (stroke (width 0.254) (type default)) (fill (type background))))\n',
           f'    (symbol "{name}_1_1"\n']
    for i, (num, pname) in enumerate(left):
        out.append(sym_pin(num, pname, -w2 - 2.54, top - i * PITCH, 0))
    for i, (num, pname) in enumerate(right):
        out.append(sym_pin(num, pname, w2 + 2.54, top - i * PITCH, 180))
    out.append('    )\n  )\n')
    return "".join(out)


def write_symbols():
    ad8307 = box_symbol(
        "AD8307", "U",
        left=[("8", "INP"), ("1", "INM"), ("3", "OFS"), ("7", "INT")],
        right=[("5", "VPS"), ("6", "ENB"), ("4", "OUT"), ("2", "COM")],
        desc="AD8307 500 MHz log amplifier / RSSI detector, SOIC-8")
    lm393 = box_symbol(
        "LM393", "U",
        left=[("3", "+INA"), ("2", "-INA"), ("5", "+INB"), ("6", "-INB")],
        right=[("8", "VCC"), ("1", "OUTA"), ("7", "OUTB"), ("4", "GND")],
        desc="LM393 dual open-collector comparator, both units in one box")
    ads = box_symbol(
        "ADS1115", "U",
        left=[("4", "AIN0"), ("5", "AIN1"), ("6", "AIN2"), ("7", "AIN3"), ("1", "ADDR")],
        right=[("8", "VDD"), ("9", "SDA"), ("10", "SCL"), ("2", "ALERT/RDY"), ("3", "GND")],
        desc="ADS1115 16-bit 4-channel I2C ADC, VSSOP-10")
    text = ('(kicad_symbol_lib (version 20241209) (generator "burst_detector_gen") '
            '(generator_version "9.0")\n' + ad8307 + lm393 + ads + ')\n')
    (HERE / "burst_detector_hat.kicad_sym").write_text(text)


if __name__ == "__main__":
    write_symbols()
    print("symbol library written")
