"""Standalone Population Dynamics & Phase-Portrait Exporter.

Runs a headless simulation, records multi-species population time-series,
and exports high-resolution publication-ready visualizations:
1. Multi-Species Oscillating Population Waves
2. 2D Ecological Phase-Portrait (Herbivores vs. Carnivores Limit Cycles)
"""

import argparse
import os
import sys
import matplotlib
matplotlib.use("Agg")  # Headless backend
import matplotlib.pyplot as plt

from src.config import Config
from src.simulation import Simulation


def generate_portfolio_plots(duration: float = 120.0, seed: int = 42, output_path: str = "assets/population_dynamics.png") -> None:
    print(f"=== Generating Ecological Portfolio Plots (Duration: {duration:.0f}s, Seed: {seed}) ===")
    config = Config()
    sim = Simulation(config=config, seed=seed)

    dt = config.step_dt
    steps = int(duration / dt)

    for i in range(steps):
        sim.step(dt)
        if (i + 1) % int(30.0 / dt) == 0:
            print(f"  Simulated {sim.time:4.0f}s / {duration:.0f}s...", flush=True)

    history = sim.metrics.detailed_history
    if not history:
        print("Error: No history snapshots recorded.", file=sys.stderr)
        return

    times = [s.time for s in history]
    rabbits = [s.counts.get("rabbit", 0) for s in history]
    deer = [s.counts.get("deer", 0) for s in history]
    goats = [s.counts.get("goat", 0) for s in history]
    foxes = [s.counts.get("fox", 0) for s in history]
    wolves = [s.counts.get("wolf", 0) for s in history]
    bears = [s.counts.get("bear", 0) for s in history]
    herbivores = [s.total_herbivores for s in history]
    carnivores = [s.total_carnivores for s in history]

    # Create dark-themed high-res figure with 2 panels
    plt.style.use("dark_background")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), dpi=150)
    fig.patch.set_facecolor("#0e121a")
    ax1.set_facecolor("#141923")
    ax2.set_facecolor("#141923")

    # Panel 1: Multi-Species Oscillating Time-Series
    ax1.set_title("Multi-Species Wildlife Population Dynamics (Time-Series)", fontsize=13, fontweight="bold", pad=12, color="#f0f4f8")
    ax1.plot(times, rabbits, label="Rabbit (Herbivore)", color="#6ee68c", linewidth=2.0)
    ax1.plot(times, deer, label="Deer (Herbivore)", color="#46c878", linewidth=1.8)
    ax1.plot(times, goats, label="Mountain Goat (Herbivore)", color="#3cd7d7", linewidth=1.8)
    ax1.plot(times, foxes, label="Fox (Carnivore)", color="#fa9632", linewidth=1.8)
    ax1.plot(times, wolves, label="Wolf (Apex Pack)", color="#f04641", linewidth=2.2)
    ax1.plot(times, bears, label="Bear (Omnivore)", color="#b45037", linewidth=2.0)

    ax1.set_xlabel("Simulated Time (seconds)", fontsize=11, color="#cbd5e1")
    ax1.set_ylabel("Living Population Count", fontsize=11, color="#cbd5e1")
    ax1.grid(True, linestyle="--", alpha=0.25, color="#64748b")
    ax1.legend(loc="upper right", framealpha=0.85, facecolor="#1e2532", edgecolor="#334155", fontsize=9)

    # Panel 2: 2D Phase-Portrait Limit Cycle (Prey vs Predators)
    ax2.set_title("2D Phase-Portrait Orbit: Herbivores vs. Carnivores", fontsize=13, fontweight="bold", pad=12, color="#f0f4f8")
    sc = ax2.scatter(herbivores, carnivores, c=times, cmap="viridis", s=18, alpha=0.85, edgecolors="none")
    ax2.plot(herbivores, carnivores, color="#94a3b8", alpha=0.4, linewidth=1.0, linestyle=":")

    # Initial and final state markers
    ax2.plot(herbivores[0], carnivores[0], "go", markersize=9, label=f"Start (t=0s: {herbivores[0]}H, {carnivores[0]}C)")
    ax2.plot(herbivores[-1], carnivores[-1], "r*", markersize=12, label=f"End (t={times[-1]:.0f}s: {herbivores[-1]}H, {carnivores[-1]}C)")

    cbar = plt.colorbar(sc, ax=ax2)
    cbar.set_label("Time (s)", color="#cbd5e1", fontsize=10)
    cbar.ax.yaxis.set_tick_params(color="#cbd5e1")

    ax2.set_xlabel("Total Herbivores (Prey: Rabbits, Deer, Goats)", fontsize=11, color="#cbd5e1")
    ax2.set_ylabel("Total Carnivores (Predators: Foxes, Wolves, Bears)", fontsize=11, color="#cbd5e1")
    ax2.grid(True, linestyle="--", alpha=0.25, color="#64748b")
    ax2.legend(loc="upper left", framealpha=0.85, facecolor="#1e2532", edgecolor="#334155", fontsize=9)

    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()

    print(f"[OK] Successfully exported population plots to: {output_path}")
    print(f"   Final Population: Herbivores={herbivores[-1]} | Carnivores={carnivores[-1]}")
    is_stable, status = sim.metrics.get_equilibrium_status()
    print(f"   Equilibrium State: {status} (Stable={is_stable})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export ecological time-series and phase-portrait plots")
    parser.add_argument("--duration", type=float, default=90.0, help="Simulation duration in seconds")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    parser.add_argument("--output", type=str, default="assets/population_dynamics.png", help="Output PNG path")
    args = parser.parse_args()

    generate_portfolio_plots(duration=args.duration, seed=args.seed, output_path=args.output)
