"""Capture screenshot preview of the in-game HUD with logo and the paused logo banner."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
from src.camera import Camera2D
from src.config import Config
from src.renderer import Renderer
from src.simulation import Simulation

def capture():
    pygame.init()
    config = Config(world_width=4800, world_height=3200, screen_width=1280, screen_height=720)
    camera = Camera2D(screen_width=1280, screen_height=720, world_width=4800, world_height=3200)
    sim = Simulation(config=config, seed=42)
    renderer = Renderer(config=config, camera=camera)
    surface = pygame.Surface((1280, 720))

    # Run a few steps to populate entities and terrain
    for _ in range(15):
        sim.step(0.016)

    # 1. Capture running game with HUD logo emblem
    renderer.draw(surface, sim, 0.016, paused=False, fps=60.0, camera=camera, speed_multiplier=1)
    
    out_dir = r"C:\Users\kurtr\.gemini\antigravity\brain\7e81f2c9-2770-4e4d-bee3-289e832d8b59"
    hud_preview_path = os.path.join(out_dir, "logo_hud_preview.png")
    pygame.image.save(surface, hud_preview_path)
    print(f"[OK] Saved HUD preview: {hud_preview_path}")

    # 2. Capture paused game with centered logo banner
    renderer.draw(surface, sim, 0.016, paused=True, fps=60.0, camera=camera, speed_multiplier=1)
    pause_preview_path = os.path.join(out_dir, "logo_paused_preview.png")
    pygame.image.save(surface, pause_preview_path)
    print(f"[OK] Saved Paused preview: {pause_preview_path}")

if __name__ == "__main__":
    capture()
