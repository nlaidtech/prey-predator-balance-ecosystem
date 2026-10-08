"""Simulation renderer for the predator-prey ecosystem.

Decoupled visualization layer that strictly reads simulation state without
influencing rules or logic.
Supports multiple view modes:
- Side-View 2.5D: Animated walk, run, attack, and die sprites with horizontal facing.
- Top-Down: 360° rotated directional sprites.
- Shapes: Debug geometric view showing vision and catch ranges.
"""

from __future__ import annotations
import math
import os
from enum import Enum
from typing import Dict, List, Optional, Tuple
import pygame

from src.config import Config
from src.entities import AnimalState, Predator, Prey
from src.simulation import Simulation


class ViewMode(str, Enum):
    SIDE_VIEW = "Side-View (Animated)"
    TOP_DOWN = "Top-Down (360° Directional)"
    SHAPES = "Plain Shapes & Vision Radii"


class SpriteCache:
    """Loads and caches shared animation frames in memory once."""

    def __init__(self, target_scale: float = 0.5) -> None:
        self.target_scale = target_scale
        self.anims: Dict[str, List[pygame.Surface]] = {}
        self.top_view_frames: List[pygame.Surface] = []
        self._load_sprites()

    def _load_sprites(self) -> None:
        base_dir = os.path.join("assets", "sprites", "wolf")
        if not os.path.exists(base_dir):
            return

        for anim_name in ["idle", "walk", "run", "attack", "hurt", "die"]:
            anim_dir = os.path.join(base_dir, anim_name)
            if not os.path.isdir(anim_dir):
                continue
            frames = []
            files = sorted(os.listdir(anim_dir))
            for f in files:
                if f.endswith(".png"):
                    surf = pygame.image.load(os.path.join(anim_dir, f))
                    try:
                        surf = surf.convert_alpha()
                    except pygame.error:
                        pass
                    if self.target_scale != 1.0:
                        nw = max(1, int(surf.get_width() * self.target_scale))
                        nh = max(1, int(surf.get_height() * self.target_scale))
                        surf = pygame.transform.smoothscale(surf, (nw, nh))
                    frames.append(surf)
            if frames:
                self.anims[anim_name] = frames

        # Load top view frames
        top_dir = os.path.join(base_dir, "top_view")
        if os.path.isdir(top_dir):
            for f in sorted(os.listdir(top_dir)):
                if f.endswith(".png"):
                    surf = pygame.image.load(os.path.join(top_dir, f))
                    try:
                        surf = surf.convert_alpha()
                    except pygame.error:
                        pass
                    if self.target_scale != 1.0:
                        nw = max(1, int(surf.get_width() * self.target_scale))
                        nh = max(1, int(surf.get_height() * self.target_scale))
                        surf = pygame.transform.smoothscale(surf, (nw, nh))
                    self.top_view_frames.append(surf)


class Renderer:
    """Renders the ecosystem simulation state to a pygame surface."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.view_mode = ViewMode.SIDE_VIEW
        self.sprite_cache = SpriteCache(target_scale=0.55)

        # Entity visual clocks (id -> (timer, frame_idx))
        self.predator_anim_states: Dict[int, Tuple[float, int]] = {}

        # Colors
        self.bg_color = (24, 28, 36)
        self.prey_color = (95, 215, 120)
        self.prey_outline = (50, 160, 80)
        self.pred_shape_color = (235, 75, 60)
        self.vision_circle_prey = (70, 190, 100, 25)
        self.vision_circle_pred = (230, 80, 70, 30)

        # Pre-initialize font
        pygame.font.init()
        self.font = pygame.font.SysFont("consolas", 15, bold=True)
        self.title_font = pygame.font.SysFont("consolas", 18, bold=True)

    def cycle_view_mode(self) -> None:
        """Cycles through available visualization modes."""
        modes = [ViewMode.SIDE_VIEW, ViewMode.TOP_DOWN, ViewMode.SHAPES]
        curr_idx = modes.index(self.view_mode)
        self.view_mode = modes[(curr_idx + 1) % len(modes)]

    def draw(self, surface: pygame.Surface, sim: Simulation, dt: float, paused: bool, fps: float) -> None:
        """Draws the complete scene for the given simulation state."""
        surface.fill(self.bg_color)

        # Draw grid backdrop for subtle spatial reference
        self._draw_grid_backdrop(surface)

        # Draw Rabbits (Prey)
        self._draw_prey(surface, sim)

        # Draw Wolves (Predators)
        self._draw_predators(surface, sim, dt)

        # Draw HUD & Metrics
        self._draw_hud(surface, sim, paused, fps)

    def _draw_grid_backdrop(self, surface: pygame.Surface) -> None:
        cell_size = 80
        w, h = int(self.config.world_width), int(self.config.world_height)
        line_color = (32, 38, 48)
        for x in range(0, w, cell_size):
            pygame.draw.line(surface, line_color, (x, 0), (x, h))
        for y in range(0, h, cell_size):
            pygame.draw.line(surface, line_color, (0, y), (w, y))

    def _draw_prey(self, surface: pygame.Surface, sim: Simulation) -> None:
        for prey in sim.prey_list:
            if not prey.alive:
                continue
            px, py = int(prey.x), int(prey.y)

            # Vision radius in Shapes mode
            if self.view_mode == ViewMode.SHAPES:
                vision_surf = pygame.Surface(
                    (int(self.config.prey_vision_radius * 2), int(self.config.prey_vision_radius * 2)),
                    pygame.SRCALPHA,
                )
                pygame.draw.circle(
                    vision_surf,
                    (70, 190, 100, 18),
                    (int(self.config.prey_vision_radius), int(self.config.prey_vision_radius)),
                    int(self.config.prey_vision_radius),
                )
                surface.blit(
                    vision_surf,
                    (px - int(self.config.prey_vision_radius), py - int(self.config.prey_vision_radius)),
                )

            # Draw rabbit as stylized glyph (body + ears facing heading)
            body_radius = 5
            pygame.draw.circle(surface, self.prey_color, (px, py), body_radius)
            pygame.draw.circle(surface, self.prey_outline, (px, py), body_radius, 1)

            # Heading indicator (ears / nose direction)
            hx = px + int(math.cos(prey.heading) * 8)
            hy = py + int(math.sin(prey.heading) * 8)
            pygame.draw.line(surface, (255, 255, 255), (px, py), (hx, hy), 2)

    def _draw_predators(self, surface: pygame.Surface, sim: Simulation, dt: float) -> None:
        active_ids = set()

        for pred in sim.predator_list:
            if not pred.alive:
                continue
            active_ids.add(pred.entity_id)
            px, py = int(pred.x), int(pred.y)

            if self.view_mode == ViewMode.SHAPES:
                self._draw_predator_shape(surface, pred, px, py)
            elif self.view_mode == ViewMode.TOP_DOWN:
                self._draw_predator_top_down(surface, pred, dt, px, py)
            else:
                self._draw_predator_animated_side(surface, pred, dt, px, py)

        # Clean up stale animation state entries
        stale = [eid for eid in self.predator_anim_states if eid not in active_ids]
        for eid in stale:
            del self.predator_anim_states[eid]

    def _draw_predator_shape(self, surface: pygame.Surface, pred: Predator, px: int, py: int) -> None:
        # Vision circle
        vision_surf = pygame.Surface(
            (int(self.config.predator_vision_radius * 2), int(self.config.predator_vision_radius * 2)),
            pygame.SRCALPHA,
        )
        pygame.draw.circle(
            vision_surf,
            (230, 80, 70, 22),
            (int(self.config.predator_vision_radius), int(self.config.predator_vision_radius)),
            int(self.config.predator_vision_radius),
        )
        surface.blit(
            vision_surf,
            (px - int(self.config.predator_vision_radius), py - int(self.config.predator_vision_radius)),
        )

        # Body
        body_radius = 8
        pygame.draw.circle(surface, self.pred_shape_color, (px, py), body_radius)
        # Heading line
        hx = px + int(math.cos(pred.heading) * 12)
        hy = py + int(math.sin(pred.heading) * 12)
        pygame.draw.line(surface, (255, 210, 120), (px, py), (hx, hy), 2)

    def _draw_predator_animated_side(
        self, surface: pygame.Surface, pred: Predator, dt: float, px: int, py: int
    ) -> None:
        # Determine animation strip based on behavioral state
        anim_key = "walk"
        frame_rate = 8.0  # FPS

        if pred.state == AnimalState.CHASE:
            anim_key = "run"
            frame_rate = 12.0
        elif pred.state == AnimalState.EAT:
            anim_key = "attack"
            frame_rate = 14.0
        elif pred.state == AnimalState.DIE:
            anim_key = "die"
            frame_rate = 6.0
        elif pred.speed < 5.0:
            anim_key = "idle"
            frame_rate = 4.0

        frames = self.sprite_cache.anims.get(anim_key, self.sprite_cache.anims.get("walk", []))
        if not frames:
            # Fallback to circle if sprite not found
            self._draw_predator_shape(surface, pred, px, py)
            return

        # Advance local animation clock
        timer, idx = self.predator_anim_states.get(pred.entity_id, (0.0, 0))
        timer += dt
        frame_duration = 1.0 / frame_rate
        if timer >= frame_duration:
            timer -= frame_duration
            idx = (idx + 1) % len(frames)
        self.predator_anim_states[pred.entity_id] = (timer, idx)

        frame = frames[idx % len(frames)]

        # Facing direction (Wolf default faces right)
        face_left = math.cos(pred.heading) < 0
        if face_left:
            frame = pygame.transform.flip(frame, True, False)

        # Center and blit
        rect = frame.get_rect(center=(px, py))
        surface.blit(frame, rect)

        # Energy bar indicator above wolf
        self._draw_energy_bar(surface, pred, px, rect.top - 6)

    def _draw_predator_top_down(
        self, surface: pygame.Surface, pred: Predator, dt: float, px: int, py: int
    ) -> None:
        top_frames = self.sprite_cache.top_view_frames
        if not top_frames:
            self._draw_predator_animated_side(surface, pred, dt, px, py)
            return

        # Animate top-down walk cycle
        timer, idx = self.predator_anim_states.get(pred.entity_id, (0.0, 0))
        timer += dt
        if timer >= 0.12:
            timer -= 0.12
            idx = (idx + 1) % len(top_frames)
        self.predator_anim_states[pred.entity_id] = (timer, idx)

        base_frame = top_frames[idx % len(top_frames)]

        # Rotate according to heading (sprite points up by default: -90 deg offset)
        angle_deg = -math.degrees(pred.heading) - 90.0
        rotated_frame = pygame.transform.rotate(base_frame, angle_deg)
        rect = rotated_frame.get_rect(center=(px, py))
        surface.blit(rotated_frame, rect)

        # Energy bar indicator above wolf
        self._draw_energy_bar(surface, pred, px, rect.top - 6)

    def _draw_energy_bar(self, surface: pygame.Surface, pred: Predator, center_x: int, top_y: int) -> None:
        bar_w = 24
        bar_h = 3
        x = center_x - bar_w // 2
        y = top_y

        fill_ratio = max(0.0, min(1.0, pred.energy / self.config.predator_max_energy))
        # Green to red color ramp based on hunger
        color = (
            int(255 * (1.0 - fill_ratio)),
            int(230 * fill_ratio),
            50
        )
        pygame.draw.rect(surface, (15, 18, 22), (x - 1, y - 1, bar_w + 2, bar_h + 2))
        pygame.draw.rect(surface, color, (x, y, int(bar_w * fill_ratio), bar_h))

    def _draw_hud(self, surface: pygame.Surface, sim: Simulation, paused: bool, fps: float) -> None:
        # HUD Panel background
        hud_w, hud_h = 480, 110
        hud_surf = pygame.Surface((hud_w, hud_h), pygame.SRCALPHA)
        pygame.draw.rect(hud_surf, (18, 22, 28, 210), (0, 0, hud_w, hud_h), border_radius=8)
        pygame.draw.rect(hud_surf, (60, 72, 88), (0, 0, hud_w, hud_h), 1, border_radius=8)

        # Text elements
        lines = [
            f"PREDATOR–PREY ECOSYSTEM  |  Time: {sim.time:5.1f}s  |  FPS: {fps:4.1f}",
            f"Rabbits (Prey): {sim.prey_count:3d}   |  Foxes (Wolf): {sim.predator_count:3d}",
            f"View Mode: {self.view_mode.value}",
            f"Status: {'PAUSED' if paused else 'RUNNING'}  [Space: Pause | R: Reset | V: Toggle View]",
        ]

        colors = [
            (245, 245, 245),
            (110, 230, 130),
            (255, 200, 80),
            (170, 180, 195),
        ]

        for i, (text, col) in enumerate(zip(lines, colors)):
            surf = self.font.render(text, True, col)
            hud_surf.blit(surf, (14, 12 + i * 22))

        surface.blit(hud_surf, (16, 16))
