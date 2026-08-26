"""
storage.py
----------
Tiny JSON-file "database" for the Step Goal Coach, plus the three functions
that are exposed to the LLM agent as tools:

    log_steps(count)      -> logs steps for today
    get_progress()        -> today's progress toward the daily goal
    get_weekly_summary()  -> rolling 7-day total + milestone check

Kept deliberately simple (single JSON file, no DB) since this is a demo /
submission project. Swap DATA_FILE handling for a real DB later if needed.
"""

import json
import os
from datetime import date, timedelta

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")
DEFAULT_GOAL = 8000

# Weekly step milestones we celebrate, in ascending order.
WEEKLY_MILESTONES = [10000, 25000, 50000, 75000, 100000]


def _today_key() -> str:
    return date.today().isoformat()


def _default_data() -> dict:
    return {"goal": DEFAULT_GOAL, "daily": {}, "milestones_hit": []}


def _load() -> dict:
    if not os.path.exists(DATA_FILE):
        return _default_data()
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        data.setdefault("goal", DEFAULT_GOAL)
        data.setdefault("daily", {})
        data.setdefault("milestones_hit", [])
        return data
    except (json.JSONDecodeError, OSError):
        return _default_data()


def _save(data: dict) -> None:
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _last_7_days() -> list[str]:
    return [(date.today() - timedelta(days=i)).isoformat() for i in range(7)]


# ---------------------------------------------------------------------------
# Tool 1: log_steps
# ---------------------------------------------------------------------------
def log_steps(count: int) -> dict:
    """Logs a number of steps the user just walked, adding them to today's total.

    Args:
        count: The number of steps to add to today's running total. Must be a
            positive integer.

    Returns:
        A dict with the steps that were added and the new total for today.
    """
    data = _load()
    today = _today_key()
    count = max(0, int(count))
    data["daily"][today] = data["daily"].get(today, 0) + count
    _save(data)
    return {
        "steps_added": count,
        "total_today": data["daily"][today],
        "goal": data["goal"],
    }


# ---------------------------------------------------------------------------
# Tool 2: get_progress
# ---------------------------------------------------------------------------
def get_progress() -> dict:
    """Gets the user's progress toward today's step goal.

    Returns:
        A dict with steps taken today, the daily goal, steps remaining
        (0 if the goal is already met), and percent complete.
    """
    data = _load()
    today = _today_key()
    steps_today = data["daily"].get(today, 0)
    goal = data["goal"]
    remaining = max(0, goal - steps_today)
    percent = round(min(100, (steps_today / goal) * 100), 1) if goal else 0
    return {
        "steps_today": steps_today,
        "goal": goal,
        "steps_remaining": remaining,
        "percent_complete": percent,
        "goal_met": steps_today >= goal,
    }


# ---------------------------------------------------------------------------
# Tool 3 (add-on): get_weekly_summary
# ---------------------------------------------------------------------------
def get_weekly_summary() -> dict:
    """Gets the user's total steps for the rolling 7-day week and checks for
    any newly reached weekly milestone (10k, 25k, 50k, 75k, 100k steps).

    Returns:
        A dict with the weekly total, a day-by-day breakdown, and info about
        the most recent milestone reached (or None if none yet).
    """
    data = _load()
    days = _last_7_days()
    breakdown = {d: data["daily"].get(d, 0) for d in reversed(days)}
    weekly_total = sum(breakdown.values())

    newly_hit = None
    for milestone in WEEKLY_MILESTONES:
        if weekly_total >= milestone and milestone not in data["milestones_hit"]:
            data["milestones_hit"].append(milestone)
            newly_hit = milestone

    # milestones_hit can only ever refer to *this* rolling week in a demo app;
    # trim any that no longer apply (simple reset when the week's total drops
    # back below a threshold, e.g. after 7 days roll over).
    data["milestones_hit"] = [m for m in data["milestones_hit"] if weekly_total >= m]
    _save(data)

    next_milestone = next((m for m in WEEKLY_MILESTONES if m > weekly_total), None)

    return {
        "weekly_total": weekly_total,
        "daily_breakdown": breakdown,
        "newly_reached_milestone": newly_hit,
        "next_milestone": next_milestone,
        "steps_to_next_milestone": (next_milestone - weekly_total) if next_milestone else 0,
    }


def get_full_state() -> dict:
    """Convenience helper (not an agent tool) that bundles progress + weekly
    summary for the frontend dashboard, without going through the LLM."""
    progress = get_progress()
    weekly = get_weekly_summary()
    return {"progress": progress, "weekly": weekly}


def set_goal(new_goal: int) -> dict:
    """Not exposed to the agent by default — lets the frontend update the
    daily step goal."""
    data = _load()
    data["goal"] = max(1, int(new_goal))
    _save(data)
    return get_progress()
