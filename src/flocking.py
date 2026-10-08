"""Collective Animal AI: Reynolds Boids Herds & Wolf Pack Tactics (Phase 6).

Implements:
1. Reynolds Boids Flocking for Herbivore Herds (Deer, Rabbits, Mountain Goats):
   - Separation: steer away from crowded herdmates to prevent unnatural overlapping.
   - Alignment: align movement direction with nearby moving herdmates.
   - Cohesion: steer toward the center of mass of the herd cluster.
   - Herd Panic Propagation: when one herd member detects a predator and flees,
     nearby herdmates immediately sense the panic and cascade into a stampede.

2. Coordinated Wolf Pack Tactics:
   - Shared Quarry Targeting & Encirclement: wolves coordinating on prey assign
     flanking pursuit angles (+35° and -35° arcs) to intercept and encircle fleeing targets.
   - Pack Energy Sharing / Feasting: nearby pack mates within feasting radius join
     in feasting on large kills (Deer, Goats) and share energy gains.
"""

from __future__ import annotations
import math
from typing import List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from src.entities import Animal


def compute_boids_steering(
    animal: Animal,
    neighbors: List[Animal],
    separation_dist: float = 26.0,
    max_steering_force: float = 0.28,
) -> Optional[float]:
    """Computes combined Reynolds Boids steering angle delta for herd animals.

    Returns an adjusted heading angle (in radians) or None if no herdmates are present.
    """
    # Filter to alive flockmates excluding self
    flockmates = [n for n in neighbors if n.alive and n.entity_id != animal.entity_id and n.profile.name == animal.profile.name]
    if not flockmates:
        return None

    sep_x, sep_y = 0.0, 0.0
    align_x, align_y = 0.0, 0.0
    center_x, center_y = 0.0, 0.0
    sep_count = 0

    for mate in flockmates:
        dx = mate.x - animal.x
        dy = mate.y - animal.y
        dist = math.hypot(dx, dy)

        # 1. Separation (repulsion from close neighbors)
        if 0.001 < dist < separation_dist:
            weight = (separation_dist - dist) / separation_dist
            sep_x -= (dx / dist) * weight
            sep_y -= (dy / dist) * weight
            sep_count += 1

        # 2. Alignment (match neighbor velocity headings)
        align_x += math.cos(mate.heading)
        align_y += math.sin(mate.heading)

        # 3. Cohesion (steer toward center of cluster)
        center_x += mate.x
        center_y += mate.y

    n_mates = float(len(flockmates))

    # Normalize alignment
    align_len = math.hypot(align_x, align_y)
    if align_len > 0.001:
        align_x /= align_len
        align_y /= align_len

    # Calculate cohesion vector
    avg_x = center_x / n_mates
    avg_y = center_y / n_mates
    coh_dx = avg_x - animal.x
    coh_dy = avg_y - animal.y
    coh_len = math.hypot(coh_dx, coh_dy)
    if coh_len > 0.001:
        coh_x = coh_dx / coh_len
        coh_y = coh_dy / coh_len
    else:
        coh_x, coh_y = 0.0, 0.0

    # Weight forces (Separation > Alignment > Cohesion)
    w_sep = 1.4 if sep_count > 0 else 0.0
    w_align = 0.8
    w_coh = 0.5

    steer_vx = w_sep * sep_x + w_align * align_x + w_coh * coh_x
    steer_vy = w_sep * sep_y + w_align * align_y + w_coh * coh_y

    steer_len = math.hypot(steer_vx, steer_vy)
    if steer_len < 0.01:
        return None

    desired_angle = math.atan2(steer_vy, steer_vx)
    # Smooth blend toward desired boids angle
    curr_angle = animal.heading
    angle_diff = (desired_angle - curr_angle + math.pi) % (2.0 * math.pi) - math.pi
    clamped_diff = max(-max_steering_force, min(max_steering_force, angle_diff))
    return (curr_angle + clamped_diff) % (2.0 * math.pi)


def check_herd_alarm(animal: Animal, neighbors: List[Animal]) -> Optional[Animal]:
    """Checks if any nearby herdmate is fleeing in panic.

    If found, returns the alarmed herdmate to trigger herd panic propagation.
    """
    for n in neighbors:
        if not n.alive or n.entity_id == animal.entity_id:
            continue
        state_val = getattr(n.state, "value", str(n.state))
        if n.profile.name == animal.profile.name and state_val == "flee":
            return n
    return None


def compute_pack_flanking_angle(
    wolf: Animal,
    quarry: Animal,
    pack_mates: List[Animal],
) -> float:
    """Computes tactical flanking pursuit heading for wolves hunting in a pack.

    Assigns lead pursuer to direct intercept, and flankers to offset angles (+35° and -35° arcs).
    """
    direct_heading = wolf.angle_to(quarry.x, quarry.y)

    # Filter other hunting wolves targeting the same quarry or in proximity
    co_hunters = [
        m for m in pack_mates
        if m.alive and m.entity_id != wolf.entity_id
        and getattr(m, "target_prey_id", None) == quarry.entity_id
    ]

    if not co_hunters:
        return direct_heading  # Solo chase

    # Rank wolves by distance to quarry
    all_pack = [wolf] + co_hunters
    all_pack.sort(key=lambda w: w.distance_to(quarry))

    # Identify this wolf's tactical role
    rank = next((i for i, w in enumerate(all_pack) if w.entity_id == wolf.entity_id), 0)

    if rank == 0:
        # Lead wolf: direct pursuit
        return direct_heading
    elif rank == 1:
        # Left flanker: arc +35 degrees (+0.61 radians)
        return (direct_heading + 0.61) % (2.0 * math.pi)
    elif rank == 2:
        # Right flanker: arc -35 degrees (-0.61 radians)
        return (direct_heading - 0.61) % (2.0 * math.pi)
    else:
        # Reserve flanker: slightly wider arc
        offset = 0.85 if rank % 2 == 1 else -0.85
        return (direct_heading + offset) % (2.0 * math.pi)


def share_pack_kill(
    killer: Animal,
    victim: Animal,
    pack_mates: List[Animal],
    feasting_radius: float = 65.0,
) -> List[Animal]:
    """Shares a large kill (Deer, Goat) with nearby pack mates within feasting radius.

    Returns list of pack mates who joined in feasting.
    """
    # Only wolves and packs share large meals
    if killer.profile.name != "wolf":
        return []

    participating: List[Animal] = []
    for mate in pack_mates:
        if not mate.alive or mate.entity_id == killer.entity_id or mate.profile.name != "wolf":
            continue

        if killer.distance_to(mate) <= feasting_radius:
            from src.entities import AnimalState
            mate.state = AnimalState.EAT
            mate.eat_timer = 0.65
            mate.target_prey_id = None
            # Share half feed energy
            mate.energy = min(
                mate.profile.max_energy,
                mate.energy + mate.profile.energy_gain_feed * 0.5,
            )
            participating.append(mate)

    return participating
