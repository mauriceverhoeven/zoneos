"""Shared test fixtures and configuration."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_soco_discover():
    """Mock the soco.discover function."""
    with patch("zoneos.speakers.soco.discover") as mock:
        yield mock


@pytest.fixture
def mock_speaker():
    """Create a single mock Sonos speaker."""
    speaker = MagicMock()
    speaker.player_name = "Living Room"
    speaker.volume = 50
    speaker.music_library.get_sonos_favorites.return_value = []
    speaker.music_library.get_favorite_radio_stations.return_value = []
    return speaker


@pytest.fixture
def mock_speakers():
    """Create multiple mock Sonos speakers."""
    speakers = []
    for name in ["Living Room", "Bedroom", "Kitchen"]:
        speaker = MagicMock()
        speaker.player_name = name
        speaker.volume = 50
        speaker.music_library.get_sonos_favorites.return_value = []
        speaker.music_library.get_favorite_radio_stations.return_value = []
        speakers.append(speaker)
    return speakers


@pytest.fixture
def mock_favorite():
    """Create a mock Sonos favorite."""
    fav = MagicMock()
    fav.title = "Test Favorite"
    fav.get_uri.return_value = "x-rincon-cpcontainer:1004206c..."
    fav.album_art_uri = "http://example.com/art.jpg"
    fav.resource_meta_data = "<DIDL-Lite>...</DIDL-Lite>"
    return fav


@pytest.fixture
def controller_with_speakers(mock_soco_discover, mock_speakers):
    """Create a controller with pre-configured speakers."""
    mock_soco_discover.return_value = mock_speakers
    from zoneos.controller import SonosController

    return SonosController()


@pytest.fixture
def flask_app():
    """Create a Flask test app."""
    from zoneos.api import create_app

    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(flask_app):
    """Create a Flask test client."""
    return flask_app.test_client()
