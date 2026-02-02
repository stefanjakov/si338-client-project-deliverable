import csv
from datetime import datetime
from pathlib import Path

ATHLETE_ID = "21615274"
ATHLETE_NAME = "Garrett Comer"
ATHLETE_URL = f"https://www.athletic.net/athlete/{ATHLETE_ID}/cross-country/"

def safe(row, key, default="N/A"):
    val = (row.get(key) or "").strip()
    return val if val else default


def read_csv_after_header(path: Path):
    with path.open(encoding="utf-8") as f:
        lines = f.read().splitlines()

    header_idx = next(
        i for i, line in enumerate(lines) if line.startswith("Name,")
    )

    reader = csv.DictReader(lines[header_idx:])
    return list(reader)


def time_to_seconds(t):
    if ":" not in t:
        return None
    t = t.replace("PR", "").strip()
    m, s = t.split(":")
    return int(m) * 60 + float(s)


def parse_date(d):
    try:
        return datetime.strptime(d, "%b %d %Y")
    except Exception:
        return None


def build_rows(records):
    rows = []

    for r in records:
        meet = safe(r, "Meet Name")
        date = safe(r, "Date")
        location = "N/A"
        distance = "5K"
        time = safe(r, "Time")
        place = safe(r, "Overall Place")
        grade = safe(r, "Grade")
        url = safe(r, "Meet Results URL", "")

        link = f'<a href="{url}" target="_blank">View Results</a>' if url != "N/A" else "N/A"

        rows.append(
            "<tr>"
            f"<td>{meet}</td>"
            f"<td>{date}</td>"
            f"<td>{location}</td>"
            f"<td>{distance}</td>"
            f"<td>{time}</td>"
            f"<td>{place}</td>"
            f"<td>{grade}</td>"
            f"<td>{link}</td>"
            "</tr>"
        )

    return "\n".join(rows)


def is_valid_grade(g):
    try:
        g = int(g)
        return 7 <= g <= 12
    except ValueError:
        return False

def build_summary(records):
    dated_rows = []
    pr_secs = None
    pr_str = "N/A"

    for r in records:
        d = parse_date(safe(r, "Date"))
        if d:
            dated_rows.append((d, r))

        t_str = safe(r, "Time")
        secs = time_to_seconds(t_str)
        if secs is not None and (pr_secs is None or secs < pr_secs):
            pr_secs = secs
            pr_str = t_str.strip()

    dated_rows.sort(key=lambda x: x[0], reverse=True)

    current_grade = "N/A"
    for _, r in dated_rows:
        g = safe(r, "Grade")
        if is_valid_grade(g):
            current_grade = str(int(g))
            break

    sr_secs = None
    sr_str = "N/A"
    if current_grade != "N/A":
        for r in records:
            g = safe(r, "Grade")
            if not is_valid_grade(g):
                continue
            if str(int(g)) != current_grade:
                continue

            t_str = safe(r, "Time")
            secs = time_to_seconds(t_str)
            if secs is not None and (sr_secs is None or secs < sr_secs):
                sr_secs = secs
                sr_str = t_str.strip()

    return pr_str, sr_str, current_grade

def fill_template(template, values):
    for k, v in values.items():
        template = template.replace(f"{{{{{k}}}}}", str(v))
    return template


def main():
    base = Path(__file__).parent
    csv_path = base / "garrett.csv"
    template_path = base / "player-template.html"
    out_path = base / "index.html"

    records = read_csv_after_header(csv_path)

    rows_html = build_rows(records)
    pr, sr, grade = build_summary(records)

    template = template_path.read_text(encoding="utf-8")

    html = fill_template(
        template,
        {
            "NAME": ATHLETE_NAME,
            "GRADE": grade,
            "SEASON_RECORD": sr,
            "PERSONAL_RECORD": pr,
        },
    )

    html = html.replace("</tbody>", rows_html + "\n</tbody>")

    out_path.write_text(html, encoding="utf-8")
    print("index.html generated")


if __name__ == "__main__":
    main()
