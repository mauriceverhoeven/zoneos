# ZoneOS - AI Coding Agent Instructions

## Project Overview

ZoneOS is a Python-based bridge that connects Sonos speakers with iPhone automations and NFC stickers. It provides a REST API and lightweight web interface for controlling Sonos speakers, enabling physical NFC tags to trigger specific audio actions.

## Architecture

### Core Components

- **SonosController** (`src/zoneos/sonos.py`): Manages speaker discovery and control using the SoCo library
- **Flask Server** (`src/zoneos/api.py`): Lightweight REST API with endpoints for speaker control, playback, and volume
- **Web Frontend** (`static/index.html`): Single-page interface for testing and manual control

### Data Flow

1. NFC tag scanned → iPhone Shortcuts app → HTTP request to ZoneOS API
2. API validates request → SonosController executes action → Sonos speaker responds
3. Web interface provides manual control and system testing

### Key Design Decisions

- **Global controller**: Single `SonosController` instance initialized at startup for efficient speaker management
- **Discovery on init**: Speakers discovered once at startup; restart server if network topology changes
- **Stateless API**: Each request is independent; no session management required

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

### Error Handling Pattern

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

# Error handling with status code
if not success:
    return jsonify({"error": "Action failed"}), 400
```

### Logging

- Use module-level logger: `logger = logging.getLogger(__name__)`
- Log speaker operations at INFO level
- Log errors at ERROR level with context

## Project Structure

```
zoneos/
├── src/zoneos/           # Main package
│   ├── __init__.py       # Package version
│   ├── __main__.py       # Entry point (Flask app initialization)
│   ├── api.py            # Flask routes and request handling
│   └── sonos.py          # SoCo wrapper and speaker management
├── static/               # Frontend assets
│   └── index.html        # Single-page web UI
├── tests/                # Pytest test suite
│   └── test_sonos.py     # SonosController tests
├── pyproject.toml        # uv/pip dependencies, ruff config
└── .python-version       # Python version (3.11)
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
