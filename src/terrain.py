"""Terrain and biome ecosystem map.

Manages 5 exact geographic zones, tile movement modifiers, dynamic vegetation/grass
biomass regeneration, river hydration sources, and prey refuge thickets.
Completely headless with ZERO rendering dependencies.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class BiomeType(str, Enum):
    HIGHLANDS = "Rocky Highlands"
    DENSE_FOREST = "Dense Forest"
    RIVER = "River & Watering Hole"
    THICKETS = "Thickets & Briars"
    MEADOW = "Open Meadow & Plains"


@dataclass(frozen=True)
class BiomeProperties:
    biome_type: BiomeType
    base_speed_mult: float
    cover_density: float          # 0.0 = clear sightlines, 0.8 = dense stealth cover
    has_grass: bool               # Supports herbivore grazing
    is_water: bool                # Drinking source
    stamina_drain_mult: float     # Fatigue rate multiplier


BIOME_DEFAULTS: Dict[BiomeType, BiomeProperties] = {
    BiomeType.HIGHLANDS: BiomeProperties(
        biome_type=BiomeType.HIGHLANDS,
        base_speed_mult=0.65,
        cover_density=0.20,
        has_grass=False,
        is_water=False,
        stamina_drain_mult=2.0,   # Rough steep climb burns stamina fast
    ),
    BiomeType.DENSE_FOREST: BiomeProperties(
        biome_type=BiomeType.DENSE_FOREST,
        base_speed_mult=0.88,
        cover_density=0.55,       # Stalking cover
        has_grass=True,
        is_water=False,
        stamina_drain_mult=1.1,
    ),
    BiomeType.RIVER: BiomeProperties(
        biome_type=BiomeType.RIVER,
        base_speed_mult=0.45,     # Water wading drag
        cover_density=0.05,
        has_grass=False,
        is_water=True,
        stamina_drain_mult=1.4,
    ),
    BiomeType.THICKETS: BiomeProperties(
        biome_type=BiomeType.THICKETS,
        base_speed_mult=0.85,     # Small animals slip through; large animals slowed more
        cover_density=0.80,       # High briar concealment
        has_grass=True,
        is_water=False,
        stamina_drain_mult=1.0,
    ),
    BiomeType.MEADOW: BiomeProperties(
        biome_type=BiomeType.MEADOW,
        base_speed_mult=1.00,     # Clean sprint surface
        cover_density=0.00,       # Wide open visibility
        has_grass=True,
        is_water=False,
        stamina_drain_mult=1.0,
    ),
}


@dataclass
class TerrainZone:
    biome_type: BiomeType
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    center: Tuple[float, float]
    resident_species: List[str]


@dataclass(frozen=True)
class TerrainProp:
    prop_id: int
    biome_type: BiomeType
    prop_name: str
    x: float
    y: float
    scale: float = 1.0


@dataclass(frozen=True)
class TerrainLandmark:
    landmark_id: str
    landmark_name: str
    biome_type: BiomeType
    x: float
    y: float
    scale: float = 1.0


@dataclass(frozen=True)
class ScenicArea:
    area_id: str
    name: str
    icon: str
    subtitle: str
    biome_type: BiomeType
    center: Tuple[float, float]
    description: str


class TerrainMap:
    """Manages territorial zone boundaries, grass regrowth, and spatial queries."""

    def __init__(self, world_width: float = 1200.0, world_height: float = 800.0) -> None:
        self.width = world_width
        self.height = world_height

        # Define the 5 exact designated zones
        mid_x = world_width * 0.5
        river_top = world_height * 0.4375  # ~350
        river_bottom = world_height * 0.5625  # ~450

        self.zones: List[TerrainZone] = [
            # Zone 1: Rocky Highlands (Northwest)
            TerrainZone(
                biome_type=BiomeType.HIGHLANDS,
                min_x=0.0,
                max_x=mid_x,
                min_y=0.0,
                max_y=river_top,
                center=(mid_x * 0.5, river_top * 0.5),
                resident_species=["goat"],
            ),
            # Zone 2: Dense Forest (Northeast)
            TerrainZone(
                biome_type=BiomeType.DENSE_FOREST,
                min_x=mid_x,
                max_x=world_width,
                min_y=0.0,
                max_y=river_top,
                center=(mid_x + (world_width - mid_x) * 0.5, river_top * 0.5),
                resident_species=["wolf", "bear"],
            ),
            # Zone 3: The River & Watering Hole (Center Strip)
            TerrainZone(
                biome_type=BiomeType.RIVER,
                min_x=0.0,
                max_x=world_width,
                min_y=river_top,
                max_y=river_bottom,
                center=(world_width * 0.5, (river_top + river_bottom) * 0.5),
                resident_species=["bear"],
            ),
            # Zone 4: Thickets & Briars (Southwest)
            TerrainZone(
                biome_type=BiomeType.THICKETS,
                min_x=0.0,
                max_x=mid_x,
                min_y=river_bottom,
                max_y=world_height,
                center=(mid_x * 0.5, river_bottom + (world_height - river_bottom) * 0.5),
                resident_species=["fox", "rabbit"],
            ),
            # Zone 5: Open Meadow & Plains (Southeast)
            TerrainZone(
                biome_type=BiomeType.MEADOW,
                min_x=mid_x,
                max_x=world_width,
                min_y=river_bottom,
                max_y=world_height,
                center=(mid_x + (world_width - mid_x) * 0.5, river_bottom + (world_height - river_bottom) * 0.5),
                resident_species=["deer", "rabbit"],
            ),
        ]

        # Scenic Landmarks & Territorial Biome Profiles
        self.scenic_areas: Dict[BiomeType, ScenicArea] = {
            BiomeType.HIGHLANDS: ScenicArea(
                area_id="highlands",
                name="Granite Highlands",
                icon="⛰️",
                subtitle="Alpine Crags & Mountain Goat Cliffs",
                biome_type=BiomeType.HIGHLANDS,
                center=(mid_x * 0.5, river_top * 0.5),
                description="Rugged steep crags where sure-footed mountain goats thrive.",
            ),
            BiomeType.DENSE_FOREST: ScenicArea(
                area_id="forest",
                name="Ancient Whispering Forest",
                icon="🌲",
                subtitle="Old-Growth Pine Canopy & Wolf Stalking Grounds",
                biome_type=BiomeType.DENSE_FOREST,
                center=(mid_x + (world_width - mid_x) * 0.5, river_top * 0.5),
                description="Shadowed woodland canopy, home to stalking wolves and roaming bears.",
            ),
            BiomeType.RIVER: ScenicArea(
                area_id="river",
                name="Azure River Basin",
                icon="🌊",
                subtitle="Central Freshwater Watering Hole & Shallows",
                biome_type=BiomeType.RIVER,
                center=(world_width * 0.5, (river_top + river_bottom) * 0.5),
                description="Life-giving winding river where herds gather to drink.",
            ),
            BiomeType.THICKETS: ScenicArea(
                area_id="thickets",
                name="Briar Thickets & Fox Hollow",
                icon="🌿",
                subtitle="Thorny Bramble Cover & Prey Refuge",
                biome_type=BiomeType.THICKETS,
                center=(mid_x * 0.5, river_bottom + (world_height - river_bottom) * 0.5),
                description="Dense tangled briars offering swift cover for rabbits and cunning foxes.",
            ),
            BiomeType.MEADOW: ScenicArea(
                area_id="meadow",
                name="Sunlit Golden Meadow",
                icon="🌾",
                subtitle="Open Prairie & Deer Grazing Plains",
                biome_type=BiomeType.MEADOW,
                center=(mid_x + (world_width - mid_x) * 0.5, river_bottom + (world_height - river_bottom) * 0.5),
                description="Sprawling flower-dotted grassland plains where deer graze freely.",
            ),
        }

        # Vegetation biomass grid (40 x 26 cells)
        self.grid_cols = 40
        self.grid_rows = 26
        self.cell_w = self.width / self.grid_cols
        self.cell_h = self.height / self.grid_rows
        # 1.0 = lush grass, 0.0 = overgrazed dirt
        self.grass_biomass: List[List[float]] = [
            [1.0 for _ in range(self.grid_cols)] for _ in range(self.grid_rows)
        ]

        # Natural landscape props and prominent territory landmarks
        self.landmarks: List[TerrainLandmark] = []
        self._generate_landmarks()

        self.props: List[TerrainProp] = []
        self._generate_props()

    def _generate_landmarks(self) -> None:
        """Places authentic pixel-art landmark assemblies at designated scenic centers."""
        mid_x = self.width * 0.5
        river_top = self.height * 0.4375
        river_bottom = self.height * 0.5625

        # 1. Meadow: Cobblestone Crossroads & Winding Trail
        m_center_x = mid_x + (self.width - mid_x) * 0.5
        m_center_y = river_bottom + (self.height - river_bottom) * 0.5
        self.landmarks.append(TerrainLandmark(
            landmark_id="meadow_crossroads",
            landmark_name="landmark_crossroads",
            biome_type=BiomeType.MEADOW,
            x=m_center_x,
            y=m_center_y,
            scale=2.5,
        ))
        self.landmarks.append(TerrainLandmark(
            landmark_id="meadow_trail_west",
            landmark_name="landmark_winding_trail",
            biome_type=BiomeType.MEADOW,
            x=m_center_x - 380.0,
            y=m_center_y + 110.0,
            scale=2.3,
        ))

        # 2. River: Central Circular Watering Hole Basin
        r_center_x = self.width * 0.5
        r_center_y = (river_top + river_bottom) * 0.5
        self.landmarks.append(TerrainLandmark(
            landmark_id="river_basin",
            landmark_name="landmark_watering_hole_basin",
            biome_type=BiomeType.RIVER,
            x=r_center_x,
            y=r_center_y,
            scale=2.2,
        ))

        # 3. Highlands: Cliff Plateau & Staircase Ramp
        h_center_x = mid_x * 0.5
        h_center_y = river_top * 0.5
        self.landmarks.append(TerrainLandmark(
            landmark_id="highlands_plateau",
            landmark_name="landmark_cliff_plateau",
            biome_type=BiomeType.HIGHLANDS,
            x=h_center_x - 130.0,
            y=h_center_y,
            scale=2.4,
        ))
        self.landmarks.append(TerrainLandmark(
            landmark_id="highlands_ramp",
            landmark_name="landmark_cliff_ramp",
            biome_type=BiomeType.HIGHLANDS,
            x=h_center_x + 180.0,
            y=h_center_y + 30.0,
            scale=2.4,
        ))

        # 4. Dense Forest: Ancient Oak Grove
        f_center_x = mid_x + (self.width - mid_x) * 0.5
        f_center_y = river_top * 0.5
        self.landmarks.append(TerrainLandmark(
            landmark_id="forest_oak_grove",
            landmark_name="landmark_ancient_oak_grove",
            biome_type=BiomeType.DENSE_FOREST,
            x=f_center_x,
            y=f_center_y,
            scale=2.4,
        ))

        # 5. Thickets: Briar Hollow Refuge Mound
        t_center_x = mid_x * 0.5
        t_center_y = river_bottom + (self.height - river_bottom) * 0.5
        self.landmarks.append(TerrainLandmark(
            landmark_id="thickets_briar_refuge",
            landmark_name="landmark_briar_hollow_refuge",
            biome_type=BiomeType.THICKETS,
            x=t_center_x,
            y=t_center_y,
            scale=2.4,
        ))

    def _generate_props(self) -> None:
        """Generates deterministic landscape props across all 5 biomes."""
        import random
        rng = random.Random(1337)

        biome_prop_pool = {
            BiomeType.HIGHLANDS: [
                ("prop_highlands_rock_pyramid", 1.2),
                ("prop_highlands_rock_throne", 1.2),
                ("prop_highlands_rock_crags", 1.1),
                ("prop_highlands_rock_slabs", 1.1),
                ("prop_highlands_pine1", 1.1),
                ("prop_highlands_pine2", 1.1),
                ("prop_highlands_pine3", 1.1),
                ("prop_highlands_pine4", 1.1),
                ("prop_highlands_cave", 1.1),
            ],
            BiomeType.DENSE_FOREST: [
                ("prop_forest_ancient_oak", 1.25),
                ("prop_forest_mossy_log", 1.05),
                ("prop_forest_bramble", 1.0),
                ("prop_forest_angled_log", 1.05),
                ("prop_forest_stump", 1.0),
            ],
            BiomeType.RIVER: [
                ("prop_river_boulders", 1.15),
            ],
            BiomeType.THICKETS: [
                ("prop_thickets_bramble_mound", 1.15),
                ("prop_thickets_leafy_mound", 1.15),
                ("prop_thickets_deadwood_log", 1.1),
                ("prop_thickets_deadwood_roots", 1.1),
                ("prop_thickets_thorn_barrier1", 1.05),
                ("prop_thickets_thorn_barrier2", 1.05),
                ("prop_thickets_berry_red", 1.0),
                ("prop_thickets_berry_blackberry", 1.0),
                ("prop_thickets_mossy_rocks", 1.0),
            ],
            BiomeType.MEADOW: [
                ("prop_meadow_rock", 1.0),
                ("prop_meadow_log", 1.0),
                ("prop_meadow_sapling", 1.1),
                ("prop_meadow_dandelion", 1.0),
                ("prop_meadow_poppy", 1.0),
                ("prop_meadow_bluebells", 1.0),
                ("prop_meadow_bush", 1.0),
                ("prop_meadow_clover", 0.95),
            ],
        }

        base_prop_counts = {
            BiomeType.HIGHLANDS: 25,
            BiomeType.DENSE_FOREST: 30,
            BiomeType.RIVER: 16,
            BiomeType.THICKETS: 25,
            BiomeType.MEADOW: 26,
        }

        # Dynamically scale prop count with world dimensions for vast wilderness
        base_area = 1200.0 * 800.0
        curr_area = self.width * self.height
        scale_mult = max(1.0, min(3.0, (curr_area / base_area) ** 0.5))

        pid = 1
        for zone in self.zones:
            pool = biome_prop_pool.get(zone.biome_type, [])
            base_count = base_prop_counts.get(zone.biome_type, 20)
            count = int(base_count * scale_mult)
            pad_x = (zone.max_x - zone.min_x) * 0.05
            pad_y = (zone.max_y - zone.min_y) * 0.06

            for _ in range(count):
                prop_name, base_scale = rng.choice(pool)
                px = rng.uniform(zone.min_x + pad_x, zone.max_x - pad_x)
                py = rng.uniform(zone.min_y + pad_y, zone.max_y - pad_y)
                scale_jitter = rng.uniform(0.9, 1.1)
                self.props.append(TerrainProp(
                    prop_id=pid,
                    biome_type=zone.biome_type,
                    prop_name=prop_name,
                    x=px,
                    y=py,
                    scale=base_scale * scale_jitter,
                ))
                pid += 1

    def get_scenic_area_at(self, x: float, y: float) -> ScenicArea:
        """Returns the designated scenic landmark for coordinates."""
        b_type = self.get_biome_at(x, y)
        return self.scenic_areas.get(b_type, self.scenic_areas[BiomeType.MEADOW])

    def get_zone_at(self, x: float, y: float) -> TerrainZone:
        """Finds the geographic territory for given coordinates."""
        for zone in self.zones:
            if zone.min_x <= x <= zone.max_x and zone.min_y <= y <= zone.max_y:
                return zone
        # Fallback to nearest zone
        return self.zones[0]

    def get_biome_at(self, x: float, y: float) -> BiomeType:
        return self.get_zone_at(x, y).biome_type

    def get_properties_at(self, x: float, y: float) -> BiomeProperties:
        return BIOME_DEFAULTS[self.get_biome_at(x, y)]

    def get_home_zone_for(self, species: str) -> TerrainZone:
        """Returns the primary designated native territory for an animal species."""
        for zone in self.zones:
            if species in zone.resident_species and zone.biome_type != BiomeType.RIVER:
                return zone
        return self.zones[4]  # Default to Meadow

    def graze_grass(self, x: float, y: float, amount: float = 0.25) -> float:
        """Herbivore grazes grass at (x, y). Returns biomass consumed."""
        col = max(0, min(self.grid_cols - 1, int(x // self.cell_w)))
        row = max(0, min(self.grid_rows - 1, int(y // self.cell_h)))
        zone = self.get_zone_at(x, y)
        if not BIOME_DEFAULTS[zone.biome_type].has_grass:
            return 0.0

        current = self.grass_biomass[row][col]
        consumed = min(current, amount)
        self.grass_biomass[row][col] -= consumed
        return consumed

    def update_regrowth(self, dt: float, regrowth_rate: float = 0.05) -> None:
        """Regrows grass biomass across fertile biomes over time."""
        for r in range(self.grid_rows):
            cy = (r + 0.5) * self.cell_h
            for c in range(self.grid_cols):
                cx = (c + 0.5) * self.cell_w
                zone = self.get_zone_at(cx, cy)
                if BIOME_DEFAULTS[zone.biome_type].has_grass:
                    # Meadow regrows faster than thickets or forest
                    rate = regrowth_rate * (1.5 if zone.biome_type == BiomeType.MEADOW else 0.8)
                    self.grass_biomass[r][c] = min(1.0, self.grass_biomass[r][c] + rate * dt)
                else:
                    self.grass_biomass[r][c] = 0.0
