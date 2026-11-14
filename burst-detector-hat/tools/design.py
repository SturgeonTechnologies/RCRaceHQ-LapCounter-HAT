"""Single source of truth for the burst-detector HAT (lap counter v0 front end).

gen_schematic.py, gen_pcb.py and gen_fab.py all read this file, so the
schematic, the board and the JLCPCB BOM can't drift apart. Coordinates are
millimetres; the board origin is the top-left corner of the HAT outline with
the 40-pin header along the top edge, x to the right, y down (same view as
the Raspberry Pi 4 mechanical drawing).

Signal chain:
  loop -> balun -> J1 (SMA) -> TVS -> resistive splitter -+-> J2 (SMA) -> RTL-SDR
                                                          +-> 3 MHz HPF -> 8 MHz LPF
      -> 52.3R termination -> AD8307 log detector -> RSSI -+-> ADS1115 AIN0 (I2C)
                                                          +-> LM393 comparator -> GPIO17
  Threshold trimmer RV1 -> comparator and ADS1115 AIN1. Second comparator drives
  a "burst" LED.
"""

PROJECT = "burst_detector_hat"
LIB = PROJECT

# Raspberry Pi HAT outline (Pi 4 mechanical drawing / HAT spec).
BOARD_W = 65.0
BOARD_H = 56.5
CORNER_R = 3.0
HOLES = [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]

# Pi 4 40-pin header: centred on x = 32.5, 3.5 mm from the top edge.
GPIO_PIN1 = (32.5 - 9.5 * 2.54, 3.5 + 1.27)       # odd row is the inner row
# Pi 4 4-pin PoE header (J14): under the top-right hole, 6.14 mm lower.
POE_CENTRE = (61.5, 3.5 + 6.14)
POE_KEEPOUT = (56.4, 6.0, 65.0, 13.4)               # x1, y1, x2, y2: no copper

R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
L1206 = "Inductor_SMD:L_1206_3216Metric"


def r(value, lcsc, pcb, sch):
    return dict(sym="Device:R", fp=R0603, value=value, lcsc=lcsc, pcb=pcb, sch=sch)


def c(value, lcsc, pcb, sch, fp=C0603):
    return dict(sym="Device:C", fp=fp, value=value, lcsc=lcsc, pcb=pcb, sch=sch)


# ref: symbol, footprint, value, LCSC part (None = not assembled), PCB (x, y, rot), schematic (x, y)
PARTS = {
    # --- connectors (hand-solder or JLC through-hole assembly) -------------
    "J1": dict(sym="Connector:Conn_Coaxial", fp="Connector_Coaxial:SMA_Amphenol_132289_EdgeMount",
               value="LOOP IN", lcsc="C3172723", pcb=(3.0, 21.0, 180), sch=(25.4, 50.8)),
    "J2": dict(sym="Connector:Conn_Coaxial", fp="Connector_Coaxial:SMA_Amphenol_132289_EdgeMount",
               value="TO SDR", lcsc="C3172723", pcb=(3.0, 40.0, 180), sch=(25.4, 88.9)),
    "J3": dict(sym="Connector_Generic:Conn_02x20_Odd_Even",
               fp="Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical",
               value="Pi GPIO (2x20 stacking)", lcsc=None,
               pcb=(GPIO_PIN1[0], GPIO_PIN1[1], 90), sch=(228.6, 76.2)),
    "J4": dict(sym="Connector_Generic:Conn_02x02_Odd_Even",
               fp="Connector_PinHeader_2.54mm:PinHeader_2x02_P2.54mm_Vertical",
               value="PoE pass-through (not connected)", lcsc=None,
               pcb=(POE_CENTRE[0] - 1.27, POE_CENTRE[1] - 1.27, 0), sch=(228.6, 139.7)),

    # --- input protection + splitter ---------------------------------------
    "D2": dict(sym="Device:D_TVS", fp="Diode_SMD:D_SOD-323", value="PESD5V0S1BA",
               lcsc="C19224", pcb=(9.5, 15.5, 90), sch=(45.72, 58.42)),
    "R10": r("16.5", "C12054", (10.0, 21.0, 0), (55.88, 50.8)),
    "R11": r("16.5", "C12054", (12.5, 30.0, 90), (66.04, 66.04)),
    "R12": r("16.5", "C12054", (16.0, 25.0, 0), (76.2, 50.8)),

    # --- 3 MHz high-pass (T) + 8 MHz low-pass (pi), 50 ohm -----------------
    "C10": c("1n C0G", "C1636", (20.0, 25.0, 0), (91.44, 50.8)),
    "L10": dict(sym="Device:L", fp=L1206, value="1.5u", lcsc="C2885920",
                pcb=(23.0, 29.0, 90), sch=(101.6, 60.96)),
    "C11": c("1n C0G", "C1636", (26.0, 25.0, 0), (111.76, 50.8)),
    "C12": c("390p C0G", "C1667", (29.0, 29.0, 90), (121.92, 60.96)),
    "L11": dict(sym="Device:L", fp=L1206, value="2.2u", lcsc="C1048",
                pcb=(32.5, 25.0, 0), sch=(132.08, 50.8)),
    "C13": c("390p C0G", "C1667", (36.0, 29.0, 90), (142.24, 60.96)),
    "R13": r("52.3", "C81321", (38.5, 29.0, 90), (152.4, 60.96)),

    # --- AD8307 log detector ------------------------------------------------
    "C2": c("10n", "C1589", (41.0, 25.0, 0), (162.56, 50.8)),
    "C3": c("10n", "C1589", (41.0, 31.5, 0), (162.56, 76.2)),
    "U1": dict(sym=f"{LIB}:AD8307", fp="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
               value="AD8307ARZ", lcsc="C495272", pcb=(47.0, 28.0, 0), sch=(76.2, 127.0)),
    "R20": r("10", "C22859", (47.0, 20.5, 0), (25.4, 165.1)),
    "C20": c("100n", "C1591", (52.0, 22.5, 90), (38.1, 172.72)),
    "C21": c("10u", "C15850", (54.5, 22.5, 90), (50.8, 172.72), fp=C0805),
    "C22": c("1n", "C1636", (44.0, 34.0, 90), (55.88, 142.24)),
    "C23": c("470p C0G", "C36252", (51.5, 32.5, 90), (101.6, 142.24)),

    # --- comparator, threshold, LED -----------------------------------------
    "U2": dict(sym=f"{LIB}:LM393", fp="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
               value="LM393DR2G", lcsc="C7955", pcb=(47.0, 42.0, 0), sch=(152.4, 127.0)),
    "C30": c("100n", "C1591", (52.0, 38.0, 90), (63.5, 172.72)),
    "R3": r("10k", "C25804", (41.0, 38.5, 0), (124.46, 116.84)),
    "R4": r("1M", "C22935", (41.0, 42.0, 0), (175.26, 104.14)),
    "R5": r("10k", "C25804", (53.0, 45.0, 90), (187.96, 116.84)),
    "R6": r("10k", "C25804", (55.5, 45.0, 90), (124.46, 144.78)),
    "R7": r("10k", "C25804", (58.0, 45.0, 90), (124.46, 160.02)),
    "R8": r("1k", "C21190", (55.5, 50.0, 0), (187.96, 144.78)),
    "D1": dict(sym="Device:LED", fp="LED_SMD:LED_0603_1608Metric", value="BURST (green)",
               lcsc="C12624", pcb=(55.5, 53.5, 180), sch=(187.96, 157.48)),
    "RV1": dict(sym="Device:R_Potentiometer_Trim", fp="Potentiometer_SMD:Potentiometer_Bourns_TC33X_Vertical",
                value="10k THRESHOLD", lcsc="C719176", pcb=(38.0, 47.5, 0), sch=(101.6, 101.6)),
    "C31": c("100n", "C1591", (33.5, 47.5, 90), (76.2, 172.72)),

    # --- ADS1115 RSSI/threshold ADC -----------------------------------------
    "U3": dict(sym=f"{LIB}:ADS1115", fp="Package_SO:MSOP-10_3x3mm_P0.5mm",
               value="ADS1115IDGSR", lcsc="C37593", pcb=(24.0, 42.0, 0), sch=(76.2, 88.9)),
    "C40": c("100n", "C1591", (29.2, 42.0, 0), (88.9, 172.72)),   # right beside VDD (pin 8)

    # --- test points ------------------------------------------------------
    "TP1": dict(sym="Connector:TestPoint", fp="TestPoint:TestPoint_Pad_D1.5mm", value="RSSI",
                lcsc=None, pcb=(17.0, 50.0, 0), sch=(203.2, 165.1)),
    "TP2": dict(sym="Connector:TestPoint", fp="TestPoint:TestPoint_Pad_D1.5mm", value="THRESH",
                lcsc=None, pcb=(21.0, 50.0, 0), sch=(213.36, 165.1)),
    "TP3": dict(sym="Connector:TestPoint", fp="TestPoint:TestPoint_Pad_D1.5mm", value="BURST",
                lcsc=None, pcb=(25.0, 50.0, 0), sch=(223.52, 165.1)),
    "TP4": dict(sym="Connector:TestPoint", fp="TestPoint:TestPoint_Pad_D1.5mm", value="GND",
                lcsc=None, pcb=(29.0, 50.0, 0), sch=(233.68, 165.1)),
}

for i, (hx, hy) in enumerate(HOLES, start=1):
    PARTS[f"H{i}"] = dict(sym="Mechanical:MountingHole", fp="MountingHole:MountingHole_2.7mm_M2.5",
                          value="M2.5", lcsc=None, pcb=(hx, hy, 0), sch=(241.3 + 8.89 * i, 165.1))

GPIO_GND = ["6", "9", "14", "20", "25", "30", "34", "39"]

# net: [(ref, pad), ...]
NETS = {
    "GND": [("J3", p) for p in GPIO_GND] + [
        ("J1", "2"), ("J2", "2"), ("D2", "2"), ("L10", "2"), ("C12", "2"), ("C13", "2"),
        ("R13", "2"), ("C3", "2"), ("U1", "2"), ("C20", "2"), ("C21", "2"), ("C22", "2"),
        ("C23", "2"), ("U2", "4"), ("C30", "2"), ("RV1", "1"), ("R7", "2"), ("U3", "1"),
        ("U3", "3"), ("C40", "2"), ("C31", "2"), ("TP4", "1")],
    "+5V": [("J3", "2"), ("J3", "4"), ("R20", "1"), ("U2", "8"), ("C30", "1")],
    "+5V_A": [("R20", "2"), ("U1", "5"), ("U1", "6"), ("C20", "1"), ("C21", "1")],
    "+3V3": [("J3", "1"), ("J3", "17"), ("R5", "1"), ("R6", "1"), ("R8", "1"),
             ("RV1", "3"), ("U3", "8"), ("C40", "1")],
    "LOOP": [("J1", "1"), ("D2", "1"), ("R10", "1")],
    "SPLIT": [("R10", "2"), ("R11", "1"), ("R12", "1")],
    "SDR": [("R11", "2"), ("J2", "1")],
    "RF_A": [("R12", "2"), ("C10", "1")],
    "HP1": [("C10", "2"), ("L10", "1"), ("C11", "1")],
    "HP2": [("C11", "2"), ("C12", "1"), ("L11", "1")],
    "RF_F": [("L11", "2"), ("C13", "1"), ("R13", "1"), ("C2", "1")],
    "INP": [("C2", "2"), ("U1", "8")],
    "INM": [("C3", "1"), ("U1", "1")],
    "OFS": [("U1", "3"), ("C22", "1")],
    "RSSI": [("U1", "4"), ("C23", "1"), ("R3", "1"), ("U3", "4"), ("TP1", "1")],
    "CMP_P": [("R3", "2"), ("R4", "1"), ("U2", "3")],
    "THRESH": [("RV1", "2"), ("C31", "1"), ("U2", "2"), ("U3", "5"), ("TP2", "1")],
    "BURST": [("U2", "1"), ("R4", "2"), ("R5", "2"), ("U2", "6"), ("J3", "11"), ("TP3", "1")],
    "REF_B": [("R6", "2"), ("R7", "1"), ("U2", "5")],
    "LED_K": [("U2", "7"), ("D1", "1")],
    "LED_A": [("R8", "2"), ("D1", "2")],
    "SDA": [("U3", "9"), ("J3", "3")],
    "SCL": [("U3", "10"), ("J3", "5")],
}

_used_gpio = {p for n in NETS.values() for ref, p in n if ref == "J3"}
# ALERT/RDY (U3.2) is left open: the Pi polls the ADC over I2C instead.
NO_CONNECT = ([("U1", "7"), ("U3", "2"), ("U3", "6"), ("U3", "7")]
              + [("J3", str(p)) for p in range(1, 41) if str(p) not in _used_gpio]
              + [("J4", str(p)) for p in range(1, 5)])

# +3V3 only feeds pull-ups, the trimmer and the ADC (<2 mA), so it routes
# as a normal signal; only the 5 V rails get the wide Power class.
POWER_NETS = {"+5V", "+5V_A"}

# Short tracks laid down before autorouting, where Freerouting kept boxing
# itself in: (net, layer, [(x, y), ...]).
PRE_ROUTES = [
    ("+3V3", "F.Cu", [(26.1125, 42.0), (28.425, 42.0)]),             # U3 VDD -> C40
    ("+3V3", "F.Cu", [(53.0, 45.825), (55.5, 45.825)]),              # R5 -> R6
    ("+3V3", "F.Cu", [(55.5, 45.825), (54.675, 46.65), (54.675, 50.0)]),  # R6 -> R8
]
