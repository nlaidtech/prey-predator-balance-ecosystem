"""In-Engine Real-Time Population Dynamics Chart HUD (Key 'C').

Renders multi-line anti-aliased population curves for all 6 individual species
over a rolling 90–120s buffer, live trends (rising, declining, stable),
and real-time ecological equilibrium indicators.
"""

from __future__ import annotations
import math
from typing import Dict, List, Optional, Tuple
import pygame

from src.metrics import DetailedSpeciesSnapshot, SimulationMetrics
from src.simulation import Simulation


class PopulationChartHUD:
    """Semi-transparent in-engine graph overlay showing live population waves."""

    def __init__(self, width: int = 600, height: int = 230) -> None:
        self.width = width
        self.height = height
        self.visible: bool = False

        # Species curve colors
        self.species_colors: Dict[str, Tuple[int, int, int]] = {
            "rabbit": (110, 230, 140),  # Bright Green
            "deer": (70, 200, 120),    # Emerald
            "goat": (60, 215, 215),    # Cyan/Teal
            "fox": (250, 150, 50),     # Orange
            "wolf": (240, 70, 65),     # Crimson
            "bear": (180, 80, 55),     # Dark Red/Brown
        }

        # Species display labels
        self.species_labels: Dict[str, str] = {
            "rabbit": "Rabbit",
            "deer": "Deer",
            "goat": "Goat",
            "fox": "Fox",
            "wolf": "Wolf",
            "bear": "Bear",
        }

        # Fonts
        pygame.font.init()
        self.title_font = pygame.font.SysFont("consolas", 12, bold=True)
        self.body_font = pygame.font.SysFont("consolas", 11, bold=True)
        self.small_font = pygame.font.SysFont("consolas", 10)

    def toggle(self) -> None:
        """Toggles graph overlay visibility."""
        self.visible = not self.visible

    def get_rect(self, screen_width: int, screen_height: int) -> pygame.Rect:
        """Computes on-screen rectangle anchored at bottom-left."""
        return pygame.Rect(16, screen_height - self.height - 16, self.width, self.height)

    def handle_click(self, sx: int, sy: int, screen_width: int, screen_height: int) -> bool:
        """Handles mouse click on the chart HUD. Returns True if consumed."""
        if not self.visible:
            return False

        rect = self.get_rect(screen_width, screen_height)
        if not rect.collidepoint(sx, sy):
            return False

        # Close button in top-right of panel
        close_btn = pygame.Rect(rect.right - 24, rect.y + 6, 18, 18)
        if close_btn.collidepoint(sx, sy):
            self.visible = False
            return True

        return True  # Click consumed by chart body

    def draw(self, surface: pygame.Surface, sim: Simulation, screen_width: int, screen_height: int) -> None:
        """Renders the population graph overlay."""
        if not self.visible:
            return

        panel_rect = self.get_rect(screen_width, screen_height)
        panel = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # 1. Panel Background
        pygame.draw.rect(panel, (14, 18, 25, 235), (0, 0, self.width, self.height), border_radius=8)
        pygame.draw.rect(panel, (60, 75, 100, 240), (0, 0, self.width, self.height), 1, border_radius=8)

        # 2. Header
        title_surf = self.title_font.render("POPULATION DYNAMICS (Key 'C')", True, (240, 245, 255))
        panel.blit(title_surf, (14, 10))

        # Close button [X]
        pygame.draw.rect(panel, (40, 50, 68), (self.width - 24, 7, 16, 16), border_radius=3)
        x_surf = self.small_font.render("x", True, (210, 220, 230))
        panel.blit(x_surf, (self.width - 19, 8))

        # Equilibrium status badge
        is_stable, status_str = sim.metrics.get_equilibrium_status()
        b_col = (45, 150, 85) if is_stable else (210, 65, 55)
        status_surf = self.small_font.render(status_str, True, (255, 255, 255))
        badge_rect = pygame.Rect(250, 9, status_surf.get_width() + 14, 18)
        pygame.draw.rect(panel, (*b_col, 220), badge_rect, border_radius=4)
        panel.blit(status_surf, (badge_rect.x + 7, badge_rect.y + 3))

        # 3. Graph Plot Area
        plot_x = 42
        plot_y = 36
        plot_w = 385
        plot_h = 160
        plot_rect = pygame.Rect(plot_x, plot_y, plot_w, plot_h)
        pygame.draw.rect(panel, (18, 23, 32), plot_rect)
        pygame.draw.rect(panel, (45, 58, 75), plot_rect, 1)

        history = sim.metrics.detailed_history
        if not history:
            surface.blit(panel, panel_rect.topleft)
            return

        # Determine scaling ranges
        all_counts: List[int] = []
        for snap in history:
            all_counts.extend(snap.counts.values())
        max_pop = max(10, max(all_counts) if all_counts else 10)
        # Round up to clean scale
        scale_max = int(math.ceil(max_pop / 25.0) * 25)

        t_min = history[0].time
        t_max = max(t_min + 1.0, history[-1].time)
        t_span = max(1.0, t_max - t_min)

        # Draw grid lines & Y-axis labels
        for frac in [0.0, 0.25, 0.5, 0.75, 1.0]:
            gy = int(plot_y + plot_h - frac * plot_h)
            pygame.draw.line(panel, (30, 40, 52), (plot_x, gy), (plot_x + plot_w, gy), 1)
            val_lbl = self.small_font.render(f"{int(frac * scale_max):3d}", True, (130, 145, 165))
            panel.blit(val_lbl, (plot_x - 30, gy - 6))

        # Time labels
        panel.blit(self.small_font.render(f"-{int(t_span)}s", True, (130, 145, 165)), (plot_x, plot_y + plot_h + 4))
        panel.blit(self.small_font.render("Now", True, (130, 145, 165)), (plot_x + plot_w - 22, plot_y + plot_h + 4))

        # 4. Plot Curves for Each Species
        for sp_name, col in self.species_colors.items():
            pts: List[Tuple[int, int]] = []
            for snap in history:
                val = snap.counts.get(sp_name, 0)
                px = plot_x + int(((snap.time - t_min) / t_span) * plot_w)
                py = plot_y + plot_h - int((val / float(scale_max)) * plot_h)
                py = max(plot_y, min(plot_y + plot_h, py))
                pts.append((px, py))

            if len(pts) >= 2:
                pygame.draw.lines(panel, col, False, pts, 2)
                # Latest point dot
                pygame.draw.circle(panel, col, pts[-1], 3)

        # 5. Legend & Trends Sidebar (Right column)
        leg_x = plot_x + plot_w + 14
        leg_y = 36
        row_h = 28

        for i, (sp_name, col) in enumerate(self.species_colors.items()):
            cur_y = leg_y + i * row_h
            # Color swatch circle
            pygame.draw.circle(panel, col, (leg_x + 6, cur_y + 8), 5)

            # Name and current count
            curr_count = history[-1].counts.get(sp_name, 0)
            label_text = f"{self.species_labels[sp_name]}: {curr_count}"
            lbl_surf = self.body_font.render(label_text, True, (230, 235, 245))
            panel.blit(lbl_surf, (leg_x + 16, cur_y + 2))

            # Trend badge
            trend_str, delta = sim.metrics.get_species_trend(sp_name, window_seconds=15.0)
            if trend_str == "rising":
                t_badge = f"+{delta} ^"
                t_col = (110, 230, 140)
            elif trend_str == "declining":
                t_badge = f"{delta} v"
                t_col = (245, 85, 80)
            else:
                t_badge = "= 0"
                t_col = (150, 165, 180)

            t_surf = self.small_font.render(t_badge, True, t_col)
            panel.blit(t_surf, (leg_x + 105, cur_y + 3))

        surface.blit(panel, panel_rect.topleft)
