"""Tests for simulation-wide rules, determinism, non-negative counts, and metrics."""

import unittest

from src.config import Config
from src.simulation import Simulation


class TestSimulation(unittest.TestCase):
    def test_determinism_same_seed_gives_identical_run(self):
        """Milestone 1 requirement: Same seed produces the exact same run."""
        sim1 = Simulation(seed=999)
        sim2 = Simulation(seed=999)

        dt = 0.1
        steps = 100

        for _ in range(steps):
            sim1.step(dt)
            sim2.step(dt)

        self.assertEqual(sim1.prey_count, sim2.prey_count)
        self.assertEqual(sim1.predator_count, sim2.predator_count)
        self.assertAlmostEqual(sim1.time, sim2.time, places=5)

        # Check exact positions of all entities
        for p1, p2 in zip(sim1.prey_list, sim2.prey_list):
            self.assertEqual(p1.entity_id, p2.entity_id)
            self.assertEqual(p1.x, p2.x)
            self.assertEqual(p1.y, p2.y)
            self.assertEqual(p1.heading, p2.heading)

        for f1, f2 in zip(sim1.predator_list, sim2.predator_list):
            self.assertEqual(f1.entity_id, f2.entity_id)
            self.assertEqual(f1.x, f2.x)
            self.assertEqual(f1.y, f2.y)
            self.assertEqual(f1.energy, f2.energy)

    def test_different_seeds_produce_different_runs(self):
        """Different seeds diverge."""
        sim1 = Simulation(seed=111)
        sim2 = Simulation(seed=222)

        for _ in range(30):
            sim1.step(0.1)
            sim2.step(0.1)

        # Initial or post-step positions must differ
        self.assertNotEqual(sim1.prey_list[0].pos, sim2.prey_list[0].pos)

    def test_non_negative_counts(self):
        """Milestone 1 requirement: Entity counts are strictly non-negative at all times."""
        sim = Simulation(seed=42)
        dt = 0.1

        for _ in range(200):
            sim.step(dt)
            self.assertGreaterEqual(sim.prey_count, 0)
            self.assertGreaterEqual(sim.predator_count, 0)

        # Check recorded snapshots as well
        for snap in sim.metrics.snapshots:
            self.assertGreaterEqual(snap.prey_count, 0)
            self.assertGreaterEqual(snap.predator_count, 0)

    def test_metrics_recording_interval(self):
        """Metrics are recorded once per simulated second."""
        cfg = Config(metrics_interval=1.0)
        sim = Simulation(config=cfg, seed=42)

        # Simulate 5 seconds in 0.1s increments
        for _ in range(50):
            sim.step(0.1)

        # Should have snapshot at t=0, 1, 2, 3, 4, 5 => 6 snapshots
        self.assertEqual(len(sim.metrics.snapshots), 6)
        self.assertAlmostEqual(sim.metrics.snapshots[0].time, 0.0, places=2)
        self.assertAlmostEqual(sim.metrics.snapshots[-1].time, 5.0, places=2)


if __name__ == "__main__":
    unittest.main()
