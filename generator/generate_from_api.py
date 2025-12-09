import os
import json
import subprocess
from datetime import datetime
import requests

def parse_form(form_str: str) -> float:
    """
    Превръща нещо като 'W L W W L' в числова форма между -1 и +1.
    """
    form_str = form_str.replace(",", " ").upper()
    tokens = [t for t in form_str.split() if t in ("W", "L", "D")]
    if not tokens:
        return 0.0
    score = 0
    for t in tokens:
        if t == "W":
            score += 1
        elif t == "L":
            score -= 1
        # D = 0
    return score / len(tokens)


def estimate_projected_score(venue: str, form_a: str, form_b: str) -> str:
    """
    Връща string range, напр. '170 – 188 runs', на база стадион + форма.
    """
    v = (venue or "").lower()

    # базов mid според стадиона
    if any(k in v for k in ["chinnaswamy", "wankhede", "eden gardens"]):
        base_mid = 185
        spread = 18
    elif any(k in v for k in ["chepauk", "arun jaitley", "delhi"]):
        base_mid = 160
        spread = 14
    elif "narendra modi" in v or "motera" in v:
        base_mid = 175
        spread = 16
    else:
        base_mid = 170
        spread = 15

    # форма на отборите
    fa = parse_form(form_a)
    fb = parse_form(form_b)
    momentum = (fa + fb) / 2  # между -1 и +1

    # корекция по форма (+/- 8 runs макс)
    mid = base_mid + int(momentum * 8)

    low = mid - spread
    high = mid + spread

    # ограничение
    low = max(130, low)
    high = min(230, high)

    return f"{low} – {high} runs"


# ============================
# CONFIG – попълваш това
# ============================

API_KEY = "YOUR_API_KEY_HERE"
API_ENDPOINT = "https://example-cricket-api.com/fixtures"  # смени с реален endpoint
IPL_LEAGUE_ID = 1234  # ID на IPL лигата в избрания API

# Default стойности, ако API не върне нищо
DEFAULT_PITCH_REPORT = """
Balanced T20 surface with decent carry.
Expected run rate: around 7.8 – 8.5.
Weather: generally clear, minimal dew expected.
"""

PROJECTED_SCORE = estimate_projected_score(VENUE, TEAM_A_FORM, TEAM_B_FORM)
print("✔ Auto projected score:", PROJECTED_SCORE)


# ============================
# 1) Взимане на днешен мач от API
# ============================

today = datetime.utcnow().strftime("%Y-%m-%d")  # формат YYYY-MM-DD

params = {
    "date": today,
    "league": IPL_LEAGUE_ID,
    "apikey": API_KEY,
}

print("⏳ Fetching fixtures from API...")

try:
    resp = requests.get(API_ENDPOINT, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
except Exception as e:
    print("❌ Error calling API:", e)
    print("Using fallback teams...")
    data = None

TEAM_A = "Team A"
TEAM_B = "Team B"
TEAM_A_FORM = "W L W W L"
TEAM_B_FORM = "L W L L W"
PITCH_REPORT = DEFAULT_PITCH_REPORT
PROJECTED_SCORE = DEFAULT_PROJECTED_SCORE

KEY_PLAYERS = [
    ("Player 1 (Team A)", "Impact player"),
    ("Player 2 (Team B)", "Powerplay threat"),
]

if data:
    # Тук трябва да адаптираш според формата на твоя API
    # Примерна структура: {"fixtures": [ { "home_team": "...", "away_team": "..." }, ... ]}
    fixtures = data.get("fixtures") or data.get("response") or []

    if fixtures:
        match = fixtures[0]  # взимаме първия мач за деня

        # Примерно – смени с реалните ключове от API
        TEAM_A = match.get("home_team") or match.get("team_home") or "Team A"
        TEAM_B = match.get("away_team") or match.get("team_away") or "Team B"

        # Ако API дава форма – може да я ползваш, иначе оставяш дефолт
        TEAM_A_FORM = match.get("home_form", TEAM_A_FORM)
        TEAM_B_FORM = match.get("away_form", TEAM_B_FORM)

        # Можеш да извлечеш и стадион, град и т.н.
        venue = match.get("venue") or match.get("stadium") or ""
        if venue:
            # ============================
# AUTO PITCH REPORT BY VENUE
# ============================

venue_name = match.get("venue") or match.get("stadium") or "Unknown"

pitch_map = {
    "Wankhede": "High-scoring batting-friendly pitch with bounce. Expect 180+ if top order settles.",
    "Eden Gardens": "Excellent batting surface early, but spinners get help after 12–14 overs.",
    "Chepauk": "Slow, spin-heavy surface. Difficult for batters, expect lower totals.",
    "Narendra Modi": "Balanced wicket with early seam movement. Settles into good batting conditions.",
    "Chinnaswamy": "Very small boundaries, extremely high scoring ground. 200+ not uncommon.",
    "Arun Jaitley": "Slow Delhi wicket, two-paced, challenging for aggressive batting."
}

# Default pitch logic if venue not recognized
DEFAULT_PITCH = "Balanced T20 wicket. Expected run rate around 7.8 – 8.4. Clear weather conditions."

PITCH_REPORT = None

for key in pitch_map:
    if key.lower() in venue_name.lower():
        PITCH_REPORT = pitch_map[key]
        break

if not PITCH_REPORT:
    PITCH_REPORT = DEFAULT_PITCH

print(f"✔ Auto pitch report based on venue: {venue_name}")

            # ============================
# AUTO KEY PLAYERS FROM API
# ============================

KEY_PLAYERS = []

try:
    # Пример: API endpoint за lineup / squad
    squad_endpoint = "https://example-cricket-api.com/squad"

    squad_params = {
        "match_id": match.get("id"),
        "apikey": API_KEY
    }

    print("⏳ Fetching squad / player stats...")
    sq = requests.get(squad_endpoint, params=squad_params).json()

    players_home = sq.get("home_team_players", [])
    players_away = sq.get("away_team_players", [])

    # Взимаме топ 2 батсмени и топ 1 боулър от API
    def extract_key_players(players, team_short):
        bat_sorted = sorted(players, key=lambda x: x.get("strike_rate", 0), reverse=True)
        bowl_sorted = sorted(players, key=lambda x: x.get("wickets", 0), reverse=True)

        result = []
        if len(bat_sorted) > 0:
            result.append((f"{bat_sorted[0]['name']} ({team_short})", "Top batsman by SR"))
        if len(bat_sorted) > 1:
            result.append((f"{bat_sorted[1]['name']} ({team_short})", "Reliable top-order contributor"))
        if len(bowl_sorted) > 0:
            result.append((f"{bowl_sorted[0]['name']} ({team_short})", "Key wicket-taking bowler"))

        return result

    KEY_PLAYERS.extend(extract_key_players(players_home, TEAM_A))
    KEY_PLAYERS.extend(extract_key_players(players_away, TEAM_B))

    print("✔ Key players extracted from API.")

except Exception as e:
    print("⚠ Could not fetch auto key players, using fallback.", e)
    KEY_PLAYERS = [
        ("Top Player A", "Impact batsman"),
        ("Top Player B", "Key bowler"),
        ("Top Player C", "Consistent performer")
    ]

            PITCH_REPORT = f"""
Balanced T20 surface at {venue}.
Expected run rate: around 7.8 – 8.5.
Weather: generally clear, minimal dew expected.
"""
        print(f"✔ Match found: {TEAM_A} vs {TEAM_B}")
    else:
        print("⚠ No fixtures found for today – using fallback values.")
else:
    print("⚠ No data from API – using fallback values.")

# ===================================
# AUTO: Date & filenames
# ===================================

file_date = datetime.now().strftime("%Y-%m-%d")  # локална дата за имената
html_file = f"../matches/{file_date}.html"
json_file = f"../data/{file_date}.json"
telegram_file = f"../telegram/{file_date}.txt"

# ===================================
# 2) JSON DATA GENERATION
# ===================================

match_data = {
    "date": file_date,
    "teamA": TEAM_A,
    "teamB": TEAM_B,
    "formA": TEAM_A_FORM,
    "formB": TEAM_B_FORM,
    "pitch": PITCH_REPORT.strip(),
    "players": [{"name": n, "meta": m} for n, m in KEY_PLAYERS],
    "score": PROJECTED_SCORE
}

os.makedirs("../data", exist_ok=True)

with open(json_file, "w", encoding="utf-8") as f:
    json.dump(match_data, f, indent=4)

print(f"✔ JSON created: {json_file}")

# ===================================
# 3) HTML PAGE GENERATION
# ===================================

html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>{TEAM_A} vs {TEAM_B} — IPL Match Preview</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link rel="stylesheet" href="../assets/css/style.css">
</head>

<body>
  <main>
    
    <h1>{TEAM_A} vs {TEAM_B} — IPL Match Preview</h1>
    <p style="color:#a3a7b5">Match Date: {file_date}</p>

    <div class="card">
      <h2>Teams</h2>
      <div style="display:flex;align-items:center;justify-content:space-between">
        <div>
          <h3>{TEAM_A}</h3>
          <p>Form: {TEAM_A_FORM}</p>
        </div>

        <div class="vs">VS</div>

        <div>
          <h3>{TEAM_B}</h3>
          <p>Form: {TEAM_B_FORM}</p>
        </div>
      </div>
    </div>

    <div class="card">
      <h2>Pitch Report</h2>
      <p>{PITCH_REPORT}</p>
    </div>

    <div class="card">
      <h2>Key Players</h2>
      <ul>
"""

for name, meta in KEY_PLAYERS:
    html_template += f"        <li><strong>{name}</strong> — {meta}</li>\n"

html_template += f"""
      </ul>
    </div>

    <div class="card">
      <h2>Projected Score (Analysis Only)</h2>
      <div class="score-box">
        <div class="score-box-value" style="font-size:40px;margin:10px 0;">
          {PROJECTED_SCORE}
        </div>
      </div>
      <p style="color:#a3a7b5;margin-top:10px;">
        Projection is for informational purposes only.
      </p>
    </div>

    <p style="font-size:12px;color:#a3a7b5;margin-top:20px;">
      Some cricket fans explore external platforms for match data.
      If affiliate links appear, this site may earn a small commission.
    </p>

    <a href="../index.html" class="btn-primary">Back to Main Page</a>

  </main>
</body>
</html>
"""

os.makedirs("../matches", exist_ok=True)

with open(html_file, "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"✔ HTML created: {html_file}")

# ===================================
# 4) TELEGRAM POST GENERATION
# ===================================

telegram_post = f"""🏏 **IPL Match Preview — {TEAM_A} vs {TEAM_B}**

📅 Date: {file_date}

🔥 **Team Form**
• {TEAM_A}: {TEAM_A_FORM}  
• {TEAM_B}: {TEAM_B_FORM}

🏟 **Pitch Report**
{PITCH_REPORT.strip()}

⭐ **Key Players**
"""

for name, meta in KEY_PLAYERS:
    telegram_post += f"• **{name}** — {meta}\n"

telegram_post += f"""

📈 **Projected Score (Analysis Only):**  
**{PROJECTED_SCORE}**

🔗 Full analysis:
https://YOUR_GITHUB_USERNAME.github.io/ipl-site/matches/{file_date}.html
"""

os.makedirs("../telegram", exist_ok=True)

with open(telegram_file, "w", encoding="utf-8") as f:
    f.write(telegram_post)

print(f"✔ Telegram post created: {telegram_file}")

# ===================================
# 5) AUTO GIT COMMIT + PUSH
# ===================================

print("⏳ Committing changes to Git...")

subprocess.run(["git", "add", "."], cwd="..")
subprocess.run(["git", "commit", "-m", f"Add API-based match page for {file_date}"], cwd="..")
subprocess.run(["git", "push"], cwd="..")

print("\n🎉 ALL DONE! API + JSON + HTML + TELEGRAM POST + AUTO PUSH COMPLETED.")
from update_rss import generate_rss
generate_rss(base_url="https://revbull.github.io/ipl-site")
# ===================================
# 7) Build Detailed Telegram Message
# ===================================

telegram_message = f"""🏏 *IPL Match Preview – {TEAM_A} vs {TEAM_B}*

📅 *Date:* {file_date}

🔥 *Team Form*
• {TEAM_A}: {TEAM_A_FORM}
• {TEAM_B}: {TEAM_B_FORM}

🏟 *Pitch Report*
{PITCH_REPORT.strip()}

⭐ *Key Players to Watch*
"""

for name, meta in KEY_PLAYERS:
    telegram_message += f"• *{name}* — {meta}\n"

telegram_message += f"""

📈 *Projected Score:*  
*{PROJECTED_SCORE}*

🔗 *Full Analysis Page:*  
https://YOUR_GITHUB_USERNAME.github.io/ipl-site/matches/{file_date}.html
"""

with open("../telegram/latest_message.txt", "w", encoding="utf-8") as f:
    f.write(telegram_message)

print("✔ Detailed Telegram message generated")


