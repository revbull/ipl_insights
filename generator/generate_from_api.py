import os
import json
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# =============================
# CONFIGURATION
# =============================

API_KEY = "c654ad58-ef3e-4152-a811-115310d6d9ee"  # ← сложи твоя CricketData API key
BASE_URL = "https://api.cricapi.com/v1"

TODAY_UTC = datetime.utcnow().strftime("%Y-%m-%d")

# =============================
# UTILITY FUNCTIONS
# =============================

def parse_form(form_str: str) -> float:
    form_str = form_str.replace(",", " ").upper()
    tokens = [t for t in form_str.split() if t in ("W", "L", "D")]
    if not tokens:
        return 0.0
    score = sum(1 if t == "W" else -1 if t == "L" else 0 for t in tokens)
    return score / len(tokens)


def form_to_icons(form_string: str) -> str:
    """
    Преобразува формата (W/L/D) в цветни икони за HTML.
    """
    tokens = form_string.replace(",", " ").upper().split()
    out = []
    for t in tokens:
        if t == "W":
            out.append("🟩")
        elif t == "L":
            out.append("🟥")
        elif t == "D":
            out.append("🟨")
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
        "Chinnaswamy": "Very small boundaries — 200+ common.",
        "Narendra Modi": "Balanced wicket with early seam movement.",
        "Chepauk": "Slow, spin-heavy, low-scoring venue.",
        "Arun Jaitley": "Two-paced wicket, tough strokeplay."
    }
    for k, v in pitch_map.items():
        if k.lower() in venue.lower():
            return v
    return "Balanced T20 wicket. Expected RR 7.8 – 8.4."


def fetch_h2h_stats(team_a, team_b):
    """
    Взима исторически мачове между двата отбора от cricScore endpoint.
    Ако няма данни, връща fallback.
    """
    try:
        url = f"{BASE_URL}/cricScore?apikey={API_KEY}"
        res = requests.get(url).json().get("data", [])

        h2h_matches = [
            m for m in res
            if (
                team_a.lower() in m.get("t1", "").lower()
                and team_b.lower() in m.get("t2", "").lower()
            )
            or (
                team_b.lower() in m.get("t1", "").lower()
                and team_a.lower() in m.get("t2", "").lower()
            )
        ]

        if not h2h_matches:
            raise Exception("No H2H data found")

        total = len(h2h_matches)
        wins_a = sum(1 for m in h2h_matches if m.get("winner", "").lower() == team_a.lower())
        wins_b = sum(1 for m in h2h_matches if m.get("winner", "").lower() == team_b.lower())

        last_5 = h2h_matches[-5:] if len(h2h_matches) >= 5 else h2h_matches
        last5_a = sum(1 for m in last_5 if m.get("winner", "").lower() == team_a.lower())
        last5_b = sum(1 for m in last_5 if m.get("winner", "").lower() == team_b.lower())

        totals = []
        for m in h2h_matches:
            for k in ("t1s", "t2s"):
                score = m.get(k, "0/0")
                try:
                    runs = int(score.split("/")[0])
                    totals.append(runs)
                except:
                    pass

        avg_total = int(sum(totals) / len(totals)) if totals else 160
        highest = max(totals) if totals else 200
        lowest = min(totals) if totals else 120

        return {
            "total": total,
            "wins_a": wins_a,
            "wins_b": wins_b,
            "last5_a": last5_a,
            "last5_b": last5_b,
            "avg_total": avg_total,
            "highest": highest,
            "lowest": lowest,
        }

    except Exception:
        return {
            "total": 12,
            "wins_a": 6,
            "wins_b": 6,
            "last5_a": 2,
            "last5_b": 3,
            "avg_total": 165,
            "highest": 210,
            "lowest": 120,
        }


def estimate_win_probability(team_a, team_b, form_a, form_b, h2h):
    """
    Лека аналитична прогноза (НЕ betting advice)
    """
    fa = parse_form(form_a)
    fb = parse_form(form_b)

    h2h_total = max(h2h["total"], 1)
    h2h_adv = (h2h["wins_a"] - h2h["wins_b"]) / h2h_total

    base = 0.5 + 0.1 * (fa - fb) + 0.1 * h2h_adv
    base = max(0.2, min(0.8, base))

    p_a = round(base * 100)
    p_b = 100 - p_a

    return {
        "teamA_win_pct": p_a,
        "teamB_win_pct": p_b
    }


def logo_path_for_team(team_name):
    """
    Съответствие между IPL тимове и PNG лога
    """
    mapping = {
        "mumbai": "mi.png",
        "chennai": "csk.png",
        "royal challengers": "rcb.png",
        "kolkata": "kkr.png",
        "sunrisers": "srh.png",
        "delhi": "dc.png",
        "punjab": "pbks.png",
        "rajasthan": "rr.png",
        "lucknow": "lsg.png",
        "gujarat": "gt.png",
    }

    name = team_name.lower()
    for key, file in mapping.items():
        if key in name:
            return os.path.join("..", "assets", "img", "logos", file)

    return ""

# =============================
# FETCH MATCH LOGIC
# =============================

def fetch_live_match():
    try:
        url = f"{BASE_URL}/currentMatches?apikey={API_KEY}"
        data = requests.get(url, timeout=15).json().get("data", [])
        ipl = [m for m in data if "Indian Premier League" in m.get("series", "")]
        return ipl[0] if ipl else None
    except:
        return None


def fetch_next_scheduled_match():
    try:
        url = f"{BASE_URL}/matchCalendar?apikey={API_KEY}"
        data = requests.get(url, timeout=15).json().get("data", [])

        future_ipl = [
            m for m in data
            if "Indian Premier League" in m.get("name", "")
        ]

        future_ipl = sorted(future_ipl, key=lambda x: x.get("date", "9999-01-01"))

        return future_ipl[0] if future_ipl else None
    except:
        return None


match = fetch_live_match()

if match:
    TEAM_A = match["teams"][0]
    TEAM_B = match["teams"][1]
    VENUE = match.get("venue", "Stadium")
    MATCH_DATE = TODAY_UTC
else:
    match = fetch_next_scheduled_match()
    if match:
        name = match.get("name", "Team A vs Team B")
        TEAM_A, TEAM_B = [x.strip() for x in name.split("vs")]
        VENUE = match.get("venue", "Cricket Stadium")
        MATCH_DATE = match.get("date", TODAY_UTC)
    else:
        TEAM_A = "Team A"
        TEAM_B = "Team B"
        VENUE = "Unknown Stadium"
        MATCH_DATE = TODAY_UTC

TEAM_A_FORM = "W L W W L"
TEAM_B_FORM = "L W L L W"

TEAM_A_FORM_ICONS = form_to_icons(TEAM_A_FORM)
TEAM_B_FORM_ICONS = form_to_icons(TEAM_B_FORM)

print("⏳ Fetching H2H stats...")
H2H = fetch_h2h_stats(TEAM_A, TEAM_B)
print("✔ H2H loaded")

PREDICTION = estimate_win_probability(TEAM_A, TEAM_B, TEAM_A_FORM, TEAM_B_FORM, H2H)

PROJECTED_SCORE = estimate_projected_score(VENUE, TEAM_A_FORM, TEAM_B_FORM)
PITCH_REPORT = auto_pitch_report(VENUE)

# =============================
# SAVE JSON
# =============================

json_data = {
    "date": MATCH_DATE,
    "teamA": TEAM_A,
    "teamB": TEAM_B,
    "venue": VENUE,
    "formA": TEAM_A_FORM,
    "formB": TEAM_B_FORM,
    "formA_icons": TEAM_A_FORM_ICONS,
    "formB_icons": TEAM_B_FORM_ICONS,
    "pitch": PITCH_REPORT,
    "players": [
        {"name": f"{TEAM_A} Star", "meta": "Impact player"},
        {"name": f"{TEAM_B} Star", "meta": "Key performer"},
    ],
    "score": PROJECTED_SCORE,
    "h2h": H2H,
    "prediction": PREDICTION
}

os.makedirs("../data", exist_ok=True)

json_path = f"../data/{MATCH_DATE}.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=4)

print("✔ JSON saved")

# =============================
# MATCH CARD IMAGE
# =============================

def generate_card(data, path):
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), (10, 12, 22))
    draw = ImageDraw.Draw(img)

    for y in range(H):
        c = 10 + int(40 * (y / H))
        draw.line([(0, y), (W, y)], fill=(c, c, c + 10))

    try:
        font_big = ImageFont.truetype("arial.ttf", 80)
        font_med = ImageFont.truetype("arial.ttf", 60)
        font_small = ImageFont.truetype("arial.ttf", 36)
    except:
        font_big = font_med = font_small = ImageFont.load_default()

    team_a = data["teamA"]
    team_b = data["teamB"]
    venue = data["venue"]
    score_range = data["score"]
    pred = data["prediction"]

    draw.text((W // 2 - 250, 80), "IPL MATCH", font=font_big, fill=(0, 220, 255))

    # Logos
    logo_a_path = logo_path_for_team(team_a)
    logo_b_path = logo_path_for_team(team_b)
    size = 140

    if logo_a_path and os.path.exists(logo_a_path):
        logo = Image.open(logo_a_path).convert("RGBA").resize((size, size))
        img.paste(logo, (80, 260), logo)

    if logo_b_path and os.path.exists(logo_b_path):
        logo = Image.open(logo_b_path).convert("RGBA").resize((size, size))
        img.paste(logo, (W - 80 - size, 260), logo)

    draw.text((80, 430), team_a, font=font_med, fill="white")
    draw.text((W - 80 - draw.textsize(team_b, font=font_med)[0], 430), team_b, font=font_med, fill="white")
    draw.text((W // 2 - 30, 430), "VS", font=font_big, fill=(255, 210, 0))

    draw.text((80, 540), venue, font=font_small, fill=(190, 190, 200))

    # Projected Score Box
    box_y = 650
    draw.rectangle([80, box_y, W - 80, box_y + 240], outline=(255, 210, 0), width=4)
    draw.text((W // 2 - 160, box_y + 40), "Projected Score", font=font_small, fill="white")
    draw.text((W // 2 - 120, box_y + 120), score_range, font=font_med, fill=(255, 210, 0))

    # Win Probability
    draw.text((80, box_y + 260), "Win Probability (analysis only):", font=font_small, fill=(180, 220, 255))
    draw.text(
        (80, box_y + 310),
        f"{team_a}: {pred['teamA_win_pct']}%  |  {team_b}: {pred['teamB_win_pct']}%",
        font=font_small,
        fill=(0, 220, 255)
    )

    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, "PNG")


card_path = f"../assets/img/cards/{MATCH_DATE}.png"
generate_card(json_data, card_path)
print("✔ Match card created")

# =============================
# HTML PAGE
# =============================

os.makedirs("../matches", exist_ok=True)

html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{TEAM_A} vs {TEAM_B} — IPL Match Preview</title>
<link rel="stylesheet" href="../assets/css/style.css">
</head>
<body>
<main>

<div style='max-width:600px;margin:0 auto 24px;'>
  <img src="../assets/img/cards/{MATCH_DATE}.png" style="width:100%;border-radius:24px;" />
</div>

<h1>{TEAM_A} vs {TEAM_B}</h1>
<p><strong>Date:</strong> {MATCH_DATE}</p>
<p><strong>Venue:</strong> {VENUE}</p>

<div class='card'>
  <h2>Pitch Report</h2>
  <p>{PITCH_REPORT}</p>
</div>

<div class='card'>
  <h2>Key Players</h2>
  <ul>
"""

for p in json_data["players"]:
    html += f"<li><strong>{p['name']}</strong> — {p['meta']}</li>"

html += f"""
  </ul>
</div>

<div class='card'>
  <h2>Projected Score</h2>
  <p>{PROJECTED_SCORE}</p>
</div>

<div class='card'>
  <h2>Head-to-Head Statistics</h2>
  <p><strong>Total Matches:</strong> {H2H['total']}</p>
  <p><strong>{TEAM_A} Wins:</strong> {H2H['wins_a']}</p>
  <p><strong>{TEAM_B} Wins:</strong> {H2H['wins_b']}</p>
  <p><strong>Last 5:</strong> {TEAM_A} {H2H['last5_a']} – {H2H['last5_b']} {TEAM_B}</p>
  <p><strong>Average Total:</strong> {H2H['avg_total']} runs</p>
  <p><strong>Highest Score:</strong> {H2H['highest']} runs</p>
  <p><strong>Lowest Score:</strong> {H2H['lowest']} runs</p>
</div>

<div class='card'>
  <h2>Recent Form Breakdown</h2>
  <p><strong>{TEAM_A} Recent Form:</strong><br>{TEAM_A_FORM_ICONS}</p>
  <p><strong>{TEAM_B} Recent Form:</strong><br>{TEAM_B_FORM_ICONS}</p>
  <p style="font-size:14px;color:#aaa;">🟩 Win 🟥 Loss 🟨 Draw / No Result</p>
</div>

<div class='card'>
  <h2>Who Will Win? (Analysis Only)</h2>
  <p>This probability estimate is for entertainment and analysis only.</p>
  <p><strong>{TEAM_A} win chance:</strong> {PREDICTION['teamA_win_pct']}%</p>
  <p><strong>{TEAM_B} win chance:</strong> {PREDICTION['teamB_win_pct']}%</p>
</div>

</main>
</body>
</html>
"""

html_path = f"../matches/{MATCH_DATE}.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

print("✔ HTML saved")

# =============================
# TELEGRAM MESSAGE
# =============================

telegram_msg = f"""🏏 *IPL Match Preview – {TEAM_A} vs {TEAM_B}*

📅 *{MATCH_DATE}*
🏟 *{VENUE}*

🔥 *Key Players:*
"""
for p in json_data["players"]:
    telegram_msg += f"• *{p['name']}* — {p['meta']}\n"

telegram_msg += f"""

📈 *Projected Score:* {PROJECTED_SCORE}

📊 *H2H:*  
• Total Matches: {H2H['total']}  
• {TEAM_A}: {H2H['wins_a']} wins  
• {TEAM_B}: {H2H['wins_b']} wins  

📉 *Recent Form:*  
• {TEAM_A}: {TEAM_A_FORM_ICONS}  
• {TEAM_B}: {TEAM_B_FORM_ICONS}  

🤖 *Win Probability (analysis only):*  
• {TEAM_A}: {PREDICTION['teamA_win_pct']}%  
• {TEAM_B}: {PREDICTION['teamB_win_pct']}%

🔗 Full Page:  
https://revbull.github.io/ipl-site/matches/{MATCH_DATE}.html
"""

os.makedirs("../telegram", exist_ok=True)
with open("../telegram/latest_message.txt", "w", encoding="utf-8") as f:
    f.write(telegram_msg)

print("✔ Telegram text saved")
print("🎉 Generator finished successfully.")
