"""Flask API for Sonos control."""

import logging

from flask import Flask, jsonify, request, send_from_directory

logger = logging.getLogger(__name__)

# Global controller instance
sonos_controller = None


def create_app() -> Flask:
    """Create and configure Flask application."""
    app = Flask(__name__, static_folder="../../static")

    @app.route("/")
    def index():
        """Serve the web interface."""
        return send_from_directory(app.static_folder, "index.html")

    @app.route("/<path:filename>")
    def static_files(filename):
        """Serve static files."""
        return send_from_directory(app.static_folder, filename)

    @app.route("/api/speakers", methods=["GET"])
    def list_speakers():
        """List all discovered Sonos speakers."""
        if not sonos_controller:
            return jsonify({"error": "Controller not initialized"}), 503

        speakers = sonos_controller.list_speakers()
        return jsonify({"speakers": speakers})

    @app.route("/api/speaker/volume/<speaker_name>", methods=["GET"])
    def get_speaker_volume(speaker_name):
        """Get volume for a specific speaker."""
        if not sonos_controller:
            return jsonify({"error": "Controller not initialized"}), 503

        volume = sonos_controller.get_volume(speaker_name)
        if volume is not None:
            return jsonify({"speaker": speaker_name, "volume": volume})
        return jsonify({"error": "Failed to get volume"}), 400

    @app.route("/api/play-favorite", methods=["POST"])
    def play_favorite():
        """Play a Sonos favorite on a speaker."""
        if not sonos_controller:
            return jsonify({"error": "Controller not initialized"}), 503

        data = request.get_json()
        if not data or "speaker" not in data or "favorite" not in data:
            return jsonify({"error": "Missing 'speaker' or 'favorite' field"}), 400

        speaker = data["speaker"]
        favorite = data["favorite"]

        success = sonos_controller.play_favorite(speaker, favorite)
        if success:
            return jsonify(
                {"status": "ok", "message": f"Playing {favorite} on {speaker}"}
            )
        return jsonify({"error": "Failed to play favorite"}), 400

    @app.route("/api/control", methods=["POST"])
    def control_playback():
        """Control playback on a speaker."""
        if not sonos_controller:
            return jsonify({"error": "Controller not initialized"}), 503

        data = request.get_json()
        if not data or "speaker" not in data or "action" not in data:
            return jsonify({"error": "Missing 'speaker' or 'action' field"}), 400

        speaker = data["speaker"]
        action = data["action"]

        valid_actions = ["play", "pause", "stop", "next", "previous"]
        if action not in valid_actions:
            return (
                jsonify({"error": f"Invalid action. Must be one of: {valid_actions}"}),
                400,
            )

        success = sonos_controller.control_playback(speaker, action)
        if success:
            return jsonify(
                {"status": "ok", "message": f"Executed {action} on {speaker}"}
            )
        return jsonify({"error": f"Failed to execute {action}"}), 400

    @app.route("/api/volume", methods=["POST"])
    def set_volume():
        """Set volume on a speaker."""
        if not sonos_controller:
            return jsonify({"error": "Controller not initialized"}), 503

        data = request.get_json()
        if not data or "speaker" not in data or "volume" not in data:
            return jsonify({"error": "Missing 'speaker' or 'volume' field"}), 400

        speaker = data["speaker"]
        volume = data["volume"]

        if not isinstance(volume, int) or volume < 0 or volume > 100:
            return (
                jsonify({"error": "Volume must be an integer between 0 and 100"}),
                400,
            )

        success = sonos_controller.set_volume(speaker, volume)
        if success:
            return jsonify(
                {"status": "ok", "message": f"Set volume to {volume} on {speaker}"}
            )
        return jsonify({"error": "Failed to set volume"}), 400

    @app.route("/api/play-uri", methods=["POST"])
    def play_uri():
        """Play audio from a URI on a speaker."""
        if not sonos_controller:
            return jsonify({"error": "Controller not initialized"}), 503

        data = request.get_json()
        if not data or "speaker" not in data or "uri" not in data:
            return jsonify({"error": "Missing 'speaker' or 'uri' field"}), 400

        speaker = data["speaker"]
        uri = data["uri"]

        success = sonos_controller.play_uri(speaker, uri)
        if success:
            return jsonify({"status": "ok", "message": f"Playing URI on {speaker}"})
        return jsonify({"error": "Failed to play URI"}), 400

    @app.route("/api/favorites", methods=["GET"])
    def list_favorites():
        """List all Sonos favorites."""
        if not sonos_controller:
            return jsonify({"error": "Controller not initialized"}), 503

        favorites = sonos_controller.get_favorites()
        return jsonify({"favorites": favorites})

    @app.route("/api/favorites/refresh", methods=["POST"])
    def refresh_favorites():
        """Refresh the favorites list from Sonos system."""
        if not sonos_controller:
            return jsonify({"error": "Controller not initialized"}), 503

        success = sonos_controller.refresh_favorites()
        if success:
            count = len(sonos_controller.get_favorites())
            return jsonify({"status": "ok", "message": f"Refreshed {count} favorites"})
        return jsonify({"error": "Failed to refresh favorites"}), 400

    @app.route("/api/group", methods=["POST"])
    def set_group():
        """Create or update the speaker group."""
        if not sonos_controller:
            return jsonify({"error": "Controller not initialized"}), 503

        data = request.get_json()
        if not data or "speakers" not in data:
            return jsonify({"error": "Missing 'speakers' field"}), 400

        speakers = data["speakers"]
        if not isinstance(speakers, list) or len(speakers) == 0:
            return jsonify({"error": "'speakers' must be a non-empty list"}), 400

        success = sonos_controller.set_group(speakers)
        if success:
            return jsonify(
                {
                    "status": "ok",
                    "message": f"Group created with {len(speakers)} speakers",
                }
            )
        return jsonify({"error": "Failed to create group"}), 400

    @app.route("/api/play-favorite-index", methods=["POST"])
    def play_favorite_index():
        """Play a favorite by index (1-based) on the group."""
        if not sonos_controller:
            return jsonify({"error": "Controller not initialized"}), 503

        data = request.get_json()
        if not data or "index" not in data:
            return jsonify({"error": "Missing 'index' field"}), 400

        index = data["index"]

        if not isinstance(index, int) or index < 1:
            return jsonify({"error": "Index must be a positive integer"}), 400

        success = sonos_controller.play_favorite_by_index(index)
        if success:
            return jsonify(
                {"status": "ok", "message": f"Playing favorite #{index} on group"}
            )
        return jsonify({"error": "Failed to play favorite"}), 400

    @app.route("/api/now-playing", methods=["GET"])
    def get_now_playing():
        """Get currently playing track information from the group coordinator."""
        if not sonos_controller:
            return jsonify({"error": "Controller not initialized"}), 503

        now_playing = sonos_controller.get_now_playing()
        if now_playing:
            return jsonify(now_playing)
        return jsonify({"title": "", "artist": "", "album_art": "", "uri": ""})

    @app.route("/api/group-status", methods=["GET"])
    def get_group_status():
        """Get current group status including members and volumes."""
        if not sonos_controller:
            return jsonify({"error": "Controller not initialized"}), 503

        status = sonos_controller.get_group_status()
        return jsonify(status)

    return app
