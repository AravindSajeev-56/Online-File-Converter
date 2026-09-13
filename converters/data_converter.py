"""
Data and Spreadsheet Converter Module for 56 File Converter
Handles XLSX, CSV, and JSON conversions.
"""

import os
import csv
import json
import html
from typing import List, Any

import openpyxl
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer


def _read_csv(file_path: str) -> List[List[str]]:
    """Read CSV file into a 2D list of strings with encoding fallback."""
    for enc in ["utf-8", "utf-8-sig", "latin1", "cp1252"]:
        try:
            with open(file_path, "r", encoding=enc, newline="") as f:
                # Detect delimiter if possible
                sample = f.read(2048)
                f.seek(0)
                delimiter = ","
                if sample:
                    try:
                        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
                        delimiter = dialect.delimiter
                    except Exception:
                        delimiter = ","
                reader = csv.reader(f, delimiter=delimiter)
                return [row for row in reader]
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not decode CSV file with supported encodings.")


def _read_xlsx(file_path: str) -> List[List[Any]]:
    """Read first sheet of an XLSX file into a 2D list of values."""
    wb = openpyxl.load_workbook(file_path, data_only=True)
    sheet = wb.active
    rows = []
    for row in sheet.iter_rows(values_only=True):
        if any(cell is not None for cell in row):
            rows.append([cell if cell is not None else "" for cell in row])
    wb.close()
    return rows


def _render_table_to_pdf(data: List[List[Any]], output_path: str, title: str = "Data Sheet"):
    """Render a 2D table into a clean PDF using ReportLab."""
    if not data:
        data = [["No data available"]]

    # Use landscape if more than 5 columns
    is_wide = len(data[0]) > 5
    page_size = landscape(letter) if is_wide else letter
    page_width = page_size[0] - 72  # margins: 36 on each side

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TableTitle',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=12
    )
    cell_style = ParagraphStyle(
        'Cell',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#111827')
    )
    header_style = ParagraphStyle(
        'HeaderCell',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=11,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )

    story = [Paragraph(html.escape(title), title_style), Spacer(1, 8)]

    # Format cell content
    formatted_data = []
    col_count = len(data[0]) if data else 1
    col_width = max(30, page_width / col_count)

    for r_idx, row in enumerate(data):
        row_cells = []
        for c_idx in range(col_count):
            val = str(row[c_idx]) if c_idx < len(row) else ""
            clean_val = html.escape(val[:100])  # limit length
            st = header_style if r_idx == 0 else cell_style
            row_cells.append(Paragraph(clean_val, st))
        formatted_data.append(row_cells)

    t = Table(formatted_data, colWidths=[col_width] * col_count, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
    ]))

    story.append(t)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=page_size,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    doc.build(story)


def xlsx_to_csv(input_path: str, output_path: str) -> str:
    """Convert XLSX to CSV."""
    rows = _read_xlsx(input_path)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)
    return output_path


def xlsx_to_json(input_path: str, output_path: str) -> str:
    """Convert XLSX to structured JSON."""
    rows = _read_xlsx(input_path)
    if not rows:
        result = []
    elif len(rows) == 1:
        result = [rows[0]]
    else:
        headers = [str(h).strip() or f"col_{i+1}" for i, h in enumerate(rows[0])]
        result = []
        for row in rows[1:]:
            obj = {}
            for i, val in enumerate(row):
                header = headers[i] if i < len(headers) else f"col_{i+1}"
                obj[header] = val
            result.append(obj)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    return output_path


def xlsx_to_html(input_path: str, output_path: str) -> str:
    """Convert XLSX to styled HTML table."""
    rows = _read_xlsx(input_path)
    table_rows = []
    for r_idx, row in enumerate(rows):
        tag = "th" if r_idx == 0 else "td"
        cells = "".join(f"<{tag}>{html.escape(str(c))}</{tag}>" for c in row)
        table_rows.append(f"<tr>{cells}</tr>")

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Excel Sheet</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 24px; background: #f8fafc; color: #1e293b; }}
  .container {{ max-width: 1200px; margin: 0 auto; overflow-x: auto; background: white; padding: 24px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
  table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
  th, td {{ border: 1px solid #e2e8f0; padding: 10px 14px; text-align: left; }}
  th {{ background: #4f46e5; color: white; font-weight: 600; }}
  tr:nth-child(even) {{ background: #f8fafc; }}
  tr:hover {{ background: #f1f5f9; }}
</style>
</head>
<body>
<div class="container">
  <h2>Spreadsheet Data</h2>
  <table>{"".join(table_rows)}</table>
</div>
</body>
</html>"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    return output_path


def xlsx_to_pdf(input_path: str, output_path: str) -> str:
    """Convert XLSX to PDF."""
    rows = _read_xlsx(input_path)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    _render_table_to_pdf(rows, output_path, title=f"Excel Sheet: {base_name}")
    return output_path


def csv_to_xlsx(input_path: str, output_path: str) -> str:
    """Convert CSV to XLSX."""
    rows = _read_csv(input_path)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Data"
    for r_idx, row in enumerate(rows, 1):
        for c_idx, val in enumerate(row, 1):
            # Attempt numeric conversion if possible
            val_to_write = val
            if val.strip().isdigit():
                try:
                    val_to_write = int(val.strip())
                except ValueError:
                    pass
            ws.cell(row=r_idx, column=c_idx, value=val_to_write)
    wb.save(output_path)
    return output_path


def csv_to_json(input_path: str, output_path: str) -> str:
    """Convert CSV to JSON."""
    rows = _read_csv(input_path)
    if not rows:
        result = []
    elif len(rows) == 1:
        result = [rows[0]]
    else:
        headers = [h.strip() or f"col_{i+1}" for i, h in enumerate(rows[0])]
        result = []
        for row in rows[1:]:
            obj = {}
            for i, val in enumerate(row):
                header = headers[i] if i < len(headers) else f"col_{i+1}"
                obj[header] = val
            result.append(obj)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    return output_path


def csv_to_html(input_path: str, output_path: str) -> str:
    """Convert CSV to HTML table."""
    rows = _read_csv(input_path)
    table_rows = []
    for r_idx, row in enumerate(rows):
        tag = "th" if r_idx == 0 else "td"
        cells = "".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in row)
        table_rows.append(f"<tr>{cells}</tr>")

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CSV Data</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 24px; background: #f8fafc; color: #1e293b; }}
  .container {{ max-width: 1200px; margin: 0 auto; overflow-x: auto; background: white; padding: 24px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
  table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
  th, td {{ border: 1px solid #e2e8f0; padding: 10px 14px; text-align: left; }}
  th {{ background: #0ea5e9; color: white; font-weight: 600; }}
  tr:nth-child(even) {{ background: #f8fafc; }}
  tr:hover {{ background: #f1f5f9; }}
</style>
</head>
<body>
<div class="container">
  <h2>CSV Data</h2>
  <table>{"".join(table_rows)}</table>
</div>
</body>
</html>"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    return output_path


def csv_to_pdf(input_path: str, output_path: str) -> str:
    """Convert CSV to PDF."""
    rows = _read_csv(input_path)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    _render_table_to_pdf(rows, output_path, title=f"CSV: {base_name}")
    return output_path


def json_to_csv(input_path: str, output_path: str) -> str:
    """Convert JSON array of objects to CSV."""
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            # Extract distinct keys from all dicts
            headers = []
            for item in data:
                if isinstance(item, dict):
                    for k in item.keys():
                        if k not in headers:
                            headers.append(k)
            writer.writerow(headers)
            for item in data:
                if isinstance(item, dict):
                    writer.writerow([item.get(k, "") for k in headers])
                else:
                    writer.writerow([item])
        elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            for row in data:
                writer.writerow(row)
        elif isinstance(data, dict):
            writer.writerow(["Key", "Value"])
            for k, v in data.items():
                writer.writerow([k, json.dumps(v) if isinstance(v, (dict, list)) else v])
        else:
            writer.writerow(["Value"])
            writer.writerow([data])
    return output_path


def json_to_xlsx(input_path: str, output_path: str) -> str:
    """Convert JSON to XLSX."""
    # Convert JSON to a temp CSV row representation then build workbook
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "JSON Data"

    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        headers = []
        for item in data:
            if isinstance(item, dict):
                for k in item.keys():
                    if k not in headers:
                        headers.append(k)
        ws.append(headers)
        for item in data:
            if isinstance(item, dict):
                ws.append([str(item.get(k, "")) if isinstance(item.get(k), (dict, list)) else item.get(k, "") for k in headers])
            else:
                ws.append([item])
    elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
        for row in data:
            ws.append(row)
    elif isinstance(data, dict):
        ws.append(["Key", "Value"])
        for k, v in data.items():
            ws.append([k, json.dumps(v) if isinstance(v, (dict, list)) else v])
    else:
        ws.append(["Value"])
        ws.append([data])

    wb.save(output_path)
    return output_path


def json_to_html(input_path: str, output_path: str) -> str:
    """Convert JSON to styled interactive/formatted HTML view."""
    with open(input_path, "r", encoding="utf-8") as f:
        raw = f.read()
    try:
        parsed = json.loads(raw)
        formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
    except Exception:
        formatted = raw

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>JSON View</title>
<style>
  body {{ font-family: monospace; padding: 24px; background: #0f172a; color: #38bdf8; margin: 0; }}
  pre {{ background: #1e293b; padding: 20px; border-radius: 8px; overflow-x: auto; line-height: 1.5; color: #f1f5f9; }}
</style>
</head>
<body>
  <pre><code>{html.escape(formatted)}</code></pre>
</body>
</html>"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    return output_path


def convert_data(input_path: str, source_ext: str, target_ext: str, output_dir: str) -> str:
    """Main data and spreadsheet conversion dispatcher."""
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    out_file = os.path.join(output_dir, f"{base_name}.{target_ext}")

    pair = (source_ext, target_ext)

    # XLSX
    if pair == ("xlsx", "csv"):
        return xlsx_to_csv(input_path, out_file)
    elif pair == ("xlsx", "json"):
        return xlsx_to_json(input_path, out_file)
    elif pair == ("xlsx", "html"):
        return xlsx_to_html(input_path, out_file)
    elif pair == ("xlsx", "pdf"):
        return xlsx_to_pdf(input_path, out_file)

    # CSV
    elif pair == ("csv", "xlsx"):
        return csv_to_xlsx(input_path, out_file)
    elif pair == ("csv", "json"):
        return csv_to_json(input_path, out_file)
    elif pair == ("csv", "html"):
        return csv_to_html(input_path, out_file)
    elif pair == ("csv", "pdf"):
        return csv_to_pdf(input_path, out_file)

    # JSON
    elif pair == ("json", "csv"):
        return json_to_csv(input_path, out_file)
    elif pair == ("json", "xlsx"):
        return json_to_xlsx(input_path, out_file)
    elif pair == ("json", "html"):
        return json_to_html(input_path, out_file)

    raise ValueError(f"Unsupported data conversion: {source_ext} -> {target_ext}")
