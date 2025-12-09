from PIL import Image, ImageDraw, ImageFont
import json
import os
from datetime import datetime

def generate_match_card(json_path, output_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    date = data["date"]
    team_a = data["teamA"]
    team_b = data["teamB"]
    venue = data.get("venue", "T20 Venue")
    score_range = data["score"]

    # Размер за Insta/Telegram (портрет)
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), (5, 6, 10))
    draw = ImageDraw.Draw(img)

    # лек градиент фон
    for y in range(H):
        ratio = y / H
        r = int(5 + 20 * ratio)
        g = int(6 + 40 * ratio)
        b = int(30 + 80 * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # шрифтове (fallback към default ако нямаш custom)
    try:
        title_font = ImageFont.truetype("arial.ttf", 80)
        team_font = ImageFont.truetype("arial.ttf", 72)
        small_font = ImageFont.truetype("arial.ttf", 32)
        mid_font = ImageFont.truetype("arial.ttf", 48)
    except:
        title_font = ImageFont.load_default()
        team_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        mid_font = ImageFont.load_default()

    # Заглавие
    title = "IPL MATCH PREVIEW"
    tw, th = draw.textsize(title, font=title_font)
    draw.text(((W - tw) / 2, 80), title, font=title_font, fill=(0, 224, 255))

    # Дата
    d_label = datetime.strptime(date, "%Y-%m-%d").strftime("%d %b %Y")
    draw.text((80, 200), d_label, font=small_font, fill=(200, 200, 210))

    # Venue
    draw.text((80, 240), venue, font=small_font, fill=(180, 180, 195))

    # Team A
    taw, tah = draw.textsize(team_a, font=team_font)
    draw.text((80, 420), team_a, font=team_font, fill=(245, 245, 247))

    # VS
    vs = "VS"
    vsw, vsh = draw.textsize(vs, font=team_font)
    draw.text(((W - vsw) / 2, 510), vs, font=team_font, fill=(255, 216, 0))

    # Team B
    tbw, tbh = draw.textsize(team_b, font=team_font)
    draw.text((W - tbw - 80, 420), team_b, font=team_font, fill=(245, 245, 247))

    # Box за projected score
    box_w, box_h = 800, 220
    box_x = (W - box_w) / 2
    box_y = 750
    draw.rounded_rectangle(
        [box_x, box_y, box_x + box_w, box_y + box_h],
        radius=40,
        outline=(255, 216, 0),
        width=4,
        fill=(15, 15, 25)
    )

    label = "PROJECTED FIRST-INNINGS SCORE"
    lw, lh = draw.textsize(label, font=small_font)
    draw.text((W / 2 - lw / 2, box_y + 30), label, font=small_font, fill=(190, 190, 200))

    sw, sh = draw.textsize(score_range, font=mid_font)
    draw.text((W / 2 - sw / 2, box_y + 90), score_range, font=mid_font, fill=(255, 216, 0))

    caption = "Analysis only · For cricket fans"
    cw, ch = draw.textsize(caption, font=small_font)
    draw.text((W / 2 - cw / 2, box_y + 150), caption, font=small_font, fill=(170, 170, 185))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, format="PNG")
    print("✔ Match card generated:", output_path)


if __name__ == "__main__":
    # използваме последния json: data/YYYY-MM-DD.json
    today = datetime.now().strftime("%Y-%m-%d")
    json_path = f"../data/{today}.json"
    out_path = f"../assets/img/cards/{today}.png"
    generate_match_card(json_path, out_path)
