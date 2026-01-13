"""Entry point for ZoneOS application."""

import logging

from zoneos.api import create_app, sonos_controller
from zoneos.sonos import SonosController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Initialize and run the Flask application."""
    global sonos_controller

    logger.info("Starting ZoneOS...")

    # Initialize Sonos controller
    import zoneos.api

    zoneos.api.sonos_controller = SonosController()

    # Create Flask app
    app = create_app()

    logger.info("ZoneOS ready! Server starting on http://0.0.0.0:8000")

    # Run Flask development server with auto-reload
    app.run(host="0.0.0.0", port=8000, debug=True)


if __name__ == "__main__":
    main()
