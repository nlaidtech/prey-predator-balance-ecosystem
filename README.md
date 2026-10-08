# Predator–Prey Balance Ecosystem

A Python agent-based simulation modeling dynamic ecological equilibrium between rabbits (prey) and foxes (predators). Built with a decoupled headless simulation core and `pygame-ce` visualization.

## Architecture

- **Strict Core / Renderer Separation**: The simulation core (`src/simulation.py`) operates purely headless with zero rendering code, making it fast, testable, and swappable.
- **Centralized Frozen Config**: All biological, behavioral, and physical constants are declared in `src/config.py` with zero magic numbers.
- **Deterministic Runs**: Driven by an isolated seeded PRNG (`random.Random(seed)`).
- **Dual Runtime Support**: App loop (`src/main.py`) supports both native desktop execution and web deployment via `pygbag` (WebAssembly) through async cooperative yielding.

## Project Structure

```text
prey-predator-balance-ecosystem/
├── src/
│   ├── __init__.py
│   ├── config.py         # Central frozen Config dataclass
│   ├── entities.py       # Animal, Prey, and Predator agent models
│   ├── metrics.py        # Time-series recorder and demographic statistics
│   ├── simulation.py     # Pure headless simulation engine
│   └── main.py           # Async desktop + web application loop
├── tests/
│   ├── __init__.py
│   ├── test_entities.py  # Unit tests for hunting, fleeing, and crowding
│   └── test_simulation.py# Unit tests for determinism and counts
├── tune.py               # Headless multi-seed balance benchmark tool
└── README.md
```

## Running Tests

Run the full unit test suite:
```bash
python -m unittest discover tests
```

## Headless Balance Tuning

Run the multi-seed headless benchmark across specified durations and seeds:
```bash
python tune.py --duration 60 --seeds 1 2 3 4 5 6
```

## Running the Application

Launch the desktop simulation:
```bash
python -m src.main
```

### Controls
- **Space**: Pause / Resume simulation
- **R**: Reset ecosystem with initial configuration
