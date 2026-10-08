"""Unit tests for InspectorCard HUD and biome watermark toggling."""

import unittest
import pygame

from src.camera import Camera2D
from src.config import Config
from src.inspector import InspectorCard
from src.renderer import Renderer
from src.simulation import Simulation


class TestInspector(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.config = Config(world_width=1200, world_height=800)
        self.sim = Simulation(config=self.config, seed=42)
        self.camera = Camera2D(
            screen_width=1280,
            screen_height=720,
            world_width=1200,
            world_height=800,
        )
        self.inspector = InspectorCard(width=310, height=370)

    def test_select_and_deselect(self):
        """Selecting an entity sets selected_id and triggers slide-in."""
        self.assertIsNone(self.inspector.selected_id)
        self.assertEqual(self.inspector.target_progress, 0.0)

        self.inspector.select(10)
        self.assertEqual(self.inspector.selected_id, 10)
        self.assertEqual(self.inspector.target_progress, 1.0)

        self.inspector.deselect()
        self.assertIsNone(self.inspector.selected_id)
        self.assertEqual(self.inspector.target_progress, 0.0)

    def test_get_rect_slide_positions(self):
        """Card rect slides in from right screen edge."""
        self.inspector.slide_progress = 0.0
        rect_closed = self.inspector.get_rect(1280, 720)
        self.assertEqual(rect_closed.x, 1280)

        self.inspector.slide_progress = 1.0
        rect_open = self.inspector.get_rect(1280, 720)
        self.assertEqual(rect_open.right, 1280 - 16)

    def test_handle_click_close_button(self):
        """Clicking [X] button deselects the inspected animal."""
        self.inspector.select(5)
        self.inspector.slide_progress = 1.0
        card_rect = self.inspector.get_rect(1280, 720)
        close_rect = self.inspector.get_close_btn_rect(card_rect)

        consumed = self.inspector.handle_click(
            close_rect.centerx, close_rect.centery,
            1280, 720,
            self.camera,
        )
        self.assertTrue(consumed)
        self.assertIsNone(self.inspector.selected_id)

    def test_handle_click_follow_camera_toggle(self):
        """Clicking Follow button sets and clears camera follow target."""
        self.inspector.select(7)
        self.inspector.slide_progress = 1.0
        card_rect = self.inspector.get_rect(1280, 720)
        follow_rect = self.inspector.get_follow_btn_rect(card_rect)

        # 1. Toggle ON
        consumed = self.inspector.handle_click(
            follow_rect.centerx, follow_rect.centery,
            1280, 720,
            self.camera,
        )
        self.assertTrue(consumed)
        self.assertEqual(self.camera.follow_target_id, 7)

        # 2. Toggle OFF
        self.inspector.handle_click(
            follow_rect.centerx, follow_rect.centery,
            1280, 720,
            self.camera,
        )
        self.assertIsNone(self.camera.follow_target_id)

    def test_update_closes_when_animal_dies(self):
        """Inspector card slides closed when inspected animal dies."""
        first_animal = self.sim.animals[0]
        self.inspector.select(first_animal.entity_id)
        self.inspector.slide_progress = 1.0

        # Kill the animal
        first_animal.alive = False
        self.inspector.update(dt=0.1, sim=self.sim)

        self.assertEqual(self.inspector.target_progress, 0.0)

    def test_renderer_toggle_biome_watermarks(self):
        """Renderer can toggle biome watermarks on and off."""
        renderer = Renderer(config=self.config, camera=self.camera)
        initial = renderer.show_biome_watermarks
        renderer.toggle_biome_watermarks()
        self.assertEqual(renderer.show_biome_watermarks, not initial)
        renderer.toggle_biome_watermarks()
        self.assertEqual(renderer.show_biome_watermarks, initial)


if __name__ == "__main__":
    unittest.main()
