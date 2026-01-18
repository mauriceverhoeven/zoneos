"""Entry point for ZoneOS application."""

import logging

from zoneos.api import create_app
from zoneos.config import config
from zoneos.controller import SonosController

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format=config.log_format,
)

logger = logging.getLogger(__name__)


def main():
    """Initialize and run the Flask application."""
    logger.info("Starting ZoneOS...")

    # Initialize Sonos controller
    import zoneos.api

    zoneos.api.sonos_controller = SonosController()

    # Create Flask app
    app = create_app()

    logger.info(f"ZoneOS ready! Server starting on http://{config.host}:{config.port}")

    # Run Flask development server
    app.run(host=config.host, port=config.port, debug=config.debug)


if __name__ == "__main__":
    main()
