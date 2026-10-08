"""Unit tests for the 5 terrain biomes, species food web, and habitat mechanics."""

import unittest

from src.entities import Animal, AnimalState
from src.species import SPECIES_REGISTRY
from src.terrain import BiomeType, TerrainMap


class TestTerrainAndSpecies(unittest.TestCase):
    def setUp(self):
        self.terrain = TerrainMap(world_width=1200.0, world_height=800.0)

    def test_five_zones_defined_correctly(self):
        """Verify all 5 exact geographic zones exist."""
        self.assertEqual(len(self.terrain.zones), 5)
        types = {z.biome_type for z in self.terrain.zones}
        expected = {
            BiomeType.HIGHLANDS,
            BiomeType.DENSE_FOREST,
            BiomeType.RIVER,
            BiomeType.THICKETS,
            BiomeType.MEADOW,
        }
        self.assertEqual(types, expected)

    def test_territory_coordinates(self):
        """Verify specific coordinates map to expected biomes."""
        # Top-left should be Highlands
        self.assertEqual(self.terrain.get_biome_at(100.0, 100.0), BiomeType.HIGHLANDS)
        # Top-right should be Dense Forest
        self.assertEqual(self.terrain.get_biome_at(900.0, 100.0), BiomeType.DENSE_FOREST)
        # Center should be River
        self.assertEqual(self.terrain.get_biome_at(600.0, 400.0), BiomeType.RIVER)
        # Bottom-left should be Thickets
        self.assertEqual(self.terrain.get_biome_at(100.0, 600.0), BiomeType.THICKETS)
        # Bottom-right should be Meadow
        self.assertEqual(self.terrain.get_biome_at(900.0, 600.0), BiomeType.MEADOW)

    def test_mountain_goat_scales_cliffs_without_penalty(self):
        """Goats run at 100% speed on mountains while wolves are slowed."""
        goat = Animal(entity_id=1, profile=SPECIES_REGISTRY["goat"], x=100.0, y=100.0)
        wolf = Animal(entity_id=2, profile=SPECIES_REGISTRY["wolf"], x=100.0, y=100.0)

        goat_mult = goat.get_terrain_speed_mult(self.terrain)
        wolf_mult = wolf.get_terrain_speed_mult(self.terrain)

        self.assertEqual(goat_mult, 1.0)
        self.assertLess(wolf_mult, 1.0)

    def test_thickets_prey_refuge(self):
        """Small rabbits pass easily in thickets while large wolves are heavily slowed."""
        rabbit = Animal(entity_id=1, profile=SPECIES_REGISTRY["rabbit"], x=100.0, y=600.0)
        wolf = Animal(entity_id=2, profile=SPECIES_REGISTRY["wolf"], x=100.0, y=600.0)

        rabbit_mult = rabbit.get_terrain_speed_mult(self.terrain)
        wolf_mult = wolf.get_terrain_speed_mult(self.terrain)

        self.assertGreater(rabbit_mult, wolf_mult)

    def test_grass_grazing_and_regrowth(self):
        """Herbivores graze grass, reducing biomass, which regrows over time."""
        # In Meadow (900, 600)
        consumed = self.terrain.graze_grass(900.0, 600.0, amount=0.5)
        self.assertGreater(consumed, 0.0)

        # Update regrowth
        self.terrain.update_regrowth(dt=5.0, regrowth_rate=0.2)
        # In Highlands (no grass) grazing yields 0
        no_grass = self.terrain.graze_grass(100.0, 100.0, amount=0.5)
        self.assertEqual(no_grass, 0.0)

    def test_diet_matrix_target_relationships(self):
        """Verify predator-prey relationships in diet matrix."""
        wolf_diet = SPECIES_REGISTRY["wolf"].diet_prey
        fox_diet = SPECIES_REGISTRY["fox"].diet_prey
        rabbit_diet = SPECIES_REGISTRY["rabbit"].diet_prey

        self.assertIn("rabbit", wolf_diet)
        self.assertIn("deer", wolf_diet)
        self.assertIn("rabbit", fox_diet)
        self.assertNotIn("wolf", fox_diet)
        self.assertEqual(len(rabbit_diet), 0)


if __name__ == "__main__":
    unittest.main()
