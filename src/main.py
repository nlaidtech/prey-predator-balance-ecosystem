"""Main application entry point.

Implements an async-compatible app loop supporting both native desktop execution
and web deployment (pygbag/WASM).
"""

import asyncio
import sys
import pygame

from src.config import Config
from src.simulation import Simulation


async def main() -> None:
    config = Config()
    sim = Simulation(config=config)

    pygame.init()
    screen = pygame.display.set_mode((int(config.world_width), int(config.world_height)))
    pygame.display.set_caption("Predator–Prey Balance Ecosystem")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 16)

    running = True
    paused = False

    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    sim = Simulation(config=config)

        if not paused:
            sim.step(dt)

        # Basic shape rendering for Milestone 1 / verification
        screen.fill((30, 34, 42))

        # Draw Prey (green circles)
        for prey in sim.prey_list:
            pygame.draw.circle(screen, (80, 220, 100), (int(prey.x), int(prey.y)), 4)

        # Draw Predators (red/orange circles)
        for pred in sim.predator_list:
            pygame.draw.circle(screen, (230, 70, 60), (int(pred.x), int(pred.y)), 6)

        # Overlay HUD
        status_text = (
            f"Time: {sim.time:5.1f}s | "
            f"Rabbits (Prey): {sim.prey_count:3d} | "
            f"Foxes (Predators): {sim.predator_count:3d} | "
            f"{'PAUSED' if paused else 'RUNNING'} [Space: Pause, R: Reset]"
        )
        hud_surface = font.render(status_text, True, (240, 240, 240))
        screen.blit(hud_surface, (16, 16))

        pygame.display.flip()
        await asyncio.sleep(0)  # Cooperative yield for pygbag browser loop

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
