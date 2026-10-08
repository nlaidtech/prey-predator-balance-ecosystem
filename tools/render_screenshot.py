import os
import sys

# Ensure repository root is on Python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from src.config import Config
from src.renderer import Renderer, ViewMode
from src.simulation import Simulation


def capture():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()

    config = Config(world_width=4800, world_height=3200, screen_width=1280, screen_height=720)
    sim = Simulation(config=config, seed=42)
    renderer = Renderer(config=config)

    # Step simulation 15 steps so animals scatter and roam
    for _ in range(15):
        sim.step(0.1)

    surface = pygame.Surface((1280, 720))

    # Points of interest
    targets = [
        ("meadow", 3600.0, 2500.0, "Cobblestone Crossroads & Golden Plains"),
        ("river", 2400.0, 1600.0, "Circular Watering Hole Basin & Azure River"),
        ("highlands", 1100.0, 700.0, "Granite Highlands Cliff Plateau & Stairs"),
        ("forest", 3600.0, 700.0, "Ancient Oak Grove & Dense Canopy"),
        ("thickets", 1200.0, 2500.0, "Briar Hollow Refuge & Berry Bushes"),
    ]

    for name, tx, ty, title in targets:
        renderer.camera.teleport_to(tx, ty)
        renderer.draw(surface, sim, dt=0.016, paused=False, fps=60.0)
        out_path = f"screenshot_{name}.png"
        pygame.image.save(surface, out_path)
        print(f"Captured {title} -> {out_path}")


if __name__ == "__main__":
    capture()
