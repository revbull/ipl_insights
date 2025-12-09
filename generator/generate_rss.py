import os
import glob
from datetime import datetime

# 🔴 Смени това с твоя GitHub username и име на репото
BASE_URL = "https://revbull.github.io/ipl-site"

def generate_rss():
    # Скриптът се изпълнява от папка generator/
    matches_path = os.path.join("..", "matches")
    files = sorted(
        glob.glob(os.path.join(matches_path, "*.html")),
        reverse=True
    )

    items = []

    for f in files[:30]:  # последните 30 мача
        filename = os.path.basename(f)           # напр. 2025-02-06.html
        date_str = filename.replace(".html", "") # 2025-02-06

        # pubDate във формат за RSS
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            dt = datetime.utcnow()

        pub_date_rss = dt.strftime("%a, %d %b %Y 12:00:00 GMT")

        link = f"{BASE_URL}/matches/{filename}"

        item = f"""
    <item>
        <title>IPL Match – {date_str}</title>
        <link>{link}</link>
        <guid>{link}</guid>
        <pubDate>{pub_date_rss}</pubDate>
        <description>IPL match preview and analytics for {date_str}.</description>
    </item>"""
        items.append(item)

    items_block = "\n".join(items)

    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
    <title>IPL Match Analytics Feed</title>
    <link>{BASE_URL}</link>
    <description>Daily IPL match previews, pitch reports, H2H and projections.</description>
    <language>en</language>
{items_block}
</channel>
</rss>
"""

    rss_path = os.path.join("..", "rss.xml")
    with open(rss_path, "w", encoding="utf-8") as f:
        f.write(rss_content)

    print("✔ RSS generated:", rss_path)


if __name__ == "__main__":
    generate_rss()
