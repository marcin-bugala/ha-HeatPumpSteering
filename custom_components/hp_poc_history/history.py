"""Bounded, read-only history reconstruction; independent of HA runtime."""
from bisect import bisect_right
from math import isfinite
from statistics import median

STEP = 300
WINDOW = 10800
LOOKBACK = 15 * 3600


def temperature(value, lower, upper):
    """Reject unavailable, NaN, infinity and impossible measurements."""
    try:
        number = float(value)
    except (ValueError, TypeError):
        return None
    return number if isfinite(number) and lower <= number <= upper else None


def reconstruct(events, runs, stamp, current):
    """Resample recorded states, not event counts. Never interpolate unknowns.

    events: five ordered lists of (Unix timestamp, state).
    runs: observed Recorder uptime intervals. Missing uptime stays missing.
    current: current switch and setpoint, only used to validate timer recovery.
    The window-start snapshot is a lower bound, not an exact transition time.
    """
    stamp = int(stamp)
    end = stamp // STEP * STEP
    start = end - LOOKBACK
    series = [sorted(rows) for rows in events]
    clocks = [[row[0] for row in rows] for rows in series]
    runs = sorted((max(start, a), min(stamp, b)) for a, b in runs if b >= start and a <= stamp)

    def at(index, when):
        pos = bisect_right(clocks[index], when) - 1
        return series[index][pos][1] if pos >= 0 else None

    def online(when):
        return any(a <= when <= b for a, b in runs)

    sampled = []
    for when in range(start, end + 1, STEP):
        values = [temperature(at(i, when), 10 if i < 2 else -35, 35)
                  if online(when) else None for i in range(3)]
        sampled.append([when, *values])

    def comfort(rows, column):
        valid = [row for row in rows if row[column] is not None]
        if len(valid) < 29 or valid[-1][0] - valid[0][0] < .8 * WINDOW:
            return None
        gaps = [b[0] - a[0] for a, b in zip(valid, valid[1:])]
        if max(gaps + [rows[-1][0] - valid[-1][0]]) > 1200:
            return None
        # A currently unavailable source cannot produce a trend sample.
        return median([row[column] for row in valid]) if rows[-1][column] is not None else None

    trend = []
    for index in range(36, len(sampled)):
        rows = sampled[index - 36:index + 1]
        trend.append([rows[-1][0], comfort(rows, 1), comfort(rows, 2)])

    def since(index, value, numeric=False):
        expected = temperature(value, -100, 100) if numeric else value
        if expected is None or (not numeric and expected not in ('on', 'off')):
            return None
        rows = series[index]
        if not rows or not online(stamp):
            return None
        result = None
        # Equal reports and restart snapshots do not reset a genuine interval.
        for when, state in rows:
            if when > stamp:
                break
            observed = temperature(state, -100, 100) if numeric else state
            if observed == expected:
                if result is None:
                    result = max(start, when)
            else:
                result = None
        if result is None:
            return None
        result = max(result, runs[0][0])
        # A long unobserved HA outage invalidates continuity, even with equal states.
        for (_, stop), (resume, _) in zip(runs, runs[1:]):
            if resume - stop > 1200 and resume > result:
                result = resume
        return int(result)

    return dict(generated_at=stamp, raw=sampled[-37:], trend=trend[-145:],
                co1=current[0], co1_since=since(3, current[0]),
                setpoint=temperature(current[1], -100, 100),
                setpoint_since=since(4, current[1], numeric=True))
