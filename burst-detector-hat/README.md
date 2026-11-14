# Burst-detector HAT (lap counter v0 front end)

Raspberry Pi 4 HAT (65 × 56.5 mm, M2.5 holes on the HAT pattern) that sits
between the timing loop and the RTL-SDR.

```
loop -> balun -> J1 SMA -> TVS -> 3-way resistive splitter -+-> J2 SMA -> RTL-SDR (IDs, via OpenStint)
                                                           +-> 3-8 MHz bandpass -> AD8307 log detector
AD8307 RSSI (25 mV/dB) -+-> ADS1115 AIN0 (I2C 0x48, pins 3/5) -> signal strength
                        +-> LM393 vs RV1 threshold -> GPIO17 (pin 11) + BURST LED
```

It tells the Pi *when* a transponder is over the loop and how strong it is.
The ID still comes from the SDR. Power is the Pi's 5 V/3.3 V header pins, so
USB-C or a PoE HAT both work. J4 is an unconnected pass-through for the Pi's
2×2 PoE header, with a copper keep-out around it.

## Ordering (JLCPCB)
- Gerbers: `fab/burst_detector_hat_gerbers.zip` (2 layers, 1.6 mm, HASL).
- Assembly (top side): `fab/bom_jlcpcb.csv` + `fab/cpl_jlcpcb.csv`.
  Check every LCSC part number and the U1/U2/U3 pin-1 rotation in JLC's preview.
- Hand-solder: J3 2×20 stacking header, J4 2×2 stacking header (optional).

## Bring-up
1. Power from the Pi; LED off with no loop connected.
2. `i2cdetect -y 1` shows `48`.
3. Turn RV1 until the LED goes out with the loop empty, then back off a little.
4. Transponder on the loop: LED on, ~650 rising edges/s on GPIO17.

## Rebuild
`source ~/tools/kicad-env.sh && JAVA=... FREEROUTING=... tools/build.sh`
regenerates everything from `tools/design.py`, autoroutes, runs ERC/DRC
(`fab/reports/`) and rewrites `fab/`.
