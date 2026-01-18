# ZoneOS - AI Coding Agent Instructions

## Project Overview

ZoneOS is a Python-based bridge that connects Sonos speakers with iPhone automations and NFC stickers. It provides a REST API and lightweight web interface for controlling Sonos speakers, enabling physical NFC tags to trigger specific audio actions.

## Architecture

### Core Components

**Modular Design (Refactored)**:

- **SpeakerManager** (`src/zoneos/speakers.py`): Handles speaker discovery and basic operations
- **FavoritesManager** (`src/zoneos/favorites.py`): Manages favorites and radio stations
- **GroupManager** (`src/zoneos/groups.py`): Coordinates multi-room audio groups
- **PlaybackController** (`src/zoneos/playback.py`): Controls playback operations
- **SonosController** (`src/zoneos/controller.py`): Main facade coordinating all managers
- **Flask Server** (`src/zoneos/api.py`): REST API with endpoints for speaker control
- **Config** (`src/zoneos/config.py`): Centralized configuration from environment variables
- **Exceptions** (`src/zoneos/exceptions.py`): Custom exception hierarchy
- **Web Frontend** (`static/index.html`): Single-page interface for testing

**Legacy Module**:

- **sonos.py**: Original monolithic controller (deprecated, kept for backward compatibility)

### Data Flow

1. NFC tag scanned → iPhone Shortcuts app → HTTP request to ZoneOS API
2. API validates request → SonosController delegates to appropriate manager → Manager executes action → Sonos speaker responds
3. Web interface provides manual control and system testing

### Key Design Decisions

- **Modular architecture**: Each component has a single responsibility
- **Custom exceptions**: Clear error propagation with specific exception types
- **Configuration management**: Environment-based config for deployment flexibility
- **Manager pattern**: SonosController acts as a facade, delegating to specialized managers
- **Stateless API**: Each request is independent; no session management required
- **Discovery on init**: Speakers discovered once at startup; restart server if network topology changes

## Development Workflow

### Initial Setup

```bash
# Clone and navigate
git clone https://github.com/mauriceverhoeven/zoneos.git
cd zoneos

# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and run
uv sync
uv run python -m zoneos
```

### Running the Server

```bash
# Run the server
uv run python -m zoneos

# Server runs on http://0.0.0.0:8000
# Access at http://localhost:8000 or http://<your-ip>:8000
```

### Testing

```bash
# Run tests with pytest
uv run pytest

# Run with coverage
uv run pytest --cov=zoneos --cov-report=html
```

### iPhone Automation Integration

Use iOS Shortcuts to make HTTP requests to ZoneOS endpoints:

- Play favorite: `POST http://your-ip:8000/api/play-favorite`
- Control playback: `POST http://your-ip:8000/api/control`
- Set volume: `POST http://your-ip:8000/api/volume`

NFC tags trigger shortcuts that call these endpoints with speaker and action parameters.

## Coding Conventions

### Python Style

- Use **ruff** for linting (configured in pyproject.toml)
- Python 3.11+ required for modern type hints (`dict[str, SoCo]` instead of `Dict[str, SoCo]`)
- Line length: 100 characters
- Use dataclasses for configuration objects
- Prefer explicit exceptions over returning `None` for errors in new code

### Error Handling Pattern

**New pattern (with custom exceptions)**:

```python
from zoneos.exceptions import SpeakerNotFoundError

try:
    speaker = speaker_manager.get_speaker(name)
    speaker.play()
except SpeakerNotFoundError as e:
    logger.error(f"Speaker error: {e}")
    raise
except SoCoException as e:
    logger.error(f"SoCo error: {e}")
    raise PlaybackError(f"Failed to play: {e}")
```

**Legacy pattern (returns bool)**:

```python
try:
    # Attempt SoCo operation
    speaker.play_uri(uri)
    logger.info("Success message")
    return True
except SoCoException as e:
    logger.error(f"Error: {e}")
    return False
```

### API Response Pattern

```python
# Success response
return jsonify({"status": "ok", "message": "Action completed"})
main.py           # Entry point (Flask app initialization)
│   ├── config.py         # Configuration management
│   ├── controller.py     # Main controller (refactored)
│   ├── api.py            # Flask routes and request handling
│   ├── exceptions.py     # Custom exception classes
│   ├── speakers.py       # Speaker discovery and management
│   ├── favorites.py      # Favorites management
│   ├── groups.py         # Group management
│   ├── playback.py       # Playback control
│   └── sonos.py          # Legacy monolithic controller (deprecated)
├── static/               # Frontend assets
│   └── index.html        # Single-page web UI
├── tests/                # Pytest test suite
│   ├── conftest.py       # Shared fixtures and mocks
│   ├── test_api.py       # API endpoint tests
│   ├── test_sonos.py     # Basic controller tests
│   └── test_sonos_advanced.py  # Advanced functionality
```

### Logging

- Use module-level logger: `logger = logging.getLogger(__name__)`
- Log speaker operations at INFO leveappropriate `sonos_controller` method

4. Handle exceptions and return `jsonify()` response with status code

### Adding a New Manager Method

1. Add method to appropriate manager class (speakers.py, favorites.py, groups.py, playback.py)
2. Raise custom exceptions from `exceptions.py` for error cases
3. Add comprehensive logging at INFO and ERROR levels
4. Update `controller.py` to expose the method if needed for API

### Testing Sonos Operations

- Use `mock_soco_discover` fixture to avoid real network calls
- Create `mock_speaker` fixtures with required attributes
- Verify both success and exception paths in tests
- Test edge cases (empty lists, invalid indices, missing speakers)
- Aim for 90%+ coverage on new code

### Adding Configuration Options

1. Add field to `Config` dataclass in `config.py`
2. Add environment variable support in `from_env()` method
3. Document new env var in README.md
4. Use `config.field_name` in code to access value

### Debugging Speaker Issues

- Check logs for discovery messages at startup
- Verify speakers are on same network as server
- Use `/api/speakers` endpoint to list discovered speakers
- Restart server to re-discover if network changes
- Check group status with `/api/group-status` endpoint
  ├── tests/ # Pytest test suite
  │ └── test_sonos.py # SonosController tests
  ├── pyproject.toml # uv/pip dependencies, ruff config
  └── .python-version # Python version (3.11)

```

## Key Dependencies

- **soco**: Sonos control library (speaker discovery, playback, metadata)
- **flask**: Lightweight WSGI web framework optimized for low-resource environments

## Common Tasks

### Adding a New API Endpoint

1. Add route decorator in `api.py` with appropriate HTTP method (`@app.route()`)
2. Parse JSON request data using `request.get_json()`
3. Validate required fields and call `sonos_controller` method
4. Return `jsonify()` response with status code

### Testing Sonos Operations

- Use `mock_soco_discover` fixture to avoid real network calls
- Create `mock_speaker` fixtures with required attributes
- Verify both success and failure paths in tests

### Debugging Speaker Issues

- Check logs for discovery messages at startup
- Verify speakers are on same network as server
- Use `/api/speakers` endpoint to list discovered speakers
- Restart server to re-discover if network changes
```
