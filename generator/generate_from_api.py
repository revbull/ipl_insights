import os
import json
import subprocess
from datetime import datetime
import requests

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

DEFAULT_PROJECTED_SCORE = "160 – 180 runs"

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

