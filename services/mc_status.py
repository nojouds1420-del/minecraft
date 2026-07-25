"""
Raw server ping using the Minecraft "Server List Ping" protocol, via the
`mcstatus` library (https://pypi.org/project/mcstatus/).

This is the one piece of this dashboard that needs absolutely nothing special
installed on the target server -- no plugin, no API key, no database access.
Any Java Edition server (public or private, vanilla or modded) answers this
ping the same way a client's server list does, and hands back online/max
player count, the MOTD, and version info.

This is intentionally kept separate from hypixel_client.py: this module is
what you point at the celebrity's *actual* private server once it exists.
The Hypixel client is only standing in for it during the demo because a
private server isn't spun up yet.
"""

import os

from mcstatus import JavaServer

from .cache import cache

# Swap this to the private server's address (host or host:port) once it
# exists. Defaults to a well-known public server so this works out of the
# box for the demo.
TARGET_SERVER = os.environ.get("MC_SERVER_ADDRESS", "mc.hypixel.net")
STATUS_TTL = 15
REQUEST_TIMEOUT = 5


class ServerUnreachableError(RuntimeError):
    pass


def _ping() -> dict:
    try:
        server = JavaServer.lookup(TARGET_SERVER, timeout=REQUEST_TIMEOUT)
        status = server.status()
    except Exception as exc:  # noqa: BLE001 - surfacing any failure the same way
        raise ServerUnreachableError(f"Could not reach {TARGET_SERVER}: {exc}") from exc

    return {
        "address": TARGET_SERVER,
        "online": True,
        "players_online": status.players.online,
        "players_max": status.players.max,
        "sample_players": [p.name for p in (status.players.sample or [])],
        "motd": status.motd.to_plain(),
        "version": status.version.name,
        "latency_ms": round(status.latency, 1),
    }


def get_server_status() -> dict:
    try:
        return cache.get_or_set("mcstatus:ping", STATUS_TTL, _ping)
    except ServerUnreachableError as exc:
        return {"address": TARGET_SERVER, "online": False, "error": str(exc)}
