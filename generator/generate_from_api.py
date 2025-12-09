import os
import json
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# =============================
# CONFIGURATION
# =============================

API_KEY = "YOUR_API_KEY_HERE"
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
    for k,v in pitch_map.items():
        if k.lower() in venue.lower():
            return v
    return "Balanced T20 wicket. Expected RR 7.8 – 8.4."

# =============================
# FETCH LIVE IPL MATCH
# =============================

def fetch_live_match():
    try:
        url = f"{BASE_URL}/currentMatches?apikey={API_KEY}"
        data = requests.get(url).json().get("data", [])
        ipl = [m for m in data if "Indian Premier League" in m.get("series", "")]
        return ipl[0] if ipl else None
    except:
        return None

# =============================
# FETCH NEXT SCHEDULED IPL MATCH
# =============================

def fetch_next_scheduled_match():
    try:
        url = f"{BASE_URL}/matchCalendar?apikey={API_KEY}"
        data = requests.get(url).json().get("data", [])

        future_ipl = [
            m for m in data 
            if "Indian Premier League" in m.get("name","") 
               or "IPL" in m.get("series","")
        ]

        # sort by date
        future_ipl = sorted(
            future_ipl, 
            key=lambda x: x.get("date", "9999-01-01")
        )

        return future_ipl[0] if future_ipl else None
    except:
        return None

# =============================
# MAIN MATCH FETCH LOGIC
# =============================

match = fetch_live_match()

if match:
    match_type = "LIVE"
    TEAM_A = match["teams"][0]
    TEAM_B = match["teams"][1]
    VENUE = match.get("venue","Stadium")
    MATCH_DATE = TODAY
else:
    match = fetch_next_scheduled_match()
    match_type = "SCHEDULED"

    if match:
        name = match.get("name","Team A vs Team B")
        if "vs" in name:
            TEAM_A, TEAM_B = [x.strip() for x in name.split("vs")]
        else:
            TEAM_A, TEAM_B = "Team A", "Team B"

        VENUE = match.get("venue","T20 Ground")
        MATCH_DATE = match.get("date", TODAY)
    else:
        # fallback
        TEAM_A = "Team A"
        TEAM_B = "Team B"
        VENUE = "Unknown Stadium"
        MATCH_DATE = TODAY

TEAM_A_FORM = "W L W W L"
TEAM_B_FORM = "L W L L W"

print(f"✔ Using match: {TEAM_A} vs {TEAM_B} ({match_type}) — {MATCH_DATE}")

# =============================
# AUTO KEY PLAYERS (fallback logic)
# =============================

KEY_PLAYERS = [
    (f"{TEAM_A} Star", "Impact player"),
    (f"{TEAM_B} Star", "Key performer")
]

# =============================
# AUTO SCORE + PITCH
# =============================

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
    "pitch": PITCH_REPORT,
    "players": [{"name": n, "meta": m} for n,m in KEY_PLAYERS],
    "score": PROJECTED_SCORE
}

os.makedirs("../data", exist_ok=True)

json_path = f"../data/{MATCH_DATE}.json"
with open(json_path,"w",encoding="utf-8") as f:
    json.dump(json_data, f, indent=4)

print("✔ JSON saved:", json_path)

# =============================
# MATCH CARD IMAGE
# =============================

def generate_card(data, path):
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), (10, 12, 22))
    draw = ImageDraw.Draw(img)

    for y in range(H):
        c = 10 + int(40 * (y/H))
        draw.line([(0,y),(W,y)], fill=(c,c,c+10))

    try:
        font_big = ImageFont.truetype("arial.ttf", 80)
        font_med = ImageFont.truetype("arial.ttf", 60)
        font_small = ImageFont.truetype("arial.ttf", 36)
    except:
        font_big = font_med = font_small = ImageFont.load_default()

    draw.text((W//2 - 260, 80), "IPL MATCH", font=font_big, fill=(0,220,255))
    draw.text((80, 300), data["teamA"], font=font_med, fill=(255,255,255))
    tw = draw.textsize(data["teamB"], font=font_med)[0]
    draw.text((W - 80 - tw, 300), data["teamB"], font=font_med, fill=(255,255,255))
    draw.text((W//2 - 40, 380), "VS", font=font_big, fill=(255,210,0))
    draw.text((80, 460), data["venue"], font=font_small, fill=(190,190,200))

    box_y = 650
    draw.rectangle([80,box_y,W-80,box_y+240], outline=(255,210,0), width=4)
    draw.text((W//2 - 170, box_y+40), "Projected Score", font=font_small, fill=(255,255,255))
    draw.text((W//2 - 120, box_y+120), data["score"], font=font_med, fill=(255,210,0))

    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, "PNG")

card_path = f"../assets/img/cards/{MATCH_DATE}.png"
generate_card(json_data, card_path)

print("✔ Match card generated:", card_path)

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

for name, meta in KEY_PLAYERS:
    html += f"<li><strong>{name}</strong> — {meta}</li>"

html += f"""
</ul>
</div>

<div class='card'>
<h2>Projected Score</h2>
<p>{PROJECTED_SCORE}</p>
</div>

</main>
</body>
</html>
"""

html_path = f"../matches/{MATCH_DATE}.html"
with open(html_path,"w",encoding="utf-8") as f:
    f.write(html)

print("✔ HTML saved:", html_path)

# =============================
# TELEGRAM MESSAGE
# =============================

telegram_msg = f"""🏏 *IPL Match Preview – {TEAM_A} vs {TEAM_B}*

📅 *{MATCH_DATE}*
🏟 *{VENUE}*

🔥 *Key Players*
"""

for n,m in KEY_PLAYERS:
    telegram_msg += f"• *{n}* — {m}\n"

telegram_msg += f"""

📈 *Projected Score:* {PROJECTED_SCORE}

🔗 Full Page:
https://YOUR_GITHUB_USERNAME.github.io/ipl-site/matches/{MATCH_DATE}.html
"""

os.makedirs("../telegram", exist_ok=True)
with open("../telegram/latest_message.txt","w",encoding="utf-8") as f:
    f.write(telegram_msg)

print("✔ Telegram text created")
print("🎉 Generator finished successfully.")
