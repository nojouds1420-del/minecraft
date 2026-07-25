"""
Resolves Minecraft UUIDs to usernames via Mojang's public session server.

Why this is needed: Hypixel's /v2/leaderboards endpoint only returns raw
player UUIDs in ranked order (see hypixel_client.get_leaderboards). To show
an actual name in the UI we look each one up here. No API key required.

Endpoint: GET https://sessionserver.mojang.com/session/minecraft/profile/<uuid>
Docs: https://minecraft.wiki/w/Mojang_API
Rate limit: roughly 200-400 requests/minute, shared across everyone calling
from this network -- which is exactly why we cache aggressively and only
resolve the handful of UUIDs actually shown on screen (top 10 per board),
never a whole leaderboard's backing data.
"""

import requests

from .cache import cache

SESSION_SERVER = "https://sessionserver.mojang.com/session/minecraft/profile"
REQUEST_TIMEOUT = 5

# Usernames essentially never change day-to-day, so we can cache far longer
# here than for the live counts/leaderboards data.
USERNAME_TTL = 6 * 60 * 60  # 6 hours


def _fetch_username(uuid: str) -> str:
    resp = requests.get(f"{SESSION_SERVER}/{uuid}", timeout=REQUEST_TIMEOUT)
    if resp.status_code == 204 or resp.status_code == 404:
        return uuid[:8]  # profile no longer resolvable; show a short id instead
    resp.raise_for_status()
    return resp.json().get("name", uuid[:8])


def resolve_username(uuid: str) -> str:
    return cache.get_or_set(f"mojang:name:{uuid}", USERNAME_TTL, lambda: _fetch_username(uuid))


def resolve_usernames(uuids: list[str]) -> dict[str, str]:
    """Resolve a list of UUIDs to a {uuid: username} dict, deduping and
    reusing the cache so the same player appearing on several leaderboards
    only costs one real request."""
    return {u: resolve_username(u) for u in dict.fromkeys(uuids)}
