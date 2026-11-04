
import os
import re
import json
import time
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
    last_error = None

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-http2"]
        )

        try:
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                )
            )

            for attempt in range(3):
                try:
                    print(f"محاولة فتح VOX رقم {attempt + 1}")

                    page.goto(
                        URL,
                        wait_until="domcontentloaded",
                        timeout=60000
                    )

                    page.wait_for_timeout(10000)

                    text = page.locator("body").inner_text()

                    if "Avengers" not in text and "Doomsday" not in text:
                        raise Exception("صفحة الفيلم لم تظهر بشكل صحيح")

                    break

                except Exception as e:
                    last_error = e

                    if attempt == 2:
                        raise Exception(
                            f"فشل فتح صفحة VOX بعد 3 محاولات: {last_error}"
                        )

                    time.sleep(5)

        finally:
            browser.close()

    times = set()

    for line in text.splitlines():
        line = " ".join(line.split())

        if re.search(
            r"\b\d{1,2}:\d{2}\s*(?:AM|PM)?\b",
            line,
            re.I
        ):
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

    if not old:
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(current), f, ensure_ascii=False)

        print("تم حفظ المواعيد الحالية")
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

    print(f"تم فحص المواعيد. مواعيد جديدة: {len(new_times)}")


if __name__ == "__main__":
    main()
