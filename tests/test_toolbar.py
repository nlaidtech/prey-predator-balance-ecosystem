"""Unit tests for Interactive Toolbar HUD and Playback Controls (Phase 4)."""

import os
import unittest
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

from src.camera import Camera2D
from src.config import Config, ViewMode
from src.simulation import Simulation
from src.toolbar import ToolbarAction, ToolbarHUD


class TestToolbarHUD(unittest.TestCase):
    """Verifies Toolbar button hitboxes, click handling, and state dispatch."""

    def setUp(self):
        self.config = Config()
        self.toolbar = ToolbarHUD(x=16, y=142, width=700, height=76)
        self.sim = Simulation(config=self.config, seed=42)
        self.cam = Camera2D(
            screen_width=1280,
            screen_height=720,
            world_width=self.config.world_width,
            world_height=self.config.world_height,
        )

    def test_init_state(self):
        self.assertEqual(self.toolbar.x, 16)
        self.assertEqual(self.toolbar.y, 142)
        self.assertEqual(self.toolbar.width, 700)
        self.assertEqual(self.toolbar.height, 76)
        self.assertTrue(self.toolbar.visible)

    def test_rect_and_buttons(self):
        rect = self.toolbar.get_rect()
        self.assertEqual(rect.x, 16)
        self.assertEqual(rect.y, 142)
        btns = self.toolbar._get_button_rects()
        self.assertIn("pause", btns)
        self.assertIn("speed_1", btns)
        self.assertIn("speed_2", btns)
        self.assertIn("speed_5", btns)
        self.assertIn("reset", btns)
        self.assertIn("view_side", btns)
        self.assertIn("view_top", btns)
        self.assertIn("view_shapes", btns)
        self.assertIn("spawn_rabbit", btns)
        self.assertIn("spawn_wolf", btns)

    def test_click_outside(self):
        action = self.toolbar.handle_click(
            sx=800, sy=100,
            sim=self.sim, cam=self.cam,
            paused=False, current_speed=1, current_view=ViewMode.SIDE_VIEW,
        )
        self.assertFalse(action.consumed)

    def test_click_pause(self):
        btns = self.toolbar._get_button_rects()
        p_btn = btns["pause"]
        action = self.toolbar.handle_click(
            sx=p_btn.centerx, sy=p_btn.centery,
            sim=self.sim, cam=self.cam,
            paused=False, current_speed=1, current_view=ViewMode.SIDE_VIEW,
        )
        self.assertTrue(action.consumed)
        self.assertTrue(action.toggle_pause)

    def test_click_speeds(self):
        btns = self.toolbar._get_button_rects()
        for sp_key, expected_val in [("speed_1", 1), ("speed_2", 2), ("speed_5", 5)]:
            s_btn = btns[sp_key]
            action = self.toolbar.handle_click(
                sx=s_btn.centerx, sy=s_btn.centery,
                sim=self.sim, cam=self.cam,
                paused=False, current_speed=1, current_view=ViewMode.SIDE_VIEW,
            )
            self.assertTrue(action.consumed)
            self.assertEqual(action.set_speed, expected_val)

    def test_click_reset(self):
        btns = self.toolbar._get_button_rects()
        r_btn = btns["reset"]
        action = self.toolbar.handle_click(
            sx=r_btn.centerx, sy=r_btn.centery,
            sim=self.sim, cam=self.cam,
            paused=False, current_speed=1, current_view=ViewMode.SIDE_VIEW,
        )
        self.assertTrue(action.consumed)
        self.assertTrue(action.reset_simulation)
        self.assertIn("Reset", self.toolbar.notification_text)

    def test_click_view_modes(self):
        btns = self.toolbar._get_button_rects()
        action_top = self.toolbar.handle_click(
            sx=btns["view_top"].centerx, sy=btns["view_top"].centery,
            sim=self.sim, cam=self.cam,
            paused=False, current_speed=1, current_view=ViewMode.SIDE_VIEW,
        )
        self.assertTrue(action_top.consumed)
        self.assertEqual(action_top.set_view_mode, ViewMode.TOP_DOWN)

        action_shapes = self.toolbar.handle_click(
            sx=btns["view_shapes"].centerx, sy=btns["view_shapes"].centery,
            sim=self.sim, cam=self.cam,
            paused=False, current_speed=1, current_view=ViewMode.SIDE_VIEW,
        )
        self.assertTrue(action_shapes.consumed)
        self.assertEqual(action_shapes.set_view_mode, ViewMode.SHAPES)

    def test_click_overlays(self):
        btns = self.toolbar._get_button_rects()
        action_c = self.toolbar.handle_click(
            sx=btns["chart"].centerx, sy=btns["chart"].centery,
            sim=self.sim, cam=self.cam,
            paused=False, current_speed=1, current_view=ViewMode.SIDE_VIEW,
        )
        self.assertTrue(action_c.consumed)
        self.assertTrue(action_c.toggle_chart)

        action_b = self.toolbar.handle_click(
            sx=btns["biomes"].centerx, sy=btns["biomes"].centery,
            sim=self.sim, cam=self.cam,
            paused=False, current_speed=1, current_view=ViewMode.SIDE_VIEW,
        )
        self.assertTrue(action_b.consumed)
        self.assertTrue(action_b.toggle_biomes)

    def test_click_quick_spawn(self):
        initial_count = len(self.sim.animals)
        btns = self.toolbar._get_button_rects()

        # Spawn Rabbit
        action_rab = self.toolbar.handle_click(
            sx=btns["spawn_rabbit"].centerx, sy=btns["spawn_rabbit"].centery,
            sim=self.sim, cam=self.cam,
            paused=False, current_speed=1, current_view=ViewMode.SIDE_VIEW,
        )
        self.assertTrue(action_rab.consumed)
        self.assertEqual(action_rab.spawned_species, "rabbit")
        self.assertEqual(len(self.sim.animals), initial_count + 1)
        self.assertEqual(self.sim.animals[-1].profile.name, "rabbit")

        # Spawn Wolf
        action_wolf = self.toolbar.handle_click(
            sx=btns["spawn_wolf"].centerx, sy=btns["spawn_wolf"].centery,
            sim=self.sim, cam=self.cam,
            paused=False, current_speed=1, current_view=ViewMode.SIDE_VIEW,
        )
        self.assertTrue(action_wolf.consumed)
        self.assertEqual(action_wolf.spawned_species, "wolf")
        self.assertEqual(len(self.sim.animals), initial_count + 2)
        self.assertEqual(self.sim.animals[-1].profile.name, "wolf")

    def test_notification_expiry(self):
        self.toolbar.notify("Alert Test", duration=1.0)
        self.assertEqual(self.toolbar.notification_text, "Alert Test")
        self.toolbar.update(0.5)
        self.assertEqual(self.toolbar.notification_text, "Alert Test")
        self.toolbar.update(0.6)
        self.assertEqual(self.toolbar.notification_text, "")

    def test_draw_headless(self):
        surface = pygame.Surface((1280, 720))
        self.toolbar.draw(
            surface=surface,
            paused=False,
            current_speed=2,
            current_view=ViewMode.SIDE_VIEW,
            chart_visible=False,
            biomes_visible=True,
            mouse_pos=(100, 150),
        )


class TestSimulationSpawnAndReset(unittest.TestCase):
    """Verifies dynamic animal injection and simulation reset."""

    def setUp(self):
        self.sim = Simulation(seed=99)

    def test_spawn_valid_species(self):
        init_cnt = len(self.sim.animals)
        animal = self.sim.spawn_animal("bear", x=500.0, y=400.0)
        self.assertIsNotNone(animal)
        self.assertEqual(animal.profile.name, "bear")
        self.assertEqual(animal.x, 500.0)
        self.assertEqual(animal.y, 400.0)
        self.assertEqual(len(self.sim.animals), init_cnt + 1)

    def test_spawn_invalid_species(self):
        init_cnt = len(self.sim.animals)
        animal = self.sim.spawn_animal("dragon")
        self.assertIsNone(animal)
        self.assertEqual(len(self.sim.animals), init_cnt)

    def test_reset(self):
        self.sim.step(5.0)
        self.assertGreater(self.sim.time, 0.0)
        self.sim.reset(seed=123)
        self.assertEqual(self.sim.time, 0.0)
        self.assertEqual(self.sim.seed, 123)
        self.assertGreater(len(self.sim.animals), 0)


if __name__ == "__main__":
    unittest.main()
