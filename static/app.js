/**
 * ZoneOS Frontend Application
 * Manages Sonos speaker control and favorites
 */

class ZoneOS {
  constructor() {
    this.allSpeakers = [];
    this.selectedSpeakers = new Set();
    this.currentlyPlayingIndex = null;
    this.nowPlayingInfo = null;
    this.pollInterval = null;
    this.init();
  }

  async init() {
    await this.loadSpeakers();
    await this.updateGroup();
    await this.loadFavorites();
    await this.updateNowPlaying();
    this.startPolling();
  }

  /**
   * Start polling for updates every 10 seconds
   */
  startPolling() {
    // Clear any existing interval
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
    }

    // Poll every 10 seconds
    this.pollInterval = setInterval(async () => {
      await this.updateNowPlaying();
      await this.updateVolumes();
      await this.updateGroupStatus();
      this.highlightCurrentFavorite();
    }, 10000);
  }

  /**
   * Update now playing display
   */
  async updateNowPlaying() {
    try {
      const resp = await fetch("/api/now-playing");
      const data = await resp.json();
      this.nowPlayingInfo = data;

      const title = data.title || "No music playing";
      const artist = data.artist || "";
      const albumArt = data.album_art || "";

      const titleEl = document.getElementById("now-playing-title");
      const artistEl = document.getElementById("now-playing-artist");
      const artEl = document.getElementById("now-playing-art");
      const placeholderEl = document.getElementById("now-playing-placeholder");

      if (titleEl) {
        titleEl.textContent = title;
        // Enable scrolling if text is too long
        const isLong = title.length > 30;
        titleEl.setAttribute("data-scrolling", isLong.toString());
        if (isLong) {
          titleEl.textContent = title + " • " + title; // Duplicate for seamless scroll
        }
      }

      if (artistEl) {
        artistEl.textContent = artist;
      }

      if (albumArt && artEl && placeholderEl) {
        artEl.src = albumArt;
        artEl.classList.remove("hidden");
        placeholderEl.classList.add("hidden");
      } else if (artEl && placeholderEl) {
        artEl.classList.add("hidden");
        placeholderEl.classList.remove("hidden");
      }

      this.highlightCurrentFavorite();
    } catch (error) {
      console.error("Failed to update now playing:", error);
    }
  }

  /**
   * Update all speaker volumes
   */
  async updateVolumes() {
    for (const speaker of this.allSpeakers) {
      try {
        const volResp = await fetch(
          `/api/speaker/volume/${encodeURIComponent(speaker)}`
        );
        const volData = await volResp.json();
        const volume = volData.volume || 50;

        const id = speaker.replace(/\s/g, "-");
        const volumeElement = document.getElementById(`volume-${id}`);
        if (volumeElement) {
          volumeElement.textContent = `${volume}%`;
        }
      } catch (error) {
        console.error(`Failed to update volume for ${speaker}:`, error);
      }
    }
  }

  /**
   * Update group status to reflect joined speakers
   */
  async updateGroupStatus() {
    try {
      const resp = await fetch("/api/group-status");
      const data = await resp.json();

      if (data.members) {
        // Update selectedSpeakers to reflect actual group
        this.selectedSpeakers = new Set(data.members);

        // Update UI to show which speakers are in the group
        for (const speaker of this.allSpeakers) {
          const id = speaker.replace(/\s/g, "-");
          const btn = document.getElementById(`speaker-btn-${id}`);
          if (btn) {
            if (this.selectedSpeakers.has(speaker)) {
              btn.classList.remove("opacity-50");
            } else {
              btn.classList.add("opacity-50");
            }
          }
        }
      }
    } catch (error) {
      console.error("Failed to update group status:", error);
    }
  }

  /**
   * Highlight the favorite that matches current playing track
   */
  highlightCurrentFavorite() {
    if (!this.nowPlayingInfo) return;

    const items = document.querySelectorAll(".favorite-item");
    const favorites = this._cachedFavorites || [];

    items.forEach((item, index) => {
      const fav = favorites[index];
      if (!fav) return;

      // Check both title and URI match (either can trigger highlight)
      const titleMatches = this.nowPlayingInfo.title && fav.title && 
                          this.nowPlayingInfo.title.trim() === fav.title.trim();
      const uriMatches = this.nowPlayingInfo.uri && fav.uri && 
                        this.nowPlayingInfo.uri.trim() === fav.uri.trim();
      
      const isPlaying = titleMatches || uriMatches;

      if (isPlaying) {
        item.classList.add(
          "playing",
          "!bg-green-50",
          "!border-green-500",
          "!border-4",
          "!shadow-xl",
          "!shadow-green-500/40",
          "scale-[1.02]"
        );
      } else {
        item.classList.remove(
          "playing",
          "!bg-green-50",
          "!border-green-500",
          "!border-4",
          "!shadow-xl",
          "!shadow-green-500/40",
          "scale-[1.02]"
        );
      }
    });
  }

  /**
   * Load and display speakers
   */
  async loadSpeakers() {
    const container = document.getElementById("speakers-container");

    try {
      const resp = await fetch("/api/speakers");
      const data = await resp.json();

      if (data.speakers && data.speakers.length > 0) {
        this.allSpeakers = data.speakers;
        this.selectedSpeakers = new Set(this.allSpeakers);

        const items = await Promise.all(
          data.speakers.map((speaker) => this.createSpeakerElement(speaker))
        );

        container.innerHTML = `
          <div class="flex flex-wrap gap-3">
            ${items.join("")}
          </div>
        `;
      } else {
        container.innerHTML = this.createEmptyState("No speakers found");
      }
    } catch (error) {
      container.innerHTML = this.createErrorState(
        `Failed to load speakers: ${error.message}`
      );
    }
  }

  /**
   * Create speaker DOM element
   */
  async createSpeakerElement(speaker) {
    const id = speaker.replace(/\s/g, "-");
    const escaped = this.escapeForAttribute(speaker);

    // Fetch current volume
    let currentVolume = 50;
    try {
      const volResp = await fetch(
        `/api/speaker/volume/${encodeURIComponent(speaker)}`
      );
      const volData = await volResp.json();
      currentVolume = volData.volume || 50;
    } catch (error) {
      console.error("Failed to fetch volume:", error);
    }

    return `
            <div 
                id="speaker-btn-${id}"
                onclick="app.toggleSpeaker('${escaped}')"
                class="flex-1 min-w-[200px] px-4 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-xl transition-all hover:shadow-lg cursor-pointer"
            >
                <div class="flex items-center justify-center gap-3 mb-2">
                    <button 
                        onclick="event.stopPropagation(); app.adjustVolume('${escaped}', -5)"
                        class="w-8 h-8 bg-white/20 hover:bg-white/30 text-white rounded-full font-bold text-lg transition-all hover:scale-110 active:scale-95 flex items-center justify-center"
                        title="Volume Down"
                    >
                        −
                    </button>
                    <span id="volume-${id}" class="font-mono font-bold text-white min-w-[3rem] text-center">${currentVolume}%</span>
                    <button 
                        onclick="event.stopPropagation(); app.adjustVolume('${escaped}', 5)"
                        class="w-8 h-8 bg-white/20 hover:bg-white/30 text-white rounded-full font-bold text-lg transition-all hover:scale-110 active:scale-95 flex items-center justify-center"
                        title="Volume Up"
                    >
                        +
                    </button>
                </div>
                <div class="text-center font-semibold text-sm">${this.escapeHtml(
                  speaker
                )}</div>
            </div>
        `;
  }

  /**
   * Toggle speaker selection
   */
  async toggleSpeaker(speaker) {
    const id = speaker.replace(/\s/g, "-");
    const btn = document.getElementById(`speaker-btn-${id}`);

    if (this.selectedSpeakers.has(speaker)) {
      if (this.selectedSpeakers.size === 1) {
        return; // Don't allow deselecting the last speaker
      }
      this.selectedSpeakers.delete(speaker);
      btn.classList.remove("bg-indigo-600", "hover:bg-indigo-700");
      btn.classList.add("bg-gray-400", "hover:bg-gray-500", "text-gray-700");
    } else {
      this.selectedSpeakers.add(speaker);
      btn.classList.remove("bg-gray-400", "hover:bg-gray-500", "text-gray-700");
      btn.classList.add("bg-indigo-600", "hover:bg-indigo-700");
    }

    await this.updateGroup();
  }

  /**
   * Update speaker group on backend
   */
  async updateGroup() {
    if (this.selectedSpeakers.size === 0) return;

    try {
      await fetch("/api/group", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ speakers: Array.from(this.selectedSpeakers) }),
      });
    } catch (error) {
      console.error("Failed to update group:", error);
    }
  }

  /**
   * Adjust speaker volume
   */
  async adjustVolume(speaker, delta) {
    try {
      const volResp = await fetch(
        `/api/speaker/volume/${encodeURIComponent(speaker)}`
      );
      const volData = await volResp.json();
      const currentVol = volData.volume || 50;
      const newVol = Math.max(0, Math.min(100, currentVol + delta));

      await fetch("/api/volume", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ speaker, volume: newVol }),
      });

      // Update the volume display
      const id = speaker.replace(/\s/g, "-");
      const volumeElement = document.getElementById(`volume-${id}`);
      if (volumeElement) {
        volumeElement.textContent = `${newVol}%`;
      }
    } catch (error) {
      console.error("Failed to adjust volume:", error);
    }
  }

  /**
   * Load and display favorites
   */
  async loadFavorites() {
    const container = document.getElementById("favorites-container");

    try {
      const resp = await fetch("/api/favorites");
      const data = await resp.json();

      if (data.favorites && data.favorites.length > 0) {
        this._cachedFavorites = data.favorites;
        const items = data.favorites.map((fav, i) =>
          this.createFavoriteElement(fav, i + 1)
        );
        container.innerHTML = `<div class="grid gap-3">${items.join("")}</div>`;
        this.highlightCurrentFavorite();
      } else {
        container.innerHTML = this.createEmptyState("No favorites found", true);
      }
    } catch (error) {
      container.innerHTML = this.createErrorState(
        `Failed to load favorites: ${error.message}`
      );
    }
  }

  /**
   * Create favorite DOM element
   */
  createFavoriteElement(fav, index) {
    const albumArt = fav.album_art
      ? `<img src="${fav.album_art}" class="w-14 h-14 rounded-lg object-cover flex-shrink-0 shadow-sm" onload="this.style.display='block'" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex'">
         <div class="w-14 h-14 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 items-center justify-center flex-shrink-0 shadow-sm hidden">
            <svg viewBox="0 0 24 24" class="w-7 h-7 fill-white opacity-90">
                <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
            </svg>
         </div>`
      : `<div class="w-14 h-14 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0 shadow-sm">
            <svg viewBox="0 0 24 24" class="w-7 h-7 fill-white opacity-90">
                <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
            </svg>
         </div>`;

    return `
            <div 
                onclick="app.playFavorite(${index})"
                class="favorite-item flex items-center gap-4 p-4 bg-white rounded-xl border-2 border-transparent transition-all duration-200 cursor-pointer hover:bg-gray-50 hover:border-indigo-500 hover:shadow-lg hover:translate-x-1 active:translate-x-0.5 min-w-0 shadow-sm"
            >
                ${albumArt}
                <div class="flex-1 min-w-0 flex flex-col gap-1.5">
                    <div class="font-semibold text-gray-900 truncate text-base">#${index} - ${this.escapeHtml(
      fav.title
    )}</div>
                    <div class="text-xs text-gray-500 font-mono truncate md:block hidden opacity-70">${this.escapeHtml(
                      fav.uri
                    )}</div>
                </div>
            </div>
        `;
  }

  /**
   * Play a favorite by index
   */
  async playFavorite(index) {
    if (this.selectedSpeakers.size === 0) {
      alert("Please select at least one speaker");
      return;
    }

    try {
      const resp = await fetch("/api/play-favorite-index", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ index }),
      });

      if (!resp.ok) {
        const data = await resp.json();
        console.error("Failed to play:", data.error);
        return;
      }

      // Update now playing immediately
      setTimeout(() => this.updateNowPlaying(), 1000);
    } catch (error) {
      console.error("Failed to play favorite:", error);
    }
  }

  /**
   * Refresh favorites from Sonos
   */
  async refreshFavorites() {
    const btn = document.querySelector(".refresh-btn");
    const icon = btn.querySelector("svg");
    btn.disabled = true;
    icon.classList.add("animate-spin");

    try {
      const resp = await fetch("/api/favorites/refresh", { method: "POST" });
      const data = await resp.json();

      if (resp.ok) {
        await this.loadFavorites();
        this.highlightCurrentFavorite();
      } else {
        document.getElementById("favorites-container").innerHTML =
          this.createErrorState(data.error || "Failed to refresh");
      }
    } catch (error) {
      document.getElementById("favorites-container").innerHTML =
        this.createErrorState(`Failed to refresh: ${error.message}`);
    } finally {
      btn.disabled = false;
      icon.classList.remove("animate-spin");
    }
  }

  /**
   * Create empty state element
   */
  createEmptyState(message, withIcon = false) {
    const icon = withIcon
      ? `
            <svg viewBox="0 0 24 24" fill="currentColor" class="w-16 h-16 mb-4 opacity-30">
                <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
            </svg>
        `
      : "";

    return `
            <div class="text-center py-10 px-5 text-gray-600">
                ${icon}
                <div>${message}</div>
            </div>
        `;
  }

  /**
   * Create error state element
   */
  createErrorState(message) {
    return `
            <div class="bg-red-50 text-red-700 p-3 rounded-md mb-4">
                ${this.escapeHtml(message)}
            </div>
        `;
  }

  /**
   * Escape HTML to prevent XSS
   */
  escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Escape text for use in HTML attributes
   */
  escapeForAttribute(text) {
    return text.replace(/'/g, "\\'").replace(/"/g, "&quot;");
  }
}

// Initialize app when DOM is ready
let app;
document.addEventListener("DOMContentLoaded", () => {
  app = new ZoneOS();
});
