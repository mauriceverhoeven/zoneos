"""Configuration management for ZoneOS."""

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration."""

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # Sonos settings
    discovery_timeout: int = 5  # seconds
    auto_group_on_startup: bool = True

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s"

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            host=os.getenv("ZONEOS_HOST", "0.0.0.0"),
            port=int(os.getenv("ZONEOS_PORT", "8000")),
            debug=os.getenv("ZONEOS_DEBUG", "true").lower() == "true",
            discovery_timeout=int(os.getenv("ZONEOS_DISCOVERY_TIMEOUT", "5")),
            auto_group_on_startup=os.getenv("ZONEOS_AUTO_GROUP", "true").lower()
            == "true",
            log_level=os.getenv("ZONEOS_LOG_LEVEL", "INFO"),
            log_format=os.getenv(
                "ZONEOS_LOG_FORMAT",
                "%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s",
            ),
        )


# Global config instance
config = Config.from_env()
