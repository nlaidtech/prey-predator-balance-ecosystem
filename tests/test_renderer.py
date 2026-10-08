"""Verification tests for the decoupled renderer."""

import unittest
import pygame

from src.config import Config
from src.renderer import Renderer, ViewMode
from src.simulation import Simulation


class TestRenderer(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.config = Config(world_width=800, world_height=600)
        self.sim = Simulation(config=self.config, seed=42)
        self.renderer = Renderer(config=self.config)
        # Use an offscreen Surface to test rendering headlessly
        self.surface = pygame.Surface((800, 600))

    def test_renderer_side_view_mode(self):
        self.renderer.view_mode = ViewMode.SIDE_VIEW
        # Advance simulation 1 step and render
        self.sim.step(0.1)
        self.renderer.draw(self.surface, self.sim, dt=0.1, paused=False, fps=60.0)

    def test_renderer_top_down_view_mode(self):
        self.renderer.view_mode = ViewMode.TOP_DOWN
        self.sim.step(0.1)
        self.renderer.draw(self.surface, self.sim, dt=0.1, paused=False, fps=60.0)

    def test_renderer_shapes_view_mode(self):
        self.renderer.view_mode = ViewMode.SHAPES
        self.sim.step(0.1)
        self.renderer.draw(self.surface, self.sim, dt=0.1, paused=False, fps=60.0)

    def test_view_mode_cycle(self):
        initial = self.renderer.view_mode
        self.renderer.cycle_view_mode()
        self.assertNotEqual(self.renderer.view_mode, initial)
        self.renderer.cycle_view_mode()
        self.renderer.cycle_view_mode()
        self.assertEqual(self.renderer.view_mode, initial)


if __name__ == "__main__":
    unittest.main()
