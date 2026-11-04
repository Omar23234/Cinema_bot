import os
import re
import json
import requests
from playwright.sync_api import sync_playwright

URL = (
    "https://egy.voxcinemas.com/showtimes"
    "?c=city-centre-almaza"
    "&c=mall-of-egypt"
    "&m=avengers-doomsday"
)

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
FILE = "seen.json"


def send_message(message):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": message},
        timeout=20
    ).raise_for_status()


def get_showtimes():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)

        # استنى تحميل مواعيد العرض
        page.wait_for_timeout(10000)

        text = page.locator("body").inner_text()
        browser.close()

    # استخراج السطور التي تحتوي على مواعيد
    times = set()

    for line in text.splitlines():
        line = " ".join(line.split())

        if re.search(r"\b\d{1,2}:\d{2}\s*(?:AM|PM)?\b", line, re.I):
            if len(line) < 200:
                times.add(line)

    return times


def main():
    current = get_showtimes()

    if not current:
        raise Exception("لم يتم العثور على مواعيد العرض")

    if os.path.exists(FILE):
        with open(FILE, "r", encoding="utf-8") as f:
            old = set(json.load(f))
    else:
        old = set()

    # أول تشغيل: حفظ المواعيد الحالية فقط
    if not old:
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(current), f, ensure_ascii=False)
        return

    new_times = current - old

    for showtime in sorted(new_times):
        send_message(
            "🎬 ميعاد عرض جديد لـ Avengers: Doomsday!\n\n"
            f"{showtime}\n\n"
            f"احجز من هنا:\n{URL}"
        )

    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(old | current), f, ensure_ascii=False)


if __name__ == "__main__":
    main()
  
