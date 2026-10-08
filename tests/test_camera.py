"""Unit tests for Camera2D engine, coordinate transformations, and Minimap."""

import unittest

from src.camera import Camera2D
from src.minimap import Minimap


class MockEntity:
    def __init__(self, entity_id: int, x: float, y: float, alive: bool = True):
        self.entity_id = entity_id
        self.x = x
        self.y = y
        self.alive = alive


class TestCamera(unittest.TestCase):
    def setUp(self):
        self.screen_w = 1280
        self.screen_h = 720
        self.world_w = 2560.0
        self.world_h = 1600.0
        self.camera = Camera2D(
            screen_width=self.screen_w,
            screen_height=self.screen_h,
            world_width=self.world_w,
            world_height=self.world_h,
            min_zoom=0.4,
            max_zoom=2.0,
        )

    def test_initial_center_position(self):
        """Camera should initially center on world."""
        self.assertAlmostEqual(self.camera.x, self.world_w * 0.5)
        self.assertAlmostEqual(self.camera.y, self.world_h * 0.5)
        self.assertAlmostEqual(self.camera.zoom, 1.0)

    def test_coordinate_transform_roundtrip(self):
        """World -> Screen -> World transform must be lossless."""
        test_points = [
            (0.0, 0.0),
            (1280.0, 800.0),
            (2560.0, 1600.0),
            (543.21, 987.65),
        ]
        for wx, wy in test_points:
            sx, sy = self.camera.world_to_screen(wx, wy)
            round_wx, round_wy = self.camera.screen_to_world(sx, sy)
            self.assertAlmostEqual(wx, round_wx, places=5)
            self.assertAlmostEqual(wy, round_wy, places=5)

    def test_zoom_scaling_and_clamping(self):
        """Zoom must clamp strictly between min_zoom and max_zoom."""
        # Test max clamp
        self.camera.zoom_by(10.0)
        self.assertEqual(self.camera.target_zoom, 2.0)

        # Test min clamp
        self.camera.zoom_by(-10.0)
        self.assertEqual(self.camera.target_zoom, 0.4)

    def test_pan_clamping_to_world_bounds(self):
        """Panning cannot drift outside world bounds."""
        self.camera.pan(-5000.0, -5000.0)
        self.assertEqual(self.camera.target_x, 0.0)
        self.assertEqual(self.camera.target_y, 0.0)

        self.camera.pan(10000.0, 10000.0)
        self.assertEqual(self.camera.target_x, self.world_w)
        self.assertEqual(self.camera.target_y, self.world_h)

    def test_follow_entity_tracking(self):
        """Camera tracks follow target during update."""
        animal = MockEntity(entity_id=42, x=500.0, y=700.0, alive=True)
        self.camera.follow(42)

        # Update over several steps
        for _ in range(30):
            self.camera.update(dt=0.1, entities=[animal])

        self.assertAlmostEqual(self.camera.x, 500.0, delta=1.0)
        self.assertAlmostEqual(self.camera.y, 700.0, delta=1.0)

        # When target dies, follow target is cleared
        animal.alive = False
        self.camera.update(dt=0.1, entities=[animal])
        self.assertIsNone(self.camera.follow_target_id)

    def test_frustum_culling_visibility(self):
        """Entities well outside the camera viewport should be culled."""
        self.camera.teleport_to(1280.0, 800.0)
        self.camera.set_zoom(1.0)

        # Entity at camera center must be visible
        self.assertTrue(self.camera.is_circle_visible(1280.0, 800.0, radius=20.0))

        # Entity far outside viewport must not be visible
        self.assertFalse(self.camera.is_circle_visible(-500.0, -500.0, radius=20.0))
    def test_glide_to_sets_target_and_smoothly_approaches(self):
        """glide_to sets target coordinates and zoom, then lerp smoothly approaches."""
        self.camera.glide_to(2000.0, 1200.0, target_zoom=1.5)
        self.assertEqual(self.camera.target_x, 2000.0)
        self.assertEqual(self.camera.target_y, 1200.0)
        self.assertEqual(self.camera.target_zoom, 1.5)
        self.assertIsNone(self.camera.follow_target_id)

        # Update over several frames
        for _ in range(40):
            self.camera.update(dt=0.1)

        self.assertAlmostEqual(self.camera.x, 2000.0, delta=5.0)
        self.assertAlmostEqual(self.camera.y, 1200.0, delta=5.0)
        self.assertAlmostEqual(self.camera.zoom, 1.5, delta=0.05)

    def test_glide_to_clamps_within_world_bounds(self):
        """glide_to clamps destination safely inside world boundaries."""
        self.camera.glide_to(-1000.0, 50000.0)
        self.assertEqual(self.camera.target_x, 0.0)
        self.assertEqual(self.camera.target_y, self.world_h)


class TestMinimap(unittest.TestCase):
    def setUp(self):
        self.minimap = Minimap(width=220, height=140, margin=16)
        self.screen_w = 1280
        self.screen_h = 720
        self.world_w = 2560.0
        self.world_h = 1600.0

    def test_minimap_placement(self):
        """Minimap rect must be in bottom-right corner with margin."""
        rect = self.minimap.get_rect(self.screen_w, self.screen_h)
        self.assertEqual(rect.right, self.screen_w - 16)
        self.assertEqual(rect.bottom, self.screen_h - 16)
        self.assertEqual(rect.width, 220)
        self.assertEqual(rect.height, 140)

    def test_minimap_click_detection(self):
        """Checks if screen coordinates fall inside minimap."""
        rect = self.minimap.get_rect(self.screen_w, self.screen_h)
        inside_x = rect.x + 50
        inside_y = rect.y + 50
        self.assertTrue(self.minimap.is_clicked(inside_x, inside_y, self.screen_w, self.screen_h))
        self.assertFalse(self.minimap.is_clicked(10, 10, self.screen_w, self.screen_h))

    def test_minimap_to_world_conversion(self):
        """Minimap click accurately translates to world space."""
        rect = self.minimap.get_rect(self.screen_w, self.screen_h)
        # Center of minimap should map to center of world
        center_x = rect.x + rect.width // 2
        center_y = rect.y + rect.height // 2
        world_pt = self.minimap.screen_to_world(
            center_x, center_y,
            self.screen_w, self.screen_h,
            self.world_w, self.world_h,
        )
        self.assertIsNotNone(world_pt)
        wx, wy = world_pt
        self.assertAlmostEqual(wx, self.world_w * 0.5, delta=20.0)
        self.assertAlmostEqual(wy, self.world_h * 0.5, delta=20.0)


if __name__ == "__main__":
    unittest.main()
