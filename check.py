import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import date

API = "https://app.acuityscheduling.com/api/scheduling/v1/availability/month"
OWNER = "da684095"
APPOINTMENT_TYPE = "72808421"
CALENDAR = "11320994"
BOOKING_URL = "https://www.demir-psychotherapie.de/terminbuchung"

WEBHOOK = os.environ.get("DISCORD_WEBHOOK", "")
INTERVAL = int(os.environ.get("INTERVAL", "900"))
MONTHS = int(os.environ.get("MONTHS", "12"))


def months_ahead(start, n):
    for i in range(n):
        m = start.month - 1 + i
        yield date(start.year + m // 12, m % 12 + 1, 1)


def fetch_month(first_of_month):
    q = urllib.parse.urlencode({
        "owner": OWNER,
        "appointmentTypeId": APPOINTMENT_TYPE,
        "calendarId": CALENDAR,
        "timezone": "Europe/Berlin",
        "month": first_of_month.isoformat(),
    })
    req = urllib.request.Request(f"{API}?{q}", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def available_dates():
    found = set()
    for m in months_ahead(date.today(), MONTHS):
        for day, open_ in fetch_month(m).items():
            if open_:
                found.add(day)
    return found


def notify(dates):
    body = json.dumps({
        "content": "@everyone **ADHS-Diagnostik: Termin frei!**\n"
                   + "\n".join(f"- {d}" for d in sorted(dates))
                   + f"\n{BOOKING_URL}"
    }).encode()
    req = urllib.request.Request(WEBHOOK, data=body, headers={
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
    })
    urllib.request.urlopen(req, timeout=30).read()


def selftest():
    ms = list(months_ahead(date(2026, 11, 1), 4))
    assert ms == [date(2026, 11, 1), date(2026, 12, 1), date(2027, 1, 1), date(2027, 2, 1)], ms
    seen = {"2027-01-05"}
    found = {"2027-01-05", "2027-02-09"}
    assert found - seen == {"2027-02-09"}
    print("ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit()
    if not WEBHOOK:
        sys.exit("DISCORD_WEBHOOK not set")
    seen = set()
    while True:
        try:
            found = available_dates()
            new = found - seen
            seen = found
            print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} available={len(found)} new={len(new)}", flush=True)
            if new:
                notify(new)
        except Exception as e:
            print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} error: {e}", flush=True)
        time.sleep(INTERVAL)
