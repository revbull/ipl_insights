import os
import json
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# =============================
# CONFIGURATION
# =============================

API_KEY = "YOUR_API_KEY_HERE"   # ← Replace with your CricketData key
BASE_URL = "https://api.cricapi.com/v1"
TODAY = datetime.utcnow().strftime("%Y-%m-%d")

# =============================
# UTILITY FUNCTIONS
# =============================

def parse_form(form_str: str) -> float:
    form_str = form_str.replace(",", " ").upper()
    tokens = [t for t in form_str.split() if t in ("W", "L", "D")]
    if not tokens:
        return 0
    score = sum(1 if t=="W" else -1 if t=="L" else 0 for t in tokens)
    return score / len(tokens)


def form_to_icons(form_string: str) -> str:
    tokens = form_string.replace(",", " ").upper().split()
    out = []
    for t in tokens:
        if t == "W": out.append("🟩")
        elif t == "L": out.append("🟥")
        elif t == "D": out.append("🟨")
    return " ".join(out)


def estimate_projected_score(venue, form_a, form_b) -> str:
    v = venue.lower()

    if any(k in v for k in ["wankhede", "eden", "chinnaswamy"]):
        base_mid = 185; spread = 18
    elif any(k in v for k in ["chepauk", "arun", "delhi"]):
        base_mid = 160; spread = 14
    elif "narendra modi" in v:
        base_mid = 175; spread = 16
    else:
        base_mid = 170; spread = 15

    momentum = (parse_form(form_a) + parse_form(form_b)) / 2
    mid = base_mid + int(momentum * 8)

    low = max(130, mid - spread)
    high = min(230, mid + spread)

    return f"{low} – {high} runs"
def auto_pitch_report(venue):
    pitch_map = {
        "Wankhede": "High-scoring batting-friendly pitch. 180+ likely.",
        "Eden": "Flat early, spin helps later overs.",
        "Chinnaswamy": "Small boundaries — 200+ possible.",
        "Narendra Modi": "Balanced wicket with early seam movement.",
        "Chepauk": "Slow, spin-friendly and low scoring.",
        "Arun Jaitley": "Two-paced wicket, strokeplay difficult."
    }

    for k, v in pitch_map.items():
        if k.lower() in venue.lower():
            return v

    return "Balanced T20 wicket. Expected RR 7.8 – 8.4."


def fetch_h2h_stats(team_a, team_b):
    try:
        url = f"{BASE_URL}/cricScore?apikey={API_KEY}"
        res = requests.get(url).json().get("data", [])

        h2h = [
            m for m in res
            if (
                team_a.lower() in m.get("t1", "").lower() and
                team_b.lower() in m.get("t2", "").lower()
            ) or (
                team_b.lower() in m.get("t1", "").lower() and
                team_a.lower() in m.get("t2", "").lower()
            )
        ]

        if not h2h:
            raise Exception()

        total = len(h2h)
        wins_a = sum(1 for m in h2h if m.get("winner", "").lower() == team_a.lower())
        wins_b = sum(1 for m in h2h if m.get("winner", "").lower() == team_b.lower())

        last5 = h2h[-5:] if len(h2h) >= 5 else h2h
        last5_a = sum(1 for m in last5 if m.get("winner", "").lower() == team_a.lower())
        last5_b = sum(1 for m in last5 if m.get("winner", "").lower() == team_b.lower())

        totals = []
        for m in h2h:
            for k in ("t1s", "t2s"):
                try:
                    runs = int(m.get(k, "0/0").split("/")[0])
                    totals.append(runs)
                except:
                    pass

        avg_total = int(sum(totals) / len(totals)) if totals else 160

        return {
            "total": total,
            "wins_a": wins_a,
            "wins_b": wins_b,
            "last5_a": last5_a,
            "last5_b": last5_b,
            "avg_total": avg_total,
            "highest": max(totals) if totals else 200,
            "lowest": min(totals) if totals else 120,
        }

    except:
        return {
            "total": 10,
            "wins_a": 5,
            "wins_b": 5,
            "last5_a": 2,
            "last5_b": 3,
            "avg_total": 165,
            "highest": 210,
            "lowest": 130,
        }


def estimate_win_probability(team_a, team_b, form_a, form_b, h2h):
    fa = parse_form(form_a)
    fb = parse_form(form_b)

    h2h_factor = (h2h["wins_a"] - h2h["wins_b"]) / max(1, h2h["total"])
    base = 0.5 + 0.12 * (fa - fb) + 0.1 * h2h_factor
    base = max(0.2, min(0.8, base))

    return {
        "teamA_win_pct": int(base * 100),
        "teamB_win_pct": int((1 - base) * 100),
    }


def fetch_live_match():
    try:
        url = f"{BASE_URL}/currentMatches?apikey={API_KEY}"
        res = requests.get(url).json().get("data", [])
        ipl = [m for m in res if "Premier League" in m.get("series", "")]
        return ipl[0] if ipl else None
    except:
        return None


def fetch_next_scheduled_match():
    try:
        url = f"{BASE_URL}/matchCalendar?apikey={API_KEY}"
        res = requests.get(url).json().get("data", [])
        fut = [m for m in res if "Premier League" in m.get("name", "")]
        fut = sorted(fut, key=lambda x: x.get("date", "9999-01-01"))
        return fut[0] if fut else None
    except:
        return None
# =============================
# MATCH SELECTION
# =============================

match = fetch_live_match()

if match:
    TEAM_A = match["teams"][0]
    TEAM_B = match["teams"][1]
    VENUE = match.get("venue", "Stadium")
    MATCH_DATE = TODAY
else:
    m = fetch_next_scheduled_match()
    if m and "vs" in m.get("name", ""):
        TEAM_A, TEAM_B = [x.strip() for x in m["name"].split("vs")]
        VENUE = m.get("venue", "Cricket Ground")
        MATCH_DATE = m.get("date", TODAY)
    else:
        TEAM_A = "Team A"
        TEAM_B = "Team B"
        VENUE = "Unknown Stadium"
        MATCH_DATE = TODAY

TEAM_A_FORM = "W L W W L"
TEAM_B_FORM = "L W L L W"

FORM_A_ICON = form_to_icons(TEAM_A_FORM)
FORM_B_ICON = form_to_icons(TEAM_B_FORM)

H2H = fetch_h2h_stats(TEAM_A, TEAM_B)
PRED = estimate_win_probability(TEAM_A, TEAM_B, TEAM_A_FORM, TEAM_B_FORM, H2H)

PROJECTED_SCORE = estimate_projected_score(VENUE, TEAM_A_FORM, TEAM_B_FORM)
PITCH = auto_pitch_report(VENUE)

# =============================
# JSON OUTPUT
# =============================

json_data = {
    "date": MATCH_DATE,
    "teamA": TEAM_A,
    "teamB": TEAM_B,
    "venue": VENUE,
    "formA": TEAM_A_FORM,
    "formB": TEAM_B_FORM,
    "formA_icons": FORM_A_ICON,
    "formB_icons": FORM_B_ICON,
    "pitch": PITCH,
    "score": PROJECTED_SCORE,
    "h2h": H2H,
    "prediction": PRED
}

os.makedirs("../data", exist_ok=True)
with open(f"../data/{MATCH_DATE}.json", "w") as f:
    json.dump(json_data, f, indent=4)

print("✔ JSON saved:", f"../data/{MATCH_DATE}.json")

# =============================
# GENERATE PNG CARD
# =============================

from match_card import generate_card

card_path = f"../assets/img/cards/{MATCH_DATE}.png"
generate_card(json_data, card_path)
# =============================
# HTML PAGE
# =============================

os.makedirs("../matches", exist_ok=True)

html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='UTF-8'>
<title>{TEAM_A} vs {TEAM_B} — IPL Match Preview</title>
<link rel="stylesheet" href="../assets/css/style.css">
</head>
<body>
<main>

<h1>{TEAM_A} vs {TEAM_B}</h1>
<p><strong>Date:</strong> {MATCH_DATE}</p>
<p><strong>Venue:</strong> {VENUE}</p>

<div class='card'>
<h2>Projected Score</h2>
<p>{PROJECTED_SCORE}</p>
</div>

<div class='card'>
<h2>Pitch Report</h2>
<p>{PITCH}</p>
</div>

<div class='card'>
<h2>H2H Summary</h2>
<p>Total matches: {H2H['total']}</p>
<p>{TEAM_A}: {H2H['wins_a']} wins</p>
<p>{TEAM_B}: {H2H['wins_b']} wins</p>
</div>

<div class='card'>
<h2>Win Probability</h2>
<p>{TEAM_A}: {PRED['teamA_win_pct']}%</p>
<p>{TEAM_B}: {PRED['teamB_win_pct']}%</p>
</div>

<img src="../assets/img/cards/{MATCH_DATE}.png" style="width:100%;margin-top:20px;" />

</main>
</body>
</html>
"""

with open(f"../matches/{MATCH_DATE}.html", "w") as f:
    f.write(html)

print("✔ HTML saved:", f"../matches/{MATCH_DATE}.html")

# =============================
# TELEGRAM MESSAGE
# =============================

telegram_msg = f"""
🏏 *IPL Preview – {TEAM_A} vs {TEAM_B}*

📅 {MATCH_DATE}
🏟 {VENUE}

🔥 *Projected Score:* {PROJECTED_SCORE}
📊 *Win Probability:*  
• {TEAM_A}: {PRED['teamA_win_pct']}%  
• {TEAM_B}: {PRED['teamB_win_pct']}%

📌 Pitch: {PITCH}

🔗 Full Page:
https://revbull.github.io/ipl_insights/matches/{MATCH_DATE}.html
"""

os.makedirs("../telegram", exist_ok=True)
with open("../telegram/latest_message.txt", "w") as f:
    f.write(telegram_msg)

print("🎉 Generator completed successfully!")
