"""Unit tests for Population Dynamics Chart HUD and detailed metrics."""

import os
import unittest
import pygame

# Run pygame in headless mode for CI/test environments
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

from src.chart import PopulationChartHUD
from src.metrics import SimulationMetrics, DetailedSpeciesSnapshot
from src.simulation import Simulation


class TestPopulationChartHUD(unittest.TestCase):
    """Verifies PopulationChartHUD layout, interactions, and drawing."""

    def setUp(self):
        self.chart = PopulationChartHUD(width=600, height=230)
        self.screen_width = 1280
        self.screen_height = 800

    def test_init_state(self):
        self.assertFalse(self.chart.visible)
        self.assertEqual(self.chart.width, 600)
        self.assertEqual(self.chart.height, 230)
        self.assertIn("rabbit", self.chart.species_colors)
        self.assertIn("wolf", self.chart.species_colors)

    def test_toggle(self):
        self.chart.toggle()
        self.assertTrue(self.chart.visible)
        self.chart.toggle()
        self.assertFalse(self.chart.visible)

    def test_get_rect(self):
        rect = self.chart.get_rect(self.screen_width, self.screen_height)
        self.assertEqual(rect.x, 16)
        self.assertEqual(rect.y, self.screen_height - 230 - 16)
        self.assertEqual(rect.width, 600)
        self.assertEqual(rect.height, 230)

    def test_handle_click_when_hidden(self):
        self.chart.visible = False
        consumed = self.chart.handle_click(50, 650, self.screen_width, self.screen_height)
        self.assertFalse(consumed)

    def test_handle_click_outside(self):
        self.chart.visible = True
        consumed = self.chart.handle_click(700, 100, self.screen_width, self.screen_height)
        self.assertFalse(consumed)
        self.assertTrue(self.chart.visible)

    def test_handle_click_body_consumed(self):
        self.chart.visible = True
        rect = self.chart.get_rect(self.screen_width, self.screen_height)
        consumed = self.chart.handle_click(rect.x + 50, rect.y + 50, self.screen_width, self.screen_height)
        self.assertTrue(consumed)
        self.assertTrue(self.chart.visible)

    def test_handle_click_close_button(self):
        self.chart.visible = True
        rect = self.chart.get_rect(self.screen_width, self.screen_height)
        # Close button is near rect.right - 24, rect.y + 6
        consumed = self.chart.handle_click(rect.right - 15, rect.y + 12, self.screen_width, self.screen_height)
        self.assertTrue(consumed)
        self.assertFalse(self.chart.visible)

    def test_draw_headless(self):
        sim = Simulation(seed=42)
        surface = pygame.Surface((self.screen_width, self.screen_height))
        # Draw while hidden
        self.chart.visible = False
        self.chart.draw(surface, sim, self.screen_width, self.screen_height)

        # Draw while visible
        self.chart.visible = True
        self.chart.draw(surface, sim, self.screen_width, self.screen_height)


class TestDetailedMetrics(unittest.TestCase):
    """Verifies detailed species history, buffer truncation, and equilibrium analysis."""

    def setUp(self):
        self.metrics = SimulationMetrics(history_window=10.0)

    def test_rolling_buffer_truncation(self):
        counts_t0 = {"rabbit": 50, "deer": 10, "goat": 10, "fox": 10, "wolf": 5, "bear": 2}
        self.metrics.record_detailed_snapshot(0.0, counts_t0)
        self.assertEqual(len(self.metrics.detailed_history), 1)

        # Record at t = 5.0
        self.metrics.record_detailed_snapshot(5.0, counts_t0)
        self.assertEqual(len(self.metrics.detailed_history), 2)

        # Record at t = 16.0 (exceeds rolling buffer 10.0s, t0 at 0.0 should be purged)
        self.metrics.record_detailed_snapshot(16.0, counts_t0)
        self.assertNotIn(0.0, [snap.time for snap in self.metrics.detailed_history])
        self.assertIn(16.0, [snap.time for snap in self.metrics.detailed_history])

    def test_get_species_trend(self):
        counts_t0 = {"rabbit": 50, "wolf": 10}
        self.metrics.record_detailed_snapshot(0.0, counts_t0)

        # Rising trend
        counts_t1 = {"rabbit": 60, "wolf": 8}
        self.metrics.record_detailed_snapshot(5.0, counts_t1)

        trend_rabbit, delta_rabbit = self.metrics.get_species_trend("rabbit", window_seconds=10.0)
        self.assertEqual(trend_rabbit, "rising")
        self.assertEqual(delta_rabbit, 10)

        trend_wolf, delta_wolf = self.metrics.get_species_trend("wolf", window_seconds=10.0)
        self.assertEqual(trend_wolf, "declining")
        self.assertEqual(delta_wolf, -2)

        # Stable trend (delta within [-1, 1])
        counts_t2 = {"rabbit": 61, "wolf": 8}
        self.metrics.record_detailed_snapshot(6.0, counts_t2)
        trend_wolf_stable, delta_wolf_stable = self.metrics.get_species_trend("wolf", window_seconds=2.0)
        self.assertEqual(trend_wolf_stable, "stable")
        self.assertEqual(delta_wolf_stable, 0)

    def test_get_equilibrium_status(self):
        # Healthy population
        counts_healthy = {"rabbit": 60, "deer": 15, "goat": 12, "fox": 10, "wolf": 6, "bear": 3}
        self.metrics.record_detailed_snapshot(1.0, counts_healthy)
        stable, status = self.metrics.get_equilibrium_status()
        self.assertTrue(stable)
        self.assertIn("DYNAMIC EQUILIBRIUM", status)

        # Prey extinction
        counts_no_prey = {"rabbit": 0, "deer": 0, "goat": 0, "fox": 5, "wolf": 3, "bear": 1}
        self.metrics.record_detailed_snapshot(2.0, counts_no_prey)
        stable, status = self.metrics.get_equilibrium_status()
        self.assertFalse(stable)
        self.assertIn("PREY EXTINCTION", status)

        # Predator extinction
        counts_no_pred = {"rabbit": 100, "deer": 20, "goat": 20, "fox": 0, "wolf": 0, "bear": 0}
        self.metrics.record_detailed_snapshot(3.0, counts_no_pred)
        stable, status = self.metrics.get_equilibrium_status()
        self.assertFalse(stable)
        self.assertIn("PREDATOR EXTINCTION", status)


if __name__ == "__main__":
    unittest.main()
