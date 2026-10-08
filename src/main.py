"""Main application entry point.

Drives the simulation and renderer through an async-compatible app loop.
Compatible with desktop execution and web deployment (pygbag/WASM).
"""

import asyncio
import sys
import pygame

from src.config import Config
from src.renderer import Renderer
from src.simulation import Simulation


async def main() -> None:
    pygame.init()
    config = Config()
    sim = Simulation(config=config)
    renderer = Renderer(config=config)

    screen = pygame.display.set_mode((int(config.world_width), int(config.world_height)))
    pygame.display.set_caption("Predator–Prey Balance Ecosystem")
    clock = pygame.time.Clock()

    running = True
    paused = False

    while running:
        raw_dt = clock.tick(60) / 1000.0
        # Cap dt to avoid large simulation jumps on window drag
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

        # Draw scene via decoupled renderer
        renderer.draw(screen, sim, dt, paused, clock.get_fps())

        pygame.display.flip()
        await asyncio.sleep(0)  # Cooperative yield for pygbag WASM loop

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
