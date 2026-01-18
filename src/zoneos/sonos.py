"""Sonos controller for speaker discovery and control."""

import logging

import soco
from soco.exceptions import SoCoException

logger = logging.getLogger(__name__)


class SonosController:
    """Manages Sonos speaker discovery and control."""

    def __init__(self):
        """Initialize controller and discover speakers."""
        self.speakers: dict[str, soco.SoCo] = {}
        self._favorites: list[dict[str, str]] = []
        self._group_coordinator: soco.SoCo | None = None
        self._group_members: set[str] = set()  # Track current group members
        self._discover_speakers()
        self.refresh_favorites()
        # Initialize group with all discovered speakers
        if self.speakers:
            self._initialize_group(list(self.speakers.keys()))

    def _discover_speakers(self):
        """Discover all Sonos speakers on the network."""
        logger.info("Discovering Sonos speakers...")
        discovered = soco.discover()

        if discovered:
            for speaker in discovered:
                self.speakers[speaker.player_name] = speaker
                logger.info(f"Found speaker: {speaker.player_name}")
        else:
            logger.warning("No Sonos speakers found on the network")

    def list_speakers(self) -> list[str]:
        """Return list of discovered speaker names."""
        return list(self.speakers.keys())

    def get_speaker(self, name: str) -> soco.SoCo | None:
        """Get a speaker by name."""
        return self.speakers.get(name)

    def play_uri(self, speaker_name: str, uri: str) -> bool:
        """Play audio from a URI on the specified speaker."""
        speaker = self.get_speaker(speaker_name)
        if not speaker:
            logger.error(f"Speaker '{speaker_name}' not found")
            return False

        try:
            speaker.play_uri(uri)
            logger.info(f"Playing URI on {speaker_name}: {uri}")
            return True
        except SoCoException as e:
            logger.error(f"Failed to play URI on {speaker_name}: {e}")
            return False

    def play_favorite(self, speaker_name: str, favorite_name: str) -> bool:
        """Play a Sonos favorite on the specified speaker."""
        speaker = self.get_speaker(speaker_name)
        if not speaker:
            logger.error(f"Speaker '{speaker_name}' not found")
            return False

        try:
            favorites = speaker.music_library.get_sonos_favorites()
            for fav in favorites:
                if fav.title == favorite_name:
                    speaker.play_uri(fav.get_uri())
                    logger.info(f"Playing favorite '{favorite_name}' on {speaker_name}")
                    return True

            logger.error(f"Favorite '{favorite_name}' not found")
            return False
        except SoCoException as e:
            logger.error(f"Failed to play favorite on {speaker_name}: {e}")
            return False

    def control_playback(self, speaker_name: str, action: str) -> bool:
        """Control playback (play, pause, stop, next, previous)."""
        speaker = self.get_speaker(speaker_name)
        if not speaker:
            logger.error(f"Speaker '{speaker_name}' not found")
            return False

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
                logger.error(f"Unknown action: {action}")
                return False

            logger.info(f"Executed '{action}' on {speaker_name}")
            return True
        except SoCoException as e:
            logger.error(f"Failed to execute '{action}' on {speaker_name}: {e}")
            return False

    def set_volume(self, speaker_name: str, volume: int) -> bool:
        """Set volume for the specified speaker (0-100)."""
        speaker = self.get_speaker(speaker_name)
        if not speaker:
            logger.error(f"Speaker '{speaker_name}' not found")
            return False

        try:
            speaker.volume = max(0, min(100, volume))
            logger.info(f"Set volume to {volume} on {speaker_name}")
            return True
        except SoCoException as e:
            logger.error(f"Failed to set volume on {speaker_name}: {e}")
            return False

    def get_volume(self, speaker_name: str) -> int | None:
        """Get current volume for the specified speaker."""
        speaker = self.get_speaker(speaker_name)
        if not speaker:
            logger.error(f"Speaker '{speaker_name}' not found")
            return None

        try:
            return speaker.volume
        except SoCoException as e:
            logger.error(f"Failed to get volume from {speaker_name}: {e}")
            return None

    def get_favorites(self) -> list[dict[str, str]]:
        """Get cached list of Sonos favorites."""
        return self._favorites

    def refresh_favorites(self) -> bool:
        """Refresh the favorites list from Sonos system."""
        if not self.speakers:
            logger.error("No speakers available to query favorites")
            return False

        speaker = next(iter(self.speakers.values()))

        try:
            favorites = speaker.music_library.get_sonos_favorites()
            favorites.extend(speaker.music_library.get_favorite_radio_stations())
            self._favorites = []
            for fav in favorites:
                try:
                    fav_data = {
                        "title": fav.title,
                        "uri": fav.get_uri(),
                    }
                    if hasattr(fav, "album_art_uri"):
                        fav_data["album_art"] = fav.album_art_uri
                    self._favorites.append(fav_data)
                except Exception as e:
                    logger.error(f"Error processing favorite '{fav}': {e}")
            logger.info(f"Refreshed {len(self._favorites)} favorites")
            return True
        except SoCoException as e:
            logger.error(f"Failed to retrieve favorites: {e}")
            return False

    def _initialize_group(self, speaker_names: list[str]) -> bool:
        """Initialize group with all speakers on startup."""
        if not speaker_names:
            logger.error("No speakers provided for group")
            return False

        speakers_to_group = []
        for name in speaker_names:
            speaker = self.get_speaker(name)
            if speaker:
                speakers_to_group.append(speaker)
            else:
                logger.error(f"Speaker '{name}' not found")

        if not speakers_to_group:
            logger.error("No valid speakers found for group")
            return False

        try:
            # First speaker becomes the coordinator
            coordinator = speakers_to_group[0]
            self._group_coordinator = coordinator
            self._group_members = {s.player_name for s in speakers_to_group}

            # Remove all speakers from their current groups
            for speaker in speakers_to_group:
                speaker.unjoin()

            # Join all other speakers to the coordinator
            for speaker in speakers_to_group[1:]:
                speaker.join(coordinator)

            logger.info(
                f"Created group with coordinator {coordinator.player_name} "
                f"and {len(speakers_to_group)-1} members"
            )
            return True
        except SoCoException as e:
            logger.error(f"Failed to create group: {e}")
            return False

    def set_group(self, speaker_names: list[str]) -> bool:
        """Update the speaker group by comparing with current members."""
        if not speaker_names:
            logger.error("No speakers provided for group")
            return False

        new_members = set(speaker_names)
        current_members = self._group_members

        # Find speakers to add and remove
        to_add = new_members - current_members
        to_remove = current_members - new_members

        # Add speakers
        for name in to_add:
            if not self._add_speaker_to_group(name):
                logger.error(f"Failed to add speaker {name}")

        # Remove speakers
        for name in to_remove:
            if not self._remove_speaker_from_group(name):
                logger.error(f"Failed to remove speaker {name}")

        return True

    def _add_speaker_to_group(self, speaker_name: str) -> bool:
        """Add a speaker to the existing group."""
        speaker = self.get_speaker(speaker_name)
        if not speaker:
            logger.error(f"Speaker '{speaker_name}' not found")
            return False

        if not self._group_coordinator:
            # No group exists, make this speaker the coordinator
            self._group_coordinator = speaker
            self._group_members = {speaker_name}
            logger.info(f"Created new group with coordinator {speaker_name}")
            return True

        try:
            speaker.join(self._group_coordinator)
            self._group_members.add(speaker_name)
            logger.info(f"Added {speaker_name} to group")
            return True
        except SoCoException as e:
            logger.error(f"Failed to add {speaker_name} to group: {e}")
            return False

    def _remove_speaker_from_group(self, speaker_name: str) -> bool:
        """Remove a speaker from the group."""
        speaker = self.get_speaker(speaker_name)
        if not speaker:
            logger.error(f"Speaker '{speaker_name}' not found")
            return False

        if speaker_name not in self._group_members:
            logger.warning(f"Speaker {speaker_name} is not in the group")
            return True

        try:
            # Check if this is the coordinator
            is_coordinator = (
                self._group_coordinator
                and speaker.player_name == self._group_coordinator.player_name
            )

            if is_coordinator:
                # Coordinator is being removed
                self._group_members.discard(speaker_name)

                if len(self._group_members) == 0:
                    # Last speaker, just unjoin
                    speaker.unjoin()
                    self._group_coordinator = None
                    logger.info(f"Removed last speaker {speaker_name}, group disbanded")
                else:
                    # Promote another speaker to coordinator FIRST to avoid interrupting playback
                    remaining_members = list(self._group_members)
                    new_coordinator_name = remaining_members[0]
                    new_coordinator = self.get_speaker(new_coordinator_name)

                    # Make the new coordinator independent first
                    new_coordinator.unjoin()

                    # Set new coordinator
                    self._group_coordinator = new_coordinator

                    # Join remaining speakers (except new coordinator and old
                    # coordinator) to new coordinator
                    for member_name in remaining_members[1:]:
                        member_speaker = self.get_speaker(member_name)
                        if (
                            member_speaker
                            and member_speaker.player_name != speaker_name
                        ):
                            member_speaker.unjoin()
                            member_speaker.join(new_coordinator)

                    # Now remove old coordinator from group
                    speaker.unjoin()

                    logger.info(
                        f"Removed coordinator {speaker_name}, "
                        f"promoted {new_coordinator_name} to coordinator"
                    )
            else:
                # Regular member, just unjoin
                speaker.unjoin()
                self._group_members.discard(speaker_name)
                logger.info(f"Removed {speaker_name} from group")

            return True
        except SoCoException as e:
            logger.error(f"Failed to remove {speaker_name} from group: {e}")
            return False

    def get_group_coordinator(self) -> soco.SoCo | None:
        """Get the current group coordinator."""
        return self._group_coordinator

    def play_favorite_by_index(self, index: int) -> bool:
        """Play a favorite by its index (1-based) on the group coordinator."""
        if not self._group_coordinator:
            # Auto-initialize group with all speakers if no group exists
            if self.speakers:
                logger.info("No group set, initializing with all speakers")
                if not self.set_group(list(self.speakers.keys())):
                    logger.error("Failed to initialize group")
                    return False
            else:
                logger.error("No speakers available")
                return False

        idx = index - 1
        if idx < 0 or idx >= len(self._favorites):
            logger.error(
                f"Invalid favorite index: {index} (must be 1-{len(self._favorites)})"
            )
            return False

        favorite = self._favorites[idx]
        favorite_title = favorite["title"]

        try:
            all_favorites = list(
                self._group_coordinator.music_library.get_sonos_favorites()
            )
            all_favorites.extend(
                self._group_coordinator.music_library.get_favorite_radio_stations()
            )

            for fav in all_favorites:
                if fav.title == favorite_title:
                    uri = fav.get_uri()
                    metadata = fav.resource_meta_data
                    self._group_coordinator.play_uri(uri, meta=metadata)
                    logger.info(
                        f"Playing favorite #{index} '{favorite_title}' on group"
                    )
                    return True

            logger.error(f"Favorite '{favorite_title}' not found in music library")
            return False
        except SoCoException as e:
            logger.error(f"Failed to play favorite #{index} on group: {e}")
            return False

    def get_now_playing(self) -> dict[str, str] | None:
        """Get currently playing track information from the group coordinator."""
        if not self._group_coordinator:
            return None

        try:
            track_info = self._group_coordinator.get_current_track_info()
            return {
                "title": track_info.get("title", ""),
                "artist": track_info.get("artist", ""),
                "album_art": track_info.get("album_art", ""),
                "uri": track_info.get("uri", ""),
            }
        except SoCoException as e:
            logger.error(f"Failed to get now playing: {e}")
            return None

    def get_group_status(self) -> dict:
        """Get current group status including members and their volumes."""
        status = {
            "members": list(self._group_members),
            "volumes": {},
        }

        for speaker_name in self._group_members:
            volume = self.get_volume(speaker_name)
            if volume is not None:
                status["volumes"][speaker_name] = volume

        return status
