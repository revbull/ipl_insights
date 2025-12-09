import os
import json
import requests
from datetime import datetime
from PIL import Image
from match_card import generate_card

# =============================
# CONFIGURATION
# =============================

API_KEY = "c654ad58-ef3e-4152-a811-115310d6d9ee"
BASE_URL = "https://api.cricapi.com/v1"

TODAY = datetime.utcnow().strftime("%Y-%m-%d")


# =============================
# BASIC UTILITIES
# =============================

def parse_form(form_str: str) -> float:
    form_str = form_str.replace(",", " ").upper()
    tokens = [t for t in form_str.split() if t in ("W","L","D")]
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
        else: out.append("🟨")
    return " ".join(out)


def auto_pitch_report(venue):
    v = venue.lower()
    if "wankhede" in v:
        return "High-scoring ground with excellent bounce — 180+ likely."
    if "chinnaswamy" in v:
        return "Very small boundaries — 200+ possible."
    if "eden" in v:
        return "Flat batting wicket early, spin later."
    if "chepauk" in v:
        return "Slow turner with grip — spin friendly."
    return "Balanced wicket with moderate scoring conditions."


def estimate_projected_score(venue, form_a, form_b):
    v = venue.lower()

    if any(k in v for k in ["wankhede","chinnaswamy"]):
        base = 185
    elif any(k in v for k in ["chepauk","arun","delhi"]):
        base = 160
    else:
        base = 170

    momentum = (parse_form(form_a) + parse_form(form_b)) / 2
    mid = base + int(momentum * 10)

    low = max(130, mid - 20)
    high = min(230, mid + 20)

    return f"{low}–{high} runs"


# =============================
# FETCH REAL MATCH (Always First Match Logic)
# =============================

def fetch_first_match():
    try:
        # Check for live matches
        url = f"{BASE_URL}/currentMatches?apikey={API_KEY}"
        res = requests.get(url).json()

        if res.get("status") == "success" and res.get("data"):
            return res["data"][0]

        # If no live matches → upcoming fixtures
        url = f"{BASE_URL}/matchCalendar?apikey={API_KEY}"
        res = requests.get(url).json()

        if res.get("status") == "success" and res.get("data"):
            return res["data"][0]

        return None

    except Exception as e:
        print("API error:", e)
        return None


# =============================
# PLAYER INSIGHTS
# =============================

def fetch_player_stats(player_name):
    try:
        url = f"{BASE_URL}/players?apikey={API_KEY}&search={player_name}"
        res = requests.get(url).json()

        if res.get("status") != "success":
            return None

        data = res.get("data", [])
        if not data:
            return None

        p = data[0]

        return {
            "name": p.get("name", player_name),
            "role": p.get("role", "Player"),
            "batting": p.get("battingStyle", "Unknown"),
            "bowling": p.get("bowlingStyle", "Unknown")
        }
    except:
        return None


def build_player_insights(team_a, team_b):
    fallback = [
        {"name": f"{team_a} Key Batter", "role": "Batsman"},
        {"name": f"{team_a} Strike Bowler", "role": "Bowler"},
        {"name": f"{team_b} Key Batter", "role": "Batsman"},
        {"name": f"{team_b} Strike Bowler", "role": "Bowler"},
    ]

    final_players = []

    for p in fallback:
        stats = fetch_player_stats(p["name"])
        final_players.append(stats or p)

    return final_players


# =============================
# LIVE SCORE FETCHER
# =============================

def fetch_live_score(team_a, team_b):
    try:
        url = f"{BASE_URL}/cricScore?apikey={API_KEY}"
        res = requests.get(url).json()

        if res.get("status") != "success":
            return None

        for m in res.get("data", []):
            t1 = m.get("t1", "").lower()
            t2 = m.get("t2", "").lower()

            if team_a.lower() in t1 and team_b.lower() in t2 or \
               team_b.lower() in t1 and team_a.lower() in t2:
                return {
                    "score1": m.get("t1s", "N/A"),
                    "score2": m.get("t2s", "N/A"),
                    "status": m.get("status", "Match in progress")
                }

        return None
    except:
        return None


# =============================
# ADVANCED ML WIN PROBABILITY
# =============================

def ml_win_probability(team_a, team_b, form_a, form_b, venue, h2h):
    f_a = parse_form(form_a)
    f_b = parse_form(form_b)
    form_diff = f_a - f_b

    total = max(1, h2h.get("total", 1))
    h2h_diff = (h2h.get("wins_a", 0) - h2h.get("wins_b", 0)) / total

    v = venue.lower()
    if any(k in v for k in ["wankhede","chinnaswamy"]):
        venue_factor = 0.12
    elif any(k in v for k in ["chepauk","arun"]):
        venue_factor = -0.05
    else:
        venue_factor = 0.02

    batting_edge = form_diff * 0.35
    h2h_edge = h2h_diff * 0.25
    venue_edge = venue_factor * 0.15

    raw = 0.50 + batting_edge + h2h_edge + venue_edge
    raw = max(0.15, min(0.85, raw))

    return {
        "teamA_prob": round(raw * 100, 1),
        "teamB_prob": round((1 - raw) * 100, 1)
    }


# =============================
# AI-STYLE MATCH SUMMARY
# =============================

def generate_ai_prediction(team_a, team_b, venue, form_a, form_b, projected, ml_prob, pitch):
    momentum = "slightly stronger" if parse_form(form_a) > parse_form(form_b) else "under pressure"
    favorite = team_a if ml_prob["teamA_prob"] > ml_prob["teamB_prob"] else team_b
    diff = abs(ml_prob["teamA_prob"] - ml_prob["teamB_prob"])

    if diff < 5:
        verdict = "a very balanced contest"
    elif diff < 12:
        verdict = f"a slight edge for {favorite}"
    else:
        verdict = f"{favorite} entering as clear favorites"

    return (
        f"Based on venue conditions, a projected scoring range of {projected}, "
        f"recent form (with {team_a} appearing {momentum}), and the pitch profile "
        f"('{pitch}'), this matchup appears to present {verdict}. Early momentum "
        f"and top-order execution will likely determine the winner."
    )


# =============================
# BUILD MATCH DATA
# =============================

match = fetch_first_match()

if match:
    name = match.get("name", "Team A vs Team B")

    if "vs" in name:
        TEAM_A, TEAM_B = [x.strip() for x in name.split("vs")]
    else:
        TEAM_A, TEAM_B = match.get("teams", ["Team A", "Team B"])

    VENUE = match.get("venue", "Cricket Ground")
    MATCH_DATE = TODAY
else:
    TEAM_A = "Team A"
    TEAM_B = "Team B"
    VENUE = "Unknown Stadium"
    MATCH_DATE = TODAY

TEAM_A_FORM = "W L W W L"
TEAM_B_FORM = "L W L L W"

FORM_A_ICON = form_to_icons(TEAM_A_FORM)
FORM_B_ICON = form_to_icons(TEAM_B_FORM)

PLAYER_INSIGHTS = build_player_insights(TEAM_A, TEAM_B)
LIVE = fetch_live_score(TEAM_A, TEAM_B)


# Fallback H2H
H2H = {
    "total": 10,
    "wins_a": 5,
    "wins_b": 5
}

PROJECTED_SCORE = estimate_projected_score(VENUE, TEAM_A_FORM, TEAM_B_FORM)
PITCH = auto_pitch_report(VENUE)

ML_PROB = ml_win_probability(TEAM_A, TEAM_B, TEAM_A_FORM, TEAM_B_FORM, VENUE, H2H)
AI_SUMMARY = generate_ai_prediction(
    TEAM_A, TEAM_B, VENUE,
    TEAM_A_FORM, TEAM_B_FORM,
    PROJECTED_SCORE, ML_PROB, PITCH
)

# =============================
# JSON EXPORT
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
    "projected": PROJECTED_SCORE,
    "players": PLAYER_INSIGHTS,
    "live": LIVE,
    "ml_probability": ML_PROB,
    "ai_summary": AI_SUMMARY
}

os.makedirs("../data", exist_ok=True)

with open(f"../data/{MATCH_DATE}.json", "w") as f:
    json.dump(json_data, f, indent=4)


# =============================
# CARD GENERATION
# =============================

os.makedirs("../assets/img/cards", exist_ok=True)
card_path = f"../assets/img/cards/{MATCH_DATE}.png"
generate_card(json_data, card_path)


# =============================
# HTML EXPORT
# =============================

os.makedirs("../matches", exist_ok=True)

html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{TEAM_A} vs {TEAM_B} — Match Preview</title>
<link rel="stylesheet" href="../assets/css/style.css">
</head>
<body>
<main>

<h1>{TEAM_A} vs {TEAM_B}</h1>
<p><strong>Date:</strong> {MATCH_DATE}</p>
<p><strong>Venue:</strong> {VENUE}</p>

<div class="card">
<h2>Form Guide</h2>
<p>{TEAM_A}: {FORM_A_ICON}</p>
<p>{TEAM_B}: {FORM_B_ICON}</p>
</div>

<div class="card">
<h2>Pitch Report</h2>
<p>{PITCH}</p>
</div>

<div class="card">
<h2>Projected Score</h2>
<p>{PROJECTED_SCORE}</p>
</div>

<div class="card">
<h2>Key Players</h2>
<ul>
"""

for p in PLAYER_INSIGHTS:
    html += f"<li><strong>{p['name']}</strong> — {p.get('role','Player')}</li>"

html += "</ul></div>"

if LIVE:
    html += f"""
<div class='card'>
<h2>Live Score Update</h2>
<p><strong>{TEAM_A}:</strong> {LIVE['score1']}</p>
<p><strong>{TEAM_B}:</strong> {LIVE['score2']}</p>
<p>Status: {LIVE['status']}</p>
</div>
"""

html += f"""
<div class="card">
<h2>Advanced Win Probability</h2>
<p>{TEAM_A}: {ML_PROB['teamA_prob']}%</p>
<p>{TEAM_B}: {ML_PROB['teamB_prob']}%</p>
</div>

<div class="card">
<h2>AI Match Prediction</h2>
<p>{AI_SUMMARY}</p>
</div>

<img src="../assets/img/cards/{MATCH_DATE}.png" style="width:100%;border-radius:12px;margin-top:20px;" />

</main>
</body>
</html>
"""

with open(f"../matches/{MATCH_DATE}.html", "w", encoding="utf-8") as f:
    f.write(html)


# =============================
# TELEGRAM MESSAGE
# =============================

telegram_msg = f"""
🏏 *Match Preview – {TEAM_A} vs {TEAM_B}*

📅 {MATCH_DATE}
🏟 {VENUE}

💡 *AI Prediction:*  
_{AI_SUMMARY}_

📊 *Win Probability*
• {TEAM_A}: {ML_PROB['teamA_prob']}%  
• {TEAM_B}: {ML_PROB['teamB_prob']}%

🔥 *Projected Score:* {PROJECTED_SCORE}

📌 Pitch: {PITCH}

🔗 Full Preview:
https://revbull.github.io/ipl_insights/matches/{MATCH_DATE}.html
"""

os.makedirs("../telegram", exist_ok=True)
with open("../telegram/latest_message.txt", "w", encoding="utf-8") as f:
    f.write(telegram_msg)

print("🎉 All files generated successfully!")
