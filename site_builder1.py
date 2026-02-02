import csv
from datetime import datetime
from pathlib import Path

ATHLETE_ID = "21615274"
ATHLETE_URL = f"https://www.athletic.net/athlete/{ATHLETE_ID}/cross-country/"

def safe_get(row, key, default="N/A"):
    value = (row.get(key) or "").strip()
    return value if value else default

import csv
from pathlib import Path

def read_csv_after_header(csv_path: Path, header_startswith="Name,"):
    """
    Reads a CSV file that may have 'preamble' lines before the real header row.
    Finds the first line that starts with header_startswith (default: 'Name,')
    and uses that as the DictReader header line.
    """
    with csv_path.open(encoding="utf-8", newline="") as f:
        # Read all lines (small file; fine for class use)
        lines = f.read().splitlines()

    header_index = None
    for i, line in enumerate(lines):
        if line.startswith(header_startswith):
            header_index = i
            break

    if header_index is None:
        raise ValueError(f"Could not find a header line starting with: {header_startswith}")

    # Feed DictReader only the header+data part
    data_lines = lines[header_index:]
    reader = csv.DictReader(data_lines)
    records = list(reader)
    return records

def parse_date(date_str):
    # Handles dates like "Aug 15 2025". If missing/unparseable, returns None.
    s = (date_str or "").strip()
    if not s or s == "N/A":
        return None
    for fmt in ("%b %d %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None

def time_to_seconds(time_str):
    # Handles mm:ss.s (e.g., 17:22.3) and ignores labels like "PR"
    s = (time_str or "").replace("PR", "").strip()
    if ":" not in s:
        return None
    try:
        mins, secs = s.split(":", 1)
        return int(mins) * 60 + float(secs)
    except ValueError:
        return None

def build_rows(records):
    rows_html = []
    for r in records:
        date = safe_get(r, "Date")
        meet = safe_get(r, "Meet Name")
        time = safe_get(r, "Time")
        place = safe_get(r, "Overall Place")
        grade = safe_get(r, "Grade")

        results_url = (r.get("Meet Results URL") or "").strip()
        meet_id = (r.get("Meet Id") or "").strip()
        race_id = (r.get("Race ID") or "").strip()

        links = []
        if results_url:
            links.append(f'<a href="{results_url}">Results</a>')
        if meet_id != "":
            links.append(f"<span>Meet ID: {meet_id}</span>")
        if race_id != "":
            links.append(f"<span>Race ID: {race_id}</span>")

        links_html = "<br>".join(links) if links else "N/A"

        rows_html.append(
            "<tr>"
            f"<td>{date}</td>"
            f"<td>{meet}</td>"
            f"<td>{time}</td>"
            f"<td>{place}</td>"
            f"<td>{grade}</td>"
            f"<td>{links_html}</td>"
            "</tr>"
        )
    return "\n".join(rows_html)

def build_summary(records):
    total = len(records)

    # Best time
    best = None
    best_time_str = "N/A"
    for r in records:
        t_str = (r.get("Time") or "").strip()
        seconds = time_to_seconds(t_str)
        if seconds is not None and (best is None or seconds < best):
            best = seconds
            best_time_str = t_str

    # Most recent date
    most_recent = None
    most_recent_meet = "N/A"
    for r in records:
        d = parse_date(r.get("Date"))
        if d is not None and (most_recent is None or d > most_recent):
            most_recent = d
            most_recent_meet = safe_get(r, "Meet Name")

    most_recent_date_str = most_recent.strftime("%b %d %Y") if most_recent else "N/A"
    return total, best_time_str, most_recent_date_str, most_recent_meet

def fill_template(template_text, replacements):
    for k, v in replacements.items():
        template_text = template_text.replace(f"{{{{{k}}}}}", str(v))
    return template_text

def main():
    from pathlib import Path

    BASE_DIR = Path(__file__).resolve().parent

    csv_path = BASE_DIR / "garrett.csv"
    template_path = BASE_DIR / "template1.html"
    out_path = BASE_DIR / "index.html"

    print(csv_path)
    print(csv_path.exists())

    

    print("***************************************")
    with csv_path.open(newline="", encoding="utf-8") as f:
        csv_path = BASE_DIR / "garrett.csv"
        records = read_csv_after_header(csv_path)

    print("Detected headers:", records[0].keys())
    print("First row:", records[0])

    rows_html = build_rows(records)
    total, best_time, recent_date, recent_meet = build_summary(records)

    template_text = template_path.read_text(encoding="utf-8")

    replacements = {
        "NAME": "Garrett Comer",
        "ATHLETE_ID": ATHLETE_ID,
        "ATHLETE_URL": ATHLETE_URL,
        "TOTAL_RACES": total,
        "BEST_TIME": best_time,
        "MOST_RECENT_DATE": recent_date,
        "MOST_RECENT_MEET": recent_meet,
        "ROWS": rows_html,
    }

    out_html = fill_template(template_text, replacements)
    out_path.write_text(out_html, encoding="utf-8")
    print("Wrote index.html")

if __name__ == "__main__":
    main()
