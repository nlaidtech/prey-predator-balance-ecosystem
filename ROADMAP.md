# Wildlife Ecosystem Simulation: Roadmap & Phased Architecture Plan

A high-performance, agent-based wildlife ecosystem simulation with multi-species ecological food webs, territorial biomes, stamina pursuit physics, and dual 2.5D/top-down animated sprites in `pygame-ce`.

---

## 📊 Current Project Status Overview

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
| **Phase 1: Big Terrain & Camera**| ⏳ **PLANNED**| Scaled reserve (2560x1600+), pan/zoom camera, follow-cam, and radar minimap. |
| **Phase 2: Target Inspector** | ⏳ **PLANNED**| Click-to-inspect animal stats card, glowing target rings, biome labels. |
| **Phase 3: Population Chart (C)**| ⏳ **PLANNED**| Live in-game time-series curve overlay & Lotka-Volterra phase-portrait exporter. |
| **Phase 4: Interactive Toolbar** | ⏳ **PLANNED**| On-screen buttons, simulation speed multiplier (1x/2x/5x), spawn palette. |
| **Phase 5: Event Feed & Emotes** | ⏳ **PLANNED**| Combat/lifecycle kill ticker and floating animal state emote badges (!, 💧, 💨). |
| **Phase 6: Boids Herds & Packs** | ⏳ **PLANNED**| Flocking alarm propagation and coordinated wolf pack flanking encirclement. |

---

## ✅ What is DONE (Completed Foundation)

### 1. Architecture & Headless Core (`src/simulation.py`, `src/config.py`)
- Complete architectural separation of simulation logic from rendering.
- Deterministic random number generator (`random.Random(seed)`).
- Fast spatial partitioning (`SpatialGrid`) providing $O(1)$ proximity queries for hundreds of entities.
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
- Size-matching hunting relationships and diet matrices.
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

## 🗺️ Detailed Phased Implementation Plan

```
                       BIG TERRAIN & UI EXPANSION ROADMAP
                                  
  ┌───────────────────────┐       ┌───────────────────────┐       ┌───────────────────────┐
  │        PHASE 1        │       │        PHASE 2        │       │        PHASE 3        │
  │   Big World & Camera  │  ──>  │  Click-to-Inspect &   │  ──>  │   Live In-Game Pop.   │
  │   + Radar Minimap     │       │   Biome Watermarks    │       │   Chart Overlay (C)   │
  └───────────────────────┘       └───────────────────────┘       └───────────────────────┘
                                                                              │
  ┌───────────────────────┐       ┌───────────────────────┐                   │
  │        PHASE 5        │       │        PHASE 4        │                   ▼
  │  Activity Feed Ticker │  <──  │  Interactive Toolbar  │ <─────────────────┘
  │  + Animal State Emotes│       │  & Speed Multipliers  │
  └───────────────────────┘       └───────────────────────┘
```

---

### 🗺️ Phase 1: Big Terrain Expansion, Smooth Camera & Minimap
> **Goal:** Transform the fixed single-screen map into an expansive, scrollable open-world wildlife reserve.

1. **Decoupled World Coordinates & Scaled Biomes**:
   - Decouple screen window resolution ($1280 \times 720$) from world dimensions ($2560 \times 1600$ or $3840 \times 2400$).
   - `TerrainMap` zones and grass biomass grid automatically scale proportionally.
   - Wildlife populations scale to occupy the spacious territories without overcrowding.
2. **Smooth Pan & Zoom Camera Engine (`Camera2D`)**:
   - **Coordinate Transforms**: World-to-screen `(world_x - cam_x) * zoom + screen_w / 2` and inverse screen-to-world for mouse picking.
   - **Panning**: Arrow keys, `WASD`, or middle/right-mouse drag to pan smoothly across the reserve.
   - **Zooming**: Mouse wheel zoom ($0.4\times$ wide reserve view up to $2.0\times$ macro close-up).
   - **World Clamping**: Camera boundaries clamped to world edges with soft spring margins.
   - **Follow-Cam**: Double-clicking or selecting an animal smoothly locks the camera to follow that animal across biomes.
3. **Interactive Corner Radar Minimap**:
   - Rendered at the bottom-right corner ($220 \times 140\,\text{px}$) with a clean semi-transparent dark backdrop.
   - Shows miniature biome territory outlines and live colored blips:
     - 🟢 Herbivores (Rabbits, Deer, Goats)
     - 🔴 Carnivores (Foxes, Wolves, Bears)
   - Viewport rectangle overlay indicating the user's current camera window.
   - **Click-to-Teleport**: Clicking anywhere on the minimap instantly pans the camera to that reserve location.

---

### 🔍 Phase 2: Click-to-Inspect Animal Card & Biome Watermarks
> **Goal:** Provide direct tactile interaction with animals and clear geographic orientation.

1. **Animal Selection & Glowing Target Ring**:
   - Left-click raycasts using screen-to-world transform to pick the nearest animal within 24 pixels.
   - Selected animal receives a pulsing circular selection reticle and vision radius outline.
2. **Animal Inspection Card**:
   - Semi-transparent HUD card sliding out from the right screen edge showing:
     - Animated sprite avatar preview of the selected animal.
     - Species name, ecological niche, and trophic status.
     - Current AI State: `Wandering`, `Grazing`, `Chasing (Target locked)`, `Fleeing`, `Drinking`, or `Exhausted`.
     - Real-time stat progress bars:
       - **Energy / Satiety**: $0\% - 100\%$
       - **Hydration / Thirst**: $0\% - 100\%$
       - **Stamina**: $0\% - 100\%$ (with sprint exhaustion alert)
     - Current interaction target (e.g., `"Chasing Deer #42"` or `"Fleeing Wolf #7"`).
     - Camera "Follow Animal" lock button.
3. **Biome Territory Watermarks & Boundaries (Toggle `B`)**:
   - Elegant, semi-transparent typographic labels positioned in each territory:
     - ⛰️ *Rocky Highlands*
     - 🌲 *Dense Forest*
     - 🌊 *Central River & Watering Hole*
     - 🌿 *Briar Thickets*
     - 🌾 *Open Meadow Plains*
   - Optional toggleable dashed territory borders to visualize habitat boundaries.

---

### 📈 Phase 3: Real-Time In-Game Population Chart Overlay (Key `C`)
> **Goal:** Render live mathematical and ecological proof of dynamic balance inside the game engine.

1. **Rolling Population History Buffer**:
   - Circular buffer recording per-second counts of all 6 individual species over the last 90–120 seconds.
2. **In-Engine Line Graph HUD (Toggle `C`)**:
   - Modern semi-transparent graph panel ($580 \times 220\,\text{px}$) toggled with Key `C`.
   - Multi-line anti-aliased curves color-coded per species:
     - 🐇 Rabbit (Bright green)
     - 🦌 Deer (Emerald)
     - 🐐 Mountain Goat (Cyan/Teal)
     - 🦊 Fox (Orange)
     - 🐺 Wolf (Crimson)
     - 🐻 Bear (Dark Red/Brown)
   - Live trend indicators ($\uparrow$ rising, $\downarrow$ declining, $\approx$ stable).
   - Coexistence equilibrium indicator verifying that neither prey nor predators are facing extinction.
3. **Standalone Exporter (`plot_metrics.py`)**:
   - Generates high-resolution Matplotlib graphs for portfolio presentation:
     - Multi-species time-series oscillating waves.
     - 2D Phase-Portrait (Prey vs. Predators) showing closed limit cycles.

---

### 🎛️ Phase 4: Interactive Toolbar & Playback Controls
> **Goal:** Transition from pure keyboard hotkeys to a modern, clickable desktop interface.

1. **Simulation Control Bar**:
   - Clean top/bottom bar with interactive buttons:
     - **Play / Pause** toggle (`Space`).
     - **Speed Multipliers**: `1x` (Real-time), `2x` (Fast), `5x` (Turbo for multi-minute evaluations).
     - **Reset** (`R`) to respawn fresh reserve seeds.
2. **Quick-Spawn Palette**:
   - One-click buttons to inject animals into the world (`+ Rabbit`, `+ Deer`, `+ Wolf`, `+ Bear`).
   - Allows users to simulate environmental shocks (e.g., an influx of predators or a burst of prey) and observe self-balancing recovery.
3. **View Mode Selector**:
   - Clickable buttons for switching between `2.5D Animated`, `Top-Down 360°`, and `Debug Shapes`.

---

### 📜 Phase 5: Live Activity Log / Event Feed & Animal State Emotes
> **Goal:** Enhance ecological storytelling and instant visual feedback during interactions.

1. **Activity Feed Ticker (Bottom-Left)**:
   - Rolling chronological log of noteworthy ecosystem events:
     - `"🐺 Wolf caught a Deer in Meadow Plains"`
     - `"🐻 Bear caught fish at Central River"`
     - `"🐇 Rabbit litter born in Briar Thickets"`
     - `"🦊 Fox exhausted from high-speed sprint"`
     - `"🐐 Mountain Goat escaped Wolf up the Highlands"`
2. **Floating Animal State Badges & Emotes**:
   - `❗` Floating exclamation alert when prey spots a stalking predator.
   - `💧` Water droplet icon when hydration drops below 25% and animal heads to river.
   - `💨` Exhaustion puff when stamina reaches 0%.
   - `❤️` Reproduction heart when animal successfully reproduces.

---

### 🦌 Phase 6: Advanced Collective AI: Herds & Packs
> **Goal:** Natural flocking and pack hunting behaviors.

1. **Flocking Herds (Reynolds Boids)**:
   - Deer and rabbits moving with Separation, Alignment, and Cohesion vectors.
   - Herd panic propagation: when one deer spots a wolf, nearby herd mates immediately flee together.
2. **Coordinated Wolf Pack Tactics**:
   - Wolves identify shared targets and take flanking angles to encircle fleeing prey.
   - Pack energy sharing when feasting on a large kill.

---

## 🎮 Summary of Controls (Planned Complete Scheme)

| Input | Action |
| :--- | :--- |
| **`WASD` / Arrow Keys** | Pan camera across the big terrain |
| **Mouse Wheel** | Zoom in / Zoom out ($0.4\times$ to $2.0\times$) |
| **Right-Click Drag** | Grab and pan the reserve camera |
| **Left-Click** | Select & inspect animal (opens Inspector Card) |
| **Minimap Click** | Teleport camera to clicked territory |
| **`C`** | Toggle real-time in-game population chart |
| **`B`** | Toggle biome watermarks and territorial boundaries |
| **`V`** | Toggle visual mode (2.5D Sprite $\leftrightarrow$ Top-Down $\leftrightarrow$ Shapes) |
| **`1` / `2` / `5`** | Set simulation speed ($1\times$, $2\times$, $5\times$) |
| **`Space`** | Pause / Resume simulation |
| **`R`** | Reset simulation with fresh seed |
| **`Esc`** | Exit simulation |
