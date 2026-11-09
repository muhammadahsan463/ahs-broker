# Motive-style ELD log packet — WERC Deliveries

Driver **Wali Abdur Rahman** · Carrier **WERC Deliveries LLC** · MC **1766777** · DOT **4475311** · Truck **01** · Trailer **01**

## What was filled

Trip / shipping fields from the 10 attached Bobtail + broker rate confirmation PDFs (Oct 2 – Nov 5, 2026):

| Load # | Broker | Pickup | Delivery | Rate |
| --- | --- | --- | --- | ---: |
| 47187241 | Armstrong | North Canton, OH 10/02 | Harrisonburg, VA 10/05 | $1,250 |
| 6479465 | Ryan | Peosta, IA 10/12 | Hanover, MD 10/13 | $1,936 |
| 2770276 | MegaCorp | Hainesport, NJ 10/13 | Norman, OK 10/15 | $2,000 |
| 0243426 | Spice | Oklahoma City, OK 10/18 | Saint Charles, MO 10/19 | $1,200 |
| S4444956 | Spot Freight | Troy, MO 10/19 | Swanton, OH 10/20 | $900 |
| 1165346 | Trident | Avilla, IN 10/20 | Rogers, MN 10/21 | $1,200 |
| 6513846 | Ryan | Des Moines, IA 10/22 | Albany, GA 10/26 | $2,100 |
| 6533137 | Ryan | Buford, GA 10/29 | Fredericksburg, PA 10/30 | $1,020 |
| 273192 | Pinnacle | New York, NY 11/02 | Buffalo, NY 11/03 | $1,300 |
| 24585956 | RXO | Latrobe, PA 11/04 | Chelmsford, MA 11/05 | $1,400 |

## Intentionally blank

- 24-hour duty status graph (Off Duty / Sleeper / Driving / On Duty)
- HOS totals, event list, engine hours, odometer “miles today”
- VIN / plate, home terminal timezone, certification signature

## Files

- `Wali_Abdur_Rahman_Motive_ELD_Log.pdf` — 12-page packet (summary chart + 10 daily shells + missing checklist)
- `Wali_Abdur_Rahman_Motive_ELD_Log.html` / `loads_data_chart.html` — browser chart + table
- `loads.json` — structured extract from the rate confirmations
- `generate_motive_eld_log.py` — regenerator

```bash
python3 docs/eld/generate_motive_eld_log.py
```

**Not** an official Motive export and **not** a certified record of duty status.
