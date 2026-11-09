#!/usr/bin/env python3
"""Generate Motive-style ELD daily log packet from rate-confirmation data.

Only carrier/driver/vehicle identity and trip fields present on rate
confirmations are filled. Duty status, driving hours, graph segments, and
event rows stay blank. Not an official Motive export / not certified RODS.
"""

from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parent
LOADS_PATH = ROOT / "loads.json"
PDF_PATH = ROOT / "Wali_Abdur_Rahman_Motive_ELD_Log.pdf"
HTML_PATH = ROOT / "Wali_Abdur_Rahman_Motive_ELD_Log.html"
CHART_HTML_PATH = ROOT / "loads_data_chart.html"
ARTIFACTS = Path("/opt/cursor/artifacts")

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


def load_data() -> dict:
    return json.loads(LOADS_PATH.read_text(encoding="utf-8"))


def _dash(value) -> str:
    if value is None:
        return "—"
    text = str(value).strip()
    return text if text else "—"


def _money(value) -> str:
    if value is None:
        return "—"
    return f"${value:,.2f}"


def _kv(c: canvas.Canvas, x: float, y: float, label: str, value: str, label_w: float = 78) -> None:
    c.setFillColor(colors.Color(0.35, 0.38, 0.40))
    c.setFont("Helvetica", 7)
    c.drawString(x, y, label.upper())
    c.setFillColor(MOTIVE_DARK)
    c.setFont("Helvetica-Bold", 9)
    # Truncate long values
    display = value if len(value) <= 48 else value[:45] + "..."
    c.drawString(x + label_w, y - 1, display)


def _header_bar(c: canvas.Canvas, width: float, y: float, subtitle: str) -> float:
    c.setFillColor(MOTIVE_TEAL)
    c.rect(0, y - 8, width, 48, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(36, y + 18, "MOTIVE")
    c.setFont("Helvetica", 9)
    c.drawString(110, y + 20, "Electronic Logging Device — Daily Log")
    c.setFont("Helvetica", 8)
    c.drawRightString(width - 36, y + 22, subtitle)
    c.drawRightString(width - 36, y + 10, "Not an official Motive export")
    return y - 28


def _footer(c: canvas.Canvas, width: float, page_no: int, total: int) -> None:
    c.setFillColor(colors.Color(0.45, 0.45, 0.45))
    c.setFont("Helvetica", 7)
    c.drawString(
        36,
        24,
        "Trip fields from rate confirmations only. Duty status / hours intentionally blank.",
    )
    c.drawRightString(width - 36, 24, f"Page {page_no} of {total}")


def draw_summary_page(c: canvas.Canvas, data: dict, page_no: int, total: int) -> None:
    width, height = letter
    y = height - 36
    y = _header_bar(c, width, y, "Load packet summary")

    carrier = data["carrier"]
    c.setFillColor(MOTIVE_DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(36, y, "Carrier / Driver Identity")
    y -= 16
    c.setStrokeColor(MED_GRAY)
    c.setFillColor(colors.white)
    c.roundRect(36, y - 78, width - 72, 78, 4, fill=1, stroke=1)
    _kv(c, 46, y - 16, "Carrier", carrier["name"], 70)
    _kv(c, 320, y - 16, "MC #", carrier["mc"], 50)
    _kv(c, 46, y - 34, "Driver", carrier["driver"], 70)
    _kv(c, 320, y - 34, "DOT #", carrier["dot"], 50)
    _kv(c, 46, y - 52, "Truck", carrier["truck"], 70)
    _kv(c, 160, y - 52, "Trailer", carrier["trailer"], 50)
    _kv(c, 320, y - 52, "DBA", carrier.get("dba", "—"), 50)
    y -= 96

    styles = getSampleStyleSheet()
    pending = ParagraphStyle(
        "Pending",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.Color(0.45, 0.28, 0.05),
    )
    note = (
        "PENDING / RULES: Duty status graph, driving hours, engine hours, odometer, "
        "and event list remain intentionally blank on every daily page. Only identity "
        "and trip fields found on the attached rate confirmations / BOL photos are filled. "
        "This packet is a document shell styled after Motive ELD layout — not certified RODS."
    )
    p = Paragraph(note, pending)
    w, h = p.wrap(width - 88, 80)
    c.setFillColor(colors.Color(1.0, 0.95, 0.85))
    c.setStrokeColor(colors.Color(0.85, 0.65, 0.20))
    c.roundRect(36, y - h - 16, width - 72, h + 16, 4, fill=1, stroke=1)
    p.drawOn(c, 44, y - h - 8)
    y -= h + 30

    loads = data["loads"]
    total_rate = sum(l.get("rate_usd") or 0 for l in loads)
    c.setFillColor(MOTIVE_DARK)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(36, y, "Loads data chart (from rate confirmations)")
    y -= 6
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.Color(0.4, 0.4, 0.4))
    c.drawString(36, y - 10, f"{len(loads)} loads · total invoice rate {_money(total_rate)} · Oct 2 – Nov 5, 2026")
    y -= 24

    # Simple bar chart of rates
    chart_left = 36
    chart_bottom = y - 130
    chart_width = width - 72
    chart_height = 110
    max_rate = max((l.get("rate_usd") or 0) for l in loads) or 1
    c.setStrokeColor(MED_GRAY)
    c.setFillColor(LIGHT_GRAY)
    c.rect(chart_left, chart_bottom, chart_width, chart_height, fill=1, stroke=1)
    bar_gap = 6
    bar_w = (chart_width - 20 - bar_gap * (len(loads) - 1)) / len(loads)
    for i, load in enumerate(loads):
        rate = load.get("rate_usd") or 0
        bh = (rate / max_rate) * (chart_height - 28)
        bx = chart_left + 10 + i * (bar_w + bar_gap)
        c.setFillColor(MOTIVE_TEAL)
        c.rect(bx, chart_bottom + 18, bar_w, bh, fill=1, stroke=0)
        c.setFillColor(MOTIVE_DARK)
        c.setFont("Helvetica", 5)
        label = str(load["load_number"])[-6:]
        c.drawCentredString(bx + bar_w / 2, chart_bottom + 4, label)
        c.setFont("Helvetica", 5)
        c.drawCentredString(bx + bar_w / 2, chart_bottom + 18 + bh + 2, f"${int(rate)}")
    y = chart_bottom - 16

    # Table header
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(MOTIVE_DARK)
    c.drawString(36, y, "Load schedule")
    y -= 12
    headers = ["Load #", "Broker", "Pickup", "Delivery", "Rate"]
    col_x = [36, 110, 250, 400, 520]
    c.setFillColor(MOTIVE_TEAL)
    c.rect(36, y - 14, width - 72, 16, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 7)
    for i, h in enumerate(headers):
        c.drawString(col_x[i], y - 10, h)
    y -= 14
    c.setFont("Helvetica", 6.5)
    for idx, load in enumerate(loads):
        if y < 60:
            break
        if idx % 2 == 0:
            c.setFillColor(LIGHT_GRAY)
            c.rect(36, y - 18, width - 72, 18, fill=1, stroke=0)
        c.setFillColor(MOTIVE_DARK)
        pu = f"{load['pickup']['date'][5:]} {load['pickup']['city']}"
        de = f"{load['delivery']['date'][5:]} {load['delivery']['city']}"
        vals = [
            str(load["load_number"])[:12],
            (load["broker"][:22]),
            pu[:28],
            de[:28],
            _money(load.get("rate_usd")),
        ]
        for i, v in enumerate(vals):
            c.drawString(col_x[i], y - 12, v)
        y -= 18

    _footer(c, width, page_no, total)
    c.showPage()


def draw_missing_page(c: canvas.Canvas, data: dict, page_no: int, total: int) -> None:
    width, height = letter
    y = height - 36
    y = _header_bar(c, width, y, "Missing items checklist")

    c.setFillColor(MOTIVE_DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(36, y, "What is still missing for a complete Motive ELD packet")
    y -= 18

    global_missing = [
        "All duty status / HOS graph segments (Off Duty, Sleeper, Driving, On Duty)",
        "All driving-hour and status totals",
        "Event list timestamps / locations from ELD (only appointment windows from RCs are known)",
        "Engine hours and odometer / total miles driven today (except RC estimated miles where present)",
        "Vehicle VIN / license plate",
        "Home terminal timezone",
        "Driver certification signature on each daily log",
        "Official Motive Vehicle Gateway export (this PDF is a styled shell only)",
    ]
    c.setFont("Helvetica-Bold", 9)
    c.drawString(36, y, "Packet-wide gaps")
    y -= 14
    c.setFont("Helvetica", 8)
    for item in global_missing:
        c.drawString(44, y, f"• {item}")
        y -= 12

    y -= 8
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(MOTIVE_DARK)
    c.drawString(36, y, "Per-load gaps from the attached files")
    y -= 14
    c.setFont("Helvetica", 7.5)
    for load in data["loads"]:
        if y < 70:
            c.setFillColor(colors.Color(0.45, 0.45, 0.45))
            c.drawString(36, y, "(continued items summarized in loads.json)")
            break
        missing = load.get("missing") or []
        if not missing:
            continue
        c.setFillColor(MOTIVE_TEAL)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(44, y, f"Load {load['load_number']} ({load['broker'][:28]})")
        y -= 11
        c.setFillColor(MOTIVE_DARK)
        c.setFont("Helvetica", 7.5)
        for m in missing:
            c.drawString(56, y, f"— {m}")
            y -= 10
        y -= 4

    _footer(c, width, page_no, total)
    c.showPage()


def draw_daily_page(c: canvas.Canvas, carrier: dict, load: dict, page_no: int, total: int) -> None:
    width, height = letter
    y = height - 36
    y = _header_bar(c, width, y, f"Load {load['load_number']}")

    # Identity
    box_h = 92
    c.setStrokeColor(MED_GRAY)
    c.setFillColor(colors.white)
    c.roundRect(36, y - box_h, width - 72, box_h, 4, fill=1, stroke=1)
    c.setFillColor(MOTIVE_DARK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(46, y - 14, "Daily Header")
    log_date = load["pickup"]["date"]
    _kv(c, 46, y - 32, "Log Date", f"{log_date} (pickup day)", 70)
    _kv(c, 320, y - 32, "Timezone", "— (home terminal)", 70)
    _kv(c, 46, y - 50, "Driver", carrier["driver"], 70)
    _kv(c, 320, y - 50, "Co-Driver", "—", 70)
    _kv(c, 46, y - 68, "Carrier", carrier["name"], 70)
    _kv(c, 320, y - 68, "MC #", carrier["mc"], 70)
    _kv(c, 46, y - 84, "Truck", carrier["truck"], 70)
    _kv(c, 160, y - 84, "Trailer", carrier["trailer"], 50)
    _kv(c, 320, y - 84, "VIN / Plate", "—", 70)
    y -= box_h + 10

    # Trip from RC
    trip_h = 88
    c.setFillColor(LIGHT_GRAY)
    c.roundRect(36, y - trip_h, width - 72, trip_h, 4, fill=1, stroke=1)
    c.setFillColor(MOTIVE_DARK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(46, y - 14, "Trip / Shipping (from rate confirmation)")
    pu = load["pickup"]
    de = load["delivery"]
    _kv(c, 46, y - 32, "Load #", str(load["load_number"]), 55)
    _kv(c, 220, y - 32, "Broker", load["broker"][:34], 50)
    _kv(c, 430, y - 32, "Rate", _money(load.get("rate_usd")), 40)
    _kv(c, 46, y - 48, "From", f"{pu['city']} · {pu.get('name','')}"[:42], 45)
    _kv(c, 320, y - 48, "To", f"{de['city']} · {de.get('name','')}"[:42], 35)
    _kv(c, 46, y - 64, "Pickup", f"{pu['date']}  {pu.get('time','')}", 50)
    _kv(c, 320, y - 64, "Delivery", f"{de['date']}  {de.get('time','')}", 55)
    ship = load.get("invoice_number") or "—"
    miles = load.get("miles")
    _kv(c, 46, y - 80, "Ship/Inv #", str(ship), 60)
    _kv(c, 220, y - 80, "Miles (RC)", _dash(miles), 60)
    _kv(c, 380, y - 80, "Commodity", _dash(load.get("commodity"))[:28], 60)
    y -= trip_h + 10

    # Pending banner
    c.setFillColor(colors.Color(1.0, 0.95, 0.85))
    c.setStrokeColor(colors.Color(0.85, 0.65, 0.20))
    c.roundRect(36, y - 28, width - 72, 28, 3, fill=1, stroke=1)
    c.setFillColor(colors.Color(0.45, 0.28, 0.05))
    c.setFont("Helvetica", 7.5)
    c.drawString(
        44,
        y - 18,
        "HOS blank by design: no estimated driving/on-duty/off-duty/sleeper times. Appointment windows are not duty status.",
    )
    y -= 40

    # Graph
    c.setFillColor(MOTIVE_DARK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(36, y, "24-Hour Duty Status Graph")
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.Color(0.4, 0.4, 0.4))
    c.drawString(200, y + 1, "Intentionally blank")
    y -= 8
    left, right = 36, width - 36
    label_w, totals_w = 118, 48
    grid_left = left + label_w
    grid_right = right - totals_w
    grid_w = grid_right - grid_left
    graph_h = 100
    c.setFont("Helvetica", 6)
    c.setFillColor(MOTIVE_DARK)
    for hour in range(0, 25, 2):
        x = grid_left + (grid_w * hour / 24.0)
        label = "M" if hour == 0 else ("N" if hour == 12 else str(hour % 12 or 12))
        c.drawCentredString(x, y - 10, label)
    c.drawRightString(right - 4, y - 10, "Total")
    y -= 14
    c.setStrokeColor(MED_GRAY)
    c.setFillColor(colors.white)
    c.rect(left, y - graph_h, right - left, graph_h, fill=1, stroke=1)
    row_h = graph_h / 4.0
    for i, (num, name) in enumerate(ROW_LABELS):
        top = y - i * row_h
        if i % 2 == 0:
            c.setFillColor(colors.Color(0.97, 0.98, 0.98))
            c.rect(left, top - row_h, right - left, row_h, fill=1, stroke=0)
        c.setStrokeColor(MED_GRAY)
        c.line(left, top - row_h, right, top - row_h)
        c.setFillColor(MOTIVE_DARK)
        c.setFont("Helvetica", 8)
        c.drawString(left + 6, top - row_h / 2 - 3, f"{num}. {name}")
        c.line(grid_right, top, grid_right, top - row_h)
        c.setFillColor(colors.Color(0.55, 0.55, 0.55))
        c.drawCentredString(grid_right + totals_w / 2, top - row_h / 2 - 3, "—")
    for hour in range(25):
        x = grid_left + (grid_w * hour / 24.0)
        c.setStrokeColor(colors.Color(0.85, 0.87, 0.88) if hour % 6 else MED_GRAY)
        c.setLineWidth(0.6 if hour % 6 else 1)
        c.line(x, y, x, y - graph_h)
    c.setLineWidth(1)
    c.setFillColor(colors.Color(0.75, 0.78, 0.80))
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString((grid_left + grid_right) / 2, y - graph_h / 2 - 4, "NO DUTY STATUS RECORDED")
    y -= graph_h + 12

    # Totals
    c.setFillColor(MOTIVE_DARK)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(36, y, "Hours of Service Totals (blank)")
    y -= 8
    c.setStrokeColor(MED_GRAY)
    c.setFillColor(colors.white)
    c.roundRect(36, y - 36, width - 72, 40, 3, fill=1, stroke=1)
    totals = [
        ("Off Duty", "—"),
        ("Sleeper", "—"),
        ("Driving", "—"),
        ("On Duty ND", "—"),
        ("Miles Today", "—"),
        ("Engine Hrs", "—"),
    ]
    for i, (label, value) in enumerate(totals):
        tx = 46 + (i % 3) * 175
        ty = y - 12 - (i // 3) * 16
        c.setFillColor(colors.Color(0.4, 0.4, 0.4))
        c.setFont("Helvetica", 6.5)
        c.drawString(tx, ty, label.upper())
        c.setFillColor(MOTIVE_DARK)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(tx + 70, ty - 1, value)
    y -= 50

    # Events
    c.setFillColor(MOTIVE_DARK)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(36, y, "Event List / Log Details")
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.Color(0.45, 0.45, 0.45))
    c.drawString(170, y + 1, "No HOS events — blank")
    y -= 8
    headers = ["Time", "Status", "Location", "Odometer", "Eng. Hrs", "Notes"]
    col_x = [40, 90, 180, 340, 410, 470]
    header_h, row_h, rows = 14, 14, 4
    table_h = header_h + rows * row_h
    c.setFillColor(LIGHT_GRAY)
    c.rect(36, y - table_h, width - 72, table_h, fill=1, stroke=1)
    c.setFillColor(MOTIVE_TEAL)
    c.rect(36, y - header_h, width - 72, header_h, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 7)
    for i, h in enumerate(headers):
        c.drawString(col_x[i], y - 10, h)
    c.setFillColor(colors.Color(0.55, 0.55, 0.55))
    c.setFont("Helvetica", 8)
    for r in range(rows):
        top = y - header_h - r * row_h
        c.setStrokeColor(MED_GRAY)
        c.line(36, top - row_h, width - 36, top - row_h)
        for i in range(len(headers)):
            c.drawString(col_x[i], top - 10, "—")
    y -= table_h + 10

    # Certification
    c.setStrokeColor(MED_GRAY)
    c.setFillColor(colors.white)
    c.roundRect(36, y - 48, width - 72, 48, 3, fill=1, stroke=1)
    c.setFillColor(MOTIVE_DARK)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(46, y - 14, "Driver Certification")
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.Color(0.4, 0.4, 0.4))
    c.drawString(46, y - 26, "Signature deferred — HOS incomplete. Trip header only from rate confirmation.")
    c.setStrokeColor(MED_GRAY)
    c.line(46, y - 38, 240, y - 38)
    c.line(260, y - 38, 380, y - 38)
    c.setFont("Helvetica", 7)
    c.setFillColor(MOTIVE_DARK)
    c.drawString(46, y - 46, f"Driver: {carrier['driver']}")
    c.drawString(260, y - 46, "Date: —")

    _footer(c, width, page_no, total)
    c.showPage()


def generate_pdf(data: dict) -> Path:
    loads = data["loads"]
    total_pages = 2 + len(loads)  # summary + missing + one per load
    c = canvas.Canvas(str(PDF_PATH), pagesize=letter)
    c.setTitle(f"Motive-style ELD Log Packet — {data['carrier']['driver']}")
    c.setAuthor(data["carrier"]["name"])
    c.setSubject("Draft ELD packet; HOS blank; trip fields from rate confirmations")

    draw_summary_page(c, data, 1, total_pages)
    page = 2
    for load in loads:
        draw_daily_page(c, data["carrier"], load, page, total_pages)
        page += 1
    draw_missing_page(c, data, page, total_pages)
    c.save()
    return PDF_PATH


def generate_html(data: dict) -> Path:
    carrier = data["carrier"]
    loads = data["loads"]
    total_rate = sum(l.get("rate_usd") or 0 for l in loads)
    rows = []
    for load in loads:
        rows.append(
            "<tr>"
            f"<td>{load['load_number']}</td>"
            f"<td>{load['broker']}</td>"
            f"<td>{load['pickup']['date']}<br/><small>{load['pickup']['city']}<br/>{load['pickup'].get('time','')}</small></td>"
            f"<td>{load['delivery']['date']}<br/><small>{load['delivery']['city']}<br/>{load['delivery'].get('time','')}</small></td>"
            f"<td>{_money(load.get('rate_usd'))}</td>"
            f"<td>{_dash(load.get('miles'))}</td>"
            f"<td>{_dash(load.get('commodity'))}</td>"
            "</tr>"
        )
    missing_items = []
    for load in loads:
        for m in load.get("missing") or []:
            missing_items.append(f"<li><strong>{load['load_number']}:</strong> {m}</li>")

    max_rate = max((l.get("rate_usd") or 0) for l in loads) or 1
    bars = []
    for load in loads:
        pct = int(round(((load.get("rate_usd") or 0) / max_rate) * 100))
        bars.append(
            f"<div class='bar-row'><span class='bar-label'>{load['load_number']}</span>"
            f"<div class='bar-track'><div class='bar-fill' style='width:{pct}%'></div></div>"
            f"<span class='bar-val'>{_money(load.get('rate_usd'))}</span></div>"
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Motive-style ELD Packet — {carrier['driver']}</title>
<style>
:root {{ --teal:#008c8c; --ink:#1f2930; --muted:#6b7280; --line:#c5ced3; --wash:#f3f5f6; --warn:#fff4d6; }}
body {{ margin:0; font-family:Helvetica,Arial,sans-serif; color:var(--ink); background:#e8ecef; }}
.wrap {{ max-width:980px; margin:24px auto; background:#fff; border:1px solid var(--line); }}
.banner {{ background:var(--teal); color:#fff; padding:14px 24px; display:flex; justify-content:space-between; }}
section {{ padding:18px 24px; }}
h1 {{ font-size:18px; margin:0 0 8px; }}
h2 {{ font-size:14px; margin:18px 0 8px; }}
.grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }}
.kv label {{ display:block; font-size:10px; text-transform:uppercase; color:var(--muted); }}
.kv div {{ font-weight:700; font-size:13px; }}
.pending {{ background:var(--warn); border:1px solid #d9a63a; padding:10px 12px; font-size:12px; color:#734a0a; }}
table {{ width:100%; border-collapse:collapse; font-size:12px; }}
th {{ background:var(--teal); color:#fff; text-align:left; padding:7px 8px; }}
td {{ border:1px solid var(--line); padding:7px 8px; vertical-align:top; }}
.bar-row {{ display:grid; grid-template-columns:110px 1fr 70px; gap:8px; align-items:center; margin:6px 0; font-size:12px; }}
.bar-track {{ background:var(--wash); height:14px; border:1px solid var(--line); }}
.bar-fill {{ background:var(--teal); height:100%; }}
.bar-val {{ text-align:right; font-weight:700; }}
.stats {{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin:12px 0; }}
.stat {{ border:1px solid var(--line); padding:10px; }}
.stat strong {{ display:block; font-size:20px; }}
ul {{ font-size:13px; line-height:1.45; }}
footer {{ padding:12px 24px; font-size:11px; color:var(--muted); border-top:1px solid var(--line); }}
</style>
</head>
<body>
<div class="wrap">
  <div class="banner"><div><strong>MOTIVE</strong> ELD Log Packet</div><span>Not an official Motive export</span></div>
  <section>
    <h1>{carrier['driver']} · {carrier['name']}</h1>
    <div class="grid">
      <div class="kv"><label>MC</label><div>{carrier['mc']}</div></div>
      <div class="kv"><label>DOT</label><div>{carrier['dot']}</div></div>
      <div class="kv"><label>Truck / Trailer</label><div>{carrier['truck']} / {carrier['trailer']}</div></div>
    </div>
    <p class="pending" style="margin-top:12px">Duty status, driving hours, engine hours, and event lists are intentionally blank on every daily page. Trip fields come only from the attached rate confirmations.</p>
    <div class="stats">
      <div class="stat"><label>Loads</label><strong>{len(loads)}</strong></div>
      <div class="stat"><label>Total invoice rate</label><strong>{_money(total_rate)}</strong></div>
      <div class="stat"><label>Date span</label><strong>Oct 2 – Nov 5, 2026</strong></div>
    </div>
    <h2>Rate chart</h2>
    {''.join(bars)}
    <h2>Loads table</h2>
    <table>
      <thead><tr><th>Load #</th><th>Broker</th><th>Pickup</th><th>Delivery</th><th>Rate</th><th>Miles</th><th>Commodity</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    <h2>Missing items</h2>
    <ul>
      <li>All HOS / duty-status graph data and totals</li>
      <li>VIN / plate, home terminal timezone, driver certification signatures</li>
      <li>Official Motive Vehicle Gateway export</li>
      {''.join(missing_items)}
    </ul>
  </section>
  <footer>Companion to {PDF_PATH.name}. Regenerated from loads.json.</footer>
</div>
</body>
</html>
"""
    HTML_PATH.write_text(html, encoding="utf-8")
    CHART_HTML_PATH.write_text(html, encoding="utf-8")
    return HTML_PATH


def main() -> None:
    data = load_data()
    pdf = generate_pdf(data)
    html = generate_html(data)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    for src in (pdf, html, CHART_HTML_PATH, LOADS_PATH):
        dest = ARTIFACTS / src.name
        dest.write_bytes(src.read_bytes())
        print(f"Artifact: {dest}")
    print(f"PDF: {pdf}")
    print(f"HTML: {html}")
    print(f"Loads: {len(data['loads'])}")


if __name__ == "__main__":
    main()
