"""Playback control for Sonos speakers."""

import logging

import soco
from soco.exceptions import SoCoException

from zoneos.exceptions import PlaybackError

logger = logging.getLogger(__name__)


class PlaybackController:
    """Handles playback operations for Sonos speakers."""

    def play_uri(self, speaker: soco.SoCo, uri: str) -> None:
        """Play audio from a URI on the specified speaker.

        Args:
            speaker: SoCo speaker instance
            uri: Audio URI to play

        Raises:
            PlaybackError: If playback fails
        """
        try:
            speaker.play_uri(uri)
            logger.info(f"Playing URI on {speaker.player_name}: {uri}")
        except SoCoException as e:
            raise PlaybackError(f"Failed to play URI on {speaker.player_name}: {e}")

    def play_uri_with_metadata(
        self, speaker: soco.SoCo, uri: str, metadata: str
    ) -> None:
        """Play audio from a URI with metadata on the specified speaker.

        Args:
            speaker: SoCo speaker instance
            uri: Audio URI to play
            metadata: DIDL-Lite metadata

        Raises:
            PlaybackError: If playback fails
        """
        try:
            speaker.play_uri(uri, meta=metadata)
            logger.info(f"Playing URI with metadata on {speaker.player_name}")
        except SoCoException as e:
            raise PlaybackError(
                f"Failed to play URI with metadata on {speaker.player_name}: {e}"
            )

    def control(self, speaker: soco.SoCo, action: str) -> None:
        """Control playback (play, pause, stop, next, previous).

        Args:
            speaker: SoCo speaker instance
            action: Playback action

        Raises:
            PlaybackError: If control action fails
        """
        try:
            if action == "play":
                speaker.play()
            elif action == "pause":
                speaker.pause()
            elif action == "stop":
                speaker.stop()
            elif action == "next":
                speaker.next()
            elif action == "previous":
                speaker.previous()
            else:
                raise PlaybackError(f"Unknown action: {action}")

            logger.info(f"Executed '{action}' on {speaker.player_name}")
        except SoCoException as e:
            raise PlaybackError(
                f"Failed to execute '{action}' on {speaker.player_name}: {e}"
            )

    def get_now_playing(self, speaker: soco.SoCo) -> dict[str, str]:
        """Get currently playing track information.

        Args:
            speaker: SoCo speaker instance

        Returns:
            Dictionary with track information

        Raises:
            PlaybackError: If retrieval fails
        """
        try:
            track_info = speaker.get_current_track_info()
            logger.info(f"Retrieved now playing from {track_info}")
            return {
                "title": track_info.get("title", ""),
                "artist": track_info.get("artist", ""),
                "album_art": track_info.get("album_art", ""),
                "uri": track_info.get("uri", ""),
            }
        except SoCoException as e:
            raise PlaybackError(
                f"Failed to get now playing from {speaker.player_name}: {e}"
            )
