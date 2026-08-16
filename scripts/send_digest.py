"""Run one digest cycle now, instead of waiting for the 17:00 scheduler.

Calls the same `run_digest_cycle` the APScheduler job calls - there is no
separate path, so what this exercises is what the schedule runs (core 24).

Delivery is idempotent per (user, digest window) by DB constraint, and the
window is the calendar date, so a second run on the same day is a no-op by
design rather than a bug. To exercise a fresh window, pass a different clock:

  python scripts/send_digest.py                       # now
  python scripts/send_digest.py --at 2026-08-17T17:00 # a different window

`--at` drives the same `now` parameter the scheduler passes and the time-based
tests use; it does not bypass the constraint, it moves to another window.

Prints every Delivery Record, including the skips. Silence is a feature
(POL-DELIV-001) and a skip with its reason is the observable form of it.

Run:  .venv\\Scripts\\python scripts\\send_digest.py
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

from smartreco.delivery import digest_window, run_digest_cycle
from smartreco.models import utcnow

USAGE = __doc__


def main(argv: list[str]) -> int:
    if argv and argv[0] in ("-h", "--help"):
        print(USAGE)
        return 0

    now = utcnow()
    if argv and argv[0] == "--at":
        if len(argv) < 2:
            raise SystemExit("--at needs a timestamp, e.g. --at 2026-08-17T17:00")
        now = datetime.fromisoformat(argv[1])

    load_dotenv()
    from apps.web.main import _init_state

    state = _init_state()
    print(f"digest window {digest_window(now)}  (clock {now:%Y-%m-%d %H:%M})")
    if not os.environ.get("TELEGRAM_BOT_TOKEN"):
        print("note: TELEGRAM_BOT_TOKEN is unset - the adapter will report "
              "unavailable and every Telegram user will be SKIPPED, recorded.")

    with state["session_factory"]() as db:
        records = run_digest_cycle(db, state["chroma"], state["backend"],
                                   state.get("gateway"), state["policies"], now)
        db.commit()

        if not records:
            print("\nno delivery records - every user already has one for this "
                  "window (idempotent by constraint); try --at another date.")
            return 0

        print(f"\n{'user':>5}  {'channel':<9} {'status':<8} reason")
        for r in records:
            print(f"{r.user_id:>5}  {r.channel or '-':<9} {r.status:<8} {r.reason or ''}")
        sent = sum(1 for r in records if r.status == "SENT")
        print(f"\n{len(records)} evaluated, {sent} sent")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
