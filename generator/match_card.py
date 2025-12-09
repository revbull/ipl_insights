import os
from PIL import Image, ImageDraw, ImageFont


# ================================================
# Helper: measure text width safely using textbbox
# ================================================
def text_width(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


# ================================================
# Helper: detect correct team logo
# ================================================
def get_team_logo(team_name):
    """
    Attempts to map the team name to a PNG file.
    If none found → returns None.
    """
    mapping = {
        "mumbai": "mi.png",
        "chennai": "csk.png",
        "kolkata": "kkr.png",
        "sunrisers": "srh.png",
        "hyderabad": "srh.png",
        "delhi": "dc.png",
        "capital": "dc.png",
        "punjab": "pbks.png",
        "kings": "pbks.png",
        "rajasthan": "rr.png",
        "royal challengers": "rcb.png",
        "bangalore": "rcb.png",
        "lucknow": "lsg.png",
        "gujarat": "gt.png",
        "titans": "gt.png",
    }

    team = team_name.lower()
    for k, file in mapping.items():
        if k in team:
            return os.path.join("..", "assets", "img", "logos", file)

    return None  # fallback: no logo found


# ================================================
# MAIN FUNCTION: generate PNG match card
# ================================================
def generate_card(data, path):
    """
    Advanced IPL match card:
    - Team logos
    - Team names
    - VS center mark
    - Projected Score panel
    - Win Probability panel
    Compatible with Pillow 10.x
    """

    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), (12, 14, 30))
    draw = ImageDraw.Draw(img)

    # Load fonts
    try:
        font_big = ImageFont.truetype("arial.ttf", 90)
        font_med = ImageFont.truetype("arial.ttf", 60)
        font_small = ImageFont.truetype("arial.ttf", 40)
        font_xs = ImageFont.truetype("arial.ttf", 32)
    except:
        font_big = font_med = font_small = font_xs = ImageFont.load_default()

    team_a = data["teamA"]
    team_b = data["teamB"]

    # --------------------------------------
    # HEADER
    # --------------------------------------
    draw.text((W//2 - 260, 60), "IPL MATCH", font=font_big, fill=(0, 220, 255))

    # --------------------------------------
    # Load team logos
    # --------------------------------------
    logo_a_path = get_team_logo(team_a)
    logo_b_path = get_team_logo(team_b)

    logo_a = logo_b = None

    if logo_a_path and os.path.exists(logo_a_path):
        try:
            logo_a = Image.open(logo_a_path).convert("RGBA").resize((260,260))
        except:
            pass

    if logo_b_path and os.path.exists(logo_b_path):
        try:
            logo_b = Image.open(logo_b_path).convert("RGBA").resize((260,260))
        except:
            pass

    # Place logos
    if logo_a:
        img.paste(logo_a, (100, 250), logo_a)
    if logo_b:
        img.paste(logo_b, (W - 360, 250), logo_b)

    # --------------------------------------
    # TEAM NAMES
    # --------------------------------------
    draw.text((120, 540), team_a.upper(), font=font_med, fill="white")
    tb = team_b.upper()
    tb_w = text_width(draw, tb, font_med)
    draw.text((W - 120 - tb_w, 540), tb, font=font_med, fill="white")

    # VS
    draw.text((W//2 - 40, 520), "VS", font=font_big, fill=(255, 210, 0))

    # --------------------------------------
    # PANEL 1: PROJECTED SCORE
    # --------------------------------------
    panel_y = 700
    panel_h = 200

    # Panel background
    draw.rounded_rectangle(
        (100, panel_y, W - 100, panel_y + panel_h),
        radius=40,
        fill=(25, 30, 55),
        outline=(0, 220, 255),
        width=4
    )

    # Title
    draw.text((140, panel_y + 20), "Projected Score", font=font_small, fill=(0, 220, 255))

    score = data["score"]
    sw = text_width(draw, score, font_med)

    draw.text(
        ((W // 2) - (sw // 2), panel_y + 90),
        score,
        font=font_med,
        fill=(255, 210, 0)
    )

    # --------------------------------------
    # PANEL 2: WIN PROBABILITY
    # --------------------------------------
    wp_y = panel_y + panel_h + 60
    wp_h = 240

    draw.rounded_rectangle(
        (100, wp_y, W - 100, wp_y + wp_h),
        radius=40,
        fill=(25, 28, 45),
        outline=(255, 210, 0),
        width=4
    )

    draw.text((140, wp_y + 20), "Win Probability", font=font_small, fill=(255, 210, 0))

    # Extract probabilities
    pA = data["prediction"]["teamA_win_pct"]
    pB = data["prediction"]["teamB_win_pct"]

    # Bars
    bar_w = W - 280
    bar_x = 140
    bar_y = wp_y + 100
    bar_h = 40

    # A bar
    draw.rounded_rectangle(
        (bar_x, bar_y, bar_x + int(bar_w * (pA/100)), bar_y + bar_h),
        radius=20,
        fill=(0, 180, 255)
    )

    # B bar
    draw.rounded_rectangle(
        (bar_x, bar_y + 70, bar_x + int(bar_w * (pB/100)), bar_y + 70 + bar_h),
        radius=20,
        fill=(255, 100, 100)
    )

    # Labels
    draw.text((bar_x, bar_y - 40), f"{team_a}: {pA}%", font=font_xs, fill="white")
    draw.text((bar_x, bar_y + 30), f"{team_b}: {pB}%", font=font_xs, fill="white")

    # --------------------------------------
    # SAVE
    # --------------------------------------
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, "PNG")

    print("✔ Match card saved with SCORE + WIN PROBABILITY:", path)

    print("✔ Match card saved with team logos:", path)
