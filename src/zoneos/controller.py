"""Refactored Sonos controller using modular components."""

import logging

from zoneos.config import config
from zoneos.favorites import FavoritesManager
from zoneos.groups import GroupManager
from zoneos.playback import PlaybackController
from zoneos.speakers import SpeakerManager

logger = logging.getLogger(__name__)


class SonosController:
    """Main controller that coordinates all Sonos operations."""

    def __init__(self):
        """Initialize controller with all managers."""
        self.speakers = SpeakerManager()
        self.favorites = FavoritesManager()
        self.groups = GroupManager()
        self.playback = PlaybackController()
        self.current_favorite_index = 0  # Track currently playing favorite

        # Initialize favorites
        if self.speakers.list_speakers():
            try:
                speaker = self.speakers.get_any_speaker()
                self.favorites.refresh(speaker)
            except Exception as e:
                logger.error(f"Failed to refresh favorites: {e}")

        # Initialize group with all speakers if configured
        if config.auto_group_on_startup and self.speakers.list_speakers():
            try:
                self.groups.initialize(self.speakers.speakers)
            except Exception as e:
                logger.error(f"Failed to initialize group: {e}")

    # Speaker operations
    def list_speakers(self) -> list[str]:
        """Return list of discovered speaker names."""
        return self.speakers.list_speakers()

    def get_speaker(self, name: str):
        """Get a speaker by name (returns None if not found for compatibility)."""
        try:
            return self.speakers.get_speaker(name)
        except Exception:
            return None

    def set_volume(self, speaker_name: str, volume: int) -> bool:
        """Set volume for the specified speaker (0-100)."""
        try:
            self.speakers.set_volume(speaker_name, volume)
            return True
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
            return False

    def get_volume(self, speaker_name: str) -> int | None:
        """Get current volume for the specified speaker."""
        try:
            return self.speakers.get_volume(speaker_name)
        except Exception as e:
            logger.error(f"Failed to get volume: {e}")
            return None

    # Favorites operations
    def get_favorites(self) -> list[dict[str, str]]:
        """Get cached list of Sonos favorites."""
        return self.favorites.get_all()

    def refresh_favorites(self) -> bool:
        """Refresh the favorites list from Sonos system."""
        try:
            speaker = self.speakers.get_any_speaker()
            self.favorites.refresh(speaker)
            return True
        except Exception as e:
            logger.error(f"Failed to refresh favorites: {e}")
            return False

    def play_favorite(self, speaker_name: str, favorite_name: str) -> bool:
        """Play a Sonos favorite on the specified speaker."""
        try:
            speaker = self.speakers.get_speaker(speaker_name)
            favorite = self.favorites.get_by_title(speaker, favorite_name)
            self.playback.play_uri_with_metadata(
                speaker, favorite["uri"], favorite["metadata"]
            )
            logger.info(f"Playing favorite '{favorite_name}' on {speaker_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to play favorite: {e}")
            return False

    def play_favorite_by_index(self, index: int) -> bool:
        """Play a favorite by its index (0-based) on the group coordinator."""
        try:
            coordinator = self.groups.get_coordinator()
            if not coordinator:
                # Auto-initialize group if no coordinator
                if self.speakers.list_speakers():
                    logger.info("No group set, initializing with all speakers")
                    self.groups.initialize(self.speakers.speakers)
                    coordinator = self.groups.get_coordinator()
                else:
                    logger.error("No speakers available")
                    return False

            if not coordinator:
                logger.error("Failed to initialize group coordinator")
                return False

            favorite = self.favorites.get_by_index(coordinator, index)
            self.playback.play_uri_with_metadata(
                coordinator, favorite["uri"], favorite["metadata"]
            )
            # Track the current favorite index
            self.current_favorite_index = index
            logger.info(f"Playing favorite #{index} '{favorite['title']}' on group")
            return True
        except Exception as e:
            logger.error(f"Failed to play favorite by index: {e}")
            return False

    def play_next_favorite(self) -> bool:
        """Play the next favorite in the list with rollover.

        Returns:
            True if successful, False otherwise
        """
        try:
            favorites = self.get_favorites()
            if not favorites:
                logger.error("No favorites available to play")
                return False

            # Move to next index with rollover (all 0-based)
            next_index = (self.current_favorite_index + 1) % len(favorites)

            # Play the favorite (already 0-based)
            return self.play_favorite_by_index(next_index)
        except Exception as e:
            logger.error(f"Failed to play next favorite: {e}")
            return False

    # Playback operations
    def play_uri(self, speaker_name: str, uri: str) -> bool:
        """Play audio from a URI on the specified speaker."""
        try:
            speaker = self.speakers.get_speaker(speaker_name)
            self.playback.play_uri(speaker, uri)
            return True
        except Exception as e:
            logger.error(f"Failed to play URI: {e}")
            return False

    def control_playback(self, speaker_name: str, action: str) -> bool:
        """Control playback (play, pause, stop, next, previous)."""
        try:
            speaker = self.speakers.get_speaker(speaker_name)
            self.playback.control(speaker, action)
            return True
        except Exception as e:
            logger.error(f"Failed to control playback: {e}")
            return False

    def get_now_playing(self) -> dict[str, str] | None:
        """Get currently playing track information from the group coordinator."""
        try:
            coordinator = self.groups.get_coordinator()
            if not coordinator:
                return None
            return self.playback.get_now_playing(coordinator)
        except Exception as e:
            logger.error(f"Failed to get now playing: {e}")
            return None

    # Group operations
    def set_group(self, speaker_names: list[str]) -> bool:
        """Update the speaker group."""
        try:
            self.groups.set_members(self.speakers.speakers, speaker_names)
            return True
        except Exception as e:
            logger.error(f"Failed to set group: {e}")
            return False

    def get_group_coordinator(self):
        """Get the current group coordinator."""
        return self.groups.get_coordinator()

    def get_group_status(self) -> dict:
        """Get current group status including members and their volumes."""
        members = list(self.groups.get_members())
        status = {"members": members, "volumes": {}}

        for speaker_name in members:
            volume = self.get_volume(speaker_name)
            if volume is not None:
                status["volumes"][speaker_name] = volume

        return status

    # Internal methods for backward compatibility with tests
    def _add_speaker_to_group(self, speaker_name: str) -> bool:
        """Add a speaker to the existing group (for backward compatibility)."""
        try:
            self.groups._add_speaker(self.speakers.speakers, speaker_name)
            return True
        except Exception as e:
            logger.error(f"Failed to add speaker to group: {e}")
            return False

    def _remove_speaker_from_group(self, speaker_name: str) -> bool:
        """Remove a speaker from the group (for backward compatibility)."""
        try:
            self.groups._remove_speaker(self.speakers.speakers, speaker_name)
            return True
        except Exception as e:
            logger.error(f"Failed to remove speaker from group: {e}")
            return False
