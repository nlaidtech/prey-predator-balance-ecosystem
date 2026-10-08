"""Headless balance tuning script.

Runs multi-seed simulations for hundreds of simulated seconds to evaluate
ecosystem stability, extinction rates, and population dynamics without rendering.
"""

import argparse
import time
from typing import List, Tuple

from src.config import Config
from src.simulation import Simulation


def run_headless_simulation(
    config: Config,
    seed: int,
    duration: float = 120.0,
    dt: float = 1.0 / 60.0,
) -> Tuple[bool, float, int, int, int, int]:
    """Runs a single simulation run.
    
    Returns:
        (survived, duration_survived, final_prey, final_predators, min_prey, min_predators)
    """
    sim = Simulation(config=config, seed=seed)
    steps = int(duration / dt)

    min_prey = sim.prey_count
    min_pred = sim.predator_count

    for _ in range(steps):
        sim.step(dt)
        min_prey = min(min_prey, sim.prey_count)
        min_pred = min(min_pred, sim.predator_count)

        if sim.is_extinct:
            return (False, sim.time, sim.prey_count, sim.predator_count, min_prey, min_pred)

    return (True, sim.time, sim.prey_count, sim.predator_count, min_prey, min_pred)


def evaluate_config(
    config: Config,
    seeds: List[int],
    duration: float = 120.0,
) -> None:
    print(f"=== Running Headless Ecosystem Benchmark ({len(seeds)} seeds, target duration={duration:.0f}s) ===")
    t0 = time.time()

    survived_runs = 0
    for seed in seeds:
        survived, elapsed, f_prey, f_pred, m_prey, m_pred = run_headless_simulation(
            config, seed, duration=duration, dt=config.step_dt
        )
        status = "STABLE" if survived else f"EXTINCT at {elapsed:5.1f}s"
        print(
            f"Seed {seed:4d}: {status:<18} | End: Prey={f_prey:3d}, Pred={f_pred:3d} "
            f"| Min: Prey={m_prey:3d}, Pred={m_pred:3d}"
        )
        if survived:
            survived_runs += 1

    wall_time = time.time() - t0
    success_rate = (survived_runs / len(seeds)) * 100.0
    print("-" * 75)
    print(f"Summary: {survived_runs}/{len(seeds)} seeds survived ({success_rate:.1f}% stability)")
    print(f"Benchmark completed in {wall_time:.2f}s wall-clock time.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Headless predator-prey balance tuner")
    parser.add_argument("--duration", type=float, default=100.0, help="Simulation seconds per run")
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5, 6], help="Random seeds to evaluate")
    args = parser.parse_args()

    cfg = Config()
    evaluate_config(cfg, seeds=args.seeds, duration=args.duration)
