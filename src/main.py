"""Main application entry point.

Runs a high-performance 60 FPS event loop on desktop while maintaining
async compatibility for web builds (pygbag/WASM).
"""

import asyncio
import sys
import pygame

from src.config import Config
from src.renderer import Renderer
from src.simulation import Simulation


def run_loop(config: Config, is_async: bool = False):
    pygame.init()
    screen = pygame.display.set_mode((int(config.world_width), int(config.world_height)))
    pygame.display.set_caption("Predator–Prey Balance Ecosystem")
    clock = pygame.time.Clock()

    sim = Simulation(config=config)
    renderer = Renderer(config=config)

    print(f"Predator–Prey Ecosystem running on desktop! (Window: {int(config.world_width)}x{int(config.world_height)})", flush=True)
    print("Controls: [Space] Pause/Resume | [R] Reset | [V] Switch View Mode", flush=True)

    running = True
    paused = False

    while running:
        raw_dt = clock.tick(60) / 1000.0
        dt = min(raw_dt, 0.1)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    sim = Simulation(config=config)
                elif event.key == pygame.K_v:
                    renderer.cycle_view_mode()

        if not paused:
            sim.step(dt)

        renderer.draw(screen, sim, dt, paused, clock.get_fps())
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
    # On desktop, run direct synchronous loop for maximum responsiveness
    list(run_loop(config, is_async=False))


if __name__ == "__main__":
    main()
