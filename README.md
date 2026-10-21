# Wildlife Ecosystem Simulation: Predator–Prey Balance

[![Play Online in Browser](https://img.shields.io/badge/Play%20Online-GitHub%20Pages-brightgreen?style=for-the-badge&logo=googlechrome)](https://nlaidtech.github.io/prey-predator-balance-ecosystem/)
[![Download Windows Application](https://img.shields.io/badge/Download-Windows%20App%20(.zip)-blue?style=for-the-badge&logo=windows)](https://github.com/nlaidtech/prey-predator-balance-ecosystem/releases/download/v1.0.0/WildlifeEcosystem-Windows-x64.zip)
[![Latest Release](https://img.shields.io/github/v/release/nlaidtech/prey-predator-balance-ecosystem?style=for-the-badge&color=orange)](https://github.com/nlaidtech/prey-predator-balance-ecosystem/releases/tag/v1.0.0)

An agent-based wildlife ecosystem simulation modeling dynamic ecological equilibrium between 6 species across 5 territorial biomes. Built with a decoupled headless Python simulation core, high-performance `pygame-ce` 2.5D visualization, and WebAssembly in-browser play.

---

## 🚀 How to Access & Play the Application

> [!NOTE]
> **Visiting this repository on GitHub?**  
> GitHub is a source-code host and cannot execute `.exe` binaries or Python scripts directly inside the file viewer.  
> Use **Option 1** to play instantly in your browser, or **Option 2** to download the standalone Windows application!

### Option 1: Play Instantly in Your Web Browser (No Install Needed)
* Click here to play directly: **[https://nlaidtech.github.io/prey-predator-balance-ecosystem/](https://nlaidtech.github.io/prey-predator-balance-ecosystem/)**
* Runs directly in any modern browser (Chrome, Edge, Firefox, Safari) using WebAssembly / Pygbag.

### Option 2: Download Standalone Windows Executable (.exe)
Pre-compiled for Windows 10 & 11 — **no Python or libraries required**:
1. Download: **[WildlifeEcosystem-Windows-x64.zip](https://github.com/nlaidtech/prey-predator-balance-ecosystem/releases/download/v1.0.0/WildlifeEcosystem-Windows-x64.zip)** (from [GitHub Releases v1.0.0](https://github.com/nlaidtech/prey-predator-balance-ecosystem/releases/tag/v1.0.0)).
2. Extract the `.zip` archive on your PC.
3. Double-click **`WildlifeEcosystem.exe`** to start instantly!

### Option 3: Run on Local PC (For Developers / Cloned Repository)
* **Desktop Shortcut**: Double-click **`Wildlife Ecosystem App`** on your Desktop.
* **One-Click Batch Launcher**: Double-click [`run_game.bat`](run_game.bat) in the project folder.
* **Python CLI**:
  ```bash
  pip install -r requirements.txt
  python main.py
  ```

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

## 🎮 Interactive Controls & Navigation

| Control | Action |
| :--- | :--- |
| **Left Click + Drag** | **Pan Reserve World**: Smoothly drag the camera anywhere across the 4800×3200 map |
| **Mouse Wheel** (or `+` / `-`) | **Zoom**: Smooth continuous zoom from bird's-eye overview (0.25×) to close-up detail (2.0×) |
| **Left Click on Animal** | **Inspect Animal**: Opens biometric HUD showing health, stamina, energy, age, and AI state |
| **Left Click on Empty Ground** | **Scenic Glide**: Smoothly glides the camera to the clicked territory and closes inspector |
| **Left Click on Minimap** | **Radar Jump**: Click anywhere on the bottom-right radar minimap to pan directly there |
| **On-Screen Toolbar** | Click buttons to toggle **Pause**, adjust speed (**1×**, **2×**, **5×**), switch **View Mode**, toggle **Chart** / **Biomes**, or **Spawn Species** |
| **`WASD` / Arrow Keys** | Continuous directional camera panning |
| **`Space`** | **Pause / Resume** simulation (displays official Wildlife Ecosystem brand logo) |
| **`C`** | Toggle **Population Dynamics Chart** overlay |
| **`B`** | Toggle **Biome Territory Watermarks** |
| **`V`** | Cycle **View Mode** (2.5D Animated Sprites $\leftrightarrow$ Top-Down 360° $\leftrightarrow$ Plain Shapes) |
| **`1` / `2` / `5`** | Set simulation speed to $1\times$, $2\times$, or $5\times$ turbo |
| **`R`** | **Reset World**: Re-seeds terrain and animal populations |
| **`Esc`** | Deselect active animal card (or quit if no card is open) |

---

## 🗺️ Project Roadmap & Phased Architecture

See [ROADMAP.md](ROADMAP.md) for the complete breakdown of completed milestones, what is missing, and the 6-phase expansion plan:
- **Phase 1**: Big Terrain World, Pan/Zoom Camera & Radar Minimap
- **Phase 2**: Click-to-Inspect Animal Card & Biome Watermarks
- **Phase 3**: Real-Time In-Game Population Chart Overlay (`C`) & Exporter
- **Phase 4**: Interactive Desktop Toolbar & Simulation Speed Multipliers ($1\times, 2\times, 5\times$)
- **Phase 5**: Live Activity Feed Ticker & Floating State Emotes
- **Phase 6**: Advanced Collective AI: Boids Herds & Wolf Pack Tactics

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
