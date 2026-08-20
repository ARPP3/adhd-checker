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
STALE_AFTER = int(os.environ.get("STALE_AFTER", "900"))


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


def post(content):
    body = json.dumps({"content": content}).encode()
    req = urllib.request.Request(WEBHOOK, data=body, headers={
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
    })
    urllib.request.urlopen(req, timeout=30).read()


def notify(dates):
    post("@everyone **ADHD assessment: appointment available!**\n"
         + "\n".join(f"- {d}" for d in sorted(dates))
         + f"\nBook here: {BOOKING_URL}")


def log(msg):
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}", flush=True)


def main():
    seen = set()
    last_ok = time.time()
    stale = False
    while True:
        try:
            found = available_dates()
            last_ok = time.time()
            new = found - seen
            log(f"available={len(found)} new={len(new)}")
            if new:
                notify(new)
            seen = found
            if stale:
                stale = False
                post(":white_check_mark: Checks are working again.")
        except Exception as e:
            log(f"error: {e}")
            if not stale and time.time() - last_ok > STALE_AFTER:
                stale = True
                try:
                    post(f"@everyone :warning: **Appointment checker is failing.**\n"
                         f"No successful check for {STALE_AFTER // 60} min. "
                         f"Latest error: `{e}`")
                except Exception as post_error:
                    log(f"could not report failure: {post_error}")
        time.sleep(INTERVAL)


def selftest():
    ms = list(months_ahead(date(2026, 11, 1), 4))
    assert ms == [date(2026, 11, 1), date(2026, 12, 1), date(2027, 1, 1), date(2027, 2, 1)], ms
    assert {"2027-01-05", "2027-02-09"} - {"2027-01-05"} == {"2027-02-09"}
    print("ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit()
    if not WEBHOOK:
        sys.exit("DISCORD_WEBHOOK not set")
    main()
