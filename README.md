# Wildlife Ecosystem Simulation: Predator–Prey Balance

An agent-based wildlife ecosystem simulation modeling dynamic ecological equilibrium between 6 species across 5 territorial biomes. Built with a decoupled headless Python simulation core and `pygame-ce` multi-mode visualization.

---

## 🌟 Key Highlights

- **5 Distinct Territorial Biomes**: Rocky Highlands, Dense Forest, Central River, Thickets & Briars, and Open Meadow.
- **6 Animated Wildlife Species**: Complete multi-frame pixel-art sprites for **Wolf**, **Rabbit**, **Deer**, **Mountain Goat**, **Bear**, and **Fox**.
- **Real-Life Ecological Physics**:
  - **Territorial Home-Ranges**: Animals spawn and reside within their native zones; hunting and hydration trigger temporary excursions.
  - **Dynamic Vegetation Regrowth**: Herbivores graze grass bare; rainfall regrows biomass over time.
  - **Stamina & Exhaustion**: Max sprint drains stamina; exhausted animals drop to a walk.
  - **Watering Hole Routine**: Periodic migration to the river to drink.
  - **Visual Corpse Pipeline**: 5-frame collapse animations on ground with smooth opacity fade-out.
- **Dual Visual Perspectives**: Press **`V`** to toggle anytime between **Side-View (2.5D Animated)**, **Top-Down (360° Directional)**, and **Debug Shapes**.
- **Strict Architecture**: Headless simulation core with zero drawing dependencies; 19 comprehensive unit tests.

---

## 🗺️ The 5 Geographic Territories

```
┌───────────────────────────────────────┬───────────────────────────────────────┐
│  ⛰️ ZONE 1: ROCKY HIGHLANDS           │  🌲 ZONE 2: DENSE FOREST              │
│  Resident: 🐐 Mountain Goats          │  Residents: 🐺 Wolves & 🐻 Bears      │
│  Cliffs, rock ledges, 100% goat speed │  Pine canopies, 50% stealth cover     │
├───────────────────────────────────────┴───────────────────────────────────────┤
│  💧 ZONE 3: CENTRAL RIVER & WATERING HOLE                                     │
│  Shared corridor: Hydration hub, salmon fishing, water wading friction       │
├───────────────────────────────────────┬───────────────────────────────────────┤
│  🌾 ZONE 4: THICKETS & BRIARS         │  🌿 ZONE 5: OPEN MEADOW & PLAINS      │
│  Residents: 🦊 Foxes & 🐇 Rabbits     │  Residents: 🦌 Deer Herds & 🐇 Rabbits│
│  Prey refuge: Obstruction to wolves   │  Rich grass pastures, open sprinting  │
└───────────────────────────────────────┴───────────────────────────────────────┘
```

---

## 🎮 Quick Start

### 1. Requirements
- Python 3.10+
- `pygame-ce`

Install dependencies:
```bash
pip install pygame-ce
```

### 2. Launch the Simulation
Run directly:
```bash
python -m src.main
```
*(Or double-click `run.bat` on Windows)*

### Controls
| Key | Action |
| :--- | :--- |
| **`V`** | **Cycle View Mode** (Side-View Animated $\leftrightarrow$ Top-Down 360° $\leftrightarrow$ Plain Shapes) |
| **`Space`** | **Pause / Resume** simulation |
| **`R`** | **Reset** ecosystem with initial population |

---

## 🧪 Testing & Verification

Run the full headless test suite:
```bash
python -m unittest discover tests
```

Run the headless balance tuning benchmark:
```bash
python tune.py --duration 60 --seeds 1 2 3 4 5 6
```

---

## 📁 Project Structure

```text
prey-predator-balance-ecosystem/
├── assets/
│   └── sprites/           # Sliced transparent sprite animations
│       ├── wolf/          # Walk, run, attack, die, idle, top-view
│       ├── rabbit/
│       ├── deer/
│       ├── goat/
│       ├── bear/
│       └── fox/
├── src/
│   ├── config.py          # Central immutable configuration
│   ├── species.py         # Species profiles & diet matrix
│   ├── terrain.py         # 5 territorial biomes & grass growth
│   ├── entities.py        # Animal agent models, stamina & hunting
│   ├── simulation.py      # Headless simulation engine
│   ├── renderer.py        # 2.5D, Top-Down, and Shapes renderer
│   ├── metrics.py         # Time-series recorder
│   └── main.py            # App loop (desktop + web compatible)
├── tests/
│   ├── test_entities.py
│   ├── test_simulation.py
│   ├── test_renderer.py
│   └── test_terrain_and_species.py
├── ROADMAP.md             # Detailed roadmap & milestone status
├── tune.py                # Headless balance benchmark runner
└── run.bat                # Windows one-click desktop launcher
```
