# Wildlife Ecosystem Simulation: Roadmap & Status Report

A high-performance, agent-based wildlife ecosystem simulation with multi-species ecological food webs, territorial biomes, stamina pursuit physics, and dual 2.5D/top-down animated sprites in `pygame-ce`.

---

## 📊 Project Status Overview

| Component | Status | Details |
| :--- | :---: | :--- |
| **Headless Simulation Core** | ✅ **DONE** | Pure logic engine, zero graphics dependencies, deterministic PRNG. |
| **Balance Tuning & Metrics** | ✅ **DONE** | 100% stability across multi-minute, multi-seed simulations. |
| **5-Zone Territorial Biomes** | ✅ **DONE** | Highlands, Dense Forest, Central River, Thickets, and Meadow. |
| **Species Roster (6 Animals)**| ✅ **DONE** | Wolf, Rabbit, Deer, Mountain Goat, Bear, and Fox. |
| **Sprite Pipeline & Animations**| ✅ **DONE** | All 6 species sliced with transparent alpha (Walk, Run, Attack, Die, Idle). |
| **Territorial Leash Physics** | ✅ **DONE** | Animals spawn in native zones and return home after hunts/drinking. |
| **Real-Life Physiological Logic**| ✅ **DONE** | Stamina exhaustion, thirst & river drinking, grass grazing & regrowth. |
| **Visual Corpse & Death Pipeline**| ✅ **DONE** | 5-frame collapse animations on ground with smooth alpha fade-out. |
| **Dual View Mode Rendering** | ✅ **DONE** | Instant toggle (`V`) between Side-View (2.5D), Top-Down 360°, and Shapes. |
| **Unit Test Suite** | ✅ **DONE** | 19 passing unit tests covering physics, biomes, entities, and renderer. |
| **Population Charts & Phase Portrait**| ⏳ **NEXT** | Live overlay (`C`) & exportable Lotka-Volterra cycle plots (Milestone 5). |
| **Advanced Boids Herding & Packs**| ⏳ **NEXT** | Flocking alarm propagation and wolf pack flanking encirclement. |
| **Packaging & Web Build (pygbag)**| 🔮 **UPCOMING**| WebAssembly browser demo deployment and portfolio documentation. |

---

## ✅ What is DONE (Completed)

### 1. Architecture & Headless Core (`src/simulation.py`, `src/config.py`)
- Complete separation of simulation logic from rendering.
- Deterministic random number generator (`random.Random(seed)`).
- Fast spatial partitioning (`SpatialGrid`) providing $O(1)$ proximity queries.
- Immutable configuration dataclass (`Config`) with zero magic numbers.

### 2. The 5 Geographic Territorial Biomes (`src/terrain.py`)
- **Zone 1: Rocky Highlands** (Northwest) — Home to Mountain Goats (cliff climbing trait, high stamina drain for others).
- **Zone 2: Dense Forest** (Northeast) — Home to Wolves and Bears (50% canopy stealth cover for stalking).
- **Zone 3: Central River** (Center Corridor) — Shared watering hole and hydration hub (slow water wading).
- **Zone 4: Thickets & Briars** (Southwest) — Home to Foxes and Rabbit Warrens (prey refuge, slows large predators).
- **Zone 5: Open Meadow** (Southeast) — Home to Deer Herds and Rabbits (fertile grass grazing and open sprint plains).
- Dynamic grass biomass depletion and rainfall regrowth.

### 3. Multi-Species Food Web (`src/species.py`, `src/entities.py`)
- Extensible `SpeciesProfile` data-driven engine covering 6 wildlife species:
  - 🐇 **Rabbit** (Herbivore, Warren/Colony, Thicket Refuge)
  - 🦌 **Deer** (Large Herbivore, Herd Runner)
  - 🐐 **Mountain Goat** (Highland Herbivore, Cliff Scaler)
  - 🦊 **Fox** (Mesopredator, Thicket Hunter)
  - 🐺 **Wolf** (Apex Pack Carnivore)
  - 🐻 **Bear** (Apex River/Forest Omnivore)
- Diet matrix and size-matching hunting relationships.
- Stamina & fatigue curve: Sprinting consumes stamina; exhaustion temporarily drops speed to a walk.
- Thirst routine: Animals periodically migrate to the Central River to drink.

### 4. Sprite Art & Animation Engine (`src/renderer.py`, `assets/sprites/`)
- Sliced and transparentized 6 complete sprite sheets:
  - Walk, Run (Sprint/Flee), Attack (Feast/Strike), Die, Idle, and Top-View.
- Real-time view mode switcher (Key `V`):
  - **Side-View (2.5D Animated)** with automatic horizontal left/right facing.
  - **Top-Down (360° Directional)** with smooth heading rotation.
  - **Debug Shapes** with vision and catch boundaries.
- Visual corpse pipeline: 5-frame collapse animation on ground followed by smooth opacity fade-out.
- Predator hunger/energy meters floating above carnivores.
- Real-time comprehensive HUD displaying active counts for all 6 species, time, and FPS.

### 5. Automated Verification (`tests/`)
- **19 passing unit tests**:
  - Determinism tests (same seed = exact same run).
  - Predation strike & feast.
  - Fleeing and vision cone reactions.
  - Carrying capacity and logistic reproduction gates.
  - Starvation & natural lifespan deaths.
  - 5-zone coordinate boundaries & terrain speed multipliers.
  - Mountain climber trait & thicket refuge mechanics.
  - Grass grazing & regrowth.
  - Headless renderer mode safety.

---

## ⏳ What is NEXT (Immediate Next Steps)

### Milestone 5: Analytics & Population Charts
1. **Live In-Game HUD Chart Overlay (Toggle `C`)**:
   - A real-time mini-graph rendered at the bottom/side of the screen plotting:
     - Herbivore populations (green/gold lines: Rabbits, Deer, Goats)
     - Carnivore populations (red/orange lines: Wolves, Foxes, Bears)
2. **Phase-Portrait Orbit Plotter (`plot_metrics.py`)**:
   - Standalone export script generating publication-ready matplotlib graphs for your portfolio:
     - **Population vs. Time**: Demonstrating oscillating Lotka-Volterra waves.
     - **Phase-Portrait (Prey vs. Predators)**: Mathematical visual proof of closed ecological limit cycles.

### Advanced Group Dynamics (Boids & Pack Hunting)
1. **Flocking Herds (Deer & Rabbits)**:
   - Reynolds Boids steering (Separation, Alignment, Cohesion).
   - Audible alarm propagation: One animal spotting a predator triggers fleeing in nearby herd mates.
2. **Coordinated Wolf Pack Pursuits**:
   - Pack leader target consensus.
   - Flanking angles cutting off fleeing prey escape routes.
   - Pack feast: wolves sharing energy near a deer kill.

---

## 🔮 What is MISSING (Future Opportunities)

1. **Environmental Weather & Day/Night Cycle**:
   - Day / Night ambient lighting (diurnal animals sleep, nocturnal foxes hunt).
   - Rainstorms that accelerate grass regrowth and river flow.
2. **Audio & Sound Effects**:
   - Ambient nature soundscape (river stream, wind, forest birds).
   - Animal vocalizations (wolf howls, deer calls, rustling brush).
3. **WebAssembly Deployment (Pygbag / Browser Demo)**:
   - Compiling the project to WebAssembly via Pygbag so visitors can run and interact with the simulation directly in a browser with zero installation.
4. **Interactive God-Mode / Sandbox Controls**:
   - Mouse brush tools to spawn animals, draw water/trees, or trigger a harsh winter.
