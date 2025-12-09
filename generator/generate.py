import os
import json
import subprocess
from datetime import datetime

# ============================
# CONFIG (попълваш само това)
# ============================

TEAM_A = "Mumbai Indians"
TEAM_B = "Chennai Super Kings"

TEAM_A_FORM = "W L W W L"
TEAM_B_FORM = "L W L L W"

PITCH_REPORT = """
Batting-friendly surface with good bounce.
Expected run rate: 8.2 – 9.0.
Weather: Clear, low dew.
"""

KEY_PLAYERS = [
    ("Rohit Sharma (MI)", "Powerplay impact"),
    ("Jasprit Bumrah (MI)", "Death overs control"),
    ("Ruturaj Gaikwad (CSK)", "Top-order stability"),
    ("Matheesha Pathirana (CSK)", "Middle overs wicket threat")
]

PROJECTED_SCORE = "170 – 188 runs"

# ===================================
# AUTO: Date & filenames
# ===================================

today = datetime.now().strftime("%Y-%m-%d")

html_file = f"../matches/{today}.html"
json_file = f"../data/{today}.json"
telegram_file = f"../telegram/{today}.txt"

# ===================================
# 1) JSON DATA GENERATION
# ===================================

data = {
    "date": today,
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
    json.dump(data, f, indent=4)

print(f"✔ JSON created: {json_file}")

# ===================================
# 2) HTML PAGE GENERATION
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
    <p style="color:#a3a7b5">Match Date: {today}</p>

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
      Some fans explore external platforms for match data.
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
# 3) TELEGRAM POST GENERATION
# ===================================

telegram_post = f"""🏏 **IPL Match Preview — {TEAM_A} vs {TEAM_B}**

📅 Date: {today}

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
https://YOUR_GITHUB_USERNAME.github.io/ipl-site/matches/{today}.html
"""

os.makedirs("../telegram", exist_ok=True)

with open(telegram_file, "w", encoding="utf-8") as f:
    f.write(telegram_post)

print(f"✔ Telegram post created: {telegram_file}")

# ===================================
# 4) AUTO GIT COMMIT + PUSH
# ===================================

print("⏳ Committing changes to Git...")

subprocess.run(["git", "add", "."], cwd="..")
subprocess.run(["git", "commit", "-m", f"Add match page for {today}"], cwd="..")
subprocess.run(["git", "push"], cwd="..")

print("\n🎉 ALL DONE! JSON + HTML + TELEGRAM POST + AUTO PUSH COMPLETED.")
