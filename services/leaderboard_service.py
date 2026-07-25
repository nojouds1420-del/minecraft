"""
Turns the raw Hypixel API responses into the shapes the frontend wants,
scoped to the site's own fixed game list (services/site_games.py) rather
than Hypixel's entire catalog -- a private server only offers a handful of
specific games, so that's all the dashboard should ever show.

This is the layer you would swap out when moving from the public Hypixel
demo to the celebrity's real private server: instead of calling
hypixel_client.get_counts()/get_leaderboards(), you'd query whatever your
Paper/Spigot stats plugin writes to its database, keyed by the same `key`
values already used in SITE_GAMES (duels, smp, minigames, genblock, ...).
The function signatures below (games_overview(), top_kills_board(),
leaderboards_for_game()) are designed to stay the same either way, so
app.py and the frontend would not need to change at all.
"""

from . import hypixel_client, mojang_client
from .site_games import SITE_GAMES, get_site_game

KILLS_HINTS = ("kill",)  # matched against a board's title/path, lowercased
MAX_LEADERS_SHOWN = 10


def _looks_like_kills_board(board: dict) -> bool:
    haystack = f"{board.get('title', '')} {board.get('path', '')}".lower()
    return any(hint in haystack for hint in KILLS_HINTS)


def _resolve_board(board: dict) -> dict:
    """Attach resolved usernames (and rank numbers) to a raw leaderboard entry."""
    uuids = (board.get("leaders") or [])[:MAX_LEADERS_SHOWN]
    names = mojang_client.resolve_usernames(uuids)
    return {
        "title": board.get("title") or board.get("prefix") or "Leaderboard",
        "entries": [
            {"rank": i + 1, "uuid": u, "username": names.get(u, u[:8])}
            for i, u in enumerate(uuids)
        ],
    }


def _raw_boards_for_hypixel_key(hypixel_key):
    if not hypixel_key:
        return []
    raw = hypixel_client.get_leaderboards().get("leaderboards", {})
    return raw.get(hypixel_key.upper(), []) or raw.get(hypixel_key, [])


def games_overview():
    """The site's games, in their configured order, each with a live player
    count where a Hypixel mapping exists. `players` is None (not 0) for a
    game with no mapping yet -- the frontend shows that as 'not live yet'
    rather than implying the game truly has zero players."""
    counts = hypixel_client.get_counts()
    hypixel_games = counts.get("games", {})

    overview = []
    for game in SITE_GAMES:
        info = hypixel_games.get(game["hypixel_key"]) if game["hypixel_key"] else None
        overview.append({
            "key": game["key"],
            "name": game["name"],
            "subtitle": game.get("subtitle"),
            "icon": game["icon"],
            "players": info.get("players") if info is not None else None,
            "has_live_data": game["hypixel_key"] is not None,
        })
    return overview


def leaderboards_for_game(site_key):
    """All leaderboard categories (Kills, Wins, ...) for one of the site's
    games, with resolved usernames. Returns [] if there's no Hypixel
    mapping yet (e.g. a fully custom game) or Hypixel has no board for it."""
    game = get_site_game(site_key)
    if game is None:
        return []
    boards = _raw_boards_for_hypixel_key(game["hypixel_key"])
    return [_resolve_board(b) for b in boards]


def top_kills_board():
    """The Kills leaderboard for whichever of the site's own games currently
    has the most players online -- used as the headline 'Top Kills' panel.
    Only looks at the site's configured games, not Hypixel's full catalog."""
    games_by_players = sorted(
        (g for g in games_overview() if g["has_live_data"]),
        key=lambda g: (g["players"] or 0),
        reverse=True,
    )
    for game in games_by_players:
        site_game = get_site_game(game["key"])
        boards = _raw_boards_for_hypixel_key(site_game["hypixel_key"])
        kills_board = next((b for b in boards if _looks_like_kills_board(b)), None)
        if kills_board:
            resolved = _resolve_board(kills_board)
            resolved["game"] = game["name"]
            resolved["game_key"] = game["key"]
            return resolved
    return None
