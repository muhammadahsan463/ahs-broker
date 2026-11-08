#!/usr/bin/env python3
"""Generate a Motive-style ELD daily log PDF.

Only known carrier/driver/vehicle fields are filled. Duty status, driving
hours, graph segments, and event rows stay blank unless supplied later from
rate confirmations. This is a working document shell — not an official Motive
export and not a certified record of duty status.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


# Known fields provided by the user (do not invent values beyond these).
CARRIER_NAME = "WERC Deliveries LLC"
DRIVER_NAME = "Wali Abdur Rahman"
MC_NUMBER = "1766777"
TRUCK_NUMBER = "01"
TRAILER_NUMBER = "01"

# Trip / rate-confirmation fields — blank until the user supplies them.
LOG_DATE: date | None = None
PICKUP_DATE: str = ""
PICKUP_TIME: str = ""
PICKUP_CITY: str = ""
DELIVERY_DETAILS: str = ""
SHIPPING_DOC: str = ""
FROM_LOCATION: str = ""
TO_LOCATION: str = ""

PENDING_NOTE = (
    "PENDING: Rate confirmation(s) for approximately the last month of loads "
    "have not been received yet. Trip dates, pickup/delivery locations, and "
    "shipping document numbers will be filled only from those confirmations. "
    "Duty status graph, driving hours, and event list remain intentionally blank."
)


@dataclass
class TripStub:
    """Optional trip header fields from a rate confirmation (not HOS events)."""

    pickup_date: str = ""
    pickup_time: str = ""
    pickup_city: str = ""
    delivery_details: str = ""
    shipping_doc: str = ""
    from_location: str = ""
    to_location: str = ""


@dataclass
class LogConfig:
    carrier_name: str = CARRIER_NAME
    driver_name: str = DRIVER_NAME
    mc_number: str = MC_NUMBER
    truck_number: str = TRUCK_NUMBER
    trailer_number: str = TRAILER_NUMBER
    log_date: date | None = LOG_DATE
    trip: TripStub = field(default_factory=TripStub)
    output_path: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent
        / "Wali_Abdur_Rahman_Motive_ELD_Log.pdf"
    )


MOTIVE_TEAL = colors.Color(0.0, 0.55, 0.55)
MOTIVE_DARK = colors.Color(0.12, 0.16, 0.18)
LIGHT_GRAY = colors.Color(0.93, 0.94, 0.95)
MED_GRAY = colors.Color(0.75, 0.78, 0.80)
ROW_LABELS = [
    ("1", "Off Duty"),
    ("2", "Sleeper Berth"),
    ("3", "Driving"),
    ("4", "On Duty (Not Driving)"),
]


def _dash(value: str | None) -> str:
    value = (value or "").strip()
    return value if value else "—"


def _draw_header(c: canvas.Canvas, cfg: LogConfig, width: float, y: float) -> float:
    c.setFillColor(MOTIVE_TEAL)
    c.rect(0, y - 8, width, 48, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(36, y + 18, "MOTIVE")
    c.setFont("Helvetica", 9)
    c.drawString(110, y + 20, "Electronic Logging Device — Daily Log")
    c.setFont("Helvetica", 8)
    c.drawRightString(width - 36, y + 22, "Driver App / Inspection Form Layout")
    c.drawRightString(width - 36, y + 10, "Not an official Motive export")
    return y - 28


def _kv(c: canvas.Canvas, x: float, y: float, label: str, value: str, label_w: float = 78) -> None:
    c.setFillColor(colors.Color(0.35, 0.38, 0.40))
    c.setFont("Helvetica", 7)
    c.drawString(x, y, label.upper())
    c.setFillColor(MOTIVE_DARK)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + label_w, y - 1, value)


def _draw_identity(c: canvas.Canvas, cfg: LogConfig, width: float, y: float) -> float:
    left = 36
    right = width - 36
    box_h = 108
    c.setStrokeColor(MED_GRAY)
    c.setFillColor(colors.white)
    c.roundRect(left, y - box_h, right - left, box_h, 4, fill=1, stroke=1)

    c.setFillColor(MOTIVE_DARK)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left + 10, y - 16, "Daily Header")

    log_date_str = cfg.log_date.isoformat() if cfg.log_date else "— (pending rate confirmation)"
    _kv(c, left + 10, y - 34, "Log Date", log_date_str, 70)
    _kv(c, left + 290, y - 34, "Timezone", "— (home terminal)", 70)

    _kv(c, left + 10, y - 52, "Driver", cfg.driver_name, 70)
    _kv(c, left + 290, y - 52, "Co-Driver", "—", 70)

    _kv(c, left + 10, y - 70, "Carrier", cfg.carrier_name, 70)
    _kv(c, left + 290, y - 70, "MC #", cfg.mc_number, 70)

    _kv(c, left + 10, y - 88, "Truck / CMV", cfg.truck_number, 70)
    _kv(c, left + 160, y - 88, "Trailer", cfg.trailer_number, 50)
    _kv(c, left + 290, y - 88, "VIN / Plate", "—", 70)

    return y - box_h - 14


def _draw_trip_block(c: canvas.Canvas, cfg: LogConfig, width: float, y: float) -> float:
    left = 36
    right = width - 36
    box_h = 78
    c.setStrokeColor(MED_GRAY)
    c.setFillColor(LIGHT_GRAY)
    c.roundRect(left, y - box_h, right - left, box_h, 4, fill=1, stroke=1)

    c.setFillColor(MOTIVE_DARK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left + 10, y - 14, "Trip / Shipping (from rate confirmation)")

    trip = cfg.trip
    _kv(c, left + 10, y - 32, "From", _dash(trip.from_location or trip.pickup_city), 50)
    _kv(c, left + 290, y - 32, "To", _dash(trip.to_location or trip.delivery_details), 40)
    _kv(c, left + 10, y - 48, "Pickup Date", _dash(trip.pickup_date), 70)
    _kv(c, left + 160, y - 48, "Pickup Time", _dash(trip.pickup_time), 70)
    _kv(c, left + 320, y - 48, "Pickup City", _dash(trip.pickup_city), 70)
    _kv(c, left + 10, y - 64, "Delivery", _dash(trip.delivery_details), 55)
    _kv(c, left + 320, y - 64, "Ship Doc #", _dash(trip.shipping_doc), 70)

    return y - box_h - 12


def _draw_pending_banner(c: canvas.Canvas, width: float, y: float) -> float:
    left = 36
    right = width - 36
    styles = getSampleStyleSheet()
    style = ParagraphStyle(
        "Pending",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.Color(0.45, 0.28, 0.05),
    )
    p = Paragraph(PENDING_NOTE, style)
    w, h = p.wrap(right - left - 16, 80)
    box_h = h + 16
    c.setFillColor(colors.Color(1.0, 0.95, 0.85))
    c.setStrokeColor(colors.Color(0.85, 0.65, 0.20))
    c.roundRect(left, y - box_h, right - left, box_h, 4, fill=1, stroke=1)
    p.drawOn(c, left + 8, y - box_h + 8)
    return y - box_h - 14


def _draw_graph(c: canvas.Canvas, width: float, y: float) -> float:
    left = 36
    right = width - 36
    graph_h = 118
    label_w = 118
    totals_w = 48
    grid_left = left + label_w
    grid_right = right - totals_w
    grid_w = grid_right - grid_left

    c.setFillColor(MOTIVE_DARK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left, y, "24-Hour Duty Status Graph")
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.Color(0.4, 0.4, 0.4))
    c.drawString(left + 160, y + 1, "Intentionally blank — no duty status or driving hours entered")
    y -= 8

    # Hour labels
    c.setFont("Helvetica", 6)
    c.setFillColor(MOTIVE_DARK)
    for hour in range(25):
        x = grid_left + (grid_w * hour / 24.0)
        label = "M" if hour == 0 else ("N" if hour == 12 else str(hour % 12 or 12))
        if hour in (0, 12, 24) or hour % 2 == 0:
            c.drawCentredString(x, y - 10, label)
    c.drawString(grid_left - 2, y - 10, "")
    c.setFont("Helvetica", 6)
    c.drawRightString(right - 4, y - 10, "Total")

    y -= 14
    row_h = graph_h / 4.0
    c.setStrokeColor(MED_GRAY)
    c.setFillColor(colors.white)
    c.rect(left, y - graph_h, right - left, graph_h, fill=1, stroke=1)

    for i, (num, name) in enumerate(ROW_LABELS):
        top = y - i * row_h
        # Alternating row tint
        if i % 2 == 0:
            c.setFillColor(colors.Color(0.97, 0.98, 0.98))
            c.rect(left, top - row_h, right - left, row_h, fill=1, stroke=0)
        c.setStrokeColor(MED_GRAY)
        c.line(left, top - row_h, right, top - row_h)
        c.setFillColor(MOTIVE_DARK)
        c.setFont("Helvetica", 8)
        c.drawString(left + 6, top - row_h / 2 - 3, f"{num}. {name}")
        # Empty total hours cell
        c.setStrokeColor(MED_GRAY)
        c.line(grid_right, top, grid_right, top - row_h)
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.Color(0.55, 0.55, 0.55))
        c.drawCentredString(grid_right + totals_w / 2, top - row_h / 2 - 3, "—")

    # Vertical hour lines (empty grid — no status polyline)
    for hour in range(25):
        x = grid_left + (grid_w * hour / 24.0)
        c.setStrokeColor(colors.Color(0.85, 0.87, 0.88) if hour % 6 else MED_GRAY)
        c.setLineWidth(0.6 if hour % 6 else 1)
        c.line(x, y, x, y - graph_h)
    c.setLineWidth(1)
    c.setStrokeColor(MED_GRAY)
    c.line(grid_left, y, grid_left, y - graph_h)

    # Center watermark on graph
    c.setFillColor(colors.Color(0.75, 0.78, 0.80, alpha=0.55))
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString((grid_left + grid_right) / 2, y - graph_h / 2 - 4, "NO DUTY STATUS RECORDED")

    return y - graph_h - 16


def _draw_legend_and_totals(c: canvas.Canvas, width: float, y: float) -> float:
    left = 36
    c.setFillColor(MOTIVE_DARK)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(left, y, "Status Legend")
    y -= 14
    legend = [
        ("Off Duty", colors.Color(0.55, 0.58, 0.60)),
        ("Sleeper Berth", colors.Color(0.35, 0.55, 0.85)),
        ("Driving", colors.Color(0.20, 0.65, 0.45)),
        ("On Duty (ND)", colors.Color(0.90, 0.55, 0.20)),
    ]
    x = left
    for name, color in legend:
        c.setFillColor(color)
        c.circle(x + 4, y + 2, 4, fill=1, stroke=0)
        c.setFillColor(MOTIVE_DARK)
        c.setFont("Helvetica", 8)
        c.drawString(x + 12, y, name)
        x += 110

    y -= 22
    c.setFont("Helvetica-Bold", 9)
    c.drawString(left, y, "Hours of Service Totals (blank)")
    y -= 12
    totals = [
        ("Off Duty", "—"),
        ("Sleeper Berth", "—"),
        ("Driving", "—"),
        ("On Duty (Not Driving)", "—"),
        ("Total Miles Today", "—"),
        ("Engine Hours", "—"),
    ]
    box_top = y + 8
    c.setStrokeColor(MED_GRAY)
    c.setFillColor(colors.white)
    c.roundRect(left, y - 40, width - 72, 52, 3, fill=1, stroke=1)
    for i, (label, value) in enumerate(totals):
        col = i % 3
        row = i // 3
        tx = left + 10 + col * 180
        ty = y - 8 - row * 18
        c.setFillColor(colors.Color(0.4, 0.4, 0.4))
        c.setFont("Helvetica", 7)
        c.drawString(tx, ty, label.upper())
        c.setFillColor(MOTIVE_DARK)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(tx + 95, ty - 1, value)
    return box_top - 56


def _draw_events(c: canvas.Canvas, width: float, y: float) -> float:
    left = 36
    right = width - 36
    c.setFillColor(MOTIVE_DARK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left, y, "Event List / Log Details")
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.Color(0.45, 0.45, 0.45))
    c.drawString(left + 140, y + 1, "No events — duty status changes not provided")
    y -= 10

    headers = ["Time", "Status", "Location", "Odometer", "Eng. Hrs", "Notes"]
    col_x = [left + 4, left + 55, left + 145, left + 310, left + 375, left + 440]
    row_h = 16
    header_h = 16
    rows = 6

    table_h = header_h + rows * row_h
    c.setStrokeColor(MED_GRAY)
    c.setFillColor(LIGHT_GRAY)
    c.rect(left, y - table_h, right - left, table_h, fill=1, stroke=1)

    c.setFillColor(MOTIVE_TEAL)
    c.rect(left, y - header_h, right - left, header_h, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 7)
    for i, h in enumerate(headers):
        c.drawString(col_x[i], y - 11, h)

    c.setFillColor(colors.Color(0.55, 0.55, 0.55))
    c.setFont("Helvetica", 8)
    for r in range(rows):
        top = y - header_h - r * row_h
        c.setStrokeColor(MED_GRAY)
        c.line(left, top - row_h, right, top - row_h)
        for i, _ in enumerate(headers):
            c.drawString(col_x[i], top - 12, "—")

    return y - table_h - 16


def _draw_certification(c: canvas.Canvas, cfg: LogConfig, width: float, y: float) -> float:
    left = 36
    right = width - 36
    box_h = 62
    c.setStrokeColor(MED_GRAY)
    c.setFillColor(colors.white)
    c.roundRect(left, y - box_h, right - left, box_h, 4, fill=1, stroke=1)
    c.setFillColor(MOTIVE_DARK)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(left + 10, y - 14, "Driver Certification")
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.Color(0.4, 0.4, 0.4))
    c.drawString(
        left + 10,
        y - 28,
        "I certify that my entries are true and correct. Signature deferred — log incomplete pending rate confirmations / HOS data.",
    )
    c.setStrokeColor(MED_GRAY)
    c.line(left + 10, y - 48, left + 220, y - 48)
    c.line(left + 240, y - 48, left + 360, y - 48)
    c.setFont("Helvetica", 7)
    c.drawString(left + 10, y - 58, f"Driver: {cfg.driver_name}")
    c.drawString(left + 240, y - 58, "Date: —")
    return y - box_h - 10


def _draw_footer(c: canvas.Canvas, width: float) -> None:
    c.setFillColor(colors.Color(0.45, 0.45, 0.45))
    c.setFont("Helvetica", 7)
    c.drawString(
        36,
        28,
        "Document shell styled after Motive ELD daily log layout (header · graph · legend · events). "
        "Duty status / hours intentionally empty.",
    )
    c.drawRightString(width - 36, 28, "Page 1 of 1")


def generate(cfg: LogConfig | None = None) -> Path:
    cfg = cfg or LogConfig()
    cfg.output_path.parent.mkdir(parents=True, exist_ok=True)
    # Apply module-level trip stubs if TripStub still empty
    if not any(
        [
            cfg.trip.pickup_date,
            cfg.trip.pickup_time,
            cfg.trip.pickup_city,
            cfg.trip.delivery_details,
            cfg.trip.shipping_doc,
            cfg.trip.from_location,
            cfg.trip.to_location,
        ]
    ):
        cfg.trip = TripStub(
            pickup_date=PICKUP_DATE,
            pickup_time=PICKUP_TIME,
            pickup_city=PICKUP_CITY,
            delivery_details=DELIVERY_DETAILS,
            shipping_doc=SHIPPING_DOC,
            from_location=FROM_LOCATION,
            to_location=TO_LOCATION,
        )

    width, height = letter
    c = canvas.Canvas(str(cfg.output_path), pagesize=letter)
    c.setTitle(f"Motive-style ELD Log — {cfg.driver_name}")
    c.setAuthor(cfg.carrier_name)
    c.setSubject("Draft ELD daily log shell; HOS blank pending rate confirmations")

    y = height - 36
    y = _draw_header(c, cfg, width, y)
    y = _draw_identity(c, cfg, width, y)
    y = _draw_trip_block(c, cfg, width, y)
    y = _draw_pending_banner(c, width, y)
    y = _draw_graph(c, width, y)
    y = _draw_legend_and_totals(c, width, y)
    y = _draw_events(c, width, y)
    y = _draw_certification(c, cfg, width, y)
    _draw_footer(c, width)
    c.showPage()
    c.save()
    return cfg.output_path


def generate_html_companion(pdf_path: Path) -> Path:
    html_path = pdf_path.with_suffix(".html")
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Motive-style ELD Log — {DRIVER_NAME}</title>
  <style>
    :root {{
      --teal: #008c8c;
      --ink: #1f2930;
      --muted: #6b7280;
      --line: #c5ced3;
      --wash: #f3f5f6;
      --warn: #fff4d6;
      --warn-border: #d9a63a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Helvetica, Arial, sans-serif;
      color: var(--ink);
      background: #e8ecef;
    }}
    .page {{
      max-width: 816px;
      margin: 24px auto;
      background: #fff;
      border: 1px solid var(--line);
      padding: 0 0 24px;
    }}
    .banner {{
      background: var(--teal);
      color: #fff;
      padding: 14px 24px;
      display: flex;
      justify-content: space-between;
      align-items: baseline;
    }}
    .banner strong {{ font-size: 18px; letter-spacing: 0.04em; }}
    .banner span {{ font-size: 12px; opacity: 0.9; }}
    section {{ padding: 16px 24px 0; }}
    h2 {{ font-size: 13px; margin: 0 0 10px; }}
    .card {{
      border: 1px solid var(--line);
      border-radius: 4px;
      padding: 12px;
      margin-bottom: 12px;
    }}
    .card.muted {{ background: var(--wash); }}
    .grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px 16px;
    }}
    .kv label {{
      display: block;
      font-size: 10px;
      text-transform: uppercase;
      color: var(--muted);
      letter-spacing: 0.04em;
    }}
    .kv div {{ font-size: 13px; font-weight: 700; margin-top: 2px; }}
    .pending {{
      background: var(--warn);
      border: 1px solid var(--warn-border);
      color: #734a0a;
      border-radius: 4px;
      padding: 10px 12px;
      font-size: 12px;
      line-height: 1.4;
      margin-bottom: 12px;
    }}
    .graph {{
      border: 1px solid var(--line);
      position: relative;
      overflow: hidden;
    }}
    .graph-head {{
      display: grid;
      grid-template-columns: 140px 1fr 48px;
      font-size: 10px;
      color: var(--muted);
      padding: 4px 0;
    }}
    .hours {{
      display: grid;
      grid-template-columns: repeat(24, 1fr);
      text-align: center;
    }}
    .row {{
      display: grid;
      grid-template-columns: 140px 1fr 48px;
      border-top: 1px solid var(--line);
      min-height: 28px;
      align-items: center;
      font-size: 12px;
    }}
    .row:nth-child(even) {{ background: #fafbfc; }}
    .row .label {{ padding-left: 8px; }}
    .row .cells {{
      display: grid;
      grid-template-columns: repeat(24, 1fr);
      height: 100%;
      border-left: 1px solid var(--line);
      border-right: 1px solid var(--line);
    }}
    .row .cells span {{ border-right: 1px solid #edf0f2; }}
    .row .total {{ text-align: center; color: var(--muted); }}
    .watermark {{
      position: absolute;
      inset: 28px 48px 0 140px;
      display: grid;
      place-items: center;
      color: #b0b8be;
      font-weight: 700;
      font-size: 14px;
      pointer-events: none;
      letter-spacing: 0.02em;
    }}
    .legend {{
      display: flex;
      gap: 18px;
      flex-wrap: wrap;
      font-size: 12px;
      margin: 8px 0 14px;
    }}
    .legend i {{
      display: inline-block;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      margin-right: 6px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }}
    th {{
      background: var(--teal);
      color: #fff;
      text-align: left;
      padding: 6px 8px;
      font-size: 11px;
    }}
    td {{
      border: 1px solid var(--line);
      padding: 6px 8px;
      color: var(--muted);
    }}
    .totals {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      border: 1px solid var(--line);
      border-radius: 4px;
      padding: 10px;
      margin-bottom: 12px;
    }}
    footer {{
      margin: 16px 24px 0;
      font-size: 11px;
      color: var(--muted);
      border-top: 1px solid var(--line);
      padding-top: 10px;
    }}
  </style>
</head>
<body>
  <article class="page">
    <header class="banner">
      <div><strong>MOTIVE</strong> &nbsp; Electronic Logging Device — Daily Log</div>
      <span>Not an official Motive export</span>
    </header>

    <section>
      <h2>Daily Header</h2>
      <div class="card">
        <div class="grid">
          <div class="kv"><label>Log Date</label><div>— (pending rate confirmation)</div></div>
          <div class="kv"><label>Timezone</label><div>— (home terminal)</div></div>
          <div class="kv"><label>Driver</label><div>{DRIVER_NAME}</div></div>
          <div class="kv"><label>Co-Driver</label><div>—</div></div>
          <div class="kv"><label>Carrier</label><div>{CARRIER_NAME}</div></div>
          <div class="kv"><label>MC #</label><div>{MC_NUMBER}</div></div>
          <div class="kv"><label>Truck / CMV</label><div>{TRUCK_NUMBER}</div></div>
          <div class="kv"><label>Trailer</label><div>{TRAILER_NUMBER}</div></div>
        </div>
      </div>

      <h2>Trip / Shipping (from rate confirmation)</h2>
      <div class="card muted">
        <div class="grid">
          <div class="kv"><label>From</label><div>—</div></div>
          <div class="kv"><label>To</label><div>—</div></div>
          <div class="kv"><label>Pickup Date</label><div>—</div></div>
          <div class="kv"><label>Pickup Time</label><div>—</div></div>
          <div class="kv"><label>Pickup City</label><div>—</div></div>
          <div class="kv"><label>Delivery</label><div>—</div></div>
          <div class="kv"><label>Ship Doc #</label><div>—</div></div>
        </div>
      </div>

      <div class="pending">{PENDING_NOTE}</div>

      <h2>24-Hour Duty Status Graph</h2>
      <p style="font-size:12px;color:var(--muted);margin:0 0 8px;">Intentionally blank — no duty status or driving hours entered</p>
      <div class="graph">
        <div class="graph-head">
          <div></div>
          <div class="hours">
            <span>M</span><span></span><span>2</span><span></span><span>4</span><span></span><span>6</span><span></span><span>8</span><span></span><span>10</span><span></span>
            <span>N</span><span></span><span>2</span><span></span><span>4</span><span></span><span>6</span><span></span><span>8</span><span></span><span>10</span><span></span>
          </div>
          <div style="text-align:center;">Total</div>
        </div>
        <div class="row"><div class="label">1. Off Duty</div><div class="cells">{"".join("<span></span>" for _ in range(24))}</div><div class="total">—</div></div>
        <div class="row"><div class="label">2. Sleeper Berth</div><div class="cells">{"".join("<span></span>" for _ in range(24))}</div><div class="total">—</div></div>
        <div class="row"><div class="label">3. Driving</div><div class="cells">{"".join("<span></span>" for _ in range(24))}</div><div class="total">—</div></div>
        <div class="row"><div class="label">4. On Duty (Not Driving)</div><div class="cells">{"".join("<span></span>" for _ in range(24))}</div><div class="total">—</div></div>
        <div class="watermark">NO DUTY STATUS RECORDED</div>
      </div>

      <div class="legend">
        <span><i style="background:#8c9499"></i>Off Duty</span>
        <span><i style="background:#598cdc"></i>Sleeper Berth</span>
        <span><i style="background:#33a673"></i>Driving</span>
        <span><i style="background:#e68c33"></i>On Duty (ND)</span>
      </div>

      <h2>Hours of Service Totals (blank)</h2>
      <div class="totals">
        <div class="kv"><label>Off Duty</label><div>—</div></div>
        <div class="kv"><label>Sleeper Berth</label><div>—</div></div>
        <div class="kv"><label>Driving</label><div>—</div></div>
        <div class="kv"><label>On Duty (Not Driving)</label><div>—</div></div>
        <div class="kv"><label>Total Miles Today</label><div>—</div></div>
        <div class="kv"><label>Engine Hours</label><div>—</div></div>
      </div>

      <h2>Event List / Log Details</h2>
      <table>
        <thead>
          <tr>
            <th>Time</th><th>Status</th><th>Location</th>
            <th>Odometer</th><th>Eng. Hrs</th><th>Notes</th>
          </tr>
        </thead>
        <tbody>
          {"".join("<tr>" + "".join("<td>—</td>" for _ in range(6)) + "</tr>" for _ in range(6))}
        </tbody>
      </table>
    </section>

    <footer>
      Document shell styled after Motive ELD daily log layout (header · graph · legend · events).
      Duty status / hours intentionally empty. Companion to {pdf_path.name}.
    </footer>
  </article>
</body>
</html>
"""
    html_path.write_text(html, encoding="utf-8")
    return html_path


def main() -> None:
    pdf = generate()
    html = generate_html_companion(pdf)
    # Also copy into artifacts for easy download from the agent run
    artifacts = Path("/opt/cursor/artifacts")
    artifacts.mkdir(parents=True, exist_ok=True)
    artifact_pdf = artifacts / pdf.name
    artifact_html = artifacts / html.name
    artifact_pdf.write_bytes(pdf.read_bytes())
    artifact_html.write_text(html.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"PDF: {pdf}")
    print(f"HTML: {html}")
    print(f"Artifact PDF: {artifact_pdf}")
    print(f"Artifact HTML: {artifact_html}")


if __name__ == "__main__":
    main()
