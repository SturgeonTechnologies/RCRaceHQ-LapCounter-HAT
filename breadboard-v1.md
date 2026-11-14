# Lap counter loop front-end HAT v1 — breadboard build

The daughter board that sits between the track loop and the RTL-SDR on a Pi 4.
It filters and amplifies the loop signal for the SDR, and it also detects
transponder bursts by itself and flags them on a GPIO pin.

Generated from the v1 design script (KiCad files for v1 will be added to this repo when the board is laid out).
That script's netlist check passes, so the hole list in section 6 matches the
schematic. **Nothing here has been built or tested yet.** Treat it as prototype 1.

- [1. What it does](#1-what-it-does)
- [2. Parts list (tick what you have)](#2-parts-list-tick-what-you-have)
- [3. Pi header pins](#3-pi-header-pins)
- [4. Schematic (ASCII)](#4-schematic-ascii)
- [5. Breadboard map](#5-breadboard-map)
- [6. Hole-by-hole placement, in build order](#6-hole-by-hole-placement-in-build-order)
- [7. Test after each stage](#7-test-after-each-stage)
- [8. On the PCB only (not on the breadboard)](#8-on-the-pcb-only-not-on-the-breadboard)

---

## 1. What it does

```
 track loop ─ balun ─ coax
                       │
                       ▼
 J1 LOOP IN ─► D3/D4 clamp ─► 3–8 MHz band-pass ─► U4 LMH6624 amp (+21 dB)
                                                          │
                                                  R19 49.9 Ω back-term
                                                          │
                                         3-way splitter (R10/R11/R12)
                                     ┌────────────────────┴──────────────┐
                                     ▼                                   ▼
                          J2 TO SDR ─► RTL-SDR (USB)          U1 AD8307 log detector
                          (about +9 dB vs. coax                     │ RSSI (25 mV/dB)
                           straight into the SDR)            ┌──────┴────────┐
                                                             ▼               ▼
                                                    U2A LM393 compare   U3 ADS1115 A0
                                                    vs. RV1 threshold   (I2C 0x48, read
                                                             │           the level)
                                                             ▼
                                                 BURST ─► Pi GPIO17 (pin 11)
                                                       └► U2B ─► D1 green LED
```

- **The SDR path** is what OpenStint decodes. The amp makes up for the splitter
  and gives the SDR a stronger, cleaner signal than raw coax.
- **The detector path** tells the Pi "a transponder is over the loop right now"
  without the SDR. The LED shows it, so you can set the threshold by eye.

## 2. Parts list (tick what you have)

Everything here is through-hole or on a breakout, except the two SOIC chips,
which go on SOIC-8 → DIP adapter boards.

### Chips and modules

| ✓ | Qty | Ref | Part | Notes |
|---|---|---|---|---|
| ☐ | 1 | U4 | **LMH6624MA** op amp, SOIC-8 | The LNA. Must be gain ≥ 10 stable; this one is. |
| ☐ | 1 | U1 | **AD8307ARZ** log detector, SOIC-8 | |
| ☐ | 2 | — | SOIC-8 → DIP-8 adapter board + 2× 4-pin male headers | For U4 and U1. Solder the chip first, then the headers. |
| ☐ | 1 | U2 | **LM393N** dual comparator, DIP-8 | Any LM393 in DIP works. |
| ☐ | 1 | U3 | **ADS1115** 16-bit ADC breakout | Adafruit 1085 or a clone. **Check the header order on yours** (section 6 assumes VDD GND SCL SDA ADDR ALRT A0 A1 A2 A3). |
| ☐ | 1 | — | DS3231 RTC module (optional) | Keeps time with no internet. I2C 0x68. |

### Resistors (1/4 W, 1 % metal film where it says so)

| ✓ | Qty | Value | Refs | Notes |
|---|---|---|---|---|
| ☐ | 1 | 10 Ω | R20 | 5 V supply filter |
| ☐ | 2 | 51 Ω | R21, R13 | 50 Ω terminations |
| ☐ | 2 | 49.9 Ω 1 % | R18, R19 | 51 Ω is fine on a breadboard |
| ☐ | 3 | 16.5 Ω 1 % | R10, R11, R12 | Splitter. 15 Ω is fine on a breadboard |
| ☐ | 1 | 499 Ω 1 % | R17 | Amp feedback. 470 Ω or 510 Ω is fine |
| ☐ | 1 | 1 kΩ | R8 | LED |
| ☐ | 7 | 10 kΩ | R3, R5, R6, R7, R14, R15, R16 | |
| ☐ | 1 | 1 MΩ | R4 | Comparator hysteresis |
| ☐ | 1 | 10 kΩ trimmer pot | RV1 | 3-leg, breadboard pitch. Sets the burst threshold |

### Capacitors

C0G/NP0 ceramic where it says C0G (the filter needs stable values). Everything
else is plain ceramic (X7R) except the two electrolytics.

| ✓ | Qty | Value | Refs | Notes |
|---|---|---|---|---|
| ☐ | 2 | 390 pF C0G | C12, C13 | Filter |
| ☐ | 1 | 470 pF C0G | C23 | RSSI smoothing |
| ☐ | 2 | 1 nF C0G | C10, C11 | Filter |
| ☐ | 1 | 1 nF | C22 | AD8307 offset pin, any type |
| ☐ | 2 | 10 nF | C2, C3 | AD8307 input coupling |
| ☐ | 8 | 100 nF | C14, C16, C17, C18, C20, C24, C30, C31 | |
| ☐ | 2 | 10 µF electrolytic, ≥ 10 V | C15, C21 | Long leg (+) to the signal/5 V side, short leg to GND |

### Inductors

| ✓ | Qty | Value | Refs | Notes |
|---|---|---|---|---|
| ☐ | 1 | 1.5 µH | L10 | Axial or radial, rated ≥ 100 mA |
| ☐ | 1 | 2.2 µH | L11 | Same |

### Diodes

| ✓ | Qty | Part | Refs | Notes |
|---|---|---|---|---|
| ☐ | 2 | 1N4148 | D3, D4 | Input clamp, back to back. Band = cathode |
| ☐ | 1 | Green LED, 3 mm or 5 mm | D1 | Long leg = anode |

### RF connectors and cables

| ✓ | Qty | Part | Notes |
|---|---|---|---|
| ☐ | 2 | SMA female pigtail (SMA jack with ~10 cm of RG-316 or bare leads) | J1 LOOP IN and J2 TO SDR. Centre wire to the hole listed, shield to GND rail. Keep the bare ends under 1 cm. |
| ☐ | 1 | SMA male ↔ SMA male cable, 15–30 cm | J2 → RTL-SDR antenna jack |
| ☐ | 1 | Your existing loop coax (balun → SMA male) | Goes into J1 instead of straight into the SDR |

### Breadboard and wiring

| ✓ | Qty | Part | Notes |
|---|---|---|---|
| ☐ | 1 | 830-point breadboard, 63 columns, rails top and bottom | Layout assumes this size |
| ☐ | 1 | Jumper wire kit (solid core, pre-cut) | ~26 short jumpers (W4–W26) |
| ☐ | 8 | Dupont female → male leads | Pi header → breadboard (section 3) |
| ☐ | — | Multimeter | Section 7 checks |

## 3. Pi header pins

| Pi pin | Name | Goes to | Wire |
|---|---|---|---|
| 1 | 3.3 V | bottom **orange (3V3) rail**, col 1 | W3 |
| 2 | 5 V | hole **a3** (then R20 → top red rail) | W1 |
| 3 | GPIO2 / SDA | ADS1115 SDA (hole i56) | W22 |
| 5 | GPIO3 / SCL | ADS1115 SCL (hole i55) | W21 |
| 6 | GND | top **blue (GND) rail**, col 1 | W2 |
| 11 | GPIO17 | BURST (hole h41) | W12 |
| 13 | GPIO27 | ADS1115 ALRT (hole i58), optional | W24 |

Pi pin 1 is the corner pin nearest the SD card end, on the inside row.
Enable I2C first: `sudo raspi-config nonint do_i2c 0` (Pi OS) or add
`dtparam=i2c_arm=on` to `config.txt` (Ubuntu), then reboot.

## 4. Schematic (ASCII)

Net names in `CAPS`. `⏚` = GND. `5V_A` is the Pi 5 V after the R20 filter (top
red rail). `3V3` is Pi pin 1 (bottom orange rail).

### 4a. Power

```
 Pi pin 2 (5 V) ──[R20 10Ω]──┬──────┬────────► 5V_A  (top red rail)
                             │      │
                          C21 10µF  C20 100nF
                           +│       │
                            ⏚       ⏚

 Pi pin 1 (3.3 V) ───────────────────────────► 3V3   (bottom orange rail)
 Pi pin 6 (GND) ─────────────────────────────► GND   (top blue rail)
 top blue rail col 63 ──── W4 ──── bottom blue rail col 63   (tie the grounds)
```

### 4b. Input clamp + 3–8 MHz band-pass

```
              LOOP              HP1               HP2           RF_F
 J1 ──────────┬───┬──[C10 1nF]──┬──[C11 1nF]──────┬──(L11 2.2µH)──┬──────┬──► to amp (4c)
 (centre)     │   │             │                 │               │      │
           D3 ▼   ▲ D4      (L10 1.5µH)     C12 390pF       C13 390pF  R21 51Ω
              │   │             │                 │               │      │
              ⏚   ⏚             ⏚                 ⏚               ⏚      ⏚
 J1 shield ─► ⏚

 D3: anode on LOOP, band (cathode) to GND.  D4: anode on GND, band on LOOP.
 They clip anything over ~0.6 V so a static zap on the loop can't reach the amp.
```

### 4c. LNA (U4 LMH6624, gain = 1 + 499/49.9 ≈ 11 = +21 dB)

```
                                          5V_A
                                           │   C17 100nF
                                           ├───||─── ⏚
                                    pin 7  │
 RF_F ──[C14 100nF]──┬──── pin 3 (+IN) ┌───┴───┐
                     │                 │  U4   │ pin 6 (OUT)
               [R14 10kΩ]              │LMH6624├────┬──────────► LNA_OUT (to 4d)
                     │       ┌─ pin 2 ─┤ (-IN) │    │
   5V_A              │       │         └───┬───┘    │
    │                │       │       pin 4 │        │
 [R15 10kΩ]          │       │             ⏚        │
    │                │       └─────[R17 499Ω]───────┘   (Rf, pin 2 ↔ pin 6)
    ├────────────────┘ VMID ≈ 2.5 V                  
    │                        pin 2 ──[R18 49.9Ω]── RG ──[C16 100nF]── ⏚   (Rg)
 [R16 10kΩ]  C15 10µF
    │         +│
    ⏚          ⏚          pins 1, 5, 8 = not connected

 VMID biases the input at half supply so the output swings around 2.5 V.
 C16 makes the gain 11 for RF but 1 for DC, so the output sits at ~2.5 V DC.
```

### 4d. Back-termination + 3-way splitter

```
 LNA_OUT ──[C18 100nF]── OUT_AC ──[R19 49.9Ω]── BT ──[R10 16.5Ω]── SPLIT ─┬─[R11 16.5Ω]── SDR ──► J2 centre → RTL-SDR
                                                                         │                       (J2 shield → ⏚)
                                                                         └─[R12 16.5Ω]── DET ──► to detector (4e)
                                                                                          │
                                                                                     [R13 51Ω]
                                                                                          │
                                                                                          ⏚
 Each leg loses 6 dB. To the SDR: +21 − 6 − 6 ≈ +9 dB vs. coax straight in.
```

### 4e. AD8307 log detector

```
                       5V_A ──┬────────────┐
                              │ C24 100nF  │
                              ├──||── ⏚    │
                        pin 6 │      pin 5 │
                          ┌───┴────────────┴──┐
 DET ──[C2 10nF]── pin 8 ─┤ INP          ENB  │
                          │      U1 AD8307    │
            ┌──── pin 1 ──┤ INM          OUT  ├── pin 4 ──┬──────► RSSI (to 4f and ADS1115 A0)
       C3 10nF            │              INT  ├── pin 7   │        25 mV per dB
            ⏚    ┌─ pin 3 ┤ OFS          COM  ├── pin 2   C23 470pF
                 │        └───────────────────┘   │       │
             C22 1nF                  (pin 7 n/c) ⏚       ⏚
                 ⏚
```

### 4f. Burst comparator, LED, threshold

```
          3V3
           │
      ┌─[RV1 10kΩ trimmer]─┐            3V3
      │      wiper         │             │
      ⏚        │                     [R5 10kΩ]   (pull-up to 3.3 V so the Pi pin is safe)
               ├── C31 100nF ── ⏚        │
             THRESH                      │
               │       ┌───────────┐     │
               └─ pin 2┤-  U2A     │pin 1│
                       │  LM393    ├─────┴────┬───────────► BURST ─► Pi GPIO17 (pin 11)
 RSSI ─[R3 10kΩ]─┬ pin 3┤+         │          │
                 │     └───────────┘          │
                 └──────[R4 1MΩ]──────────────┘   (hysteresis, stops chatter)

 BURST goes HIGH while a transponder is over the loop (RSSI above THRESH).

 LED driver (other half, U2B):
   5V_A ── pin 8 (VCC), C30 100nF to ⏚;  pin 4 = GND
   BURST ─────────────────────── pin 6 (INB−)
   3V3 ─[R6 10kΩ]─┬─[R7 10kΩ]─ ⏚        REF_B ≈ 1.65 V ── pin 5 (INB+)
                  └─ REF_B
   3V3 ─[R8 1kΩ]── D1 anode ▶| cathode ── pin 7 (OUTB)
   → LED is ON during a burst.

 ADS1115 (U3): VDD=3V3, GND, ADDR=GND (0x48), SCL=Pi pin 5, SDA=Pi pin 3,
               A0=RSSI, A1=THRESH, ALRT=Pi pin 13 (optional), A2/A3 unused.
```

## 5. Breadboard map

Rows **a–e** are the top half, **f–j** the bottom half. Each column number is
one 5-hole strip in each half. Rails:

- top red **+** = **5V_A**, top blue **−** = **GND**
- bottom blue **−** = **GND**, bottom orange/red **+** = **3V3** (not 5 V!)

```
 col:  1      5          13 15     19 21 23  26 29 32 35    38 41    44 47 50  53            62
       ├──────┴──────────┤ ├──────────────┤  ├─────┤  ├──────┤ ├──────┤ ├──┤  ├──────────────┤
         power, J1,           U4 LMH6624      splitter  U1        U2       RV1   U3 ADS1115
         clamp, band-pass     + bias          J2 SDR    AD8307    LM393    LED   (header in row j,
                                                                                 board hangs off
                                                                                 the bottom edge)
```

**IC orientation:** every IC straddles the centre gap with the **notch to the
LEFT**, so pin 1 is **bottom-left** (row f) and pin 8 is top-left (row e).
Pins 1–4 run left→right along row f; pins 5–8 run right→left along row e.

## 6. Hole-by-hole placement, in build order

"rail col N" means any hole on that rail near column N; the column is only a
suggestion to keep leads short.

### Stage 1 — power (no chips yet)

| Ref | Value | Holes |
|---|---|---|
| W1 | Pi pin 2 (5 V) | a3 → Pi pin 2 |
| R20 | 10 Ω | b3 ↔ 5V_A rail (top) col 4 |
| C21 | 10 µF (+ to rail) | 5V_A rail (top) col 6 ↔ GND rail (top) col 6 |
| C20 | 100 nF | 5V_A rail (top) col 8 ↔ GND rail (top) col 8 |
| W2 | Pi pin 6 (GND) | GND rail (top) col 1 → Pi pin 6 |
| W3 | Pi pin 1 (3.3 V) | 3V3 rail (bottom) col 1 → Pi pin 1 |
| W4 | GND rail link | GND rail (top) col 63 ↔ GND rail (bottom) col 63 |

### Stage 2 — input, clamp, band-pass

| Ref | Value | Holes |
|---|---|---|
| J1 | LOOP IN centre | j5 |
| J1s | LOOP IN shield | GND rail (bottom) col 3 |
| D3 | 1N4148, band → rail | i5 ↔ GND rail (bottom) col 4 |
| D4 | 1N4148, band → hole 5 | GND rail (bottom) col 6 ↔ h5 |
| C10 | 1 nF C0G | g5 ↔ j8 |
| L10 | 1.5 µH | i8 ↔ GND rail (bottom) col 8 |
| C11 | 1 nF C0G | h8 ↔ j11 |
| C12 | 390 pF C0G | i11 ↔ GND rail (bottom) col 11 |
| L11 | 2.2 µH | h11 ↔ j13 |
| C13 | 390 pF C0G | i13 ↔ GND rail (bottom) col 12 |
| R21 | 51 Ω | h13 ↔ GND rail (bottom) col 14 |
| C14 | 100 nF | g13 ↔ j17 |

### Stage 3 — LNA (U4 LMH6624 on its adapter, pin 1 at f15)

| Ref | Value | Holes |
|---|---|---|
| U4 | LMH6624 | pin 1 NC → f15, pin 2 −IN → f16, pin 3 +IN → f17, pin 4 V− → f18, pin 5 NC → e18, pin 6 OUT → e17, pin 7 V+ → e16, pin 8 NC → e15 |
| W5 | V− to GND | j18 ↔ GND rail (bottom) col 18 |
| W6 | V+ to 5V_A | a16 ↔ 5V_A rail (top) col 16 |
| C17 | 100 nF (right at the pin) | b16 ↔ GND rail (top) col 15 |
| R14 | 10 kΩ | i17 ↔ j21 |
| R15 | 10 kΩ | i21 ↔ j23 |
| W7 | 5V_A to R15 | 5V_A rail (top) col 23 ↔ i23 |
| R16 | 10 kΩ | h21 ↔ GND rail (bottom) col 21 |
| C15 | 10 µF (+ to h/g21) | g21 ↔ GND rail (bottom) col 22 |
| R17 | 499 Ω (Rf) | d17 ↔ g16 |
| R18 | 49.9 Ω (Rg) | j16 ↔ j19 |
| C16 | 100 nF | i19 ↔ GND rail (bottom) col 19 |

Keep R17, R18 and C17 short and tight to the adapter. Long leads here are the
most likely cause of oscillation.

### Stage 4 — back-termination, splitter, J2

| Ref | Value | Holes |
|---|---|---|
| C18 | 100 nF | a17 ↔ a20 |
| R19 | 49.9 Ω | b20 ↔ a23 |
| R10 | 16.5 Ω | b23 ↔ a26 |
| R11 | 16.5 Ω | b26 ↔ a29 |
| J2 | TO SDR centre | b29 |
| J2s | TO SDR shield | GND rail (top) col 30 |
| R12 | 16.5 Ω | c26 ↔ a32 |
| R13 | 51 Ω | b32 ↔ GND rail (top) col 32 |
| C2 | 10 nF | c32 ↔ a35 |

### Stage 5 — AD8307 detector (U1 on its adapter, pin 1 at f35)

| Ref | Value | Holes |
|---|---|---|
| U1 | AD8307 | pin 1 INM → f35, pin 2 COM → f36, pin 3 OFS → f37, pin 4 OUT → f38, pin 5 ENB → e38, pin 6 VPS → e37, pin 7 INT → e36, pin 8 INP → e35 |
| C3 | 10 nF | j35 ↔ GND rail (bottom) col 34 |
| W8 | COM to GND | j36 ↔ GND rail (bottom) col 36 |
| C22 | 1 nF | j37 ↔ GND rail (bottom) col 37 |
| C23 | 470 pF C0G | j38 ↔ GND rail (bottom) col 39 |
| W9 | VPS to 5V_A | a37 ↔ 5V_A rail (top) col 37 |
| W10 | ENB to 5V_A | a38 ↔ 5V_A rail (top) col 38 |
| C24 | 100 nF | b37 ↔ GND rail (top) col 36 |

### Stage 6 — LM393 comparator, LED, threshold (U2, pin 1 at f41)

| Ref | Value | Holes |
|---|---|---|
| U2 | LM393N | pin 1 OUTA → f41, pin 2 INA− → f42, pin 3 INA+ → f43, pin 4 GND → f44, pin 5 INB+ → e44, pin 6 INB− → e43, pin 7 OUTB → e42, pin 8 VCC → e41 |
| R3 | 10 kΩ | i38 ↔ j43 |
| R4 | 1 MΩ | j41 ↔ i43 |
| R5 | 10 kΩ | i41 ↔ 3V3 rail (bottom) col 41 |
| W11 | BURST to INB− | g41 ↔ d43 |
| W12 | Pi pin 11 (GPIO17) | h41 → Pi pin 11 |
| W13 | GND | j44 ↔ GND rail (bottom) col 44 |
| W14 | VCC to 5V_A | a41 ↔ 5V_A rail (top) col 41 |
| C30 | 100 nF | b41 ↔ GND rail (top) col 40 |
| D1 | green LED, long leg in 47 | a47 ↔ a42 |
| R8 | 1 kΩ | b47 ↔ a50 |
| R6 | 10 kΩ | a44 ↔ b50 |
| R7 | 10 kΩ | b44 ↔ GND rail (top) col 45 |
| W15 | 3V3 to top col 50 | c50 ↔ 3V3 rail (bottom) col 50 |
| RV1 | 10 kΩ trimmer | legs j47, j48 (wiper, middle), j49 |
| W16 | RV1 end to GND | i47 ↔ GND rail (bottom) col 47 |
| W17 | RV1 end to 3V3 | i49 ↔ 3V3 rail (bottom) col 49 |
| W18 | THRESH to INA− | i48 ↔ j42 |
| C31 | 100 nF | h48 ↔ GND rail (bottom) col 46 |

### Stage 7 — ADS1115 (header pins in row j, cols 53–62, board hanging off the edge)

| Ref | Value | Holes |
|---|---|---|
| U3 | ADS1115 | VDD → j53, GND → j54, SCL → j55, SDA → j56, ADDR → j57, ALRT → j58, A0 → j59, A1 → j60, A2 → j61, A3 → j62 |
| W19 | VDD to 3V3 | i53 ↔ 3V3 rail (bottom) col 52 |
| W20 | GND | i54 ↔ GND rail (bottom) col 52 |
| W21 | Pi pin 5 (SCL) | i55 → Pi pin 5 |
| W22 | Pi pin 3 (SDA) | i56 → Pi pin 3 |
| W23 | ADDR to GND (0x48) | i57 ↔ GND rail (bottom) col 51 |
| W24 | Pi pin 13 (GPIO27), optional | i58 → Pi pin 13 |
| W25 | RSSI to A0 | h38 ↔ i59 |
| W26 | THRESH to A1 | g48 ↔ i60 |

Optional DS3231 RTC: VCC → 3V3 rail, GND → GND rail, SCL → any free hole in
col 55 (f–i), SDA → any free hole in col 56.

## 7. Test after each stage

Power the Pi off while placing parts. Test with the Pi on.

1. **After stage 1:** top red rail ≈ 5.0 V, bottom orange rail ≈ 3.3 V, both
   grounds 0 Ω to each other.
2. **After stage 3:** U4 pin 3 ≈ 2.5 V and pin 6 ≈ 2.5 V DC. If pin 6 sits near
   0 V or 5 V, or U4 gets warm, check the wiring and shorten R17/R18/C17 leads.
3. **After stage 4:** connect J2 to the SDR and J1 to the loop. Start the lap
   counter as usual and compare OpenStint's noise floor and frame quality with
   coax straight in. The signal should be stronger.
4. **After stage 5:** U1 pin 4 (RSSI) sits at a few hundred mV with no
   transponder and rises when one is held over the loop.
5. **After stage 6:** with no car on the loop, turn RV1 until the LED is just
   off. Pass a transponder over the loop: the LED should flash. On the Pi:
   `gpiomon gpiochip0 17` (libgpiod 1.x) or `gpiomon -c gpiochip0 17` (2.x)
   prints edges as it passes.
6. **After stage 7:** `sudo i2cdetect -y 1` shows **48** (and **68** if the RTC
   is fitted).

If the amp misbehaves, the SDR still works with the loop coax plugged straight
into it, exactly as it does today.

## 8. On the PCB only (not on the breadboard)

These are in the v1 board design but skipped here:

- **K1 relay + J5 PAD input:** a TQ2-5V relay switches between the track loop
  (J1) and a learning pad (J5), driven from GPIO22 through a 2N7002. On the
  breadboard, J1 goes straight in.
- **U5 DS3231MZ RTC** with CR1220 holder (the module above stands in for it).
- **U6 CAT24C32 HAT ID EEPROM** at 0x50 on the Pi's ID_SD/ID_SC pins.
- **Power:** DC barrel jack or the Pi 4 PoE header → buck to 5.2 V → back-powers
  the Pi. GPIO23 reads "running on PoE". To try PoE now, use an off-the-shelf
  802.3at splitter with a USB-C 5 V output, and compare OpenStint's noise floor on
  USB-C vs. PoE, since switch-mode supplies can put noise inside 3–8 MHz.
