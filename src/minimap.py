"""Interactive radar minimap for the wildlife ecosystem simulation.

Renders an interactive radar at the bottom-right corner showing
biome zones, live animal blips, camera viewport outline, and supports
click-to-teleport camera navigation.
"""

from __future__ import annotations
from typing import Optional, Tuple
import pygame

from src.camera import Camera2D
from src.simulation import Simulation
from src.species import TrophicRole
from src.terrain import BiomeType


class Minimap:
    """Corner radar minimap displaying reserve territories and live blips."""

    def __init__(self, width: int = 220, height: int = 140, margin: int = 16) -> None:
        self.width = width
        self.height = height
        self.margin = margin

        # Biome mini colors
        self.biome_colors = {
            BiomeType.HIGHLANDS: (55, 62, 72),
            BiomeType.DENSE_FOREST: (20, 38, 26),
            BiomeType.RIVER: (28, 75, 125),
            BiomeType.THICKETS: (60, 54, 34),
            BiomeType.MEADOW: (32, 85, 46),
        }

        # Cached surface for transparent rendering
        self._panel_surface: Optional[pygame.Surface] = None

    def get_rect(self, screen_width: int, screen_height: int) -> pygame.Rect:
        """Computes the on-screen destination rectangle for the minimap."""
        return pygame.Rect(
            screen_width - self.width - self.margin,
            screen_height - self.height - self.margin,
            self.width,
            self.height,
        )

    def is_clicked(self, sx: int, sy: int, screen_width: int, screen_height: int) -> bool:
        """Returns True if the screen coordinate lies within the minimap."""
        return self.get_rect(screen_width, screen_height).collidepoint(sx, sy)

    def screen_to_world(
        self,
        sx: int,
        sy: int,
        screen_width: int,
        screen_height: int,
        world_width: float,
        world_height: float,
    ) -> Optional[Tuple[float, float]]:
        """Converts a screen click on the minimap into world coordinates."""
        rect = self.get_rect(screen_width, screen_height)
        if not rect.collidepoint(sx, sy):
            return None

        rel_x = max(0.0, min(1.0, (sx - rect.x) / float(rect.width)))
        rel_y = max(0.0, min(1.0, (sy - rect.y) / float(rect.height)))
        return (rel_x * world_width, rel_y * world_height)

    def draw(
        self,
        surface: pygame.Surface,
        sim: Simulation,
        camera: Camera2D,
        badge_font: Optional[pygame.font.Font] = None,
    ) -> None:
        """Renders the minimap on the target surface."""
        rect = self.get_rect(camera.screen_width, camera.screen_height)

        # 1. Background panel
        if self._panel_surface is None or self._panel_surface.get_size() != (self.width, self.height):
            self._panel_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        panel = self._panel_surface
        panel.fill((0, 0, 0, 0))

        # Base backdrop with rounded corners
        pygame.draw.rect(panel, (12, 16, 22, 220), (0, 0, self.width, self.height), border_radius=6)

        scale_x = float(self.width) / sim.terrain.width
        scale_y = float(self.height) / sim.terrain.height

        # 2. Draw miniature biome territories
        for zone in sim.terrain.zones:
            col = self.biome_colors.get(zone.biome_type, (40, 40, 40))
            zx = int(zone.min_x * scale_x)
            zy = int(zone.min_y * scale_y)
            zw = int((zone.max_x - zone.min_x) * scale_x)
            zh = int((zone.max_y - zone.min_y) * scale_y)
            pygame.draw.rect(panel, (*col, 200), (zx, zy, zw, zh))
            pygame.draw.rect(panel, (20, 24, 30, 255), (zx, zy, zw, zh), 1)

        # River highlight line
        if len(sim.terrain.zones) > 2:
            water_zone = sim.terrain.zones[2]
            mid_y = int(((water_zone.min_y + water_zone.max_y) * 0.5) * scale_y)
            pygame.draw.line(panel, (60, 130, 195, 255), (0, mid_y), (self.width, mid_y), 2)

        # 3. Draw live animal blips
        for animal in sim.animals:
            if not animal.alive:
                continue
            bx = int(animal.x * scale_x)
            by = int(animal.y * scale_y)
            if 0 <= bx < self.width and 0 <= by < self.height:
                if animal.profile.trophic_role == TrophicRole.HERBIVORE:
                    # Green blip for herbivores
                    panel.set_at((bx, by), (80, 230, 100, 255))
                    if animal.profile.name == "deer":  # Larger blip for large herbivores
                        pygame.draw.circle(panel, (90, 240, 110, 255), (bx, by), 1)
                else:
                    # Red/orange blip for predators and bears
                    pygame.draw.circle(panel, (245, 75, 70, 255), (bx, by), 2)

        # 4. Viewport camera bounding box
        vp_min_x, vp_min_y, vp_max_x, vp_max_y = camera.get_viewport_world_bounds()
        cam_x1 = max(0, int(vp_min_x * scale_x))
        cam_y1 = max(0, int(vp_min_y * scale_y))
        cam_x2 = min(self.width, int(vp_max_x * scale_x))
        cam_y2 = min(self.height, int(vp_max_y * scale_y))
        cam_w = max(4, cam_x2 - cam_x1)
        cam_h = max(4, cam_y2 - cam_y1)

        # Draw gold viewport outline with subtle inner tint
        vp_surface = pygame.Surface((cam_w, cam_h), pygame.SRCALPHA)
        vp_surface.fill((255, 230, 90, 25))
        panel.blit(vp_surface, (cam_x1, cam_y1))
        pygame.draw.rect(panel, (255, 230, 90, 230), (cam_x1, cam_y1, cam_w, cam_h), 1)

        # Panel border
        pygame.draw.rect(panel, (70, 85, 105, 240), (0, 0, self.width, self.height), 1, border_radius=6)

        # Header watermark
        if badge_font:
            header = badge_font.render("RESERVE RADAR", True, (210, 220, 230))
            header.set_alpha(150)
            panel.blit(header, (6, 4))

        # Blit finished minimap to screen
        surface.blit(panel, rect.topleft)
