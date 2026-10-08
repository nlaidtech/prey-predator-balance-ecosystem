"""2D Camera Engine for the wildlife ecosystem simulation.

Provides smooth pan, zoom, coordinate transforms, frustum culling,
follow-camera tracking, and radar minimap coordinate mapping.
"""

from __future__ import annotations
import math
from typing import Optional, Tuple


class Camera2D:
    """Pan-and-zoom 2D camera with smooth interpolation and viewport management."""

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        world_width: float,
        world_height: float,
        min_zoom: float = 0.25,
        max_zoom: float = 2.5,
    ) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.world_width = world_width
        self.world_height = world_height
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom

        # Center camera on world initially
        self.x: float = world_width * 0.5
        self.y: float = world_height * 0.5
        self.target_x: float = self.x
        self.target_y: float = self.y

        # Zoom level
        self.zoom: float = 1.0
        self.target_zoom: float = 1.0

        # Follow camera
        self.follow_target_id: Optional[int] = None

        # Drag state
        self.is_dragging: bool = False
        self.drag_start_screen: Tuple[int, int] = (0, 0)
        self.drag_start_cam: Tuple[float, float] = (self.x, self.y)

        # Pan speed for keyboard (world units per second)
        self.pan_speed: float = 800.0

    # ---------------------------------------------------------
    # Coordinate Transforms
    # ---------------------------------------------------------

    def world_to_screen(self, wx: float, wy: float) -> Tuple[float, float]:
        """Converts a world position (wx, wy) to a screen pixel position (sx, sy)."""
        sx = (wx - self.x) * self.zoom + self.screen_width * 0.5
        sy = (wy - self.y) * self.zoom + self.screen_height * 0.5
        return (sx, sy)

    def screen_to_world(self, sx: float, sy: float) -> Tuple[float, float]:
        """Converts a screen pixel position (sx, sy) to a world position (wx, wy)."""
        wx = (sx - self.screen_width * 0.5) / self.zoom + self.x
        wy = (sy - self.screen_height * 0.5) / self.zoom + self.y
        return (wx, wy)

    def scale_length(self, length: float) -> float:
        """Scales a world length by current zoom."""
        return length * self.zoom

    def get_viewport_world_bounds(self) -> Tuple[float, float, float, float]:
        """Returns the world-space bounding box currently visible on screen.

        Returns (min_x, min_y, max_x, max_y).
        """
        top_left = self.screen_to_world(0.0, 0.0)
        bottom_right = self.screen_to_world(float(self.screen_width), float(self.screen_height))
        return (top_left[0], top_left[1], bottom_right[0], bottom_right[1])

    def is_circle_visible(self, wx: float, wy: float, radius: float = 30.0) -> bool:
        """Frustum culling: checks if a circle in world space intersects the viewport."""
        min_x, min_y, max_x, max_y = self.get_viewport_world_bounds()
        return not (
            wx + radius < min_x
            or wx - radius > max_x
            or wy + radius < min_y
            or wy - radius > max_y
        )

    def is_in_view(self, wx: float, wy: float, margin: float = 30.0) -> bool:
        """Checks if a world position is within the visible viewport plus margin."""
        return self.is_circle_visible(wx, wy, radius=margin)

    def is_rect_visible(self, min_x: float, min_y: float, max_x: float, max_y: float) -> bool:
        """Checks if a world rectangle intersects the viewport."""
        vp_min_x, vp_min_y, vp_max_x, vp_max_y = self.get_viewport_world_bounds()
        return not (
            max_x < vp_min_x
            or min_x > vp_max_x
            or max_y < vp_min_y
            or min_y > vp_max_y
        )

    # ---------------------------------------------------------
    # Camera Movement & Zoom Controls
    # ---------------------------------------------------------

    def pan(self, dx: float, dy: float) -> None:
        """Pans the target position by (dx, dy) in world units. Stops following target."""
        self.follow_target_id = None
        self.target_x += dx
        self.target_y += dy
        self._clamp_target()

    def zoom_by(self, delta: float, mouse_screen_pos: Optional[Tuple[int, int]] = None) -> None:
        """Adjusts target zoom level. If mouse_screen_pos is provided, zooms toward cursor."""
        old_target_zoom = self.target_zoom
        new_zoom = max(self.min_zoom, min(self.max_zoom, self.target_zoom + delta))
        if abs(new_zoom - old_target_zoom) < 1e-5:
            return

        self.target_zoom = new_zoom

        # If zooming toward a screen point, adjust target_x/target_y so cursor stays fixed
        if mouse_screen_pos is not None:
            mx, my = mouse_screen_pos
            # World pos under cursor before zoom
            cursor_wx = (mx - self.screen_width * 0.5) / old_target_zoom + self.target_x
            cursor_wy = (my - self.screen_height * 0.5) / old_target_zoom + self.target_y
            # Reposition target so cursor_wx/wy stays under mx/my at new_zoom
            self.target_x = cursor_wx - (mx - self.screen_width * 0.5) / new_zoom
            self.target_y = cursor_wy - (my - self.screen_height * 0.5) / new_zoom
            self._clamp_target()

    def set_zoom(self, zoom: float) -> None:
        """Instantly sets zoom level, clamped between min and max."""
        clamped = max(self.min_zoom, min(self.max_zoom, zoom))
        self.zoom = clamped
        self.target_zoom = clamped

    def glide_to(self, wx: float, wy: float, target_zoom: Optional[float] = None) -> None:
        """Smoothly glides the camera center to (wx, wy) via lerp. Stops following target."""
        self.follow_target_id = None
        self.target_x = max(0.0, min(self.world_width, wx))
        self.target_y = max(0.0, min(self.world_height, wy))
        if target_zoom is not None:
            self.target_zoom = max(self.min_zoom, min(self.max_zoom, target_zoom))

    def teleport_to(self, wx: float, wy: float) -> None:
        """Instantly moves camera center to (wx, wy). Stops following target."""
        self.follow_target_id = None
        self.target_x = max(0.0, min(self.world_width, wx))
        self.target_y = max(0.0, min(self.world_height, wy))
        self.x = self.target_x
        self.y = self.target_y

    def follow(self, target_id: Optional[int]) -> None:
        """Sets an animal entity_id to follow."""
        self.follow_target_id = target_id

    def start_drag(self, screen_x: int, screen_y: int) -> None:
        """Begins right-click/middle-click drag pan."""
        self.follow_target_id = None
        self.is_dragging = True
        self.drag_start_screen = (screen_x, screen_y)
        self.drag_start_cam = (self.x, self.y)

    def handle_drag(self, screen_x: int, screen_y: int) -> None:
        """Updates camera position during drag."""
        if not self.is_dragging:
            return
        dx_screen = screen_x - self.drag_start_screen[0]
        dy_screen = screen_y - self.drag_start_screen[1]
        # Invert: dragging mouse right moves world right, camera moves left
        dx_world = dx_screen / self.zoom
        dy_world = dy_screen / self.zoom
        self.target_x = self.drag_start_cam[0] - dx_world
        self.target_y = self.drag_start_cam[1] - dy_world
        self._clamp_target()
        self.x = self.target_x
        self.y = self.target_y

    def end_drag(self) -> None:
        """Ends drag operation."""
        self.is_dragging = False

    def _clamp_target(self) -> None:
        """Clamps target position to world boundaries."""
        self.target_x = max(0.0, min(self.world_width, self.target_x))
        self.target_y = max(0.0, min(self.world_height, self.target_y))

    # ---------------------------------------------------------
    # Frame Update (Lerp smoothing)
    # ---------------------------------------------------------

    def update(self, dt: float, entities: Optional[list] = None) -> None:
        """Updates camera position and zoom with smooth lerp interpolation."""
        # 1. Update target if following an entity
        if self.follow_target_id is not None and entities:
            found = False
            for e in entities:
                if getattr(e, "entity_id", None) == self.follow_target_id and getattr(e, "alive", False):
                    self.target_x = e.x
                    self.target_y = e.y
                    self._clamp_target()
                    found = True
                    break
            if not found:
                self.follow_target_id = None

        # 2. Smoothly interpolate position (exponential decay lerp)
        pos_factor = 1.0 - math.exp(-12.0 * dt)
        self.x += (self.target_x - self.x) * pos_factor
        self.y += (self.target_y - self.y) * pos_factor

        # 3. Smoothly interpolate zoom
        zoom_factor = 1.0 - math.exp(-14.0 * dt)
        self.zoom += (self.target_zoom - self.zoom) * zoom_factor
