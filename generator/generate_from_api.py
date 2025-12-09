import os
import json
import subprocess
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# ============================
# CONFIG
# ============================

API_KEY = "YOUR_API_KEY_HERE"
BASE_URL = "https://api.cricapi.com/v1"

# ============================
# UTIL FUNCTIONS
# ============================

def parse_form(form_str: str) -> float:
    form_str = form_str.replace(",", " ").upper()
    tokens = [t for t in form_str.split() if t in ("W", "L", "D")]
    if not tokens:
        return 0
    score = 0
    for t in tokens:
        if t == "W": score += 1
        elif t == "L": score -= 1
    return score / len(tokens)


def estimate_projected_score(venue: str, form_a: str, form_b: str) -> str:
    v = (venue or "").lower()

    if any(k in v for k in ["chinnaswamy", "wankhede", "eden"]):
        base_mid = 185; spread = 18
    elif any(k in v for k in ["chepauk", "arun jaitley", "delhi"]):
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
        "Wankhede": "High-scoring pitch with bounce, 180+ possible.",
        "Eden": "Flat early but spin helps later.",
        "Chinnaswamy": "Very small boundaries, 200+ common.",
        "Chepauk": "Slow surface, spin-friendly, low scoring.",
        "Narendra Modi": "Balanced wicket with early seam movement.",
        "Arun Jaitley": "Two-paced Delhi pitch, difficult strokeplay."
    }
    for k, v in pitch_map.items():
        if k.lower() in venue.lower():
            return v
    return "Balanced T20 wicket. Expected RR 7.8 – 8.4."


# ============================
# FETCH MATCH FROM API
# ============================

print("⏳ Fetching today's matches...")

today_api = datetime.utcnow().strftime("%Y-%m-%d")
matches_url = f"{BASE_URL}/currentMatches?apikey={API_KEY}"

try:
    resp = requests.get(matches_url).json()
    all_matches = resp.get("data", [])
except:
    all_matches = []

ipl_matches = [m for m in all_matches if "Indian Premier League" in m.get("series", "")]
match = ipl_matches[0] if ipl_matches else None

if not match:
    print("⚠ No IPL match found today.")
    TEAM_A = "Team A"; TEAM_B = "Team B"; VENUE = "Unknown Stadium"
    TEAM_A_FORM = "W L W W L"; TEAM_B_FORM = "L W L L W"
else:
    TEAM_A, TEAM_B = match["teams"][0], match["teams"][1]
    VENUE = match.get("venue", "Stadium")
    TEAM_A_FORM = "W L W W L"
    TEAM_B_FORM = "L W L L W"

print(f"✔ Match: {TEAM_A} vs {TEAM_B} at {VENUE}")

# ============================
# FETCH SQUAD FOR KEY PLAYERS
# ============================

KEY_PLAYERS = []

if match:
    squad_url = f"{BASE_URL}/match_info?apikey={API_KEY}&id={match['id']}"
    try:
        squad_data = requests.get(squad_url).json().get("data", {})
        players = squad_data.get("players", [])
    except:
        players = []
else:
    players = []

players_a = [p for p in players if p.get("teamName") == TEAM_A]
players_b = [p for p in players if p.get("teamName") == TEAM_B]

def select_top(players_list, team_tag):
    if not players_list:
        return []
    bats = sorted([p for p in players_list if "BAT" in p.get("role","").upper()],
                  key=lambda x: x.get("strikeRate", 0), reverse=True)
    bowl = sorted([p for p in players_list if "BOWL" in p.get("role","").upper()],
                  key=lambda x: x.get("wickets", 0), reverse=True)

    out = []
    if bats: 
        out.append((f"{bats[0]['name']} ({team_tag})", "Top batsman"))
    if len(bats) > 1: 
        out.append((f"{bats[1]['name']} ({team_tag})", "Consistent batsman"))
    if bowl: 
        out.append((f"{bowl[0]['name']} ({team_tag})", "Wicket taker"))
    return out

KEY_PLAYERS = select_top(players_a, TEAM_A) + select_top(players_b, TEAM_B)

if not KEY_PLAYERS:
    KEY_PLAYERS = [
        ("Star Player 1", "Impact batsman"),
        ("Star Player 2", "Key bowler")
    ]

# ============================
# AUTO SCORE + PITCH REPORT
# ============================

PROJECTED_SCORE = estimate_projected_score(VENUE, TEAM_A_FORM, TEAM_B_FORM)
PITCH_REPORT = auto_pitch_report(VENUE)

# ============================
# SAVE JSON
# ============================

file_date = datetime.now().strftime("%Y-%m-%d")

json_data = {
    "date": file_date,
    "teamA": TEAM_A,
    "teamB": TEAM_B,
    "venue": VENUE,
    "formA": TEAM_A_FORM,
    "formB": TEAM_B_FORM,
    "pitch": PITCH_REPORT,
    "players": [{"name": n, "meta": m} for n, m in KEY_PLAYERS],
    "score": PROJECTED_SCORE
}

os.makedirs("../data", exist_ok=True)

with open(f"../data/{file_date}.json", "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=4)

print("✔ JSON saved")

# ============================
# GENERATE MATCH CARD IMAGE
# ============================

def generate_card(data, path):
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), (5, 6, 10))
    draw = ImageDraw.Draw(img)

    # Gradient background
    for y in range(H):
        shade = int(10 + (y / H) * 60)
        draw.line([(0, y), (W, y)], fill=(shade, shade, shade+20))

    try:
        font_big = ImageFont.truetype("arial.ttf", 80)
        font_med = ImageFont.truetype("arial.ttf", 60)
        font_small = ImageFont.truetype("arial.ttf", 38)
    except:
        font_big = font_med = font_small = ImageFont.load_default()

    # Title
    draw.text((W//2 - 250, 80), "IPL MATCH", font=font_big, fill=(0,220,255))

    # Teams
    draw.text((80, 300), data["teamA"], font=font_med, fill=(255,255,255))
    draw.text((W - 80 - draw.textsize(data["teamB"], font=font_med)[0], 300),
              data["teamB"], font=font_med, fill=(255,255,255))

    draw.text((W//2 - 40, 370), "VS", font=font_big, fill=(255,210,0))

    # Venue
    draw.text((80, 450), data["venue"], font=font_small, fill=(200,200,210))

    # Score box
    box_y = 600
    draw.rectangle([80, box_y, W-80, box_y+240], outline=(255,210,0), width=4)

    draw.text((W//2 - 200, box_y+40), "Projected Score:", font=font_small, fill=(255,255,255))
    draw.text((W//2 - 120, box_y+120), data["score"], font=font_med, fill=(255,210,0))

    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, "PNG")

card_path = f"../assets/img/cards/{file_date}.png"
generate_card(json_data, card_path)
print("✔ Match card created:", card_path)

# ============================
# HTML PAGE
# ============================

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

<div style="max-width:600px;margin:0 auto 24px;">
  <img src="../assets/img/cards/{file_date}.png" 
       style="width:100%;border-radius:24px;box-shadow:0 18px 45px rgba(0,0,0,.7);" />
</div>

<h1>{TEAM_A} vs {TEAM_B}</h1>
<p><strong>Date:</strong> {file_date}</p>
<p><strong>Venue:</strong> {VENUE}</p>

<div class="card">
  <h2>Pitch Report</h2>
  <p>{PITCH_REPORT}</p>
</div>

<div class="card">
  <h2>Key Players</h2>
  <ul>
"""

for name, meta in KEY_PLAYERS:
    html += f"<li><strong>{name}</strong> — {meta}</li>\n"

html += f"""
  </ul>
</div>

<div class="card">
<h2>Projected Score</h2>
<p>{PROJECTED_SCORE}</p>
</div>

</main>
</body>
</html>
"""

with open(f"../matches/{file_date}.html","w",encoding="utf-8") as f:
    f.write(html)

print("✔ HTML page created")

# ============================
# TELEGRAM MESSAGE
# ============================

telegram_msg = f"""🏏 *IPL Match Preview – {TEAM_A} vs {TEAM_B}*

📅 *{file_date}*
🏟 *{VENUE}*

🔥 *Key Players:*
"""

for name, meta in KEY_PLAYERS:
    telegram_msg += f"• *{name}* — {meta}\n"

telegram_msg += f"""

📈 *Projected Score:* {PROJECTED_SCORE}

🔗 More details:
https://revbull.github.io/ipl-site/matches/{file_date}.html
"""

os.makedirs("../telegram", exist_ok=True)

with open("../telegram/latest_message.txt","w",encoding="utf-8") as f:
    f.write(telegram_msg)

print("✔ Telegram message saved")

# ============================
# (OPTIONAL) GIT PUSH
# ============================

print("✔ Generator finished successfully.")
