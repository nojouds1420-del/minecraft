"""
The site's own game list -- this is what actually gets shown as cards on
the dashboard, in this exact order. It replaced the earlier approach of
just listing whatever games Hypixel happens to report, because a private
server only offers a handful of specific games, not Hypixel's full catalog.

Each entry can optionally set `hypixel_key` to reuse a matching public
Hypixel game for live numbers during the demo (must match a key from
Hypixel's /v2/counts and /v2/leaderboards responses, e.g. "DUELS", "SMP").
Set it to None for a game that doesn't exist on Hypixel at all
(like a fully custom minigame) -- the card still renders, just without a
live count or leaderboard until the real private server is wired in.

`icon` selects which inline SVG glyph static/js/app.js draws on the card.
Add more icon cases in app.js's ICONS map if you add a game that needs a
new one.
"""

SITE_GAMES = [
    {"key": "duels", "name": "Duels", "hypixel_key": "DUELS", "icon": "sword"},
    {"key": "smp", "name": "SMP", "subtitle": "Survival Multiplayer", "hypixel_key": "SMP", "icon": "house"},
    {"key": "minigames", "name": "Minigames", "hypixel_key": "ARCADE", "icon": "dice"},
    {"key": "genblock", "name": "Genblock", "hypixel_key": None, "icon": "cube"},
]

_BY_KEY = {g["key"]: g for g in SITE_GAMES}


def get_site_game(key: str) -> dict | None:
    return _BY_KEY.get(key)
