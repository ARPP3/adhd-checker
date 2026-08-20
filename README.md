# Appointment checker

Watches the ADHD assessment calendar at
<https://www.demir-psychotherapie.de/terminbuchung> and pings a Discord
webhook when a slot opens up.

The booking widget on that page is Squarespace/Acuity Scheduling, so this
queries the same JSON endpoint the calendar itself uses:

```
GET https://app.acuityscheduling.com/api/scheduling/v1/availability/month
      ?owner=da684095&appointmentTypeId=72808421&calendarId=11320994
      &timezone=Europe/Berlin&month=YYYY-MM-01
-> {"2026-09-01": false, "2026-09-02": false, ...}
```

`month` must be the first of the month. One request per month, so a cycle
with `MONTHS=12` makes 12 requests. No browser, no dependencies, stdlib only.

## Alerts

- **Slot found** - pings `@everyone` with the dates and the booking link.
  Only newly opened dates are announced, so a slot that stays open does not
  repeat. If a date disappears and comes back, it alerts again.
- **Checker broken** - if nothing has succeeded for `STALE_AFTER` seconds,
  it says so once, then says so again when checks recover. This exists
  because a silently failing checker looks identical to "no appointments".

## Configuration

Copy `.env.example` to `.env` and fill in the webhook. All values are
environment variables; see that file for what each one does.

## Run

```sh
docker compose up -d --build
docker compose logs -f
```

Each cycle logs one line:

```
2026-08-20 18:08:54 available=0 new=0
```

## Update

```sh
git pull && docker compose up -d --build
```

Changing only `.env` needs no rebuild - `docker compose up -d` is enough.

## Test

```sh
python check.py --selftest
```

To check the Discord side without waiting for a real slot:

```sh
DISCORD_WEBHOOK=... python -c "import check; check.notify({'2027-02-09'})"
```
