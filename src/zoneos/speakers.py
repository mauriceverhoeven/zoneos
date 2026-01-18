"""Speaker discovery and management."""

import logging

import soco

from zoneos.exceptions import NoSpeakersAvailableError, SpeakerNotFoundError

logger = logging.getLogger(__name__)


class SpeakerManager:
    """Manages Sonos speaker discovery and basic operations."""

    def __init__(self):
        """Initialize speaker manager and discover speakers."""
        self.speakers: dict[str, soco.SoCo] = {}
        self._discover_speakers()

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

    def get_speaker(self, name: str) -> soco.SoCo:
        """Get a speaker by name.

        Args:
            name: Speaker name

        Returns:
            SoCo speaker instance

        Raises:
            SpeakerNotFoundError: If speaker not found
        """
        speaker = self.speakers.get(name)
        if not speaker:
            raise SpeakerNotFoundError(f"Speaker '{name}' not found")
        return speaker

    def get_any_speaker(self) -> soco.SoCo:
        """Get any available speaker.

        Returns:
            First available speaker

        Raises:
            NoSpeakersAvailableError: If no speakers available
        """
        if not self.speakers:
            raise NoSpeakersAvailableError("No speakers available")
        return next(iter(self.speakers.values()))

    def set_volume(self, speaker_name: str, volume: int) -> None:
        """Set volume for the specified speaker (0-100).
        
        Volume is automatically rounded to the nearest multiple of 5.

        Args:
            speaker_name: Name of the speaker
            volume: Volume level (0-100)

        Raises:
            SpeakerNotFoundError: If speaker not found
            SoCoException: If volume setting fails
        """
        speaker = self.get_speaker(speaker_name)
        # Round to nearest multiple of 5
        rounded_volume = round(volume / 5) * 5
        # Clamp to 0-100 range
        clamped_volume = max(0, min(100, rounded_volume))
        speaker.volume = clamped_volume
        logger.info(f"Set volume to {clamped_volume} on {speaker_name}")

    def get_volume(self, speaker_name: str) -> int:
        """Get current volume for the specified speaker.

        Args:
            speaker_name: Name of the speaker

        Returns:
            Current volume level

        Raises:
            SpeakerNotFoundError: If speaker not found
            SoCoException: If volume retrieval fails
        """
        speaker = self.get_speaker(speaker_name)
        return speaker.volume
