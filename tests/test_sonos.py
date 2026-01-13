"""Test basic Sonos controller functionality."""

from unittest.mock import MagicMock, patch

import pytest

from zoneos.sonos import SonosController


@pytest.fixture
def mock_soco_discover():
    """Mock the soco.discover function."""
    with patch("zoneos.sonos.soco.discover") as mock:
        yield mock


@pytest.fixture
def mock_speaker():
    """Create a mock Sonos speaker."""
    speaker = MagicMock()
    speaker.player_name = "Living Room"
    return speaker


def test_discover_speakers(mock_soco_discover, mock_speaker):
    """Test speaker discovery."""
    mock_soco_discover.return_value = [mock_speaker]

    controller = SonosController()

    assert len(controller.list_speakers()) == 1
    assert "Living Room" in controller.list_speakers()


def test_no_speakers_found(mock_soco_discover):
    """Test when no speakers are found."""
    mock_soco_discover.return_value = None

    controller = SonosController()

    assert len(controller.list_speakers()) == 0


def test_get_speaker(mock_soco_discover, mock_speaker):
    """Test getting a speaker by name."""
    mock_soco_discover.return_value = [mock_speaker]

    controller = SonosController()
    speaker = controller.get_speaker("Living Room")

    assert speaker is not None
    assert speaker.player_name == "Living Room"


def test_play_uri_success(mock_soco_discover, mock_speaker):
    """Test playing a URI successfully."""
    mock_soco_discover.return_value = [mock_speaker]

    controller = SonosController()
    result = controller.play_uri("Living Room", "http://example.com/audio.mp3")

    assert result is True
    mock_speaker.play_uri.assert_called_once_with("http://example.com/audio.mp3")


def test_play_uri_speaker_not_found(mock_soco_discover, mock_speaker):
    """Test playing URI when speaker doesn't exist."""
    mock_soco_discover.return_value = [mock_speaker]

    controller = SonosController()
    result = controller.play_uri("Bedroom", "http://example.com/audio.mp3")

    assert result is False


def test_control_playback(mock_soco_discover, mock_speaker):
    """Test playback control."""
    mock_soco_discover.return_value = [mock_speaker]

    controller = SonosController()

    assert controller.control_playback("Living Room", "play") is True
    mock_speaker.play.assert_called_once()

    assert controller.control_playback("Living Room", "pause") is True
    mock_speaker.pause.assert_called_once()


def test_set_volume(mock_soco_discover, mock_speaker):
    """Test setting volume."""
    mock_soco_discover.return_value = [mock_speaker]

    controller = SonosController()
    result = controller.set_volume("Living Room", 50)

    assert result is True
    assert mock_speaker.volume == 50
