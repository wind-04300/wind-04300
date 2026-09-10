#!/usr/bin/env python3
"""Write a dated activity log so every day gets at least one contribution.

The other workflows (3d-contrib / cards / snake) only commit when the generated
files actually change. On a quiet day they print "No changes to commit", which
leaves a blank square in the contribution graph and starves the snake. This
script forces a real file change once per day, which is then committed and
counted as a contribution.

Deliberately written in plain Python instead of shell so it behaves identically
on every runner (no locale / quoting surprises).
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

# GitHub's runner clock is UTC; the graph is read in the account's local time.
CN_TZ = timezone(timedelta(hours=8))

now = datetime.now(CN_TZ)
day = now.strftime("%Y-%m-%d")
clock = now.strftime("%H:%M")

os.makedirs("activity", exist_ok=True)
path = os.path.join("activity", f"{day}.md")

if os.path.exists(path):
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(f"- heartbeat {clock}\n")
else:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"# {day}\n\n")
        fh.write("Daily heartbeat - keeps the contribution graph alive.\n\n")
        fh.write(f"- heartbeat {clock}\n")

print(f"wrote {path}")
print(f"activity entries: {len(os.listdir('activity'))}")
