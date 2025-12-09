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
    Creates a polished IPL match card:
    - Team logos on each side
    - VS in the center
    - Clean header
    - Pillow 10.x compatible
    """

    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), (10, 12, 22))
    draw = ImageDraw.Draw(img)

    # Load fonts
    try:
        font_big = ImageFont.truetype("arial.ttf", 80)
        font_med = ImageFont.truetype("arial.ttf", 60)
        font_small = ImageFont.truetype("arial.ttf", 36)
    except:
        font_big = font_med = font_small = ImageFont.load_default()

    team_a = data["teamA"]
    team_b = data["teamB"]

    # --------------------------------------
    # TITLE
    # --------------------------------------
    draw.text((W // 2 - 250, 80), "IPL MATCH", font=font_big, fill=(0, 220, 255))

    # --------------------------------------
    # LOAD LOGOS
    # --------------------------------------
    logo_a_path = get_team_logo(team_a)
    logo_b_path = get_team_logo(team_b)

    logo_a = None
    logo_b = None

    if logo_a_path and os.path.exists(logo_a_path):
        try:
            logo_a = Image.open(logo_a_path).convert("RGBA")
            logo_a = logo_a.resize((260, 260), Image.LANCZOS)
        except:
            pass

    if logo_b_path and os.path.exists(logo_b_path):
        try:
            logo_b = Image.open(logo_b_path).convert("RGBA")
            logo_b = logo_b.resize((260, 260), Image.LANCZOS)
        except:
            pass

    # --------------------------------------
    # PLACE LOGOS
    # --------------------------------------
    if logo_a:
        img.paste(logo_a, (120, 260), logo_a)

    if logo_b:
        img.paste(logo_b, (W - 120 - 260, 260), logo_b)

    # --------------------------------------
    # TEAM NAMES
    # --------------------------------------
    # Left team
    draw.text((140, 550), team_a.upper(), font=font_med, fill="white")

    # Right team — calculate width
    t_width = text_width(draw, team_b.upper(), font_med)
    draw.text((W - 140 - t_width, 550), team_b.upper(), font=font_med, fill="white")

    # --------------------------------------
    # VS TEXT
    # --------------------------------------
    draw.text((W // 2 - 40, 530), "VS", font=font_big, fill=(255, 210, 0))

    # --------------------------------------
    # SAVE FINAL PNG
    # --------------------------------------
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, "PNG")

    print("✔ Match card saved with team logos:", path)
