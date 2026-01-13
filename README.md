# ZoneOS 🎵

A lightweight Python bridge that connects Sonos speakers with iPhone automations and NFC stickers. Control your Sonos system using physical NFC tags or the web interface.

## Features

- 🔍 **Auto-discovery**: Automatically finds Sonos speakers on your network
- 📱 **iPhone Integration**: Works seamlessly with iOS Shortcuts and NFC tags
- 🌐 **Web Interface**: Clean, modern UI for manual control and testing
- 🎯 **REST API**: Simple HTTP endpoints for automation
- ⚡ **Fast & Lightweight**: Built with Flask for low-resource environments like Raspberry Pi

## Quick Start

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Sonos speakers on the same network

### Installation

```bash
# Clone the repository
git clone https://github.com/mauriceverhoeven/zoneos.git
cd zoneos

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and run
uv sync
uv run python -m zoneos
```

The server will start on `http://localhost:8000`

## Usage

### Web Interface

Open `http://localhost:8000` in your browser to access the control interface. You can:

- Select speakers
- Control playback (play, pause, stop, next, previous)
- Adjust volume
- Play Sonos favorites
- Play audio from URLs

### API Endpoints

#### List Speakers

```bash
GET /api/speakers
```

#### Play a Favorite

```bash
POST /api/play-favorite
Content-Type: application/json

{
  "speaker": "Living Room",
  "favorite": "Chill Radio"
}
```

#### Control Playback

```bash
POST /api/control
Content-Type: application/json

{
  "speaker": "Living Room",
  "action": "play"  # play, pause, stop, next, previous
}
```

#### Set Volume

```bash
POST /api/volume
Content-Type: application/json

{
  "speaker": "Living Room",
  "volume": 50
}
```

#### Play URI

```bash
POST /api/play-uri
Content-Type: application/json

{
  "speaker": "Living Room",
  "uri": "http://example.com/audio.mp3"
}
```

### iPhone + NFC Integration

1. **Find your server's IP address** on your local network
2. **Create an iOS Shortcut**:
   - Add "Get Contents of URL" action
   - Set URL to `http://YOUR_IP:8000/api/play-favorite`
   - Set Method to POST
   - Add Request Body (JSON):
     ```json
     {
       "speaker": "Living Room",
       "favorite": "Morning Playlist"
     }
     ```
3. **Link to NFC tag**: Add automation trigger "When NFC Tag Is Scanned"
4. **Scan and enjoy**: Tap your NFC sticker to trigger the action

### Example Use Cases

- **Morning routine**: Tap an NFC tag on your bedside table to start morning music
- **Workout mode**: Stick an NFC tag on your yoga mat to play workout playlists
- **Dinner time**: Kitchen NFC tag that starts ambient dinner music
- **Kids' room**: Let kids tap a tag to play their favorite songs (with volume limits!)

## Development

### Project Structure

```
zoneos/
├── src/zoneos/           # Main package
│   ├── __init__.py       # Package version
│   ├── __main__.py       # Entry point
│   ├── api.py            # FastAPI routes
│   └── sonos.py          # Sonos controller
├── static/               # Web frontend
│   └── index.html        # Single-page UI
├── tests/                # Test suite
└── pyproject.toml        # Dependencies
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=zoneos --cov-report=html
```

### Linting

```bash
# Check code style
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .
```

## Troubleshooting

### No speakers found

- Ensure Sonos speakers are powered on and connected to the same network
- Check firewall settings (port 8000 should be accessible)
- Restart the server to re-discover speakers

### iPhone can't connect

- Verify your computer's IP address hasn't changed
- Ensure iPhone and server are on the same network
- Check that port 8000 is not blocked

### API returns 503 errors

- The controller may not be initialized yet
- Wait a few seconds after starting the server
- Check logs for discovery errors

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [SoCo](https://github.com/SoCo/SoCo) - Sonos Controller library
- Powered by [Flask](https://flask.palletsprojects.com/)
- Package management by [uv](https://github.com/astral-sh/uv)
