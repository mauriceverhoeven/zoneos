"""Advanced tests for SonosController functionality."""

from soco.exceptions import SoCoException

from zoneos.controller import SonosController


def test_play_favorite_success(mock_soco_discover, mock_speaker, mock_favorite):
    """Test playing a favorite successfully."""
    mock_speaker.music_library.get_sonos_favorites.return_value = [mock_favorite]
    mock_soco_discover.return_value = [mock_speaker]

    controller = SonosController()
    result = controller.play_favorite("Living Room", "Test Favorite")

    assert result is True
    mock_speaker.play_uri.assert_called_once()


def test_play_favorite_not_found(mock_soco_discover, mock_speaker):
    """Test playing a favorite that doesn't exist."""
    mock_speaker.music_library.get_sonos_favorites.return_value = []
    mock_soco_discover.return_value = [mock_speaker]

    controller = SonosController()
    result = controller.play_favorite("Living Room", "Nonexistent")

    assert result is False


def test_play_favorite_exception(mock_soco_discover, mock_speaker):
    """Test playing favorite with SoCo exception."""
    mock_speaker.music_library.get_sonos_favorites.side_effect = SoCoException("Error")
    mock_soco_discover.return_value = [mock_speaker]

    controller = SonosController()
    result = controller.play_favorite("Living Room", "Test")

    assert result is False


def test_control_playback_all_actions(mock_soco_discover, mock_speaker):
    """Test all playback control actions."""
    mock_soco_discover.return_value = [mock_speaker]
    controller = SonosController()

    assert controller.control_playback("Living Room", "play") is True
    mock_speaker.play.assert_called_once()

    assert controller.control_playback("Living Room", "pause") is True
    mock_speaker.pause.assert_called_once()

    assert controller.control_playback("Living Room", "stop") is True
    mock_speaker.stop.assert_called_once()

    assert controller.control_playback("Living Room", "next") is True
    mock_speaker.next.assert_called_once()

    assert controller.control_playback("Living Room", "previous") is True
    mock_speaker.previous.assert_called_once()


def test_control_playback_invalid_action(mock_soco_discover, mock_speaker):
    """Test control playback with invalid action."""
    mock_soco_discover.return_value = [mock_speaker]
    controller = SonosController()

    result = controller.control_playback("Living Room", "invalid_action")
    assert result is False


def test_control_playback_exception(mock_soco_discover, mock_speaker):
    """Test control playback with SoCo exception."""
    mock_speaker.play.side_effect = SoCoException("Error")
    mock_soco_discover.return_value = [mock_speaker]

    controller = SonosController()
    result = controller.control_playback("Living Room", "play")

    assert result is False


def test_set_volume_boundary_values(mock_soco_discover, mock_speaker):
    """Test setting volume with boundary values and rounding to modulo 5."""
    mock_soco_discover.return_value = [mock_speaker]
    controller = SonosController()

    # Test minimum
    controller.set_volume("Living Room", 0)
    assert mock_speaker.volume == 0

    # Test maximum
    controller.set_volume("Living Room", 100)
    assert mock_speaker.volume == 100

    # Test clamping above max (rounds to 150 -> 150, clamps to 100)
    controller.set_volume("Living Room", 150)
    assert mock_speaker.volume == 100

    # Test clamping below min (rounds to -10 -> -10, clamps to 0)
    controller.set_volume("Living Room", -10)
    assert mock_speaker.volume == 0

    # Test rounding to nearest 5
    controller.set_volume("Living Room", 23)  # Should round to 25
    assert mock_speaker.volume == 25

    controller.set_volume("Living Room", 22)  # Should round to 20
    assert mock_speaker.volume == 20

    controller.set_volume("Living Room", 27)  # Should round to 25
    assert mock_speaker.volume == 25

    controller.set_volume("Living Room", 28)  # Should round to 30
    assert mock_speaker.volume == 30


def test_get_volume_exception(mock_soco_discover, mock_speaker):
    """Test getting volume with SoCo exception."""
    type(mock_speaker).volume = property(
        lambda self: (_ for _ in ()).throw(SoCoException("Error"))
    )
    mock_soco_discover.return_value = [mock_speaker]

    controller = SonosController()
    result = controller.get_volume("Living Room")

    assert result is None


def test_refresh_favorites_success(mock_soco_discover, mock_speaker, mock_favorite):
    """Test refreshing favorites successfully."""
    mock_speaker.music_library.get_sonos_favorites.return_value = [mock_favorite]
    mock_speaker.music_library.get_favorite_radio_stations.return_value = []
    mock_soco_discover.return_value = [mock_speaker]

    controller = SonosController()
    result = controller.refresh_favorites()

    assert result is True
    favorites = controller.get_favorites()
    assert len(favorites) == 1
    assert favorites[0]["title"] == "Test Favorite"


def test_refresh_favorites_no_speakers(mock_soco_discover):
    """Test refreshing favorites with no speakers available."""
    mock_soco_discover.return_value = None
    controller = SonosController()

    result = controller.refresh_favorites()
    assert result is False


def test_refresh_favorites_exception(mock_soco_discover, mock_speaker):
    """Test refreshing favorites with SoCo exception."""
    mock_speaker.music_library.get_sonos_favorites.side_effect = SoCoException("Error")
    mock_soco_discover.return_value = [mock_speaker]

    controller = SonosController()
    result = controller.refresh_favorites()

    assert result is False


def test_group_operations(mock_soco_discover, mock_speakers):
    """Test group creation and management."""
    mock_soco_discover.return_value = mock_speakers

    controller = SonosController()

    # Initial group should have all speakers
    coordinator = controller.get_group_coordinator()
    assert coordinator is not None

    # Test setting a new group
    result = controller.set_group(["Living Room", "Bedroom"])
    assert result is True


def test_add_speaker_to_group(mock_soco_discover, mock_speakers):
    """Test adding a speaker to existing group."""
    mock_soco_discover.return_value = mock_speakers[
        :2
    ]  # Only first 2 speakers initially
    controller = SonosController()

    # Add a new speaker to group
    result = controller._add_speaker_to_group("Bedroom")
    assert result is True


def test_add_speaker_to_empty_group(mock_soco_discover, mock_speaker):
    """Test adding first speaker creates coordinator."""
    mock_soco_discover.return_value = [mock_speaker]
    controller = SonosController()

    # Clear group
    controller._group_coordinator = None
    controller._group_members = set()

    result = controller._add_speaker_to_group("Living Room")
    assert result is True
    assert controller.get_group_coordinator() is not None


def test_remove_speaker_from_group(mock_soco_discover, mock_speakers):
    """Test removing a speaker from group."""
    mock_soco_discover.return_value = mock_speakers
    controller = SonosController()

    result = controller._remove_speaker_from_group("Kitchen")
    assert result is True


def test_remove_coordinator_from_group(mock_soco_discover, mock_speakers):
    """Test removing coordinator promotes new coordinator."""
    mock_soco_discover.return_value = mock_speakers
    controller = SonosController()

    coordinator_name = controller.get_group_coordinator().player_name

    result = controller._remove_speaker_from_group(coordinator_name)
    assert result is True

    # New coordinator should be set
    new_coordinator = controller.get_group_coordinator()
    assert new_coordinator is not None
    assert new_coordinator.player_name != coordinator_name


def test_remove_last_speaker(mock_soco_discover, mock_speaker):
    """Test removing the last speaker from group."""
    mock_soco_discover.return_value = [mock_speaker]
    controller = SonosController()

    result = controller._remove_speaker_from_group("Living Room")
    assert result is True
    assert controller.get_group_coordinator() is None


def test_play_favorite_by_index_success(
    mock_soco_discover, mock_speaker, mock_favorite
):
    """Test playing favorite by index (0-based)."""
    mock_speaker.music_library.get_sonos_favorites.return_value = [mock_favorite]
    mock_speaker.music_library.get_favorite_radio_stations.return_value = []
    mock_soco_discover.return_value = [mock_speaker]

    controller = SonosController()
    result = controller.play_favorite_by_index(0)

    assert result is True
    mock_speaker.play_uri.assert_called()


def test_play_favorite_by_index_invalid(mock_soco_discover, mock_speaker):
    """Test playing favorite with invalid index."""
    mock_speaker.music_library.get_sonos_favorites.return_value = []
    mock_speaker.music_library.get_favorite_radio_stations.return_value = []
    mock_soco_discover.return_value = [mock_speaker]

    controller = SonosController()

    # Test index out of bounds (no favorites available)
    result = controller.play_favorite_by_index(0)
    assert result is False

    # Test negative index
    result = controller.play_favorite_by_index(-1)
    assert result is False


def test_play_favorite_by_index_no_coordinator(
    mock_soco_discover, mock_speaker, mock_favorite
):
    """Test playing favorite without coordinator auto-initializes group."""
    mock_speaker.music_library.get_sonos_favorites.return_value = [mock_favorite]
    mock_speaker.music_library.get_favorite_radio_stations.return_value = []
    mock_soco_discover.return_value = [mock_speaker]

    controller = SonosController()

    # Verify group coordinator was initialized
    assert controller.get_group_coordinator() is not None


def test_get_now_playing_success(mock_soco_discover, mock_speaker):
    """Test getting now playing information."""
    mock_speaker.get_current_track_info.return_value = {
        "title": "Test Song",
        "artist": "Test Artist",
        "album_art": "http://example.com/art.jpg",
        "uri": "x-rincon-cpcontainer:1",
    }
    mock_soco_discover.return_value = [mock_speaker]

    controller = SonosController()
    info = controller.get_now_playing()

    assert info is not None
    assert info["title"] == "Test Song"
    assert info["artist"] == "Test Artist"


def test_get_now_playing_no_coordinator(mock_soco_discover, mock_speaker):
    """Test getting now playing without coordinator."""
    mock_soco_discover.return_value = [mock_speaker]
    controller = SonosController()

    # Clear the coordinator properly
    controller.groups._coordinator = None

    info = controller.get_now_playing()
    assert info is None


def test_get_now_playing_exception(mock_soco_discover, mock_speaker):
    """Test getting now playing with SoCo exception."""
    mock_speaker.get_current_track_info.side_effect = SoCoException("Error")
    mock_soco_discover.return_value = [mock_speaker]

    controller = SonosController()
    info = controller.get_now_playing()

    assert info is None


def test_get_group_status(mock_soco_discover, mock_speakers):
    """Test getting group status."""
    mock_soco_discover.return_value = mock_speakers

    controller = SonosController()
    status = controller.get_group_status()

    assert "members" in status
    assert "volumes" in status
    assert len(status["members"]) == 3


def test_initialize_preserves_playing_group(mock_soco_discover, mock_speakers):
    """Test that initialize preserves existing group when content is playing."""
    from unittest.mock import MagicMock

    # Set up speakers with one playing
    mock_soco_discover.return_value = mock_speakers
    playing_speaker = mock_speakers[0]

    # Mock transport info to indicate playing state
    playing_speaker.get_current_transport_info.return_value = {
        "current_transport_state": "PLAYING"
    }

    # Mock group structure
    mock_group = MagicMock()
    mock_group.coordinator = playing_speaker
    mock_group.members = mock_speakers[:2]  # Only first 2 speakers in group
    playing_speaker.group = mock_group

    controller = SonosController()

    # Verify existing group was preserved
    assert controller.get_group_coordinator() == playing_speaker
    assert len(controller.groups.get_members()) == 2

    # Verify unjoin was NOT called (group preserved)
    playing_speaker.unjoin.assert_not_called()
    mock_speakers[1].unjoin.assert_not_called()


def test_initialize_creates_group_when_not_playing(mock_soco_discover, mock_speakers):
    """Test that initialize creates new group when no content is playing."""
    mock_soco_discover.return_value = mock_speakers

    # Mock transport info to indicate stopped state
    for speaker in mock_speakers:
        speaker.get_current_transport_info.return_value = {
            "current_transport_state": "STOPPED"
        }

    controller = SonosController()

    # Verify new group was created with all speakers
    assert controller.get_group_coordinator() is not None
    assert len(controller.groups.get_members()) == 3

    # Verify unjoin was called to reset groups
    for speaker in mock_speakers:
        speaker.unjoin.assert_called()


def test_play_next_favorite_success(mock_soco_discover, mock_speaker):
    """Test playing next favorite advances through the list."""
    from unittest.mock import MagicMock

    # Create multiple favorites
    fav1 = MagicMock()
    fav1.title = "Favorite 1"
    fav1.get_uri.return_value = "uri1"
    fav1.resource_meta_data = "<DIDL-Lite>1</DIDL-Lite>"

    fav2 = MagicMock()
    fav2.title = "Favorite 2"
    fav2.get_uri.return_value = "uri2"
    fav2.resource_meta_data = "<DIDL-Lite>2</DIDL-Lite>"

    fav3 = MagicMock()
    fav3.title = "Favorite 3"
    fav3.get_uri.return_value = "uri3"
    fav3.resource_meta_data = "<DIDL-Lite>3</DIDL-Lite>"

    mock_speaker.music_library.get_sonos_favorites.return_value = [fav1, fav2, fav3]
    mock_speaker.music_library.get_favorite_radio_stations.return_value = []
    mock_soco_discover.return_value = [mock_speaker]

    controller = SonosController()

    # First call: starts at index 0, calculates next as (0+1)%3=1, plays favorite at index 1, sets index to 1
    result = controller.play_next_favorite()
    assert result is True
    assert (
        controller.current_favorite_index == 1
    )  # Played favorite at index 1 (second favorite)

    # Second call: at index 1, calculates next as (1+1)%3=2, plays favorite at index 2, sets index to 2
    result = controller.play_next_favorite()
    assert result is True
    assert (
        controller.current_favorite_index == 2
    )  # Played favorite at index 2 (third favorite)

    # Third call: at index 2, calculates next as (2+1)%3=0, plays favorite at index 0, sets index to 0
    result = controller.play_next_favorite()
    assert result is True
    assert controller.current_favorite_index == 0  # Rolled over to first favorite


def test_play_next_favorite_rollover(mock_soco_discover, mock_speaker):
    """Test that play_next_favorite rolls over to the beginning."""
    from unittest.mock import MagicMock

    fav1 = MagicMock()
    fav1.title = "Favorite 1"
    fav1.get_uri.return_value = "uri1"
    fav1.resource_meta_data = "<DIDL-Lite>1</DIDL-Lite>"

    fav2 = MagicMock()
    fav2.title = "Favorite 2"
    fav2.get_uri.return_value = "uri2"
    fav2.resource_meta_data = "<DIDL-Lite>2</DIDL-Lite>"

    mock_speaker.music_library.get_sonos_favorites.return_value = [fav1, fav2]
    mock_speaker.music_library.get_favorite_radio_stations.return_value = []
    mock_soco_discover.return_value = [mock_speaker]

    controller = SonosController()

    # Play through the list
    controller.play_next_favorite()  # index 0 -> plays index 1, sets to 1
    controller.play_next_favorite()  # index 1 -> plays index 0 (rollover), sets to 0

    # Verify we rolled over to index 0
    assert controller.current_favorite_index == 0


def test_play_next_favorite_no_favorites(mock_soco_discover, mock_speaker):
    """Test play_next_favorite when no favorites available."""
    mock_speaker.music_library.get_sonos_favorites.return_value = []
    mock_speaker.music_library.get_favorite_radio_stations.return_value = []
    mock_soco_discover.return_value = [mock_speaker]

    controller = SonosController()

    result = controller.play_next_favorite()
    assert result is False
