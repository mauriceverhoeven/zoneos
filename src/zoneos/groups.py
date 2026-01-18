"""Group management for Sonos speakers."""

import logging

import soco
from soco.exceptions import SoCoException

from zoneos.exceptions import GroupOperationError, SpeakerNotFoundError

logger = logging.getLogger(__name__)


class GroupManager:
    """Manages Sonos speaker groups."""

    def __init__(self):
        """Initialize group manager."""
        self._coordinator: soco.SoCo | None = None
        self._members: set[str] = set()

    def initialize(self, speakers: dict[str, soco.SoCo]) -> None:
        """Initialize group with all available speakers.

        If content is already playing, preserves the existing group structure
        instead of forcefully creating a new one.

        Args:
            speakers: Dictionary of speaker name to SoCo instance

        Raises:
            GroupOperationError: If group initialization fails
        """
        if not speakers:
            logger.warning("No speakers available for group initialization")
            return

        speaker_list = list(speakers.values())

        # Check if any speaker is currently playing
        playing_speaker = None
        for speaker in speaker_list:
            try:
                transport_info = speaker.get_current_transport_info()
                if transport_info and transport_info.get("current_transport_state") in [
                    "PLAYING",
                    "PAUSED_PLAYBACK",
                ]:
                    playing_speaker = speaker
                    logger.info(
                        f"Detected {speaker.player_name} is already playing/paused"
                    )
                    break
            except SoCoException:
                continue

        # If content is playing, use existing group structure
        if playing_speaker:
            try:
                # Get the coordinator of the playing speaker's group
                coordinator = playing_speaker.group.coordinator
                group_members = {m.player_name for m in playing_speaker.group.members}

                self._coordinator = coordinator
                self._members = group_members

                logger.info(
                    f"Preserved existing group with coordinator {coordinator.player_name} "
                    f"and {len(group_members)} members (content is playing)"
                )
                return
            except (SoCoException, AttributeError) as e:
                logger.warning(f"Failed to read existing group structure: {e}")
                # Fall through to create new group

        # No content playing, create new group from all speakers
        try:
            # First speaker becomes the coordinator
            self._coordinator = speaker_list[0]
            self._members = {s.player_name for s in speaker_list}

            # Remove all speakers from their current groups
            for speaker in speaker_list:
                speaker.unjoin()

            # Join all other speakers to the coordinator
            for speaker in speaker_list[1:]:
                speaker.join(self._coordinator)

            logger.info(
                f"Initialized group with coordinator {self._coordinator.player_name} "
                f"and {len(speaker_list)-1} members"
            )
        except SoCoException as e:
            raise GroupOperationError(f"Failed to initialize group: {e}")

    def set_members(
        self, speakers: dict[str, soco.SoCo], member_names: list[str]
    ) -> None:
        """Update the speaker group by comparing with current members.

        Args:
            speakers: Dictionary of all available speakers
            member_names: List of speaker names to be in group

        Raises:
            GroupOperationError: If group update fails
        """
        if not member_names:
            raise GroupOperationError("No speakers provided for group")

        new_members = set(member_names)
        current_members = self._members

        # Find speakers to add and remove
        to_add = new_members - current_members
        to_remove = current_members - new_members

        # Add speakers
        for name in to_add:
            self._add_speaker(speakers, name)

        # Remove speakers
        for name in to_remove:
            self._remove_speaker(speakers, name)

    def _add_speaker(self, speakers: dict[str, soco.SoCo], speaker_name: str) -> None:
        """Add a speaker to the existing group.

        Args:
            speakers: Dictionary of all available speakers
            speaker_name: Name of speaker to add

        Raises:
            SpeakerNotFoundError: If speaker not found
            GroupOperationError: If add operation fails
        """
        speaker = speakers.get(speaker_name)
        if not speaker:
            raise SpeakerNotFoundError(f"Speaker '{speaker_name}' not found")

        if not self._coordinator:
            # No group exists, make this speaker the coordinator
            self._coordinator = speaker
            self._members = {speaker_name}
            logger.info(f"Created new group with coordinator {speaker_name}")
            return

        try:
            speaker.join(self._coordinator)
            self._members.add(speaker_name)
            logger.info(f"Added {speaker_name} to group")
        except SoCoException as e:
            raise GroupOperationError(f"Failed to add {speaker_name} to group: {e}")

    def _remove_speaker(
        self, speakers: dict[str, soco.SoCo], speaker_name: str
    ) -> None:
        """Remove a speaker from the group.

        Args:
            speakers: Dictionary of all available speakers
            speaker_name: Name of speaker to remove

        Raises:
            SpeakerNotFoundError: If speaker not found
            GroupOperationError: If remove operation fails
        """
        speaker = speakers.get(speaker_name)
        if not speaker:
            raise SpeakerNotFoundError(f"Speaker '{speaker_name}' not found")

        if speaker_name not in self._members:
            logger.warning(f"Speaker {speaker_name} is not in the group")
            return

        try:
            is_coordinator = (
                self._coordinator
                and speaker.player_name == self._coordinator.player_name
            )

            if is_coordinator:
                self._remove_coordinator(speakers, speaker, speaker_name)
            else:
                speaker.unjoin()
                self._members.discard(speaker_name)
                logger.info(f"Removed {speaker_name} from group")
        except SoCoException as e:
            raise GroupOperationError(
                f"Failed to remove {speaker_name} from group: {e}"
            )

    def _remove_coordinator(
        self, speakers: dict[str, soco.SoCo], speaker: soco.SoCo, speaker_name: str
    ) -> None:
        """Remove coordinator and promote new one if needed."""
        self._members.discard(speaker_name)

        if len(self._members) == 0:
            # Last speaker, just unjoin
            speaker.unjoin()
            self._coordinator = None
            logger.info(f"Removed last speaker {speaker_name}, group disbanded")
        else:
            # Promote another speaker to coordinator
            remaining_members = list(self._members)
            new_coordinator_name = remaining_members[0]
            new_coordinator = speakers.get(new_coordinator_name)

            if not new_coordinator:
                raise GroupOperationError(
                    f"New coordinator '{new_coordinator_name}' not found"
                )

            # Make the new coordinator independent
            new_coordinator.unjoin()
            self._coordinator = new_coordinator

            # Rejoin remaining speakers
            for member_name in remaining_members[1:]:
                member_speaker = speakers.get(member_name)
                if member_speaker and member_speaker.player_name != speaker_name:
                    member_speaker.unjoin()
                    member_speaker.join(new_coordinator)

            # Remove old coordinator
            speaker.unjoin()

            logger.info(
                f"Removed coordinator {speaker_name}, "
                f"promoted {new_coordinator_name} to coordinator"
            )

    def get_coordinator(self) -> soco.SoCo | None:
        """Get the current group coordinator.

        Returns:
            Group coordinator or None if no group
        """
        return self._coordinator

    def get_members(self) -> set[str]:
        """Get set of group member names.

        Returns:
            Set of speaker names in group
        """
        return self._members.copy()
