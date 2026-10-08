"""Live Activity Feed Ticker & Event Log (Phase 5).

Chronological rolling HUD ticker displaying noteworthy ecological events:
- Predation kills (🐺 Wolf caught a Deer in Meadow Plains)
- Births and reproduction (🐇 Rabbit offspring born in Briar Thickets)
- Sprint exhaustion (🦊 Fox exhausted from high-speed sprint)
- Prey escapes (🐐 Mountain Goat escaped Wolf up the Highlands)

Includes click-to-teleport: clicking any event pans the camera to the event location.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import pygame

from src.camera import Camera2D


@dataclass(frozen=True)
class ActivityEvent:
    """Represents a single noteworthy ecological event in the reserve."""
    time: float
    message: str
    category: str        # "kill", "birth", "exhaustion", "escape"
    species: str
    biome_name: str
    x: float
    y: float


class ActivityFeedHUD:
    """Rolling semi-transparent HUD ticker at bottom-left."""

    def __init__(self, width: int = 370, max_display_items: int = 5) -> None:
        self.width = width
        self.item_height = 22
        self.max_display_items = max_display_items
        self.events: List[ActivityEvent] = []
        self.event_lifetime: float = 6.5  # Seconds before fading out

        # Category colors
        self.category_colors: Dict[str, Tuple[int, int, int]] = {
            "kill": (240, 70, 70),       # Crimson Red
            "birth": (110, 230, 140),    # Vibrant Green
            "exhaustion": (245, 160, 50),# Orange/Amber
            "escape": (70, 200, 240),    # Sky Cyan
        }

        # Category icons
        self.category_icons: Dict[str, str] = {
            "kill": "⚔",
            "birth": "✦",
            "exhaustion": "⚡",
            "escape": "💨",
        }

        # Fonts
        pygame.font.init()
        self.font = pygame.font.SysFont("consolas", 11)
        self.icon_font = pygame.font.SysFont("segoe ui symbol", 11)
        self.header_font = pygame.font.SysFont("consolas", 10, bold=True)

    def add_event(self, event: ActivityEvent) -> None:
        """Adds a new event to the head of the log."""
        self.events.append(event)
        # Keep maximum 20 in memory
        if len(self.events) > 20:
            self.events.pop(0)

    def get_recent_events(self, current_time: float) -> List[Tuple[ActivityEvent, float]]:
        """Returns non-expired events with their remaining alpha (0.0 to 1.0)."""
        active: List[Tuple[ActivityEvent, float]] = []
        for evt in reversed(self.events):
            age = current_time - evt.time
            if age > self.event_lifetime:
                continue
            # Fade out in the last 2.0 seconds
            if age > self.event_lifetime - 2.0:
                alpha = max(0.0, (self.event_lifetime - age) / 2.0)
            else:
                alpha = 1.0
            active.append((evt, alpha))
            if len(active) >= self.max_display_items:
                break
        return active

    def get_rect(self, screen_width: int, screen_height: int, chart_visible: bool) -> pygame.Rect:
        """Computes on-screen rectangle dynamically positioned above chart or at bottom-left."""
        num_items = min(self.max_display_items, max(1, len(self.events)))
        h = 24 + num_items * self.item_height
        if chart_visible:
            # Sit directly above the chart (chart height: 230, margin: 16)
            y = screen_height - 230 - 16 - h - 10
        else:
            y = screen_height - h - 16
        return pygame.Rect(16, y, self.width, h)

    def handle_click(
        self,
        sx: int,
        sy: int,
        screen_width: int,
        screen_height: int,
        chart_visible: bool,
        current_time: float,
        cam: Camera2D,
    ) -> bool:
        """Handles mouse click. If clicked on an event, teleports camera to event location."""
        rect = self.get_rect(screen_width, screen_height, chart_visible)
        if not rect.collidepoint(sx, sy):
            return False

        active_events = self.get_recent_events(current_time)
        if not active_events:
            return True

        local_y = sy - rect.y - 24
        if local_y < 0:
            return True

        clicked_idx = local_y // self.item_height
        if 0 <= clicked_idx < len(active_events):
            evt, _ = active_events[clicked_idx]
            cam.teleport_to(evt.x, evt.y)
            return True

        return True

    def draw(
        self,
        surface: pygame.Surface,
        screen_width: int,
        screen_height: int,
        chart_visible: bool,
        current_time: float,
    ) -> None:
        """Renders the rolling activity log ticker."""
        active = self.get_recent_events(current_time)
        if not active:
            return

        panel_rect = self.get_rect(screen_width, screen_height, chart_visible)
        panel = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)

        # 1. Background Panel
        pygame.draw.rect(panel, (14, 18, 24, 215), (0, 0, panel_rect.width, panel_rect.height), border_radius=6)
        pygame.draw.rect(panel, (50, 65, 82), (0, 0, panel_rect.width, panel_rect.height), 1, border_radius=6)

        # 2. Header
        hdr_surf = self.header_font.render("ACTIVITY LOG (Click to Focus)", True, (160, 180, 205))
        panel.blit(hdr_surf, (10, 6))

        # 3. Event Rows
        for i, (evt, alpha) in enumerate(active):
            row_y = 24 + i * self.item_height
            row_surf = pygame.Surface((panel_rect.width - 12, self.item_height - 2), pygame.SRCALPHA)

            cat_col = self.category_colors.get(evt.category, (200, 200, 200))
            # Left category color strip
            pygame.draw.rect(row_surf, (*cat_col, int(230 * alpha)), (0, 0, 3, self.item_height - 2), border_radius=1)

            # Icon & Message
            icon = self.category_icons.get(evt.category, "•")
            time_str = f"[{evt.time:4.1f}s] {icon} {evt.message}"

            # Text render
            txt_color = (
                min(255, int(cat_col[0] * 0.7 + 70)),
                min(255, int(cat_col[1] * 0.7 + 70)),
                min(255, int(cat_col[2] * 0.7 + 70)),
            )
            txt_surf = self.font.render(time_str, True, txt_color)
            txt_surf.set_alpha(int(255 * alpha))
            row_surf.blit(txt_surf, (8, 2))

            panel.blit(row_surf, (6, row_y))

        surface.blit(panel, (panel_rect.x, panel_rect.y))
