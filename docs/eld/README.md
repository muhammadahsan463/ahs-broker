# Motive-style ELD log (WERC Deliveries)

Working document shell for driver **Wali Abdur Rahman** at **WERC Deliveries LLC**.

## Filled from user input

| Field | Value |
| --- | --- |
| Carrier | WERC Deliveries LLC |
| Driver | Wali Abdur Rahman |
| MC # | 1766777 |
| Truck | 01 |
| Trailer | 01 |

## Intentionally blank

- Log date / trip from–to / pickup & delivery details (awaiting rate confirmations)
- 24-hour duty status graph
- HOS totals (off duty, sleeper, driving, on duty)
- Event list rows
- Miles / engine hours
- Driver certification signature

## Pending

Rate confirmation(s) covering approximately the last month of loads. When those arrive, trip header fields (pickup date/time/city, delivery details, shipping doc) can be filled from the confirmations only. **Duty status and driving hours stay blank unless the user supplies actual HOS data — never estimate.**

## Files

- `Wali_Abdur_Rahman_Motive_ELD_Log.pdf` — printable Motive-style daily log layout
- `Wali_Abdur_Rahman_Motive_ELD_Log.html` — same content for browser preview
- `generate_motive_eld_log.py` — regenerates the PDF/HTML

```bash
python3 docs/eld/generate_motive_eld_log.py
```

This is **not** an official Motive export and is **not** a certified record of duty status.
