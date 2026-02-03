from pathlib import Path
import csv
from datetime import datetime

BASE_DIR = Path(__file__).parent
ATHLETES_DIR = BASE_DIR / "athletes"
TEAM_TEMPLATE = BASE_DIR / "team-template.html"
OUTPUT_PATH = BASE_DIR / "index.html"



def safe(row, key, default="N/A"):
    val = (row.get(key) or "").strip()
    return val if val else default


def parse_date(d):
    try:
        return datetime.strptime(d, "%b %d %Y")
    except Exception:
        return None


def time_to_seconds(t):
    if ":" not in t:
        return None
    t = t.replace("PR", "").strip()
    m, s = t.split(":")
    return int(m) * 60 + float(s)


def is_valid_grade(g):
    try:
        g = int(g)
        return 7 <= g <= 12
    except Exception:
        return False


def read_csv_after_header(path: Path):
    with path.open(encoding="utf-8") as f:
        lines = f.read().splitlines()

    header_idx = next(
        i for i, line in enumerate(lines) if line.startswith("Name,")
    )

    return list(csv.DictReader(lines[header_idx:]))


def build_summary(records):
    dated_rows = []
    pr_secs = None
    pr_str = "N/A"

    for r in records:
        d = parse_date(safe(r, "Date"))
        if d:
            dated_rows.append((d, r))

        secs = time_to_seconds(safe(r, "Time"))
        if secs is not None and (pr_secs is None or secs < pr_secs):
            pr_secs = secs
            pr_str = safe(r, "Time")

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

            secs = time_to_seconds(safe(r, "Time"))
            if secs is not None and (sr_secs is None or secs < sr_secs):
                sr_secs = secs
                sr_str = safe(r, "Time")

    return pr_str, sr_str, current_grade



def build_athlete_card(athlete_id: str) -> str:
    athlete_dir = ATHLETES_DIR / athlete_id
    csv_files = list(athlete_dir.glob("*.csv"))

    if not csv_files:
        return ""

    records = read_csv_after_header(csv_files[0])
    pr, sr, grade = build_summary(records)

    name = records[0].get("Name", "Athlete")
    link = f"./athletes/{athlete_id}/index.html"

    return f"""
    <div class="athlete-card">
      <a href="{link}" class="athlete-name">{name}</a>
      <div class="athlete-meta">
        <span class="athlete-grade">Grade: {grade}</span>
        <span class="athlete-sr">SR: {sr}</span>
        <span class="athlete-pr">PR: {pr}</span>
      </div>
    </div>
    """


def main():
    cards = []

    for athlete_dir in sorted(ATHLETES_DIR.iterdir()):
        if athlete_dir.is_dir():
            card = build_athlete_card(athlete_dir.name)
            if card:
                cards.append(card)

    template = TEAM_TEMPLATE.read_text(encoding="utf-8")
    html = template.replace("{{ATHLETE_CARDS}}", "\n".join(cards))

    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print("Team roster generated")


if __name__ == "__main__":
    main()
