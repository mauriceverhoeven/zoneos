"""Test Flask API endpoints."""

import json
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_controller():
    """Mock the sonos_controller instance."""
    controller = MagicMock()
    controller.list_speakers.return_value = ["Living Room", "Bedroom"]
    controller.get_volume.return_value = 50
    controller.get_favorites.return_value = [
        {"title": "Radio 1", "uri": "x-rincon-cpcontainer:1"},
        {"title": "Playlist", "uri": "x-rincon-cpcontainer:2"},
    ]
    controller.get_group_status.return_value = {
        "members": ["Living Room", "Bedroom"],
        "volumes": {"Living Room": 50, "Bedroom": 45},
    }
    controller.get_now_playing.return_value = {
        "title": "Test Song",
        "artist": "Test Artist",
        "album_art": "http://example.com/art.jpg",
        "uri": "x-rincon-cpcontainer:1",
    }
    return controller


@pytest.fixture
def client_with_controller(flask_app, mock_controller):
    """Create a Flask test client with mocked controller."""
    import zoneos.api

    zoneos.api.sonos_controller = mock_controller
    return flask_app.test_client()


def test_index_route(client):
    """Test the root route serves HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"html" in response.data or b"DOCTYPE" in response.data


def test_list_speakers(client_with_controller, mock_controller):
    """Test GET /api/speakers endpoint."""
    response = client_with_controller.get("/api/speakers")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert "speakers" in data
    assert data["speakers"] == ["Living Room", "Bedroom"]


def test_list_speakers_no_controller(client):
    """Test GET /api/speakers with no controller initialized."""
    import zoneos.api

    zoneos.api.sonos_controller = None
    response = client.get("/api/speakers")
    assert response.status_code == 503


def test_get_speaker_volume(client_with_controller, mock_controller):
    """Test GET /api/speaker/volume/<speaker_name> endpoint."""
    response = client_with_controller.get("/api/speaker/volume/Living Room")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["speaker"] == "Living Room"
    assert data["volume"] == 50


def test_get_speaker_volume_failure(client_with_controller, mock_controller):
    """Test GET /api/speaker/volume when speaker not found."""
    mock_controller.get_volume.return_value = None
    response = client_with_controller.get("/api/speaker/volume/Unknown")
    assert response.status_code == 400


def test_play_favorite_success(client_with_controller, mock_controller):
    """Test POST /api/play-favorite endpoint."""
    mock_controller.play_favorite.return_value = True

    response = client_with_controller.post(
        "/api/play-favorite",
        data=json.dumps({"speaker": "Living Room", "favorite": "Radio 1"}),
        content_type="application/json",
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "ok"
    mock_controller.play_favorite.assert_called_once_with("Living Room", "Radio 1")


def test_play_favorite_missing_fields(client_with_controller):
    """Test POST /api/play-favorite with missing fields."""
    response = client_with_controller.post(
        "/api/play-favorite",
        data=json.dumps({"speaker": "Living Room"}),
        content_type="application/json",
    )
    assert response.status_code == 400


def test_play_favorite_failure(client_with_controller, mock_controller):
    """Test POST /api/play-favorite when playback fails."""
    mock_controller.play_favorite.return_value = False

    response = client_with_controller.post(
        "/api/play-favorite",
        data=json.dumps({"speaker": "Living Room", "favorite": "Unknown"}),
        content_type="application/json",
    )
    assert response.status_code == 400


def test_control_playback_success(client_with_controller, mock_controller):
    """Test POST /api/control endpoint."""
    mock_controller.control_playback.return_value = True

    for action in ["play", "pause", "stop", "next", "previous"]:
        response = client_with_controller.post(
            "/api/control",
            data=json.dumps({"speaker": "Living Room", "action": action}),
            content_type="application/json",
        )
        assert response.status_code == 200


def test_control_playback_invalid_action(client_with_controller):
    """Test POST /api/control with invalid action."""
    response = client_with_controller.post(
        "/api/control",
        data=json.dumps({"speaker": "Living Room", "action": "invalid"}),
        content_type="application/json",
    )
    assert response.status_code == 400


def test_set_volume_success(client_with_controller, mock_controller):
    """Test POST /api/volume endpoint."""
    mock_controller.set_volume.return_value = True

    response = client_with_controller.post(
        "/api/volume",
        data=json.dumps({"speaker": "Living Room", "volume": 75}),
        content_type="application/json",
    )

    assert response.status_code == 200
    # Volume is rounded to nearest 5, so 75 stays 75
    mock_controller.set_volume.assert_called_once_with("Living Room", 75)


def test_set_volume_invalid_range(client_with_controller):
    """Test POST /api/volume with invalid volume range."""
    response = client_with_controller.post(
        "/api/volume",
        data=json.dumps({"speaker": "Living Room", "volume": 150}),
        content_type="application/json",
    )
    assert response.status_code == 400

    response = client_with_controller.post(
        "/api/volume",
        data=json.dumps({"speaker": "Living Room", "volume": -10}),
        content_type="application/json",
    )
    assert response.status_code == 400


def test_set_volume_non_integer(client_with_controller):
    """Test POST /api/volume with non-integer volume."""
    response = client_with_controller.post(
        "/api/volume",
        data=json.dumps({"speaker": "Living Room", "volume": "fifty"}),
        content_type="application/json",
    )
    assert response.status_code == 400


def test_play_uri_success(client_with_controller, mock_controller):
    """Test POST /api/play-uri endpoint."""
    mock_controller.play_uri.return_value = True

    response = client_with_controller.post(
        "/api/play-uri",
        data=json.dumps(
            {"speaker": "Living Room", "uri": "http://example.com/audio.mp3"}
        ),
        content_type="application/json",
    )

    assert response.status_code == 200
    mock_controller.play_uri.assert_called_once_with(
        "Living Room", "http://example.com/audio.mp3"
    )


def test_list_favorites(client_with_controller, mock_controller):
    """Test GET /api/favorites endpoint."""
    response = client_with_controller.get("/api/favorites")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert "favorites" in data
    assert len(data["favorites"]) == 2


def test_refresh_favorites_success(client_with_controller, mock_controller):
    """Test POST /api/favorites/refresh endpoint."""
    mock_controller.refresh_favorites.return_value = True

    response = client_with_controller.post("/api/favorites/refresh")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["status"] == "ok"


def test_set_group_success(client_with_controller, mock_controller):
    """Test POST /api/group endpoint."""
    mock_controller.set_group.return_value = True

    response = client_with_controller.post(
        "/api/group",
        data=json.dumps({"speakers": ["Living Room", "Bedroom"]}),
        content_type="application/json",
    )

    assert response.status_code == 200
    mock_controller.set_group.assert_called_once_with(["Living Room", "Bedroom"])


def test_set_group_empty_list(client_with_controller):
    """Test POST /api/group with empty speaker list."""
    response = client_with_controller.post(
        "/api/group", data=json.dumps({"speakers": []}), content_type="application/json"
    )
    assert response.status_code == 400


def test_play_favorite_by_index_success(client_with_controller, mock_controller):
    """Test POST /api/play-favorite-index endpoint."""
    mock_controller.play_favorite_by_index.return_value = True

    response = client_with_controller.post(
        "/api/play-favorite-index",
        data=json.dumps({"index": 0}),
        content_type="application/json",
    )

    assert response.status_code == 200
    mock_controller.play_favorite_by_index.assert_called_once_with(0)


def test_play_favorite_by_index_invalid(client_with_controller):
    """Test POST /api/play-favorite-index with invalid index."""
    response = client_with_controller.post(
        "/api/play-favorite-index",
        data=json.dumps({"index": -1}),
        content_type="application/json",
    )
    assert response.status_code == 400


def test_get_now_playing(client_with_controller, mock_controller):
    """Test GET /api/now-playing endpoint."""
    response = client_with_controller.get("/api/now-playing")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["title"] == "Test Song"
    assert data["artist"] == "Test Artist"


def test_get_now_playing_no_data(client_with_controller, mock_controller):
    """Test GET /api/now-playing when no track is playing."""
    mock_controller.get_now_playing.return_value = None

    response = client_with_controller.get("/api/now-playing")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["title"] == ""


def test_get_group_status(client_with_controller, mock_controller):
    """Test GET /api/group-status endpoint."""
    response = client_with_controller.get("/api/group-status")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert "members" in data
    assert "volumes" in data
    assert len(data["members"]) == 2


def test_play_next_favorite_success(client_with_controller, mock_controller):
    """Test GET /api/next endpoint."""
    mock_controller.play_next_favorite.return_value = True

    response = client_with_controller.get("/api/next")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["status"] == "ok"
    mock_controller.play_next_favorite.assert_called_once()


def test_play_next_favorite_failure(client_with_controller, mock_controller):
    """Test GET /api/next when no favorites available."""
    mock_controller.play_next_favorite.return_value = False

    response = client_with_controller.get("/api/next")
    assert response.status_code == 400
