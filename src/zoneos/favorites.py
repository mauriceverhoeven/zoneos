"""Favorites management for Sonos."""

import logging

import soco

from zoneos.exceptions import FavoriteNotFoundError

logger = logging.getLogger(__name__)


class FavoritesManager:
    """Manages Sonos favorites."""

    def __init__(self):
        """Initialize favorites manager."""
        self._favorites: list[dict[str, str]] = []

    def refresh(self, speaker: soco.SoCo) -> None:
        """Refresh the favorites list from Sonos system.

        Args:
            speaker: A SoCo speaker instance to query

        Raises:
            SoCoException: If favorites retrieval fails
        """
        favorites = list(speaker.music_library.get_sonos_favorites())
        favorites.extend(speaker.music_library.get_favorite_radio_stations())

        self._favorites = []
        for fav in favorites:
            try:
                fav_data = {
                    "title": fav.title,
                    "uri": fav.get_uri(),
                }
                if hasattr(fav, "album_art_uri"):
                    fav_data["album_art"] = fav.album_art_uri
                self._favorites.append(fav_data)
            except Exception as e:
                logger.error(f"Error processing favorite '{fav}': {e}")

        logger.info(f"Refreshed {len(self._favorites)} favorites")

    def get_all(self) -> list[dict[str, str]]:
        """Get cached list of Sonos favorites.

        Returns:
            List of favorite dictionaries
        """
        return self._favorites

    def get_by_title(self, speaker: soco.SoCo, title: str) -> dict[str, str]:
        """Get a favorite by its title and return full favorite object.

        Args:
            speaker: SoCo speaker instance to query
            title: Favorite title

        Returns:
            Dictionary with favorite data including metadata

        Raises:
            FavoriteNotFoundError: If favorite not found
        """
        all_favorites = list(speaker.music_library.get_sonos_favorites())
        all_favorites.extend(speaker.music_library.get_favorite_radio_stations())

        for fav in all_favorites:
            if fav.title == title:
                return {
                    "title": fav.title,
                    "uri": fav.get_uri(),
                    "metadata": fav.resource_meta_data,
                }

        raise FavoriteNotFoundError(f"Favorite '{title}' not found")

    def get_by_index(self, speaker: soco.SoCo, index: int) -> dict[str, str]:
        """Get a favorite by its index (1-based) and return full favorite object.

        Args:
            speaker: SoCo speaker instance to query
            index: 1-based index of favorite

        Returns:
            Dictionary with favorite data including metadata

        Raises:
            IndexError: If index out of range
            FavoriteNotFoundError: If favorite at index not found
        """
        if index < 1 or index > len(self._favorites):
            raise IndexError(
                f"Invalid favorite index: {index} (must be 1-{len(self._favorites)})"
            )

        favorite = self._favorites[index - 1]
        return self.get_by_title(speaker, favorite["title"])
