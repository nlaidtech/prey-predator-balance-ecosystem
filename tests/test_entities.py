"""Tests for entity behaviors: movement, fleeing, predation, energy, and reproduction."""

import math
import random
import unittest

from src.config import Config
from src.entities import AnimalState, Prey, Predator


class TestEntities(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.rng = random.Random(123)

    def test_fox_adjacent_to_rabbit_eats_it(self):
        """Milestone 1 requirement: A fox adjacent to a rabbit eats it."""
        fox = Predator(entity_id=1, x=100.0, y=100.0, speed=0.0, initial_energy=20.0)
        # Place rabbit well within predator_catch_radius (16.0)
        rabbit = Prey(entity_id=2, x=105.0, y=100.0, speed=0.0)

        initial_energy = fox.energy
        # Step behavior with rabbit adjacent
        caught = fox.update_behavior(dt=0.1, config=self.config, rng=self.rng, nearest_prey=rabbit)

        self.assertIsNotNone(caught)
        self.assertEqual(caught.entity_id, rabbit.entity_id)
        self.assertEqual(fox.state, AnimalState.EAT)
        self.assertGreater(fox.energy, initial_energy)

    def test_rabbit_flees_when_predator_in_vision(self):
        """Rabbit flees away from a predator within vision range."""
        fox = Predator(entity_id=1, x=100.0, y=100.0)
        rabbit = Prey(entity_id=2, x=140.0, y=100.0)  # Distance 40 < vision_radius 110

        initial_dist = rabbit.distance_to(fox)
        rabbit.update_behavior(dt=0.1, config=self.config, rng=self.rng, nearest_predator=fox)

        self.assertEqual(rabbit.state, AnimalState.FLEE)
        new_dist = rabbit.distance_to(fox)
        self.assertGreater(new_dist, initial_dist)

    def test_rabbit_crowding_limits_birth_rate(self):
        """Crowding: birth rate shrinks as rabbits reach carrying capacity."""
        rabbit = Prey(entity_id=1, x=200.0, y=200.0)
        rabbit.reproduction_cooldown = 0.0

        # At carrying capacity, probability must be 0
        can_rep = rabbit.can_reproduce(
            self.config,
            current_prey_count=self.config.prey_carrying_capacity,
            rng=self.rng,
            dt=1.0,
        )
        self.assertFalse(can_rep)

        # Above carrying capacity, probability must also be 0
        can_rep_over = rabbit.can_reproduce(
            self.config,
            current_prey_count=self.config.prey_carrying_capacity + 50,
            rng=self.rng,
            dt=1.0,
        )
        self.assertFalse(can_rep_over)

    def test_fox_starvation_and_death(self):
        """Predator without food burns energy and starves to death."""
        fox = Predator(entity_id=1, x=500.0, y=500.0, initial_energy=1.0)
        # dt large enough to deplete 1.0 energy at 1.8/s
        dt = 1.0
        caught = fox.update_behavior(dt=dt, config=self.config, rng=self.rng, nearest_prey=None)

        self.assertIsNone(caught)
        self.assertFalse(fox.alive)
        self.assertEqual(fox.state, AnimalState.DIE)
        self.assertLessEqual(fox.energy, 0.0)

    def test_boundary_enforcement(self):
        """Animals cannot walk past configured boundary padding."""
        rabbit = Prey(entity_id=1, x=5.0, y=5.0, heading=math.pi)  # Heading left
        rabbit.enforce_boundaries(self.config)
        self.assertGreaterEqual(rabbit.x, self.config.boundary_padding)
        self.assertGreaterEqual(rabbit.y, self.config.boundary_padding)


if __name__ == "__main__":
    unittest.main()
