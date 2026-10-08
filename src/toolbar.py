"""Interactive Desktop Toolbar HUD & Playback Controls (Phase 4).

Provides a fully interactive, clickable on-screen interface for:
- Play / Pause simulation toggle
- Speed multipliers: 1x (Real-time), 2x (Fast), 5x (Turbo)
- World reset button with fresh seed
- View Mode selector: 2.5D Animated Sprite, Top-Down 360°, Debug Shapes
- Overlay toggles: Population Chart (C), Biome Watermarks (B)
- Quick-Spawn palette: Instant entity injection for all 6 species to test ecological shocks
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import pygame

from src.camera import Camera2D
from src.config import ViewMode
from src.simulation import Simulation


@dataclass
class ToolbarAction:
    """Action resulting from an interactive toolbar click."""
    consumed: bool = False
    toggle_pause: bool = False
    set_speed: Optional[int] = None
    reset_simulation: bool = False
    set_view_mode: Optional[ViewMode] = None
    toggle_chart: bool = False
    toggle_biomes: bool = False
    spawned_species: Optional[str] = None


class ToolbarHUD:
    """Modern on-screen clickable toolbar panel."""

    def __init__(self, x: int = 16, y: int = 142, width: int = 700, height: int = 76) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.visible: bool = True
        self.notification_text: str = ""
        self.notification_timer: float = 0.0

        # Species accent colors matching minimap & chart
        self.species_colors: Dict[str, Tuple[int, int, int]] = {
            "rabbit": (110, 230, 140),
            "deer": (70, 200, 120),
            "goat": (60, 215, 215),
            "fox": (250, 150, 50),
            "wolf": (240, 70, 65),
            "bear": (180, 80, 55),
        }

        # Fonts
        pygame.font.init()
        self.font = pygame.font.SysFont("consolas", 11, bold=True)
        self.small_font = pygame.font.SysFont("consolas", 10, bold=True)
        self.label_font = pygame.font.SysFont("consolas", 10)

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, dt: float) -> None:
        """Updates transient visual timers."""
        if self.notification_timer > 0.0:
            self.notification_timer = max(0.0, self.notification_timer - dt)
            if self.notification_timer <= 0.0:
                self.notification_text = ""

    def notify(self, message: str, duration: float = 2.0) -> None:
        """Displays transient flash feedback in the toolbar."""
        self.notification_text = message
        self.notification_timer = duration

    def _get_button_rects(self) -> Dict[str, pygame.Rect]:
        """Calculates absolute screen rectangles for all toolbar buttons."""
        ox, oy = self.x, self.y
        return {
            # Row 1: Playback & Speed & Reset
            "pause": pygame.Rect(ox + 10, oy + 8, 76, 26),
            "speed_1": pygame.Rect(ox + 90, oy + 8, 32, 26),
            "speed_2": pygame.Rect(ox + 126, oy + 8, 32, 26),
            "speed_5": pygame.Rect(ox + 162, oy + 8, 32, 26),
            "reset": pygame.Rect(ox + 198, oy + 8, 64, 26),

            # Row 1: View Modes
            "view_side": pygame.Rect(ox + 312, oy + 8, 56, 26),
            "view_top": pygame.Rect(ox + 372, oy + 8, 48, 26),
            "view_shapes": pygame.Rect(ox + 424, oy + 8, 56, 26),

            # Row 1: Overlays
            "chart": pygame.Rect(ox + 508, oy + 8, 86, 26),
            "biomes": pygame.Rect(ox + 598, oy + 8, 92, 26),

            # Row 2: Quick-Spawn Buttons
            "spawn_rabbit": pygame.Rect(ox + 66, oy + 42, 80, 24),
            "spawn_deer": pygame.Rect(ox + 150, oy + 42, 68, 24),
            "spawn_goat": pygame.Rect(ox + 222, oy + 42, 68, 24),
            "spawn_fox": pygame.Rect(ox + 294, oy + 42, 64, 24),
            "spawn_wolf": pygame.Rect(ox + 362, oy + 42, 68, 24),
            "spawn_bear": pygame.Rect(ox + 434, oy + 42, 68, 24),
        }

    def handle_click(
        self,
        sx: int,
        sy: int,
        sim: Simulation,
        cam: Camera2D,
        paused: bool,
        current_speed: int,
        current_view: ViewMode,
    ) -> ToolbarAction:
        """Handles mouse click against toolbar buttons."""
        rect = self.get_rect()
        if not rect.collidepoint(sx, sy):
            return ToolbarAction(consumed=False)

        btns = self._get_button_rects()

        # Playback Controls
        if btns["pause"].collidepoint(sx, sy):
            return ToolbarAction(consumed=True, toggle_pause=True)
        if btns["speed_1"].collidepoint(sx, sy):
            return ToolbarAction(consumed=True, set_speed=1)
        if btns["speed_2"].collidepoint(sx, sy):
            return ToolbarAction(consumed=True, set_speed=2)
        if btns["speed_5"].collidepoint(sx, sy):
            return ToolbarAction(consumed=True, set_speed=5)
        if btns["reset"].collidepoint(sx, sy):
            self.notify("↺ Reserve Reset!", 1.5)
            return ToolbarAction(consumed=True, reset_simulation=True)

        # View Modes
        if btns["view_side"].collidepoint(sx, sy):
            return ToolbarAction(consumed=True, set_view_mode=ViewMode.SIDE_VIEW)
        if btns["view_top"].collidepoint(sx, sy):
            return ToolbarAction(consumed=True, set_view_mode=ViewMode.TOP_DOWN)
        if btns["view_shapes"].collidepoint(sx, sy):
            return ToolbarAction(consumed=True, set_view_mode=ViewMode.SHAPES)

        # Overlay HUD Toggles
        if btns["chart"].collidepoint(sx, sy):
            return ToolbarAction(consumed=True, toggle_chart=True)
        if btns["biomes"].collidepoint(sx, sy):
            return ToolbarAction(consumed=True, toggle_biomes=True)

        # Quick-Spawn Actions (spawns animal at current camera focus)
        spawn_map = {
            "spawn_rabbit": "rabbit",
            "spawn_deer": "deer",
            "spawn_goat": "goat",
            "spawn_fox": "fox",
            "spawn_wolf": "wolf",
            "spawn_bear": "bear",
        }
        for btn_key, sp_name in spawn_map.items():
            if btns[btn_key].collidepoint(sx, sy):
                # Spawn at camera center
                spawned = sim.spawn_animal(sp_name, x=cam.x, y=cam.y)
                if spawned:
                    label = sp_name.capitalize()
                    self.notify(f"+1 {label} Spawned!", 1.8)
                    return ToolbarAction(consumed=True, spawned_species=sp_name)

        return ToolbarAction(consumed=True)

    def draw(
        self,
        surface: pygame.Surface,
        paused: bool,
        current_speed: int,
        current_view: ViewMode,
        chart_visible: bool,
        biomes_visible: bool,
        mouse_pos: Tuple[int, int],
    ) -> None:
        """Renders the sleek interactive toolbar panel."""
        panel_rect = self.get_rect()
        panel = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # 1. Background Panel
        pygame.draw.rect(panel, (16, 20, 26, 225), (0, 0, self.width, self.height), border_radius=8)
        pygame.draw.rect(panel, (55, 68, 85), (0, 0, self.width, self.height), 1, border_radius=8)

        btns = self._get_button_rects()
        mx, my = mouse_pos

        # Helper to draw interactive button
        def draw_btn(
            key: str,
            text: str,
            is_active: bool = False,
            active_color: Tuple[int, int, int] = (45, 120, 200),
            accent_border: Optional[Tuple[int, int, int]] = None,
            font: Optional[pygame.font.Font] = None,
        ) -> None:
            brect = btns[key]
            # Convert screen rect to panel-local rect
            local_r = pygame.Rect(brect.x - self.x, brect.y - self.y, brect.width, brect.height)
            is_hover = brect.collidepoint(mx, my)

            if is_active:
                bg_col = (*active_color, 240)
                border_col = (255, 255, 255)
                text_col = (255, 255, 255)
            elif is_hover:
                bg_col = (48, 60, 78, 240)
                border_col = accent_border if accent_border else (140, 160, 190)
                text_col = (250, 250, 255)
            else:
                bg_col = (26, 32, 44, 210)
                border_col = accent_border if accent_border else (60, 72, 88)
                text_col = (195, 205, 220)

            pygame.draw.rect(panel, bg_col, local_r, border_radius=4)
            pygame.draw.rect(panel, border_col, local_r, 1, border_radius=4)

            use_font = font if font is not None else self.font
            txt_surf = use_font.render(text, True, text_col)
            txt_rect = txt_surf.get_rect(center=local_r.center)
            panel.blit(txt_surf, txt_rect)

        # 2. Draw Playback & Speed Controls
        draw_btn("pause", "▶ RESUME" if paused else "⏸ PAUSE", is_active=paused, active_color=(200, 60, 60))
        draw_btn("speed_1", "1x", is_active=(current_speed == 1), active_color=(45, 140, 90))
        draw_btn("speed_2", "2x", is_active=(current_speed == 2), active_color=(35, 130, 180))
        draw_btn("speed_5", "5x", is_active=(current_speed == 5), active_color=(170, 75, 190))
        draw_btn("reset", "↺ RESET")

        # Vertical Dividers
        pygame.draw.line(panel, (45, 55, 70), (272, 6), (272, 36), 1)
        pygame.draw.line(panel, (45, 55, 70), (494, 6), (494, 36), 1)

        # 3. Draw View Mode Selector
        view_lbl = self.small_font.render("VIEW:", True, (140, 155, 175))
        panel.blit(view_lbl, (278, 14))

        draw_btn("view_side", "2.5D", is_active=(current_view == ViewMode.SIDE_VIEW), active_color=(185, 125, 45))
        draw_btn("view_top", "TOP", is_active=(current_view == ViewMode.TOP_DOWN), active_color=(185, 125, 45))
        draw_btn("view_shapes", "SHAPES", is_active=(current_view == ViewMode.SHAPES), active_color=(185, 125, 45))

        # 4. Draw Overlay HUD Toggles
        draw_btn("chart", "CHART [C]", is_active=chart_visible, active_color=(50, 120, 175))
        draw_btn("biomes", "BIOMES [B]", is_active=biomes_visible, active_color=(60, 130, 85))

        # 5. Row 2: Quick-Spawn Palette
        spawn_lbl = self.small_font.render("SPAWN:", True, (140, 155, 175))
        panel.blit(spawn_lbl, (14, 47))

        draw_btn("spawn_rabbit", "+ Rabbit", accent_border=self.species_colors["rabbit"], font=self.small_font)
        draw_btn("spawn_deer", "+ Deer", accent_border=self.species_colors["deer"], font=self.small_font)
        draw_btn("spawn_goat", "+ Goat", accent_border=self.species_colors["goat"], font=self.small_font)
        draw_btn("spawn_fox", "+ Fox", accent_border=self.species_colors["fox"], font=self.small_font)
        draw_btn("spawn_wolf", "+ Wolf", accent_border=self.species_colors["wolf"], font=self.small_font)
        draw_btn("spawn_bear", "+ Bear", accent_border=self.species_colors["bear"], font=self.small_font)

        # 6. Notification or Hint Badge
        if self.notification_text:
            notif_surf = self.small_font.render(self.notification_text, True, (255, 220, 100))
            panel.blit(notif_surf, (514, 47))
        else:
            hint_surf = self.label_font.render("[Click] to spawn at camera", True, (110, 125, 145))
            panel.blit(hint_surf, (514, 47))

        surface.blit(panel, (self.x, self.y))
