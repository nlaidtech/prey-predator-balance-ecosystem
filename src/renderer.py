"""Multi-species wildlife renderer with 5 textured biomes.

Draws territorial landscape, animated sprites for all 6 wildlife species
(Wolf, Rabbit, Deer, Mountain Goat, Bear, Fox), dynamic corpses, and population HUD.
Strictly read-only visualization layer.
"""

from __future__ import annotations
import math
import os
from enum import Enum
from typing import Dict, List, Optional, Tuple
import pygame

from src.config import Config
from src.entities import Animal, AnimalState
from src.simulation import Simulation
from src.species import SPECIES_REGISTRY, SpeciesProfile
from src.terrain import BiomeType, TerrainMap, TerrainZone


class ViewMode(str, Enum):
    SIDE_VIEW = "Side-View (Animated)"
    TOP_DOWN = "Top-Down (360° Directional)"
    SHAPES = "Plain Shapes & Vision Radii"


class SpeciesSpriteSet:
    """Manages cached animation strips and directional frames for a single species."""

    def __init__(self, species_name: str, target_scale: float = 0.5) -> None:
        self.species_name = species_name
        self.target_scale = target_scale
        self.anims: Dict[str, List[pygame.Surface]] = {}
        self.top_view_frames: List[pygame.Surface] = []
        self._load_sprites()

    def _load_sprites(self) -> None:
        base_dir = os.path.join("assets", "sprites", self.species_name)
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


class SpriteCache:
    """Central cache holding animated surfaces for all 6 wildlife species."""

    def __init__(self) -> None:
        self.species: Dict[str, SpeciesSpriteSet] = {}
        for sp_name, profile in SPECIES_REGISTRY.items():
            self.species[sp_name] = SpeciesSpriteSet(sp_name, target_scale=profile.scale)


class Renderer:
    """Renders the complete living wildlife ecosystem."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.view_mode = ViewMode.SIDE_VIEW
        self.sprite_cache = SpriteCache()

        # Entity visual clocks (id -> (timer, frame_idx))
        self.anim_states: Dict[int, Tuple[float, int]] = {}
        self.corpses: List[Dict] = []

        # Species Colors for Shapes View
        self.shape_colors = {
            "rabbit": (120, 220, 140),
            "deer": (210, 160, 90),
            "goat": (230, 230, 240),
            "fox": (245, 125, 45),
            "wolf": (170, 70, 60),
            "bear": (120, 65, 40),
        }

        # Biome Base Colors
        self.biome_colors = {
            BiomeType.HIGHLANDS: (78, 86, 98),       # Slate Mountain Rock
            BiomeType.DENSE_FOREST: (24, 46, 32),    # Deep Pine Woodland
            BiomeType.RIVER: (35, 92, 150),          # Winding Freshwater River
            BiomeType.THICKETS: (75, 68, 44),        # Thorny Brush & Briars
            BiomeType.MEADOW: (42, 108, 58),         # Lush Grassland Plains
        }

        # Fonts
        pygame.font.init()
        self.font = pygame.font.SysFont("consolas", 14, bold=True)
        self.badge_font = pygame.font.SysFont("consolas", 12, bold=True)

    def cycle_view_mode(self) -> None:
        modes = [ViewMode.SIDE_VIEW, ViewMode.TOP_DOWN, ViewMode.SHAPES]
        curr_idx = modes.index(self.view_mode)
        self.view_mode = modes[(curr_idx + 1) % len(modes)]

    def draw(self, surface: pygame.Surface, sim: Simulation, dt: float, paused: bool, fps: float) -> None:
        # Ingest recent deaths
        if hasattr(sim, "recent_deaths") and sim.recent_deaths:
            for death in sim.recent_deaths:
                self.corpses.append({
                    "species": death.species,
                    "x": death.x,
                    "y": death.y,
                    "heading": death.heading,
                    "timer": 0.0,
                    "cause": death.cause,
                })

        # 1. Draw 5 Territorial Biomes
        self._draw_terrain(surface, sim.terrain)

        # 2. Draw Dying Corpses on Ground
        self._draw_corpses(surface, dt)

        # 3. Draw All Wildlife Animals
        self._draw_animals(surface, sim, dt)

        # 4. Draw Comprehensive HUD
        self._draw_hud(surface, sim, paused, fps)

    def _draw_terrain(self, surface: pygame.Surface, terrain: TerrainMap) -> None:
        """Draws the 5 distinct geographic zones with subtle textures and borders."""
        # Draw base zone rectangles
        for zone in terrain.zones:
            col = self.biome_colors[zone.biome_type]
            rect = pygame.Rect(
                int(zone.min_x), int(zone.min_y),
                int(zone.max_x - zone.min_x), int(zone.max_y - zone.min_y)
            )
            pygame.draw.rect(surface, col, rect)

            # Zone subtle border
            pygame.draw.rect(surface, (20, 24, 30), rect, 1)

            # Zone label watermark
            lbl_surf = self.badge_font.render(zone.biome_type.value.upper(), True, (240, 240, 240))
            lbl_surf.set_alpha(65)
            surface.blit(lbl_surf, (int(zone.min_x + 14), int(zone.min_y + 12)))

        # Draw water ripple line on River (Zone 3)
        water_zone = terrain.zones[2]
        mid_y = int((water_zone.min_y + water_zone.max_y) * 0.5)
        pygame.draw.line(surface, (60, 130, 195), (0, mid_y), (int(terrain.width), mid_y), 2)

    def _draw_corpses(self, surface: pygame.Surface, dt: float) -> None:
        surviving = []
        for corpse in self.corpses:
            corpse["timer"] += dt
            if corpse["timer"] >= 1.5:
                continue
            surviving.append(corpse)

            sp_name = corpse["species"]
            sp_set = self.sprite_cache.species.get(sp_name)
            if not sp_set or not sp_set.anims.get("die"):
                continue

            frames = sp_set.anims["die"]
            frame_idx = min(len(frames) - 1, int(corpse["timer"] / 0.12))
            frame = frames[frame_idx]

            if math.cos(corpse["heading"]) < 0:
                frame = pygame.transform.flip(frame, True, False)

            # Alpha fade
            if corpse["timer"] > 1.0:
                alpha = int(255 * max(0.0, (1.5 - corpse["timer"]) / 0.5))
                frame = frame.copy()
                frame.set_alpha(alpha)

            rect = frame.get_rect(center=(int(corpse["x"]), int(corpse["y"])))
            surface.blit(frame, rect)

        self.corpses = surviving

    def _draw_animals(self, surface: pygame.Surface, sim: Simulation, dt: float) -> None:
        active_ids = set()

        # Sort animals by Y coordinate for natural 2.5D depth sorting (draw top-to-bottom)
        sorted_animals = sorted(sim.animals, key=lambda a: a.y)

        for animal in sorted_animals:
            if not animal.alive:
                continue
            active_ids.add(animal.entity_id)
            px, py = int(animal.x), int(animal.y)

            # Stalking focus line for chasing predators
            if animal.state == AnimalState.CHASE and animal.target_prey_id:
                quarry = next((q for q in sim.animals if q.entity_id == animal.target_prey_id and q.alive), None)
                if quarry:
                    pygame.draw.line(surface, (230, 60, 50), (px, py), (int(quarry.x), int(quarry.y)), 1)

            if self.view_mode == ViewMode.SHAPES:
                self._draw_animal_shape(surface, animal, px, py)
            elif self.view_mode == ViewMode.TOP_DOWN:
                self._draw_animal_top_down(surface, animal, dt, px, py)
            else:
                self._draw_animal_animated(surface, animal, dt, px, py)

        # Cleanup stale anim states
        stale = [eid for eid in self.anim_states if eid not in active_ids]
        for eid in stale:
            del self.anim_states[eid]

    def _draw_animal_shape(self, surface: pygame.Surface, animal: Animal, px: int, py: int) -> None:
        col = self.shape_colors.get(animal.profile.name, (200, 200, 200))
        radius = int(8 * animal.profile.scale * 2.0)
        pygame.draw.circle(surface, col, (px, py), radius)
        # Heading line
        hx = px + int(math.cos(animal.heading) * (radius + 6))
        hy = py + int(math.sin(animal.heading) * (radius + 6))
        pygame.draw.line(surface, (255, 255, 255), (px, py), (hx, hy), 2)

    def _draw_animal_animated(self, surface: pygame.Surface, animal: Animal, dt: float, px: int, py: int) -> None:
        sp_name = animal.profile.name
        sp_set = self.sprite_cache.species.get(sp_name)
        if not sp_set:
            self._draw_animal_shape(surface, animal, px, py)
            return

        # Determine animation cycle
        anim_key = "walk"
        frame_rate = 8.0

        if animal.state in [AnimalState.CHASE, AnimalState.FLEE]:
            anim_key = "run"
            frame_rate = 14.0
        elif animal.state == AnimalState.EAT:
            anim_key = "attack"
            frame_rate = 12.0
        elif animal.state == AnimalState.DRINK:
            anim_key = "idle"
            frame_rate = 4.0
        elif animal.speed < 5.0:
            anim_key = "idle"
            frame_rate = 4.0

        frames = sp_set.anims.get(anim_key, sp_set.anims.get("walk", []))
        if not frames:
            self._draw_animal_shape(surface, animal, px, py)
            return

        # Advance local animation clock
        timer, idx = self.anim_states.get(animal.entity_id, (0.0, 0))
        timer += dt
        duration = 1.0 / frame_rate
        if timer >= duration:
            timer -= duration
            idx = (idx + 1) % len(frames)
        self.anim_states[animal.entity_id] = (timer, idx)

        frame = frames[idx % len(frames)]

        # Horizontal facing
        if math.cos(animal.heading) < 0:
            frame = pygame.transform.flip(frame, True, False)

        rect = frame.get_rect(center=(px, py))
        surface.blit(frame, rect)

        # Health/Energy bar for carnivores and apex beasts
        if animal.profile.diet_prey:
            self._draw_energy_bar(surface, animal, px, rect.top - 5)

    def _draw_animal_top_down(self, surface: pygame.Surface, animal: Animal, dt: float, px: int, py: int) -> None:
        sp_set = self.sprite_cache.species.get(animal.profile.name)
        if not sp_set or not sp_set.top_view_frames:
            self._draw_animal_animated(surface, animal, dt, px, py)
            return

        top_frames = sp_set.top_view_frames
        timer, idx = self.anim_states.get(animal.entity_id, (0.0, 0))
        timer += dt
        if timer >= 0.12:
            timer -= 0.12
            idx = (idx + 1) % len(top_frames)
        self.anim_states[animal.entity_id] = (timer, idx)

        base_frame = top_frames[idx % len(top_frames)]
        angle_deg = -math.degrees(animal.heading) - 90.0
        rotated = pygame.transform.rotate(base_frame, angle_deg)
        rect = rotated.get_rect(center=(px, py))
        surface.blit(rotated, rect)

    def _draw_energy_bar(self, surface: pygame.Surface, animal: Animal, center_x: int, top_y: int) -> None:
        w, h = 24, 3
        x = center_x - w // 2
        ratio = max(0.0, min(1.0, animal.energy / animal.profile.max_energy))
        col = (int(255 * (1.0 - ratio)), int(230 * ratio), 50)
        pygame.draw.rect(surface, (15, 18, 22), (x - 1, top_y - 1, w + 2, h + 2))
        pygame.draw.rect(surface, col, (x, top_y, int(w * ratio), h))

    def _draw_hud(self, surface: pygame.Surface, sim: Simulation, paused: bool, fps: float) -> None:
        # Count species
        counts: Dict[str, int] = {}
        for a in sim.animals:
            if a.alive:
                counts[a.profile.name] = counts.get(a.profile.name, 0) + 1

        hud_w, hud_h = 620, 115
        hud_surf = pygame.Surface((hud_w, hud_h), pygame.SRCALPHA)
        pygame.draw.rect(hud_surf, (16, 20, 26, 225), (0, 0, hud_w, hud_h), border_radius=8)
        pygame.draw.rect(hud_surf, (55, 68, 85), (0, 0, hud_w, hud_h), 1, border_radius=8)

        line1 = f"WILDLIFE ECOSYSTEM SIMULATION  |  Time: {sim.time:5.1f}s  |  FPS: {fps:4.1f}"
        line2 = (
            f"🐇 Rabbits:{counts.get('rabbit', 0):3d}  "
            f"🦌 Deer:{counts.get('deer', 0):2d}  "
            f"🐐 Goats:{counts.get('goat', 0):2d}  "
            f"🦊 Foxes:{counts.get('fox', 0):2d}  "
            f"🐺 Wolves:{counts.get('wolf', 0):2d}  "
            f"🐻 Bears:{counts.get('bear', 0):2d}"
        )
        line3 = f"View: {self.view_mode.value}  |  Biomes: 5 Territorial Zones"
        line4 = f"Status: {'PAUSED' if paused else 'RUNNING'}  [Space: Pause | R: Reset | V: Toggle View]"

        for i, (text, col) in enumerate([
            (line1, (245, 245, 245)),
            (line2, (110, 230, 140)),
            (line3, (255, 200, 80)),
            (line4, (165, 180, 195)),
        ]):
            txt_surf = self.font.render(text, True, col)
            hud_surf.blit(txt_surf, (14, 10 + i * 23))

        surface.blit(hud_surf, (16, 16))
