# PCB Files

This folder has the KiCad files for the PCBs fabricated. The ADXL 343 Adapter
and Revision 1 of the Project were fabricated. The files in the `kicad-lib`
folder may be needed to edit these files.

## Errata

### Project Revision 1
  * Q1 uses the incorrect footprint. They should be rotated 120 degrees
    counter-clockwise.
  * D2 and D3 don't have decoupling capacitors. They should have 1uF capacitors.
  * D2 doesn't have a decoupling resistor on the data line. It should have a
    470R on the input.
