import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
from src.config import Config
from src.camera import Camera2D
from src.renderer import Renderer, ViewMode
from src.simulation import Simulation

def test_everything():
    pygame.init()
    config = Config(world_width=4800, world_height=3200, screen_width=1280, screen_height=720)
    camera = Camera2D(screen_width=1280, screen_height=720, world_width=4800, world_height=3200)
    sim = Simulation(config=config, seed=42)
    renderer = Renderer(config=config, camera=camera)
    surface = pygame.Surface((1280, 720))

    print("[TEST] Running 100 simulation steps...")
    for step_i in range(100):
        sim.step(0.016)
        renderer.draw(surface, sim, 0.016, paused=False, fps=60.0, camera=camera, speed_multiplier=1)
    print("[OK] 100 steps completed without error.")

    print("[TEST] Testing toolbar clicks and animal spawns...")
    for species in ["rabbit", "deer", "goat", "fox", "wolf", "bear"]:
        sim.spawn_animal(species, x=camera.x, y=camera.y)
    renderer.draw(surface, sim, 0.016, paused=False, fps=60.0, camera=camera)
    print("[OK] Animal spawning works.")

    print("[TEST] Testing animal selection & inspection...")
    if sim.animals:
        a = sim.animals[0]
        renderer.inspector.select(a.entity_id)
        renderer.draw(surface, sim, 0.016, paused=False, fps=60.0, camera=camera)
        renderer.inspector.deselect()
    print("[OK] Inspector works.")

    print("[TEST] Testing view modes...")
    for mode in [ViewMode.SIDE_VIEW, ViewMode.TOP_DOWN, ViewMode.SHAPES]:
        renderer.view_mode = mode
        renderer.draw(surface, sim, 0.016, paused=False, fps=60.0, camera=camera)
    renderer.view_mode = ViewMode.SIDE_VIEW
    print("[OK] View modes work.")

    print("[TEST] Testing chart and biomes overlay...")
    renderer.toggle_chart()
    renderer.toggle_biome_watermarks()
    renderer.draw(surface, sim, 0.016, paused=False, fps=60.0, camera=camera)
    renderer.toggle_chart()
    renderer.toggle_biome_watermarks()
    print("[OK] Chart & biomes work.")

    print("[TEST] Testing camera panning & zooming...")
    camera.pan(100.0, -100.0)
    camera.zoom_by(0.5, (640, 360))
    camera.zoom_by(-0.8, (640, 360))
    camera.teleport_to(2400.0, 1600.0)
    renderer.draw(surface, sim, 0.016, paused=False, fps=60.0, camera=camera)
    print("[OK] Camera zoom/pan works.")

    print("[TEST] Testing minimap clicks...")
    for sx in [1100, 1200]:
        for sy in [600, 680]:
            w_coords = renderer.minimap.screen_to_world(sx, sy, 1280, 720, 4800, 3200)
            if w_coords:
                camera.glide_to(w_coords[0], w_coords[1])
                renderer.trigger_terrain_focus(w_coords[0], w_coords[1], sim.terrain)
    renderer.draw(surface, sim, 0.016, paused=False, fps=60.0, camera=camera)
    print("[OK] Minimap works.")

    print("\nALL RUNTIME CHECKS PASSED FLAWLESSLY!")

if __name__ == "__main__":
    test_everything()
