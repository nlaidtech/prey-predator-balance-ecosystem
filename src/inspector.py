"""Animal Inspector Card HUD component.

Provides an interactive slide-out card on the right screen edge displaying
an inspected animal's avatar, species traits, live AI state, energy/thirst/stamina
gauges, current quarry/threat, and camera follow toggle.
"""

from __future__ import annotations
import math
from typing import Optional, Tuple
import pygame

from src.camera import Camera2D
from src.entities import Animal, AnimalState
from src.simulation import Simulation


class InspectorCard:
    """Slide-out inspection card displaying deep telemetry for a selected animal."""

    def __init__(self, width: int = 310, height: int = 370) -> None:
        self.width = width
        self.height = height
        self.selected_id: Optional[int] = None

        # Slide-out animation progress: 0.0 (closed) to 1.0 (open)
        self.slide_progress: float = 0.0
        self.target_progress: float = 0.0

        # Local avatar animation clock
        self.avatar_timer: float = 0.0
        self.avatar_frame_idx: int = 0

        # UI fonts
        pygame.font.init()
        self.title_font = pygame.font.SysFont("consolas", 16, bold=True)
        self.body_font = pygame.font.SysFont("consolas", 13, bold=True)
        self.small_font = pygame.font.SysFont("consolas", 11)

    def select(self, entity_id: Optional[int]) -> None:
        """Selects an animal entity ID or deselects if None."""
        self.selected_id = entity_id
        self.target_progress = 1.0 if entity_id is not None else 0.0

    def deselect(self) -> None:
        """Closes the inspector card."""
        self.selected_id = None
        self.target_progress = 0.0

    def get_rect(self, screen_width: int, screen_height: int) -> pygame.Rect:
        """Computes current on-screen rectangle with slide animation."""
        x_closed = screen_width
        x_open = screen_width - self.width - 16
        current_x = int(x_closed + (x_open - x_closed) * self.slide_progress)
        y = 16  # Top-right alignment
        return pygame.Rect(current_x, y, self.width, self.height)

    def get_follow_btn_rect(self, card_rect: pygame.Rect) -> pygame.Rect:
        """Rectangle for 'Follow Camera' button."""
        return pygame.Rect(card_rect.x + 16, card_rect.y + self.height - 42, self.width - 32, 28)

    def get_close_btn_rect(self, card_rect: pygame.Rect) -> pygame.Rect:
        """Rectangle for close 'X' button."""
        return pygame.Rect(card_rect.right - 28, card_rect.y + 10, 20, 20)

    def handle_click(
        self,
        sx: int,
        sy: int,
        screen_width: int,
        screen_height: int,
        camera: Camera2D,
    ) -> bool:
        """Handles mouse click on the inspector card. Returns True if consumed."""
        if self.slide_progress < 0.2:
            return False

        card_rect = self.get_rect(screen_width, screen_height)
        if not card_rect.collidepoint(sx, sy):
            return False

        # Close button
        if self.get_close_btn_rect(card_rect).collidepoint(sx, sy):
            self.deselect()
            if camera.follow_target_id == self.selected_id:
                camera.follow(None)
            return True

        # Follow button
        if self.get_follow_btn_rect(card_rect).collidepoint(sx, sy):
            if camera.follow_target_id == self.selected_id:
                camera.follow(None)
            else:
                camera.follow(self.selected_id)
            return True

        return True  # Click consumed by card background

    def update(self, dt: float, sim: Simulation) -> None:
        """Updates slide transition and checks entity liveness."""
        # Check if selected animal died or vanished
        if self.selected_id is not None:
            alive_match = next((a for a in sim.animals if a.entity_id == self.selected_id and a.alive), None)
            if alive_match is None:
                # Animal died
                self.target_progress = 0.0
                if self.slide_progress < 0.05:
                    self.selected_id = None

        # Smooth slide lerp
        factor = 1.0 - math.exp(-14.0 * dt)
        self.slide_progress += (self.target_progress - self.slide_progress) * factor

        # Avatar animation timer
        self.avatar_timer += dt
        if self.avatar_timer >= 0.12:
            self.avatar_timer -= 0.12
            self.avatar_frame_idx = (self.avatar_frame_idx + 1) % 6

    def draw(
        self,
        surface: pygame.Surface,
        sim: Simulation,
        camera: Camera2D,
        sprite_cache,
    ) -> None:
        """Renders the slide-out inspector card."""
        if self.slide_progress < 0.01:
            return

        card_rect = self.get_rect(camera.screen_width, camera.screen_height)
        animal = next((a for a in sim.animals if a.entity_id == self.selected_id and a.alive), None)
        if not animal:
            return

        # 1. Background Card Surface with alpha
        card_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(card_surf, (15, 19, 26, 235), (0, 0, self.width, self.height), border_radius=10)
        pygame.draw.rect(card_surf, (55, 75, 105, 240), (0, 0, self.width, self.height), 1, border_radius=10)

        # 2. Header
        sp_name = animal.profile.name.capitalize()
        title_txt = f"{sp_name} #{animal.entity_id}"
        t_surf = self.title_font.render(title_txt, True, (245, 245, 245))
        card_surf.blit(t_surf, (16, 12))

        # Close button [X]
        close_rect_local = pygame.Rect(self.width - 28, 10, 20, 20)
        pygame.draw.rect(card_surf, (40, 50, 68), close_rect_local, border_radius=4)
        x_txt = self.body_font.render("x", True, (200, 210, 225))
        card_surf.blit(x_txt, (self.width - 23, 8))

        # Subtitle: Trophic role & Native Zone
        zone_name = animal.home_zone.biome_type.value if animal.home_zone else "Wandering"
        role_txt = f"{animal.profile.trophic_role.value}  |  {zone_name}"
        r_surf = self.small_font.render(role_txt, True, (150, 185, 215))
        card_surf.blit(r_surf, (16, 34))

        # Divider line
        pygame.draw.line(card_surf, (45, 60, 80), (16, 52), (self.width - 16, 52), 1)

        # 3. Avatar Box
        avatar_box = pygame.Rect(16, 60, 68, 68)
        pygame.draw.rect(card_surf, (24, 32, 44), avatar_box, border_radius=6)
        pygame.draw.rect(card_surf, (60, 80, 105), avatar_box, 1, border_radius=6)

        # Render animated sprite inside avatar box
        sp_set = sprite_cache.species.get(animal.profile.name)
        if sp_set and sp_set.anims.get("walk"):
            frames = sp_set.anims["walk"]
            frame = frames[self.avatar_frame_idx % len(frames)]
            # Center inside box
            f_rect = frame.get_rect(center=avatar_box.center)
            card_surf.blit(frame, f_rect)

        # 4. AI State Badge
        state_colors = {
            AnimalState.WANDER: ((45, 110, 180), "WANDERING"),
            AnimalState.GRAZE: ((45, 160, 80), "GRAZING"),
            AnimalState.CHASE: ((215, 60, 55), "CHASING (HUNT)"),
            AnimalState.FLEE: ((230, 140, 35), "FLEEING (EVADE)"),
            AnimalState.DRINK: ((35, 150, 210), "DRINKING (RIVER)"),
            AnimalState.EAT: ((185, 55, 150), "FEASTING"),
        }
        badge_col, state_str = state_colors.get(animal.state, ((100, 100, 100), animal.state.value.upper()))
        badge_rect = pygame.Rect(94, 64, 198, 24)
        pygame.draw.rect(card_surf, (*badge_col, 200), badge_rect, border_radius=4)
        s_surf = self.body_font.render(state_str, True, (255, 255, 255))
        card_surf.blit(s_surf, (badge_rect.x + 8, badge_rect.y + 4))

        # Speed & Coordinates
        pos_txt = f"Speed: {animal.speed:4.1f} px/s"
        coords_txt = f"Pos: ({animal.x:.0f}, {animal.y:.0f})"
        card_surf.blit(self.small_font.render(pos_txt, True, (190, 205, 220)), (94, 94))
        card_surf.blit(self.small_font.render(coords_txt, True, (160, 180, 200)), (94, 110))

        # Divider line
        pygame.draw.line(card_surf, (45, 60, 80), (16, 138), (self.width - 16, 138), 1)

        # 5. Live Telemetry Progress Bars
        bar_x = 16
        bar_w = self.width - 32
        start_y = 150

        # Bar A: Energy / Satiety
        e_ratio = max(0.0, min(1.0, animal.energy / animal.profile.max_energy))
        self._draw_meter(
            card_surf,
            x=bar_x,
            y=start_y,
            width=bar_w,
            height=14,
            label=f"Energy: {animal.energy:4.1f} / {animal.profile.max_energy:.0f}",
            ratio=e_ratio,
            color=(int(255 * (1.0 - e_ratio)), int(225 * e_ratio), 45),
        )

        # Bar B: Hydration / Thirst
        thirst_ratio = max(0.0, min(1.0, 1.0 - (animal.thirst / animal.max_thirst)))
        self._draw_meter(
            card_surf,
            x=bar_x,
            y=start_y + 36,
            width=bar_w,
            height=14,
            label=f"Hydration: {int(thirst_ratio * 100)}%",
            ratio=thirst_ratio,
            color=(45, 160, 235),
        )

        # Bar C: Stamina
        stam_ratio = max(0.0, min(1.0, animal.stamina / animal.max_stamina))
        stam_col = (235, 195, 45) if not animal.is_exhausted else (180, 80, 220)
        stam_lbl = "Stamina: EXHAUSTED" if animal.is_exhausted else f"Stamina: {int(stam_ratio * 100)}%"
        self._draw_meter(
            card_surf,
            x=bar_x,
            y=start_y + 72,
            width=bar_w,
            height=14,
            label=stam_lbl,
            ratio=stam_ratio,
            color=stam_col,
        )

        # 6. Interaction Target Info
        target_str = "No immediate threat / quarry"
        if animal.state == AnimalState.CHASE and animal.target_prey_id:
            target_str = f"Target: Hunting Quarry #{animal.target_prey_id}"
        elif animal.state == AnimalState.FLEE:
            target_str = "Status: Fleeing approaching predator!"
        elif animal.state == AnimalState.DRINK:
            target_str = "Status: Rehydrating at Central River"
        elif animal.state == AnimalState.GRAZE:
            target_str = "Status: Grazing grass biomass"

        info_box = pygame.Rect(16, 272, bar_w, 42)
        pygame.draw.rect(card_surf, (22, 28, 38), info_box, border_radius=4)
        pygame.draw.rect(card_surf, (50, 65, 85), info_box, 1, border_radius=4)
        t_info = self.small_font.render(target_str, True, (220, 230, 240))
        card_surf.blit(t_info, (info_box.x + 8, info_box.y + 12))

        # 7. Follow Camera Button
        is_following = (camera.follow_target_id == animal.entity_id)
        btn_rect_local = pygame.Rect(16, self.height - 42, bar_w, 28)
        btn_col = (45, 140, 85) if is_following else (35, 55, 80)
        btn_txt = "[V] FOLLOWING ANIMAL" if is_following else "CAMERA: FOLLOW ANIMAL"

        pygame.draw.rect(card_surf, btn_col, btn_rect_local, border_radius=6)
        pygame.draw.rect(card_surf, (80, 110, 145), btn_rect_local, 1, border_radius=6)
        b_surf = self.body_font.render(btn_txt, True, (255, 255, 255))
        b_pos = b_surf.get_rect(center=btn_rect_local.center)
        card_surf.blit(b_surf, b_pos)

        # Blit card surface onto main screen
        surface.blit(card_surf, card_rect.topleft)

    def _draw_meter(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        width: int,
        height: int,
        label: str,
        ratio: float,
        color: Tuple[int, int, int],
    ) -> None:
        """Draws a titled progress gauge."""
        lbl_surf = self.small_font.render(label, True, (200, 215, 230))
        surface.blit(lbl_surf, (x, y))

        bg_rect = pygame.Rect(x, y + 15, width, height)
        pygame.draw.rect(surface, (15, 18, 24), bg_rect, border_radius=3)
        fill_w = max(0, int(width * ratio))
        if fill_w > 0:
            fill_rect = pygame.Rect(x, y + 15, fill_w, height)
            pygame.draw.rect(surface, color, fill_rect, border_radius=3)
        pygame.draw.rect(surface, (50, 65, 85), bg_rect, 1, border_radius=3)
