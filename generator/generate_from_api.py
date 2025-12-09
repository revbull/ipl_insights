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
    Fetch basic H2H from cricScore endpoint.
    Compatible with limited data.
    """
    try:
        url = f"{BASE_URL}/cricScore?apikey={API_KEY}"
        res = requests.get(url).json().get("data", [])

        h2h_matches = [
            m for m in res
            if (
                team_a.lower() in m.get("t1", "").lower() and
                team_b.lower() in m.get("t2", "").lower()
            ) or (
                team_b.lower() in m.get("t1", "").lower() and
                team_a.lower() in m.get("t2", "").lower()
            )
        ]

        if not h2h_matches:
            raise Exception("No H2H")

        total = len(h2h_matches)
        wins_a = sum(1 for m in h2h_matches if m.get("winner", "").lower() == team_a.lower())
        wins_b = sum(1 for m in h2h_matches if m.get("winner", "").lower() == team_b.lower())

        last_5 = h2h_matches[-5:] if len(h2h_matches) >= 5 else h2h_matches
        last5_a = sum(1 for m in last_5 if m.get("winner", "").lower() == team_a.lower())
        last5_b = sum(1 for m in last_5 if m.get("winner", "").lower() == team_b.lower())

        totals = []
        for m in h2h_matches:
            for k in ("t1s", "t2s"):
                try:
                    runs = int(m.get(k, "0/0").split("/")[0])
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

    base = 0.5 + 0.1 * (fa - fb) + 0.1 * h2h_factor
    base = max(0.2, min(0.8, base))

    p_a = round(base * 100)
    p_b = 100 - p_a

    return {
        "teamA_win_pct": p_a,
        "teamB_win_pct": p_b,
    }


def logo_path_for_team(team_name):
    mapping = {
        "mumbai": "mi.png",
        "chennai": "csk.png",
        "kolkata": "kkr.png",
        "sunrisers": "srh.png",
        "delhi": "dc.png",
        "punjab": "pbks.png",
        "rajasthan": "rr.png",
        "lucknow": "lsg.png",
        "gujarat": "gt.png",
        "royal challengers": "rcb.png",
    }
    name = team_name.lower()
    for k, v in mapping.items():
        if k in name:
            return os.path.join("..", "assets", "img", "logos", v)
    return ""

# =============================
# MATCH FETCH
# =============================

def fetch_live_match():
    try:
        url = f"{BASE_URL}/currentMatches?apikey={API_KEY}"
        data = requests.get(url).json().get("data", [])
        ipl = [m for m in data if "Premier League" in m.get("series", "")]
        return ipl[0] if ipl else None
    except:
        return None


def fetch_next_scheduled_match():
    try:
        url = f"{BASE_URL}/matchCalendar?apikey={API_KEY}"
        data = requests.get(url).json().get("data", [])

        fut = [m for m in data if "Premier League" in m.get("name", "")]
        fut = sorted(fut, key=lambda x: x.get("date", "9999-01-01"))

        return fut[0] if fut else None
    except:
        return None


match = fetch_live_match()

if match:
    TEAM_A = match["teams"][0]
    TEAM_B = match["teams"][1]
    VENUE = match.get("venue", "Stadium")
    MATCH_DATE = TODAY_UTC
else:
    m = fetch_next_scheduled_match()
    if m:
        if "vs" in m.get("name", ""):
            TEAM_A, TEAM_B = [x.strip() for x in m["name"].split("vs")]
        else:
            TEAM_A = "Team A"
            TEAM_B = "Team B"
        VENUE = m.get("venue", "Cricket Ground")
        MATCH_DATE = m.get("date", TODAY_UTC)
    else:
        TEAM_A = "Team A"
        TEAM_B = "Team B"
        VENUE = "Unknown Stadium"
        MATCH_DATE = TODAY_UTC


# =============================
# FORM & ANALYTICS
# =============================

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
    "prediction": PRED,
}

os.makedirs("../data", exist_ok=True)
with open(f"../data/{MATCH_DATE}.json", "w") as f:
    json.dump(json_data, f, indent=4)


# =============================
# FIXED — PNG MATCH CARD (NO textsize)
# =============================

def text_width(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]

def generate_card(data, path):
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), (10, 12, 22))
    draw = ImageDraw.Draw(img)

    try:
        font_big = ImageFont.truetype("arial.ttf", 80)
        font_med = ImageFont.truetype("arial.ttf", 60)
        font_small = ImageFont.truetype("arial.ttf", 36)
    except:
        font_big = font_med = font_small = ImageFont.load_default()

    team_a = data["teamA"]
    team_b = data["teamB"]

    draw.text((W//2 - 250, 80), "IPL MATCH", font=font_big, fill=(0,220,255))

    # TEAM A label
    draw.text((80, 430), team_a, font=font_med, fill="white")

    # TEAM B label — FIXED
    tb_width = text_width(draw, team_b, font_med)
    draw.text((W - 80 - tb_width, 430), team_b, font=font_med, fill="white")

    # VS
    draw.text((W//2 - 30, 430), "VS", font=font_big, fill=(255,210,0))

    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


generate_card(json_data, f"../assets/img/cards/{MATCH_DATE}.png")

