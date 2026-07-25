"""
Minecraft server dashboard -- Flask backend.

Routes:
  GET /                          the dashboard page
  GET /api/status                raw server ping (works on any Java server) + live network total
  GET /api/games                 the site's game cards with live player counts
  GET /api/leaderboards/top-kills   headline "Top Kills" panel
  GET /api/leaderboards/<game_key>  full set of boards (Kills, Wins, ...) for one game

Right now every /api/* route is backed by the public Hypixel network (see
services/hypixel_client.py) so this can be demoed today, before the private
server exists. See README.md for exactly what changes when you point this
at the real server instead.
"""

import os
import logging

from flask import Flask, jsonify, render_template
from dotenv import load_dotenv

load_dotenv()

from services import mc_status, hypixel_client, leaderboard_service  # noqa: E402

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("mc_dashboard")


def _error_response(exc: Exception, status: int = 502):
    log.warning("Upstream error: %s", exc)
    return jsonify({"error": str(exc)}), status


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    ping = mc_status.get_server_status()
    try:
        network_total = hypixel_client.get_counts().get("playerCount")
    except hypixel_client.HypixelAPIError as exc:
        return jsonify({"ping": ping, "network_total": None, "network_error": str(exc)})
    return jsonify({"ping": ping, "network_total": network_total})


@app.route("/api/games")
def api_games():
    try:
        return jsonify(leaderboard_service.games_overview())
    except hypixel_client.HypixelAPIError as exc:
        return _error_response(exc)


@app.route("/api/leaderboards/top-kills")
def api_top_kills():
    try:
        board = leaderboard_service.top_kills_board()
    except hypixel_client.HypixelAPIError as exc:
        return _error_response(exc)
    if board is None:
        return jsonify({"error": "No kills-style leaderboard is currently available."}), 404
    return jsonify(board)


@app.route("/api/leaderboards/<game_key>")
def api_leaderboards_for_game(game_key: str):
    try:
        boards = leaderboard_service.leaderboards_for_game(game_key)
    except hypixel_client.HypixelAPIError as exc:
        return _error_response(exc)
    return jsonify(boards)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
