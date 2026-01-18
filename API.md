# ZoneOS API Documentation

## Overview

ZoneOS provides a REST API for controlling Sonos speakers. All endpoints return JSON responses.

## Base URL

```
http://localhost:8000
```

## Response Format

### Success Response

```json
{
  "status": "ok",
  "message": "Action completed successfully"
}
```

### Error Response

```json
{
  "error": "Error message describing what went wrong"
}
```

## Endpoints

### Speaker Management

#### List All Speakers

```http
GET /api/speakers
```

**Response:**

```json
{
  "speakers": ["Living Room", "Bedroom", "Kitchen"]
}
```

#### Get Speaker Volume

```http
GET /api/speaker/volume/<speaker_name>
```

**Response:**

```json
{
  "speaker": "Living Room",
  "volume": 50
}
```

**Error Codes:**

- `400`: Speaker not found or volume retrieval failed
- `503`: Controller not initialized

### Playback Control

#### Play Favorite

```http
POST /api/play-favorite
Content-Type: application/json

{
  "speaker": "Living Room",
  "favorite": "Radio 538"
}
```

**Response:**

```json
{
  "status": "ok",
  "message": "Playing Radio 538 on Living Room"
}
```

**Error Codes:**

- `400`: Missing fields, speaker not found, or favorite not found
- `503`: Controller not initialized

#### Play Favorite by Index

```http
POST /api/play-favorite-index
Content-Type: application/json

{
  "index": 1
}
```

Plays the favorite at the specified 1-based index on the group coordinator.

**Response:**

```json
{
  "status": "ok",
  "message": "Playing favorite #1 on group"
}
```

**Error Codes:**

- `400`: Invalid index or playback failed
- `503`: Controller not initialized

#### Control Playback

```http
POST /api/control
Content-Type: application/json

{
  "speaker": "Living Room",
  "action": "play"
}
```

**Valid Actions:**

- `play`: Start playback
- `pause`: Pause playback
- `stop`: Stop playback
- `next`: Skip to next track
- `previous`: Skip to previous track

**Response:**

```json
{
  "status": "ok",
  "message": "Executed play on Living Room"
}
```

**Error Codes:**

- `400`: Invalid action or execution failed
- `503`: Controller not initialized

#### Play URI

```http
POST /api/play-uri
Content-Type: application/json

{
  "speaker": "Living Room",
  "uri": "http://example.com/audio.mp3"
}
```

**Response:**

```json
{
  "status": "ok",
  "message": "Playing URI on Living Room"
}
```

**Error Codes:**

- `400`: Missing fields or playback failed
- `503`: Controller not initialized

#### Get Now Playing

```http
GET /api/now-playing
```

**Response:**

```json
{
  "title": "Song Title",
  "artist": "Artist Name",
  "album_art": "http://example.com/art.jpg",
  "uri": "x-rincon-cpcontainer:1234"
}
```

Returns empty strings if nothing is playing.

### Volume Control

#### Set Volume

```http
POST /api/volume
Content-Type: application/json

{
  "speaker": "Living Room",
  "volume": 50
}
```

**Parameters:**

- `volume`: Integer between 0 and 100

**Response:**

```json
{
  "status": "ok",
  "message": "Set volume to 50 on Living Room"
}
```

**Error Codes:**

- `400`: Invalid volume range or speaker not found
- `503`: Controller not initialized

### Favorites Management

#### List All Favorites

```http
GET /api/favorites
```

**Response:**

```json
{
  "favorites": [
    {
      "title": "Radio 538",
      "uri": "x-rincon-cpcontainer:1004206c...",
      "album_art": "http://example.com/art.jpg"
    },
    {
      "title": "My Playlist",
      "uri": "x-rincon-cpcontainer:1006206c..."
    }
  ]
}
```

#### Refresh Favorites

```http
POST /api/favorites/refresh
```

Refreshes the favorites list from the Sonos system.

**Response:**

```json
{
  "status": "ok",
  "message": "Refreshed 15 favorites"
}
```

**Error Codes:**

- `400`: Refresh failed
- `503`: Controller not initialized

### Group Management

#### Set Group

```http
POST /api/group
Content-Type: application/json

{
  "speakers": ["Living Room", "Bedroom", "Kitchen"]
}
```

Updates the speaker group. Speakers not in the list will be removed from the group.

**Response:**

```json
{
  "status": "ok",
  "message": "Group created with 3 speakers"
}
```

**Error Codes:**

- `400`: Empty speaker list or group creation failed
- `503`: Controller not initialized

#### Get Group Status

```http
GET /api/group-status
```

**Response:**

```json
{
  "members": ["Living Room", "Bedroom"],
  "volumes": {
    "Living Room": 50,
    "Bedroom": 45
  }
}
```

## Configuration

The API can be configured via environment variables:

| Variable                   | Default   | Description                         |
| -------------------------- | --------- | ----------------------------------- |
| `ZONEOS_HOST`              | `0.0.0.0` | Server host address                 |
| `ZONEOS_PORT`              | `8000`    | Server port                         |
| `ZONEOS_DEBUG`             | `true`    | Enable debug mode                   |
| `ZONEOS_DISCOVERY_TIMEOUT` | `5`       | Speaker discovery timeout (seconds) |
| `ZONEOS_AUTO_GROUP`        | `true`    | Auto-group all speakers on startup  |
| `ZONEOS_LOG_LEVEL`         | `INFO`    | Logging level                       |

## Error Handling

All endpoints follow a consistent error handling pattern:

- `400 Bad Request`: Invalid input, missing parameters, or operation failed
- `503 Service Unavailable`: Controller not initialized (speakers not discovered)

Error responses include a descriptive message:

```json
{
  "error": "Speaker 'Unknown' not found"
}
```

## Rate Limiting

There is currently no rate limiting implemented. Consider implementing rate limiting if exposing the API to the internet.

## Security Considerations

- The API has no authentication mechanism
- Should only be exposed on trusted networks
- Do not expose directly to the internet without adding authentication
- Consider using a reverse proxy with authentication for production deployments

## Examples

### Using curl

```bash
# List speakers
curl http://localhost:8000/api/speakers

# Play favorite
curl -X POST http://localhost:8000/api/play-favorite \
  -H "Content-Type: application/json" \
  -d '{"speaker": "Living Room", "favorite": "Radio 538"}'

# Set volume
curl -X POST http://localhost:8000/api/volume \
  -H "Content-Type: application/json" \
  -d '{"speaker": "Living Room", "volume": 75}'

# Control playback
curl -X POST http://localhost:8000/api/control \
  -H "Content-Type: application/json" \
  -d '{"speaker": "Living Room", "action": "pause"}'
```

### Using Python requests

```python
import requests

BASE_URL = "http://localhost:8000"

# List speakers
response = requests.get(f"{BASE_URL}/api/speakers")
speakers = response.json()["speakers"]

# Play favorite
requests.post(
    f"{BASE_URL}/api/play-favorite",
    json={"speaker": "Living Room", "favorite": "Radio 538"}
)

# Set volume
requests.post(
    f"{BASE_URL}/api/volume",
    json={"speaker": "Living Room", "volume": 75}
)
```

### Using iOS Shortcuts

1. Add "Get Contents of URL" action
2. Set URL to `http://YOUR_IP:8000/api/play-favorite`
3. Set Method to `POST`
4. Set Request Body to `JSON`:
   ```json
   {
     "speaker": "Living Room",
     "favorite": "Morning Playlist"
   }
   ```
5. Add automation trigger (NFC tag, time, location, etc.)
