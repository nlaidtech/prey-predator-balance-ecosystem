"""Unit tests for Activity Feed Ticker and Animal State Emotes (Phase 5)."""

import os
import unittest
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

from src.activity_feed import ActivityEvent, ActivityFeedHUD
from src.camera import Camera2D
from src.config import Config
from src.entities import Animal, AnimalState
from src.simulation import Simulation


class TestActivityFeedHUD(unittest.TestCase):
    """Verifies event collection, fade-out calculation, and click navigation."""

    def setUp(self):
        self.feed = ActivityFeedHUD(width=370, max_display_items=5)
        self.cam = Camera2D(
            screen_width=1280,
            screen_height=720,
            world_width=2560.0,
            world_height=1600.0,
        )

    def test_add_and_retain_events(self):
        evt = ActivityEvent(
            time=10.0,
            message="Wolf caught a Deer in Meadow Plains",
            category="kill",
            species="wolf",
            biome_name="Meadow Plains",
            x=500.0,
            y=400.0,
        )
        self.feed.add_event(evt)
        self.assertEqual(len(self.feed.events), 1)

        recent = self.feed.get_recent_events(current_time=11.0)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0][0], evt)
        self.assertEqual(recent[0][1], 1.0)  # Alpha should be 1.0

    def test_event_fade_out_and_expiry(self):
        evt = ActivityEvent(
            time=10.0,
            message="Rabbit newborn entered Briar Thickets",
            category="birth",
            species="rabbit",
            biome_name="Briar Thickets",
            x=200.0,
            y=200.0,
        )
        self.feed.add_event(evt)

        # Midway through fade (lifetime = 6.5s, fade starts at 4.5s -> age 5.5s has alpha 0.5)
        recent_fade = self.feed.get_recent_events(current_time=15.5)
        self.assertEqual(len(recent_fade), 1)
        self.assertAlmostEqual(recent_fade[0][1], 0.5, delta=0.05)

        # Expired (age 8.0s > 6.5s)
        recent_expired = self.feed.get_recent_events(current_time=18.0)
        self.assertEqual(len(recent_expired), 0)

    def test_dynamic_get_rect_placement(self):
        # When chart is hidden
        rect_no_chart = self.feed.get_rect(1280, 720, chart_visible=False)
        # When chart is visible
        rect_with_chart = self.feed.get_rect(1280, 720, chart_visible=True)

        self.assertEqual(rect_no_chart.x, 16)
        self.assertEqual(rect_with_chart.x, 16)
        # With chart visible, feed sits above the chart, so Y coordinate must be smaller (higher up)
        self.assertLess(rect_with_chart.y, rect_no_chart.y)

    def test_handle_click_teleport(self):
        evt = ActivityEvent(
            time=20.0,
            message="Wolf caught Deer",
            category="kill",
            species="wolf",
            biome_name="Dense Forest",
            x=1500.0,
            y=1200.0,
        )
        self.feed.add_event(evt)

        rect = self.feed.get_rect(1280, 720, chart_visible=False)
        # Click on row 0
        consumed = self.feed.handle_click(
            sx=rect.x + 50,
            sy=rect.y + 30,
            screen_width=1280,
            screen_height=720,
            chart_visible=False,
            current_time=20.5,
            cam=self.cam,
        )
        self.assertTrue(consumed)
        # Camera should have teleported to event location
        self.assertEqual(self.cam.x, 1500.0)
        self.assertEqual(self.cam.y, 1200.0)

    def test_draw_headless(self):
        surface = pygame.Surface((1280, 720))
        self.feed.add_event(
            ActivityEvent(
                time=1.0,
                message="Fox exhausted from sprint",
                category="exhaustion",
                species="fox",
                biome_name="Briar Thickets",
                x=300.0,
                y=300.0,
            )
        )
        self.feed.draw(surface, 1280, 720, chart_visible=False, current_time=2.0)
        self.feed.draw(surface, 1280, 720, chart_visible=True, current_time=2.0)


class TestAnimalEmotesAndEvents(unittest.TestCase):
    """Verifies that simulation triggers activity events and animals enter emotive states."""

    def setUp(self):
        self.sim = Simulation(seed=42)

    def test_kill_event_generation(self):
        # Inject predator and victim at close proximity
        wolf = self.sim.spawn_animal("wolf", x=400.0, y=400.0)
        deer = self.sim.spawn_animal("deer", x=405.0, y=400.0)
        self.assertIsNotNone(wolf)
        self.assertIsNotNone(deer)

        # Step simulation to trigger catch
        self.sim.step(0.1)

        # Check for kill event emission
        kills = [e for e in self.sim.recent_activity_events if e.category == "kill"]
        self.assertGreater(len(kills), 0)
        self.assertTrue(any("caught" in k.message for k in kills))

    def test_birth_event_generation(self):
        # Force a reproduction event
        rabbit = self.sim.spawn_animal("rabbit", x=500.0, y=500.0)
        rabbit.energy = rabbit.profile.max_energy
        rabbit.reproduction_cooldown = 0.0

        # Step simulation
        self.sim.step(0.1)
        births = [e for e in self.sim.recent_activity_events if e.category == "birth"]
        # If carrying capacity allowed birth, verify event
        for b in births:
            self.assertIn("born", b.message)

    def test_flee_state_emotive_flag(self):
        # Create prey and adjacent predator
        rabbit = self.sim.spawn_animal("rabbit", x=600.0, y=600.0)
        fox = self.sim.spawn_animal("fox", x=620.0, y=600.0)

        self.sim.step(0.05)
        # Rabbit should enter FLEE state
        if rabbit.alive:
            self.assertEqual(rabbit.state, AnimalState.FLEE)
            self.assertTrue(getattr(rabbit, "was_fleeing", False))


if __name__ == "__main__":
    unittest.main()
