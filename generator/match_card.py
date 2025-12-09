from PIL import Image, ImageDraw, ImageFont
import os

# ====================================================
# MATCH CARD GENERATOR (Updated for "projected" score)
# ====================================================

def load_font(size):
    """
    Safely load a font. Fallback to default if unavailable.
    """
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        return ImageFont.load_default()

def generate_card(data, output_path):
    """
    Generates a match preview card PNG.
    Works with keys from generate_from_api.py including:
      - teamA, teamB
      - venue
      - projected (replaces old 'score')
    """

    # Extract data safely
    team_a = data.get("teamA", "Team A")
    team_b = data.get("teamB", "Team B")
    venue = data.get("venue", "Stadium")
    projected = data.get("projected", "N/A")
    date = data.get("date", "")

    # Card dimensions
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), (10, 12, 22))
    draw = ImageDraw.Draw(img)

    # Background gradient
    for y in range(H):
        c = 10 + int(40 * (y / H))
        draw.line([(0, y), (W, y)], fill=(c, c, c + 10))

    # Fonts
    font_title = load_font(80)
    font_team = load_font(70)
    font_small = load_font(40)
    font_proj = load_font(65)

    # Title
    draw.text((W // 2 - 200, 60), "MATCH PREVIEW", font=font_title, fill=(0, 220, 255))

    # Teams
    draw.text((100, 250), team_a, font=font_team, fill="white")
    tw = draw.textlength(team_b, font=font_team)
    draw.text((W - tw - 100, 250), team_b, font=font_team, fill="white")

    # VS
    draw.text((W // 2 - 40, 340), "VS", font=font_title, fill=(255, 210, 0))

    # Venue
    draw.text((100, 450), venue, font=font_small, fill=(200, 200, 210))

    # Date
    draw.text((100, 520), f"Date: {date}", font=font_small, fill=(200, 200, 210))

    # Projected Score Box
    box_y = 700
    draw.rectangle([80, box_y, W - 80, box_y + 250], outline=(255, 210, 0), width=4)

    draw.text((W // 2 - 200, box_y + 40), "Projected Score", font=font_small, fill="white")
    draw.text((W // 2 - 150, box_y + 130), projected, font=font_proj, fill=(255, 210, 0))

    # Save card
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")

    print("✔ Match card generated:", output_path)
