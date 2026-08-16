"""Concurrency bench - N virtual shoppers against a running instance.

Drives the real HTTP surface the browser drives: page loads, event batches in
the same shape the tracking client sends, and the recommendations page. It
measures what a shopper feels (page latency, time to a first recommendation)
and what breaks first under load (write-lock contention, shed reasoning,
gateway errors).

Point it at an instance you are willing to fill with junk accounts - it
registers one per virtual shopper.

  python scripts/loadtest.py --shoppers 50 --seconds 120 --base http://127.0.0.1:8001

Writes nothing to the repository. Costs gateway calls: each shopper's browsing
can trigger reasoning, bounded by the per-user cooldown and the instance's
run ceiling.
"""

import argparse
import json
import random
import statistics
import sys
import threading
import time
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

import httpx

CATEGORIES = ["CRM", "HR", "Finance", "Marketing", "DevOps", "Customer Support",
              "Data & Analytics", "Security", "Work Management"]
SEARCHES = ["payroll onboarding", "crm pipeline leads", "ticketing helpdesk",
            "invoicing ledger", "cicd kubernetes", "warehouse etl",
            "edr threat endpoint", "task management"]

samples: list[tuple[str, int, float]] = []          # (label, status, seconds)
first_reco: dict[str, float] = {}
errors: Counter = Counter()
lock = threading.Lock()


def record(label: str, status: int, elapsed: float) -> None:
    with lock:
        samples.append((label, status, elapsed))


def timed(client: httpx.Client, label: str, method: str, url: str, **kw):
    start = time.perf_counter()
    try:
        response = client.request(method, url, **kw)
    except Exception as exc:
        record(label, 0, time.perf_counter() - start)
        with lock:
            errors[f"{label}:{type(exc).__name__}"] += 1
        return None
    elapsed = time.perf_counter() - start
    record(label, response.status_code, elapsed)
    if response.status_code >= 500:
        with lock:
            errors[f"{label}:{response.status_code}"] += 1
            body = response.text[:200].lower()
            if "database is locked" in body:
                errors["DATABASE IS LOCKED"] += 1
    return response


def events_for(products: list[str], category: str) -> list[dict]:
    """The shapes the tracking client actually sends (Core 22)."""
    now = datetime.now(timezone.utc)
    out, n = [], 0

    def add(etype, **meta):
        nonlocal n
        n += 1
        out.append({"event_id": str(uuid.uuid4()), "session_id": "load",
                    "event_type": etype,
                    "ts": (now + timedelta(seconds=n)).isoformat(),
                    "metadata": meta})

    add("CATEGORY_VIEWED", category=category)
    add("SEARCH", query=random.choice(SEARCHES))
    for pid in products:
        add("PRODUCT_VIEWED", category=category.lower(), product_id=pid)
        add("DOCUMENTATION_VIEWED", topic="tickets", product_id=pid)
        add("PRICING_VIEWED", product_id=pid)
    return out


def shopper(index: int, base: str, deadline: float, product_ids: list[str]) -> None:
    email = f"load-{index}-{uuid.uuid4().hex[:6]}@example.com"
    started = time.perf_counter()
    with httpx.Client(base_url=base, timeout=60, follow_redirects=True) as client:
        r = timed(client, "register", "POST", "/auth/register",
                  json={"email": email, "password": "pw123456"})
        if r is None or r.status_code != 201:
            return
        r = timed(client, "login", "POST", "/auth/login",
                  json={"email": email, "password": "pw123456"})
        if r is None or r.status_code != 200:
            return

        category = CATEGORIES[index % len(CATEGORIES)]
        while time.perf_counter() < deadline:
            picks = random.sample(product_ids, k=min(3, len(product_ids)))
            timed(client, "GET /", "GET", "/", params={"category": category})
            for pid in picks:
                timed(client, "GET /product", "GET", f"/product/{pid}")
            timed(client, "POST /events/batch", "POST", "/events/batch",
                  json={"events": events_for(picks, category)})
            r = timed(client, "GET /for-you", "GET", "/for-you")
            if r is not None and r.status_code == 200 and "Why this?" in r.text:
                with lock:
                    first_reco.setdefault(email, time.perf_counter() - started)
            time.sleep(random.uniform(0.4, 1.2))          # think time


def percentiles(values: list[float]) -> tuple[float, float, float]:
    ordered = sorted(values)
    def at(p):
        return ordered[min(len(ordered) - 1, int(len(ordered) * p))]
    return at(0.50), at(0.95), at(0.99)


def main(argv) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shoppers", type=int, default=50)
    ap.add_argument("--seconds", type=int, default=120)
    ap.add_argument("--base", default="http://127.0.0.1:8001")
    args = ap.parse_args(argv)

    with httpx.Client(base_url=args.base, timeout=30) as probe:
        ready = probe.get("/ready")
        print(f"readiness: {ready.status_code} {ready.text[:160]}")
        if ready.status_code != 200:
            print("instance is not ready - refusing to measure a warm-up")
            return 1
    product_ids = [f"PROD-{n:03d}" for n in range(100, 130)]

    print(f"\n{args.shoppers} shoppers for {args.seconds}s against {args.base}\n")
    deadline = time.perf_counter() + args.seconds
    threads = [threading.Thread(target=shopper, args=(i, args.base, deadline, product_ids),
                                daemon=True)
               for i in range(args.shoppers)]
    wall = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=args.seconds + 120)
    wall = time.perf_counter() - wall

    by_label: dict[str, list[float]] = defaultdict(list)
    statuses: Counter = Counter()
    for label, status, elapsed in samples:
        by_label[label].append(elapsed)
        statuses[status] += 1

    print(f"{'endpoint':<22} {'n':>6} {'p50':>8} {'p95':>8} {'p99':>8} {'max':>8}")
    print("-" * 64)
    for label in sorted(by_label):
        vals = by_label[label]
        p50, p95, p99 = percentiles(vals)
        print(f"{label:<22} {len(vals):>6} {p50:>8.3f} {p95:>8.3f} {p99:>8.3f} {max(vals):>8.3f}")

    print(f"\nrequests: {len(samples)} in {wall:.1f}s "
          f"= {len(samples)/wall:.1f}/s")
    print("statuses:", dict(sorted(statuses.items())))
    if first_reco:
        got = list(first_reco.values())
        p50, p95, _ = percentiles(got)
        print(f"first recommendation: {len(got)}/{args.shoppers} shoppers "
              f"| p50 {p50:.1f}s | p95 {p95:.1f}s")
    else:
        print(f"first recommendation: 0/{args.shoppers} shoppers saw one")
    print("errors:", dict(errors) if errors else "none")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
