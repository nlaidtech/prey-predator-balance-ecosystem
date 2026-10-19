"""Main application entry point with Camera2D, Minimap, and Animal Inspector.

Runs a high-performance 60 FPS event loop on desktop while maintaining
async compatibility for web builds (pygbag/WASM).
"""

import asyncio
import math
import os
import sys

# Ensure repository root is on sys.path whether executed directly or as module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from src.camera import Camera2D
from src.config import Config, get_resource_path
from src.renderer import Renderer
from src.simulation import Simulation


def run_loop(config: Config, is_async: bool = False):
    pygame.init()
    scr_w = getattr(config, "screen_width", 1280)
    scr_h = getattr(config, "screen_height", 720)

    # Set application icon if available
    icon_path = get_resource_path(os.path.join("assets", "icon.png"))
    if os.path.isfile(icon_path):
        try:
            icon_surf = pygame.image.load(icon_path)
            pygame.display.set_icon(icon_surf)
        except Exception:
            pass

    screen = pygame.display.set_mode((int(scr_w), int(scr_h)))
    pygame.display.set_caption("Predator–Prey Balance Ecosystem (Big Reserve World)")
    clock = pygame.time.Clock()

    camera = Camera2D(
        screen_width=int(scr_w),
        screen_height=int(scr_h),
        world_width=config.world_width,
        world_height=config.world_height,
    )
    sim = Simulation(config=config)
    renderer = Renderer(config=config, camera=camera)

    print("Predator–Prey Ecosystem initialized!", flush=True)
    print(f"  Viewport: {int(scr_w)}x{int(scr_h)} | Reserve World: {int(config.world_width)}x{int(config.world_height)}", flush=True)
    print("  Controls: [Drag Ground] Pan Reserve | [Click Ground] Scenic Glide | [Click Animal] Inspect | [WASD/Wheel] Camera", flush=True)

    running = True
    paused = False
    speed_multiplier = 1

    # Mouse drag tracking for smooth Left-Click world exploration
    left_drag_active = False
    left_drag_start_pos = (0, 0)
    left_drag_cam_start = (camera.x, camera.y)
    left_has_dragged = False

    while running:
        raw_dt = clock.tick(60) / 1000.0
        dt = min(raw_dt, 0.1)

        # 1. Process Event Stream
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if renderer.inspector.selected_id is not None:
                        renderer.inspector.deselect()
                    else:
                        running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    sim = Simulation(config=config)
                    camera.teleport_to(config.world_width * 0.5, config.world_height * 0.5)
                    renderer.inspector.deselect()
                elif event.key == pygame.K_1:
                    speed_multiplier = 1
                elif event.key == pygame.K_2:
                    speed_multiplier = 2
                elif event.key == pygame.K_5:
                    speed_multiplier = 5
                elif event.key == pygame.K_v:
                    renderer.cycle_view_mode()
                elif event.key == pygame.K_b:
                    renderer.toggle_biome_watermarks()
                elif event.key == pygame.K_c:
                    renderer.toggle_chart()

            # Mouse wheel zoom
            elif event.type == pygame.MOUSEWHEEL:
                mouse_pos = pygame.mouse.get_pos()
                camera.zoom_by(event.y * 0.12, mouse_screen_pos=mouse_pos)

            # Mouse button clicks & drag panning
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # 1. Check if Interactive Toolbar was clicked
                    action = renderer.toolbar.handle_click(
                        event.pos[0], event.pos[1],
                        sim=sim,
                        cam=camera,
                        paused=paused,
                        current_speed=speed_multiplier,
                        current_view=renderer.view_mode,
                    )
                    if action.consumed:
                        if action.toggle_pause:
                            paused = not paused
                        if action.set_speed is not None:
                            speed_multiplier = action.set_speed
                        if action.reset_simulation:
                            sim = Simulation(config=config)
                            camera.teleport_to(config.world_width * 0.5, config.world_height * 0.5)
                            renderer.inspector.deselect()
                        if action.set_view_mode is not None:
                            renderer.view_mode = action.set_view_mode
                        if action.toggle_chart:
                            renderer.toggle_chart()
                        if action.toggle_biomes:
                            renderer.toggle_biome_watermarks()
                        continue

                    # 2. Check if Inspector Card was clicked
                    if renderer.inspector.handle_click(
                        event.pos[0], event.pos[1],
                        camera.screen_width, camera.screen_height,
                        camera,
                    ):
                        continue

                    # 3. Check if Population Chart was clicked
                    if renderer.chart.handle_click(
                        event.pos[0], event.pos[1],
                        camera.screen_width, camera.screen_height,
                    ):
                        continue

                    # 4. Check if Activity Feed was clicked (teleport to event)
                    if renderer.activity_feed.handle_click(
                        event.pos[0], event.pos[1],
                        camera.screen_width, camera.screen_height,
                        renderer.chart.visible,
                        sim.time,
                        camera,
                    ):
                        continue

                    # 5. Check if Minimap was clicked (glide camera to territory)
                    m_world = renderer.minimap.screen_to_world(
                        event.pos[0], event.pos[1],
                        camera.screen_width, camera.screen_height,
                        sim.terrain.width, sim.terrain.height,
                    )
                    if m_world:
                        camera.glide_to(m_world[0], m_world[1])
                        renderer.trigger_terrain_focus(m_world[0], m_world[1], sim.terrain)
                        continue

                    # 6. Not on any HUD: begin Left-Click Drag or Click on terrain/animal
                    left_drag_active = True
                    left_drag_start_pos = event.pos
                    left_drag_cam_start = (camera.x, camera.y)
                    left_has_dragged = False

                elif event.button in (2, 3):  # Middle or Right click to drag pan
                    camera.start_drag(event.pos[0], event.pos[1])
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZEALL)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and left_drag_active:
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                    if not left_has_dragged:
                        # Genuine CLICK on terrain or animal (no dragging)
                        wx, wy = camera.screen_to_world(event.pos[0], event.pos[1])
                        click_radius = 45.0 / camera.zoom
                        target = sim.spatial_grid.find_nearest_candidate(
                            wx, wy, click_radius,
                            predicate=lambda a: a.alive,
                        )
                        if target:
                            renderer.inspector.select(target.entity_id)
                        else:
                            # Clicked scenic terrain area!
                            renderer.inspector.deselect()
                            camera.glide_to(wx, wy)
                            renderer.trigger_terrain_focus(wx, wy, sim.terrain)
                    left_drag_active = False
                    left_has_dragged = False

                elif event.button in (2, 3):
                    camera.end_drag()
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

            elif event.type == pygame.MOUSEMOTION:
                if left_drag_active:
                    dx_screen = event.pos[0] - left_drag_start_pos[0]
                    dy_screen = event.pos[1] - left_drag_start_pos[1]
                    dist = math.hypot(dx_screen, dy_screen)
                    if dist > 5.0 or left_has_dragged:
                        left_has_dragged = True
                        camera.follow_target_id = None
                        dx_world = dx_screen / camera.zoom
                        dy_world = dy_screen / camera.zoom
                        camera.target_x = left_drag_cam_start[0] - dx_world
                        camera.target_y = left_drag_cam_start[1] - dy_world
                        camera._clamp_target()
                        camera.x = camera.target_x
                        camera.y = camera.target_y
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZEALL)
                elif camera.is_dragging:
                    camera.handle_drag(event.pos[0], event.pos[1])

        # 2. Continuous Keyboard Panning (WASD / Arrows)
        keys = pygame.key.get_pressed()
        pan_speed = (camera.pan_speed / camera.zoom) * dt
        dx, dy = 0.0, 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= pan_speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += pan_speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= pan_speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += pan_speed
        if dx != 0.0 or dy != 0.0:
            camera.pan(dx, dy)

        # 3. Step Simulation with sub-stepping for speed multipliers
        if not paused:
            for _ in range(speed_multiplier):
                sim.step(dt)

        # 4. Render Scene with Camera, Toolbar & Inspector
        renderer.draw(screen, sim, dt, paused, clock.get_fps(), camera=camera, speed_multiplier=speed_multiplier)
        pygame.display.flip()

        if is_async:
            yield

    pygame.quit()


async def main_async() -> None:
    config = Config()
    gen = run_loop(config, is_async=True)
    for _ in gen:
        await asyncio.sleep(0)


def main() -> None:
    config = Config()
    list(run_loop(config, is_async=False))


if __name__ == "__main__":
    main()
