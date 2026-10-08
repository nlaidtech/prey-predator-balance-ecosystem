"""Multi-species wildlife renderer with textured biomes, natural props, Camera2D, and Animal Inspector.

Draws territorial landscape with sliced pixel-art terrain tiles, deterministic props
(trees, boulders, bushes, flowers, logs), animated sprites for all 6 wildlife species
(Wolf, Rabbit, Deer, Mountain Goat, Bear, Fox), dynamic corpses, selection reticle,
slide-out Animal Inspector Card, interactive radar minimap, and population HUD.
Strictly read-only visualization layer.
"""

from __future__ import annotations
import math
import os
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union
import pygame

from src.activity_feed import ActivityFeedHUD
from src.camera import Camera2D
from src.chart import PopulationChartHUD
from src.config import Config, ViewMode
from src.entities import Animal, AnimalState
from src.inspector import InspectorCard
from src.minimap import Minimap
from src.simulation import Simulation
from src.species import SPECIES_REGISTRY, SpeciesProfile
from src.terrain import BiomeType, ScenicArea, TerrainMap, TerrainProp, TerrainZone
from src.toolbar import ToolbarHUD


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


class TerrainSpriteCache:
    """Loads and caches sliced biome ground tiles, landmarks, and decorative landscape props."""

    def __init__(self) -> None:
        self.ground_tiles: Dict[BiomeType, pygame.Surface] = {}
        self.landmarks: Dict[str, pygame.Surface] = {}
        self.props: Dict[str, pygame.Surface] = {}
        self._load_terrain_assets()

    def _load_terrain_assets(self) -> None:
        base_dir = os.path.join("assets", "terrain")
        if not os.path.isdir(base_dir):
            return

        # 1. Ground tiles
        ground_map = {
            BiomeType.MEADOW: os.path.join(base_dir, "meadow", "ground_lush.png"),
            BiomeType.DENSE_FOREST: os.path.join(base_dir, "forest", "ground_moss.png"),
            BiomeType.HIGHLANDS: os.path.join(base_dir, "highlands", "ground_rock.png"),
            BiomeType.THICKETS: os.path.join(base_dir, "thickets", "ground_roots.png"),
            BiomeType.RIVER: os.path.join(base_dir, "river", "water_stream.png"),
        }
        for b_type, p in ground_map.items():
            if os.path.isfile(p):
                try:
                    surf = pygame.image.load(p)
                    self.ground_tiles[b_type] = surf
                except pygame.error:
                    pass

        # 2. Landmarks & Props
        for sub in ["meadow", "forest", "highlands", "thickets", "river"]:
            s_dir = os.path.join(base_dir, sub)
            if not os.path.isdir(s_dir):
                continue
            for fname in os.listdir(s_dir):
                if not fname.endswith(".png"):
                    continue
                name_key = os.path.splitext(fname)[0]
                p = os.path.join(s_dir, fname)
                try:
                    surf = pygame.image.load(p)
                    if fname.startswith("landmark_"):
                        self.landmarks[name_key] = surf
                    elif fname.startswith("prop_"):
                        self.props[name_key] = surf
                except pygame.error:
                    pass


class Renderer:
    """Renders the complete living wildlife ecosystem with textured terrain, smooth camera, and minimap."""

    def __init__(self, config: Config, camera: Optional[Camera2D] = None) -> None:
        self.config = config
        self.view_mode = ViewMode.SIDE_VIEW
        self.sprite_cache = SpriteCache()
        self.terrain_cache = TerrainSpriteCache()

        # Initialize or accept Camera2D
        scr_w = getattr(config, "screen_width", int(config.world_width))
        scr_h = getattr(config, "screen_height", int(config.world_height))
        if camera is not None:
            self.camera = camera
        else:
            self.camera = Camera2D(
                screen_width=scr_w,
                screen_height=scr_h,
                world_width=config.world_width,
                world_height=config.world_height,
            )

        # Interactive corner radar minimap
        self.minimap = Minimap(width=220, height=140, margin=16)

        # Animal Inspector Card
        self.inspector = InspectorCard(width=310, height=370)

        # Real-time Population Chart HUD (Key 'C')
        self.chart = PopulationChartHUD(width=600, height=230)

        # Interactive Desktop Toolbar HUD (Phase 4)
        self.toolbar = ToolbarHUD(x=16, y=142, width=700, height=76)

        # Live Activity Feed Ticker (Phase 5)
        self.activity_feed = ActivityFeedHUD(width=370, max_display_items=5)

        # Biome watermarks & boundary lines toggle (Key 'B')
        self.show_biome_watermarks: bool = True

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

        # Biome Base Colors (used as undertone and fallback)
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
        self.watermark_font = pygame.font.SysFont("consolas", 18, bold=True)
        self.emoji_font = pygame.font.SysFont("segoe ui emoji", 13)
        self.banner_font = pygame.font.SysFont("consolas", 16, bold=True)
        self.banner_sub_font = pygame.font.SysFont("consolas", 12)

        # Ground interaction ripples and floating scenic area banner
        self.ripples: List[Dict] = []
        self.scenic_banner: Optional[Dict] = None

        # Scaled tile cache for high-performance ground rendering
        self._scaled_tile_cache: Dict[Tuple[int, int, int], pygame.Surface] = {}

        # Precompute procedural landscape decor (wildflowers, crags, dappled light)
        self._init_procedural_decor(config.world_width, config.world_height)

    def _get_scaled_tile(self, surf: pygame.Surface, width: int, height: int) -> pygame.Surface:
        """Retrieves or caches a smoothscaled tile surface for current dimensions."""
        key = (id(surf), width, height)
        cached = self._scaled_tile_cache.get(key)
        if cached is not None:
            return cached
        if len(self._scaled_tile_cache) > 128:
            self._scaled_tile_cache.clear()
        scaled = pygame.transform.smoothscale(surf, (width, height))
        self._scaled_tile_cache[key] = scaled
        return scaled

    def _init_procedural_decor(self, world_w: float, world_h: float) -> None:
        """Precomputes deterministic landscape decor elements (flowers, crags, dappled light)."""
        import random
        rng = random.Random(42)
        mid_x = world_w * 0.5
        river_top = world_h * 0.4375
        river_bottom = world_h * 0.5625

        # 1. Meadow wildflowers: (wx, wy, color, size)
        self.decor_flowers = []
        flower_colors = [
            (245, 220, 70),   # Buttercup gold
            (235, 75, 75),    # Poppy red
            (245, 245, 250),  # White daisy
            (175, 120, 240),  # Lavender
        ]
        num_flowers = int(280 * ((world_w * world_h) / (2560.0 * 1600.0)) ** 0.5)
        for _ in range(num_flowers):
            fx = rng.uniform(mid_x + 20, world_w - 20)
            fy = rng.uniform(river_bottom + 20, world_h - 20)
            col = rng.choice(flower_colors)
            sz = rng.choice([2, 3, 3, 4])
            self.decor_flowers.append((fx, fy, col, sz))

        # 2. Forest dappled light: (wx, wy, radius, phase)
        self.decor_dappled_light = []
        num_lights = int(140 * ((world_w * world_h) / (2560.0 * 1600.0)) ** 0.5)
        for _ in range(num_lights):
            lx = rng.uniform(mid_x + 30, world_w - 30)
            ly = rng.uniform(30, river_top - 30)
            rad = rng.uniform(22.0, 48.0)
            phase = rng.uniform(0.0, 6.28)
            self.decor_dappled_light.append((lx, ly, rad, phase))

        # 3. Highlands crags & stone terraces: (wx, wy, len_x, len_y, color)
        self.decor_crags = []
        num_crags = int(160 * ((world_w * world_h) / (2560.0 * 1600.0)) ** 0.5)
        for _ in range(num_crags):
            cx = rng.uniform(30, mid_x - 30)
            cy = rng.uniform(30, river_top - 30)
            col = rng.choice([(86, 96, 114), (54, 60, 72), (102, 112, 130)])
            w = rng.uniform(8.0, 28.0)
            h = rng.uniform(4.0, 10.0)
            self.decor_crags.append((cx, cy, w, h, col))

        # 4. Thickets bramble sprigs & root paths: (wx, wy, length, angle)
        self.decor_brambles = []
        num_brambles = int(160 * ((world_w * world_h) / (2560.0 * 1600.0)) ** 0.5)
        for _ in range(num_brambles):
            bx = rng.uniform(30, mid_x - 30)
            by = rng.uniform(river_bottom + 30, world_h - 30)
            length = rng.uniform(10.0, 26.0)
            angle = rng.uniform(0.0, 3.14)
            self.decor_brambles.append((bx, by, length, angle))

    def cycle_view_mode(self) -> None:
        modes = [ViewMode.SIDE_VIEW, ViewMode.TOP_DOWN, ViewMode.SHAPES]
        curr_idx = modes.index(self.view_mode)
        self.view_mode = modes[(curr_idx + 1) % len(modes)]

    def toggle_biome_watermarks(self) -> None:
        """Toggles territory boundary lines and watermarks (Key 'B')."""
        self.show_biome_watermarks = not self.show_biome_watermarks

    def toggle_chart(self) -> None:
        """Toggles the in-engine real-time population chart HUD (Key 'C')."""
        self.chart.toggle()

    def draw(
        self,
        surface: pygame.Surface,
        sim: Simulation,
        dt: float,
        paused: bool,
        fps: float,
        camera: Optional[Camera2D] = None,
        speed_multiplier: int = 1,
    ) -> None:
        """Full scene rendering pipeline with Camera2D, terrain sprites, Toolbar and Inspector Card."""
        cam = camera if camera is not None else self.camera
        cam.update(dt, sim.animals)
        self.inspector.update(dt, sim)
        self.toolbar.update(dt)

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

        # Ingest recent activity events (Phase 5)
        if hasattr(sim, "recent_activity_events") and sim.recent_activity_events:
            for evt in sim.recent_activity_events:
                self.activity_feed.add_event(evt)

        # Clear background
        surface.fill((10, 12, 16))

        # 1. Draw Organic Biomes (procedural terrain + flora + winding river)
        self._draw_terrain(surface, sim.terrain, cam, sim.time)

        # 1.5 Draw Click Ripples on Ground
        self._draw_ripples(surface, dt, cam)

        # 2. Draw Target Selection Reticle & Vision Circles
        self._draw_selection_reticle(surface, sim, cam)

        # 3. Draw Dying Corpses on Ground
        self._draw_corpses(surface, dt, cam)

        # 4. Draw Depth-Sorted Entities: Natural Props + Wildlife Animals
        self._draw_depth_entities(surface, sim, dt, cam)

        # 4.5 Draw Floating State Emotes (Phase 5: !, 💧, 💨, ❤️)
        self._draw_animal_emotes(surface, sim, cam)

        # 5. Draw Interactive Radar Minimap
        self.minimap.draw(surface, sim, cam, self.badge_font)

        # 6. Draw Slide-Out Animal Inspector Card
        self.inspector.draw(surface, sim, cam, self.sprite_cache)

        # 7. Draw Real-Time Population Dynamics Chart (Key 'C')
        self.chart.draw(surface, sim, cam.screen_width, cam.screen_height)

        # 8. Draw Interactive Desktop Toolbar (Phase 4)
        self.toolbar.draw(
            surface=surface,
            paused=paused,
            current_speed=speed_multiplier,
            current_view=self.view_mode,
            chart_visible=self.chart.visible,
            biomes_visible=self.show_biome_watermarks,
            mouse_pos=pygame.mouse.get_pos(),
        )

        # 8.5 Draw Live Activity Feed Ticker (Phase 5)
        self.activity_feed.draw(
            surface=surface,
            screen_width=cam.screen_width,
            screen_height=cam.screen_height,
            chart_visible=self.chart.visible,
            current_time=sim.time,
        )

        # 8.8 Draw Floating Scenic Area Banner
        self._draw_scenic_banner(surface, dt, cam.screen_width, cam.screen_height)

        # 9. Draw Comprehensive HUD
        self._draw_hud(surface, sim, paused, fps, cam)

    def _draw_selection_reticle(self, surface: pygame.Surface, sim: Simulation, cam: Camera2D) -> None:
        """Draws glowing pulsing selection ring and perception radii for inspected animal."""
        if self.inspector.selected_id is None:
            return

        animal = next((a for a in sim.animals if a.entity_id == self.inspector.selected_id and a.alive), None)
        if not animal:
            return

        sx, sy = cam.world_to_screen(animal.x, animal.y)

        # 1. Vision Range Outline (translucent cyan)
        vr = int(cam.scale_length(animal.profile.vision_radius))
        if vr > 4:
            pygame.draw.circle(surface, (70, 190, 255), (int(sx), int(sy)), vr, 1)

        # 2. Catch Radius Outline (crimson for predators)
        if animal.profile.diet_prey:
            cr = max(4, int(cam.scale_length(animal.profile.catch_radius)))
            pygame.draw.circle(surface, (245, 75, 75), (int(sx), int(sy)), cr, 1)

        # 3. Pulsing Target Reticle Ring
        base_r = int(22 * cam.zoom)
        pulse = int(math.sin(sim.time * 7.0) * 4 * cam.zoom)
        ring_r = max(8, base_r + pulse)
        pygame.draw.circle(surface, (90, 220, 255), (int(sx), int(sy)), ring_r, 2)

        # 4 Corner brackets around reticle
        bracket_offset = ring_r + 5
        bracket_len = max(4, int(6 * cam.zoom))
        for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            bx = int(sx + dx * bracket_offset)
            by = int(sy + dy * bracket_offset)
            pygame.draw.line(surface, (120, 235, 255), (bx, by), (bx - dx * bracket_len, by), 2)
            pygame.draw.line(surface, (120, 235, 255), (bx, by), (bx, by - dy * bracket_len), 2)

    def _draw_terrain(self, surface: pygame.Surface, terrain: TerrainMap, cam: Camera2D, current_time: float = 0.0) -> None:
        """Draws the 5 distinct geographic zones with organic procedural terrain, flora, and landmarks."""
        vp_min_x, vp_min_y, vp_max_x, vp_max_y = cam.get_viewport_world_bounds()

        watermark_labels = {
            BiomeType.HIGHLANDS: "ROCKY HIGHLANDS",
            BiomeType.DENSE_FOREST: "DENSE FOREST",
            BiomeType.RIVER: "AZURE RIVER BASIN",
            BiomeType.THICKETS: "THICKETS & BRIARS",
            BiomeType.MEADOW: "OPEN MEADOW & PLAINS",
        }

        # 1. Base zone fills, authentic pixel-art ground tiling & natural decor
        for zone in terrain.zones:
            if not cam.is_rect_visible(zone.min_x, zone.min_y, zone.max_x, zone.max_y):
                continue

            sx1, sy1 = cam.world_to_screen(zone.min_x, zone.min_y)
            sx2, sy2 = cam.world_to_screen(zone.max_x, zone.max_y)
            rect = pygame.Rect(int(sx1), int(sy1), int(sx2 - sx1) + 1, int(sy2 - sy1) + 1)

            # Base rich tone undertone
            col = self.biome_colors[zone.biome_type]
            pygame.draw.rect(surface, col, rect)

            # Draw authentic tiled pixel-art ground texture (unless in plain Shapes mode)
            if self.view_mode != ViewMode.SHAPES:
                tile = self.terrain_cache.ground_tiles.get(zone.biome_type)
                if tile:
                    int_min_x = max(zone.min_x, vp_min_x)
                    int_max_x = min(zone.max_x, vp_max_x)
                    int_min_y = max(zone.min_y, vp_min_y)
                    int_max_y = min(zone.max_y, vp_max_y)
                    if int_min_x < int_max_x and int_min_y < int_max_y:
                        tw, th = tile.get_width(), tile.get_height()
                        sw = max(2, int(tw * cam.zoom))
                        sh = max(2, int(th * cam.zoom))
                        scaled_tile = self._get_scaled_tile(tile, sw, sh)
                        c_start = int(int_min_x // tw)
                        c_end = int(int_max_x // tw) + 1
                        r_start = int(int_min_y // th)
                        r_end = int(int_max_y // th) + 1
                        for r in range(r_start, r_end):
                            wy = r * th
                            for c in range(c_start, c_end):
                                wx = c * tw
                                tsx, tsy = cam.world_to_screen(wx, wy)
                                surface.blit(scaled_tile, (int(tsx), int(tsy)))

                # Layer atmospheric natural accents
                if zone.biome_type == BiomeType.MEADOW:
                    for fx, fy, fcol, fsz in self.decor_flowers:
                        if vp_min_x <= fx <= vp_max_x and vp_min_y <= fy <= vp_max_y:
                            fsx, fsy = cam.world_to_screen(fx, fy)
                            r = max(1, int(fsz * cam.zoom))
                            pygame.draw.circle(surface, fcol, (int(fsx), int(fsy)), r)
                            if r >= 3:
                                pygame.draw.circle(surface, (255, 255, 240), (int(fsx), int(fsy)), max(1, r - 2))

                elif zone.biome_type == BiomeType.DENSE_FOREST:
                    for lx, ly, rad, phase in self.decor_dappled_light:
                        if vp_min_x - rad <= lx <= vp_max_x + rad and vp_min_y - rad <= ly <= vp_max_y + rad:
                            drift_x = lx + math.sin(current_time * 0.8 + phase) * 8.0
                            drift_y = ly + math.cos(current_time * 0.6 + phase) * 5.0
                            lsx, lsy = cam.world_to_screen(drift_x, drift_y)
                            srad = max(4, int(rad * cam.zoom))
                            light_surf = pygame.Surface((srad * 2, srad * 2), pygame.SRCALPHA)
                            pygame.draw.circle(light_surf, (58, 98, 66, 32), (srad, srad), srad)
                            surface.blit(light_surf, (int(lsx - srad), int(lsy - srad)))

                elif zone.biome_type == BiomeType.HIGHLANDS:
                    for cx, cy, w, h, c_col in self.decor_crags:
                        if vp_min_x <= cx <= vp_max_x and vp_min_y <= cy <= vp_max_y:
                            csx, csy = cam.world_to_screen(cx, cy)
                            sw = max(3, int(w * cam.zoom))
                            sh = max(2, int(h * cam.zoom))
                            pygame.draw.ellipse(surface, c_col, (int(csx), int(csy), sw, sh))

                elif zone.biome_type == BiomeType.THICKETS:
                    for bx, by, length, angle in self.decor_brambles:
                        if vp_min_x <= bx <= vp_max_x and vp_min_y <= by <= vp_max_y:
                            bsx, bsy = cam.world_to_screen(bx, by)
                            ex = bx + math.cos(angle) * length
                            ey = by + math.sin(angle) * length
                            esx, esy = cam.world_to_screen(ex, ey)
                            pygame.draw.line(surface, (92, 82, 56), (int(bsx), int(bsy)), (int(esx), int(esy)), max(1, int(1.5 * cam.zoom)))

        # 2. Draw organic winding river with sandbanks & animated water current ripples
        self._draw_river_organic(surface, terrain, cam, current_time)

        # 3. Draw Authentic Pixel-Art Landmark Assemblies (Crossroads, Cliff Plateau, Watering Hole Basin)
        if self.view_mode != ViewMode.SHAPES and hasattr(terrain, "landmarks") and terrain.landmarks:
            for lm in terrain.landmarks:
                if not cam.is_circle_visible(lm.x, lm.y, radius=450.0):
                    continue
                surf = self.terrain_cache.landmarks.get(lm.landmark_name)
                if not surf:
                    surf = self.terrain_cache.props.get(lm.landmark_name)
                if not surf:
                    continue

                sx, sy = cam.world_to_screen(lm.x, lm.y)
                final_scale = cam.zoom * lm.scale
                pw = max(4, int(surf.get_width() * final_scale))
                ph = max(4, int(surf.get_height() * final_scale))
                scaled_lm = self._get_scaled_tile(surf, pw, ph)
                rect = scaled_lm.get_rect(center=(int(sx), int(sy)))
                surface.blit(scaled_lm, rect)

        # 4. Zone typographic watermark & boundary details (Toggle 'B')
        if self.show_biome_watermarks:
            for zone in terrain.zones:
                if not cam.is_rect_visible(zone.min_x, zone.min_y, zone.max_x, zone.max_y):
                    continue
                sx1, sy1 = cam.world_to_screen(zone.min_x, zone.min_y)
                sx2, sy2 = cam.world_to_screen(zone.max_x, zone.max_y)
                rect = pygame.Rect(int(sx1), int(sy1), int(sx2 - sx1) + 1, int(sy2 - sy1) + 1)
                self._draw_dashed_rect(surface, rect, (65, 85, 110), dash_len=8)
                center_sx, center_sy = cam.world_to_screen(zone.center[0], zone.center[1])
                lbl_text = watermark_labels.get(zone.biome_type, zone.biome_type.value)
                wm_surf = self.watermark_font.render(lbl_text, True, (240, 245, 255))
                wm_surf.set_alpha(85)
                wm_rect = wm_surf.get_rect(center=(int(center_sx), int(center_sy)))
                surface.blit(wm_surf, wm_rect)

    def _draw_river_organic(self, surface: pygame.Surface, terrain: TerrainMap, cam: Camera2D, current_time: float) -> None:
        """Draws winding river with curved shorelines, sandbars, and animated water current ripples."""
        vp_min_x, vp_min_y, vp_max_x, vp_max_y = cam.get_viewport_world_bounds()
        river_top_base = terrain.height * 0.4375
        river_bottom_base = terrain.height * 0.5625

        if vp_max_y < river_top_base - 100 or vp_min_y > river_bottom_base + 100:
            return

        x_start = max(0.0, vp_min_x - 60.0)
        x_end = min(terrain.width, vp_max_x + 60.0)
        if x_end <= x_start:
            return

        step = max(24.0, 36.0 / cam.zoom)
        xs = []
        curr_x = x_start
        while curr_x <= x_end:
            xs.append(curr_x)
            curr_x += step
        if xs[-1] < x_end:
            xs.append(x_end)

        def top_bank(x: float) -> float:
            return river_top_base + 26.0 * math.sin(x * 0.0032) + 14.0 * math.cos(x * 0.0078)

        def bottom_bank(x: float) -> float:
            return river_bottom_base + 24.0 * math.sin(x * 0.0029 + 1.2) + 15.0 * math.cos(x * 0.0072)

        top_pts = [cam.world_to_screen(x, top_bank(x)) for x in xs]
        bottom_pts = [cam.world_to_screen(x, bottom_bank(x)) for x in xs]

        # Upper Sandbank shore
        sand_top_pts = [cam.world_to_screen(x, top_bank(x) - 16.0) for x in xs]
        upper_sand_poly = sand_top_pts + list(reversed(top_pts))
        if len(upper_sand_poly) >= 3:
            pygame.draw.polygon(surface, (194, 166, 118), [(int(p[0]), int(p[1])) for p in upper_sand_poly])

        # Lower Sandbank shore
        sand_bottom_pts = [cam.world_to_screen(x, bottom_bank(x) + 16.0) for x in xs]
        lower_sand_poly = bottom_pts + list(reversed(sand_bottom_pts))
        if len(lower_sand_poly) >= 3:
            pygame.draw.polygon(surface, (194, 166, 118), [(int(p[0]), int(p[1])) for p in lower_sand_poly])

        # Main River Azure Body (shallows & deep core)
        water_poly = top_pts + list(reversed(bottom_pts))
        if len(water_poly) >= 3:
            pygame.draw.polygon(surface, (36, 112, 172), [(int(p[0]), int(p[1])) for p in water_poly])

            deep_top = [cam.world_to_screen(x, top_bank(x) + 14.0) for x in xs]
            deep_bottom = [cam.world_to_screen(x, bottom_bank(x) - 14.0) for x in xs]
            deep_poly = deep_top + list(reversed(deep_bottom))
            if len(deep_poly) >= 3:
                pygame.draw.polygon(surface, (22, 78, 138), [(int(p[0]), int(p[1])) for p in deep_poly])

        # Animated Shimmering Current Flow Ripples
        for r_idx in range(3):
            frac = (r_idx + 1) / 4.0
            wave_pts = []
            drift = current_time * 26.0 + r_idx * 50.0
            for x in xs:
                tb = top_bank(x)
                bb = bottom_bank(x)
                base_wy = tb + frac * (bb - tb)
                wy = base_wy + 6.0 * math.sin((x + drift) * 0.015)
                wsx, wsy = cam.world_to_screen(x, wy)
                wave_pts.append((int(wsx), int(wsy)))
            if len(wave_pts) >= 2:
                pygame.draw.lines(surface, (100, 205, 255), False, wave_pts, max(1, int(1.5 * cam.zoom)))

    def _draw_ripples(self, surface: pygame.Surface, dt: float, cam: Camera2D) -> None:
        """Renders expanding concentric ripple rings on the ground from user clicks."""
        surviving = []
        for r in self.ripples:
            r["timer"] += dt
            if r["timer"] >= r["max_time"]:
                continue
            surviving.append(r)

            if not cam.is_circle_visible(r["wx"], r["wy"], radius=80.0):
                continue

            progress = r["timer"] / r["max_time"]
            curr_r = (r["radius"] + (r["max_radius"] - r["radius"]) * progress) * cam.zoom
            alpha = int(220 * (1.0 - progress))
            if alpha <= 0 or curr_r < 2:
                continue

            sx, sy = cam.world_to_screen(r["wx"], r["wy"])
            sz = int(curr_r * 2 + 6)
            r_surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
            center = (sz // 2, sz // 2)

            pygame.draw.circle(r_surf, (80, 220, 255, alpha), center, int(curr_r), max(1, int(2 * cam.zoom)))
            if curr_r > 12:
                pygame.draw.circle(r_surf, (245, 215, 80, int(alpha * 0.7)), center, int(curr_r * 0.6), 1)

            surface.blit(r_surf, (int(sx - sz // 2), int(sy - sz // 2)))

        self.ripples = surviving

    def _draw_scenic_banner(self, surface: pygame.Surface, dt: float, screen_w: int, screen_h: int) -> None:
        """Renders sleek top-center floating glass badge when a scenic landmark is active."""
        if not self.scenic_banner:
            return

        self.scenic_banner["timer"] += dt
        timer = self.scenic_banner["timer"]
        duration = self.scenic_banner["duration"]

        if timer >= duration:
            self.scenic_banner = None
            return

        if timer < 0.3:
            alpha_ratio = timer / 0.3
        elif timer > duration - 0.6:
            alpha_ratio = max(0.0, (duration - timer) / 0.6)
        else:
            alpha_ratio = 1.0

        alpha = int(235 * alpha_ratio)
        if alpha <= 0:
            return

        name = self.scenic_banner["name"]
        icon = self.scenic_banner["icon"]
        subtitle = self.scenic_banner["subtitle"]

        title_surf = self.banner_font.render(f"{icon}  {name}", True, (245, 250, 255))
        sub_surf = self.banner_sub_font.render(subtitle, True, (135, 215, 250))

        pw = max(title_surf.get_width(), sub_surf.get_width()) + 44
        ph = title_surf.get_height() + sub_surf.get_height() + 20
        px = (screen_w - pw) // 2
        py = 22

        banner_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(banner_surf, (14, 20, 28, alpha), (0, 0, pw, ph), border_radius=10)
        border_col = (70, 185, 235, int(alpha * 0.85))
        pygame.draw.rect(banner_surf, border_col, (0, 0, pw, ph), width=2, border_radius=10)

        banner_surf.blit(title_surf, ((pw - title_surf.get_width()) // 2, 7))
        banner_surf.blit(sub_surf, ((pw - sub_surf.get_width()) // 2, 7 + title_surf.get_height() + 3))

        surface.blit(banner_surf, (px, py))

    def add_click_ripple(self, wx: float, wy: float) -> None:
        """Emits an animated expanding ring on ground coordinates."""
        self.ripples.append({
            "wx": wx,
            "wy": wy,
            "radius": 4.0,
            "max_radius": 55.0,
            "timer": 0.0,
            "max_time": 0.85,
        })

    def trigger_scenic_banner(self, area: ScenicArea) -> None:
        """Displays floating location banner for scenic landmark."""
        self.scenic_banner = {
            "name": area.name,
            "icon": area.icon,
            "subtitle": area.subtitle,
            "timer": 0.0,
            "duration": 3.2,
        }

    def trigger_terrain_focus(self, wx: float, wy: float, terrain: TerrainMap) -> None:
        """Triggers ground ripple animation and displays scenic territory banner."""
        self.add_click_ripple(wx, wy)
        area = terrain.get_scenic_area_at(wx, wy)
        self.trigger_scenic_banner(area)

    def _draw_dashed_rect(self, surface: pygame.Surface, rect: pygame.Rect, color: Tuple[int, int, int], dash_len: int = 8) -> None:
        """Draws dashed boundary borders around a rectangle."""
        # Top & Bottom edges
        for x in range(rect.left, rect.right, dash_len * 2):
            pygame.draw.line(surface, color, (x, rect.top), (min(rect.right, x + dash_len), rect.top), 1)
            pygame.draw.line(surface, color, (x, rect.bottom), (min(rect.right, x + dash_len), rect.bottom), 1)
        # Left & Right edges
        for y in range(rect.top, rect.bottom, dash_len * 2):
            pygame.draw.line(surface, color, (rect.left, y), (rect.left, min(rect.bottom, y + dash_len)), 1)
            pygame.draw.line(surface, color, (rect.right, y), (rect.right, min(rect.bottom, y + dash_len)), 1)

    def _draw_corpses(self, surface: pygame.Surface, dt: float, cam: Camera2D) -> None:
        surviving = []
        for corpse in self.corpses:
            corpse["timer"] += dt
            if corpse["timer"] >= 1.5:
                continue
            surviving.append(corpse)

            if not cam.is_circle_visible(corpse["x"], corpse["y"], radius=40.0):
                continue

            sp_name = corpse["species"]
            sp_set = self.sprite_cache.species.get(sp_name)
            if not sp_set or not sp_set.anims.get("die"):
                continue

            frames = sp_set.anims["die"]
            frame_idx = min(len(frames) - 1, int(corpse["timer"] / 0.12))
            frame = frames[frame_idx]

            if math.cos(corpse["heading"]) < 0:
                frame = pygame.transform.flip(frame, True, False)

            # Apply camera zoom scaling if needed
            if abs(cam.zoom - 1.0) > 0.05:
                nw = max(1, int(frame.get_width() * cam.zoom))
                nh = max(1, int(frame.get_height() * cam.zoom))
                frame = pygame.transform.smoothscale(frame, (nw, nh))

            # Alpha fade
            if corpse["timer"] > 1.0:
                alpha = int(255 * max(0.0, (1.5 - corpse["timer"]) / 0.5))
                frame = frame.copy()
                frame.set_alpha(alpha)

            sx, sy = cam.world_to_screen(corpse["x"], corpse["y"])
            rect = frame.get_rect(center=(int(sx), int(sy)))
            surface.blit(frame, rect)

        self.corpses = surviving

    def _draw_depth_entities(self, surface: pygame.Surface, sim: Simulation, dt: float, cam: Camera2D) -> None:
        """Unified 2.5D depth sort for both animals and natural props (trees, boulders, bushes)."""
        active_ids = set()
        draw_queue = []

        # 1. Animals
        for a in sim.animals:
            if not a.alive:
                continue
            active_ids.add(a.entity_id)
            if cam.is_circle_visible(a.x, a.y, radius=60.0):
                draw_queue.append((a.y, "animal", a))

        # 2. Natural Props (trees, boulders, bushes, flowers)
        if hasattr(sim.terrain, "props") and sim.terrain.props and self.view_mode != ViewMode.SHAPES:
            for p in sim.terrain.props:
                if cam.is_circle_visible(p.x, p.y, radius=80.0):
                    draw_queue.append((p.y, "prop", p))

        # Sort top-to-bottom for natural 2.5D overlap
        draw_queue.sort(key=lambda item: item[0])

        for _, kind, obj in draw_queue:
            if kind == "prop":
                self._draw_prop(surface, obj, cam)
            else:
                self._draw_single_animal(surface, obj, sim, dt, cam)

        # Cleanup stale anim states
        stale = [eid for eid in self.anim_states if eid not in active_ids]
        for eid in stale:
            del self.anim_states[eid]

    def _draw_prop(self, surface: pygame.Surface, prop: TerrainProp, cam: Camera2D) -> None:
        """Draws a single natural terrain prop with soft drop-shadow and zoom scaling."""
        prop_surf = self.terrain_cache.props.get(prop.prop_name)
        if not prop_surf:
            return

        sx, sy = cam.world_to_screen(prop.x, prop.y)
        final_scale = cam.zoom * prop.scale

        if abs(final_scale - 1.0) > 0.05:
            pw = max(4, int(prop_surf.get_width() * final_scale))
            ph = max(4, int(prop_surf.get_height() * final_scale))
            scaled_prop = pygame.transform.smoothscale(prop_surf, (pw, ph))
        else:
            scaled_prop = prop_surf
            pw = scaled_prop.get_width()
            ph = scaled_prop.get_height()

        # Draw soft translucent ground drop-shadow beneath prop
        sw = max(6, int(pw * 0.75))
        sh = max(3, int(ph * 0.28))
        shadow_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 75), (0, 0, sw, sh))
        surface.blit(shadow_surf, (int(sx - sw * 0.5), int(sy + ph * 0.35 - sh * 0.5)))

        rect = scaled_prop.get_rect(center=(int(sx), int(sy)))
        surface.blit(scaled_prop, rect)

    def _draw_single_animal(self, surface: pygame.Surface, animal: Animal, sim: Simulation, dt: float, cam: Camera2D) -> None:
        sx, sy = cam.world_to_screen(animal.x, animal.y)
        px, py = int(sx), int(sy)

        # Draw soft creature drop-shadow beneath feet
        ash_w = max(4, int(18 * animal.profile.scale * 2.0 * cam.zoom))
        ash_h = max(2, int(8 * animal.profile.scale * 2.0 * cam.zoom))
        ash_surf = pygame.Surface((ash_w, ash_h), pygame.SRCALPHA)
        pygame.draw.ellipse(ash_surf, (0, 0, 0, 70), (0, 0, ash_w, ash_h))
        surface.blit(ash_surf, (px - ash_w // 2, py + int(6 * cam.zoom) - ash_h // 2))

        # Stalking focus line for chasing predators
        if animal.state == AnimalState.CHASE and animal.target_prey_id:
            quarry = next((q for q in sim.animals if q.entity_id == animal.target_prey_id and q.alive), None)
            if quarry and cam.is_circle_visible(quarry.x, quarry.y, radius=60.0):
                qx, qy = cam.world_to_screen(quarry.x, quarry.y)
                pygame.draw.line(surface, (230, 60, 50), (px, py), (int(qx), int(qy)), max(1, int(cam.zoom)))

        if self.view_mode == ViewMode.SHAPES:
            self._draw_animal_shape(surface, animal, px, py, cam.zoom)
        elif self.view_mode == ViewMode.TOP_DOWN:
            self._draw_animal_top_down(surface, animal, dt, px, py, cam.zoom)
        else:
            self._draw_animal_animated(surface, animal, dt, px, py, cam.zoom)

    def _draw_animal_shape(self, surface: pygame.Surface, animal: Animal, px: int, py: int, zoom: float) -> None:
        col = self.shape_colors.get(animal.profile.name, (200, 200, 200))
        radius = max(2, int(8 * animal.profile.scale * 2.0 * zoom))
        pygame.draw.circle(surface, col, (px, py), radius)
        # Heading line
        hx = px + int(math.cos(animal.heading) * (radius + 6 * zoom))
        hy = py + int(math.sin(animal.heading) * (radius + 6 * zoom))
        pygame.draw.line(surface, (255, 255, 255), (px, py), (hx, hy), max(1, int(2 * zoom)))

    def _draw_animal_animated(self, surface: pygame.Surface, animal: Animal, dt: float, px: int, py: int, zoom: float) -> None:
        sp_name = animal.profile.name
        sp_set = self.sprite_cache.species.get(sp_name)
        if not sp_set:
            self._draw_animal_shape(surface, animal, px, py, zoom)
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
            self._draw_animal_shape(surface, animal, px, py, zoom)
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

        # Scale with camera zoom
        if abs(zoom - 1.0) > 0.05:
            nw = max(1, int(frame.get_width() * zoom))
            nh = max(1, int(frame.get_height() * zoom))
            frame = pygame.transform.smoothscale(frame, (nw, nh))

        rect = frame.get_rect(center=(px, py))
        surface.blit(frame, rect)

        # Health/Energy bar for carnivores and apex beasts
        if animal.profile.diet_prey:
            self._draw_energy_bar(surface, animal, px, rect.top - 5, zoom)

    def _draw_animal_top_down(self, surface: pygame.Surface, animal: Animal, dt: float, px: int, py: int, zoom: float) -> None:
        sp_set = self.sprite_cache.species.get(animal.profile.name)
        if not sp_set or not sp_set.top_view_frames:
            self._draw_animal_animated(surface, animal, dt, px, py, zoom)
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

        if abs(zoom - 1.0) > 0.05:
            nw = max(1, int(rotated.get_width() * zoom))
            nh = max(1, int(rotated.get_height() * zoom))
            rotated = pygame.transform.smoothscale(rotated, (nw, nh))

        rect = rotated.get_rect(center=(px, py))
        surface.blit(rotated, rect)

    def _draw_energy_bar(self, surface: pygame.Surface, animal: Animal, center_x: int, top_y: int, zoom: float = 1.0) -> None:
        w = max(16, int(24 * zoom))
        h = max(2, int(3 * zoom))
        x = center_x - w // 2
        ratio = max(0.0, min(1.0, animal.energy / animal.profile.max_energy))
        col = (int(255 * (1.0 - ratio)), int(230 * ratio), 50)
        pygame.draw.rect(surface, (15, 18, 22), (x - 1, top_y - 1, w + 2, h + 2))
        pygame.draw.rect(surface, col, (x, top_y, int(w * ratio), h))

    def _draw_hud(self, surface: pygame.Surface, sim: Simulation, paused: bool, fps: float, cam: Camera2D) -> None:
        # Count species
        counts: Dict[str, int] = {}
        for a in sim.animals:
            if a.alive:
                counts[a.profile.name] = counts.get(a.profile.name, 0) + 1

        hud_w, hud_h = 700, 118
        hud_surf = pygame.Surface((hud_w, hud_h), pygame.SRCALPHA)
        pygame.draw.rect(hud_surf, (16, 20, 26, 225), (0, 0, hud_w, hud_h), border_radius=8)
        pygame.draw.rect(hud_surf, (55, 68, 85), (0, 0, hud_w, hud_h), 1, border_radius=8)

        line1 = f"WILDLIFE ECOSYSTEM  |  Time: {sim.time:5.1f}s  |  FPS: {fps:4.1f}  |  Zoom: {cam.zoom:.2f}x"
        line2 = (
            f"🐇 Rabbits:{counts.get('rabbit', 0):3d}  "
            f"🦌 Deer:{counts.get('deer', 0):2d}  "
            f"🐐 Goats:{counts.get('goat', 0):2d}  "
            f"🦊 Foxes:{counts.get('fox', 0):2d}  "
            f"🐺 Wolves:{counts.get('wolf', 0):2d}  "
            f"🐻 Bears:{counts.get('bear', 0):2d}"
        )
        follow_str = f"Following #{cam.follow_target_id}" if cam.follow_target_id else "Free Camera"
        line3 = f"View: {self.view_mode.value}  |  Camera: ({cam.x:.0f}, {cam.y:.0f}) [{follow_str}]"
        line4 = f"[Click] Toolbar / Animal | [1/2/5] Speed | [C] Chart | [B] Biomes | [V] View | [Space] Pause"

        for i, (text, col) in enumerate([
            (line1, (245, 245, 245)),
            (line2, (110, 230, 140)),
            (line3, (255, 200, 80)),
            (line4, (165, 180, 195)),
        ]):
            txt_surf = self.font.render(text, True, col)
            hud_surf.blit(txt_surf, (14, 10 + i * 23))

        surface.blit(hud_surf, (16, 16))

    def _draw_animal_emotes(self, surface: pygame.Surface, sim: Simulation, cam: Camera2D) -> None:
        """Renders floating state badges (!, 💧, 💨, ❤️) directly above living animals in camera view."""
        for animal in sim.animals:
            if not animal.alive:
                continue

            # Frustum culling check
            if not cam.is_in_view(animal.x, animal.y, margin=35.0):
                continue

            emote_symbol = None
            emote_bg = (24, 30, 42, 220)
            emote_border = (70, 85, 110)

            # 1. Reproduction Love Heart (❤️)
            if animal.reproduction_cooldown > animal.profile.reproduction_cooldown - 1.8:
                emote_symbol = "❤️"
                emote_bg = (55, 18, 28, 230)
                emote_border = (235, 80, 110)

            # 2. Threat Exclamation / Alert (❗)
            elif animal.state == AnimalState.FLEE:
                emote_symbol = "❗"
                emote_bg = (60, 20, 20, 230)
                emote_border = (245, 75, 75)

            # 3. Exhaustion Puff (💨)
            elif animal.stamina < 15.0 and animal.state in [AnimalState.CHASE, AnimalState.FLEE]:
                emote_symbol = "💨"
                emote_bg = (48, 38, 20, 230)
                emote_border = (240, 180, 50)

            # 4. Thirst Droplet (💧)
            elif animal.state == AnimalState.DRINK or animal.thirst > 65.0:
                emote_symbol = "💧"
                emote_bg = (18, 38, 58, 230)
                emote_border = (65, 180, 245)

            if emote_symbol:
                sx, sy = cam.world_to_screen(animal.x, animal.y)
                bob = math.sin(sim.time * 6.0 + float(animal.entity_id)) * 2.5
                badge_x = int(sx)
                badge_y = int(sy - 22 * cam.zoom + bob)

                bw, bh = 20, 18
                badge_rect = pygame.Rect(badge_x - bw // 2, badge_y - bh // 2, bw, bh)
                badge_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
                pygame.draw.rect(badge_surf, emote_bg, (0, 0, bw, bh), border_radius=5)
                pygame.draw.rect(badge_surf, emote_border, (0, 0, bw, bh), 1, border_radius=5)

                glyph_surf = self.emoji_font.render(emote_symbol, True, (255, 255, 255))
                g_rect = glyph_surf.get_rect(center=(bw // 2, bh // 2))
                badge_surf.blit(glyph_surf, g_rect)

                surface.blit(badge_surf, badge_rect)
