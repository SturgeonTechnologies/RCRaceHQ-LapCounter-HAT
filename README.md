# RC Race HQ Lap Counter HAT

Open hardware for the [RC Race HQ](https://www.rcracehq.com) lap counter: a
Raspberry Pi 4 HAT that sits between the track's timing loop and the RTL-SDR.

| Path | What | Status |
|---|---|---|
| [`burst-detector-hat/`](burst-detector-hat) | v0: splitter + AD8307 log detector + LM393 burst flag + ADS1115 signal strength. KiCad project, gerbers, JLCPCB BOM/CPL | Fab files done, board not built or tested yet |
| [`breadboard-v1.md`](breadboard-v1.md) | v1 loop front end (LMH6624 amp + detector) as a breadboard build: parts checklist, ASCII schematic, hole-by-hole steps | Not built or tested yet |

Transponder IDs come from the RTL-SDR through
[OpenStint](https://github.com/zsellera/openstint). The HAT tells the Pi
*when* a transponder is over the loop and how strong it is. Without a HAT, the
loop coax goes straight into the RTL-SDR, which is how the lap counter runs
today.

Software and Pi setup:
[RCRaceHQ-LapCounter-Install](https://github.com/SturgeonTechnologies/RCRaceHQ-LapCounter-Install)
and [RCRaceHQ-LapCounter-App](https://github.com/SturgeonTechnologies/RCRaceHQ-LapCounter-App).

## Buy or build

Anyone may build this board. Assembled, tested boards will be available from
RC Race HQ.

## License

[CERN-OHL-S-2.0](LICENSE). You may build, modify and sell boards made from
this design. If you ship a modified board, you must publish your modified
design files under the same licence. See [NOTICE](NOTICE). "RC Race HQ" is a
trademark of Sturgeon Technologies LLC and isn't covered by the licence.
