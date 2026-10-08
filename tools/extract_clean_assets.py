"""Extracts clean tiles, landmarks, and isolated transparent props from the 5 user tileset sheets."""

import os
from PIL import Image
import numpy as np


def make_transparent(im_crop, threshold=238):
    """Converts near-white background to crystal-clear transparent alpha and trims border."""
    im_crop = im_crop.convert("RGBA")
    arr = np.array(im_crop)
    # Background is near-white
    is_bg = (arr[:, :, 0] > threshold) & (arr[:, :, 1] > threshold) & (arr[:, :, 2] > threshold)
    arr[is_bg, 3] = 0
    # Clean edges: slight alpha smoothing for fringe pixels
    fringe = (arr[:, :, 0] > 215) & (arr[:, :, 1] > 215) & (arr[:, :, 2] > 215) & ~is_bg
    arr[fringe, 3] = 160
    clean = Image.fromarray(arr)
    bbox = clean.getbbox()
    if bbox:
        clean = clean.crop(bbox)
    return clean


def main():
    base_user = r"C:\Users\kurtr\.gemini\antigravity\brain\7e81f2c9-2770-4e4d-bee3-289e832d8b59\.user_uploaded"
    out_dir = "assets/terrain"

    # =========================================================================
    # 1. MEADOW
    # =========================================================================
    meadow_path = os.path.join(base_user, "media_1791457539485_b01d1191.jpg")
    if os.path.exists(meadow_path):
        m_img = Image.open(meadow_path)
        m_dir = os.path.join(out_dir, "meadow")
        os.makedirs(m_dir, exist_ok=True)

        # Ground tiles (clean cut, no borders)
        m_img.crop((46, 66, 178, 250)).save(os.path.join(m_dir, "ground_lush.png"))
        m_img.crop((190, 66, 350, 250)).save(os.path.join(m_dir, "ground_pasture.png"))
        m_img.crop((46, 268, 178, 362)).save(os.path.join(m_dir, "ground_trail.png"))

        # Landmarks
        m_img.crop((356, 568, 626, 752)).save(os.path.join(m_dir, "landmark_crossroads.png"))
        m_img.crop((44, 568, 312, 752)).save(os.path.join(m_dir, "landmark_winding_trail.png"))

        # Transparent Props
        make_transparent(m_img.crop((660, 630, 775, 745))).save(os.path.join(m_dir, "prop_rock.png"))
        make_transparent(m_img.crop((778, 630, 890, 750))).save(os.path.join(m_dir, "prop_log.png"))
        make_transparent(m_img.crop((895, 620, 985, 750))).save(os.path.join(m_dir, "prop_tree.png"))
        make_transparent(m_img.crop((390, 75, 455, 145))).save(os.path.join(m_dir, "prop_flowers.png"))
        make_transparent(m_img.crop((390, 160, 455, 235))).save(os.path.join(m_dir, "prop_poppy.png"))
        make_transparent(m_img.crop((390, 250, 455, 315))).save(os.path.join(m_dir, "prop_bluebells.png"))
        make_transparent(m_img.crop((555, 160, 630, 240))).save(os.path.join(m_dir, "prop_bush.png"))
        make_transparent(m_img.crop((460, 385, 540, 460))).save(os.path.join(m_dir, "prop_clover.png"))
        print("Meadow extracted cleanly.")

    # =========================================================================
    # 2. RIVER
    # =========================================================================
    river_path = os.path.join(base_user, "media_1791457539487_028ef792.jpg")
    if os.path.exists(river_path):
        r_img = Image.open(river_path)
        r_dir = os.path.join(out_dir, "river")
        os.makedirs(r_dir, exist_ok=True)

        # River landmark strips (winding water with banks & rocks)
        r_img.crop((44, 60, 312, 280)).save(os.path.join(r_dir, "water_stream.png"))
        r_img.crop((44, 290, 312, 495)).save(os.path.join(r_dir, "water_pool.png"))
        r_img.crop((44, 510, 312, 750)).save(os.path.join(r_dir, "water_rapids.png"))

        # Circular Watering Hole Ponds (landmarks!)
        make_transparent(r_img.crop((660, 60, 820, 230))).save(os.path.join(r_dir, "prop_pond1.png"))
        make_transparent(r_img.crop((830, 60, 980, 230))).save(os.path.join(r_dir, "prop_pond2.png"))
        make_transparent(r_img.crop((660, 240, 820, 410))).save(os.path.join(r_dir, "prop_pond_boulders.png"))
        make_transparent(r_img.crop((830, 240, 980, 410))).save(os.path.join(r_dir, "prop_pond_canopy.png"))

        # Water foam / rapids / rocks
        make_transparent(r_img.crop((660, 560, 820, 750))).save(os.path.join(r_dir, "prop_foam.png"))
        make_transparent(r_img.crop((55, 60, 140, 140))).save(os.path.join(r_dir, "prop_shore_left.png"))
        make_transparent(r_img.crop((230, 60, 305, 140))).save(os.path.join(r_dir, "prop_shore_right.png"))
        print("River extracted cleanly.")

    # =========================================================================
    # 3. FOREST
    # =========================================================================
    forest_path = os.path.join(base_user, "media_1791457539503_0c179880.jpg")
    if os.path.exists(forest_path):
        f_img = Image.open(forest_path)
        f_dir = os.path.join(out_dir, "forest")
        os.makedirs(f_dir, exist_ok=True)

        # Forest ground tiles
        f_img.crop((44, 66, 230, 255)).save(os.path.join(f_dir, "ground_moss.png"))
        f_img.crop((240, 66, 426, 255)).save(os.path.join(f_dir, "ground_foliage.png"))

        # Forest landmark: Ancient Oak Tree & Canopy
        make_transparent(f_img.crop((420, 480, 625, 750))).save(os.path.join(f_dir, "prop_tree.png"))
        make_transparent(f_img.crop((660, 60, 980, 410))).save(os.path.join(f_dir, "prop_canopy.png"))
        make_transparent(f_img.crop((290, 490, 410, 750))).save(os.path.join(f_dir, "prop_stump.png"))
        make_transparent(f_img.crop((130, 510, 285, 610))).save(os.path.join(f_dir, "prop_log.png"))
        make_transparent(f_img.crop((150, 615, 285, 750))).save(os.path.join(f_dir, "prop_bush.png"))
        print("Forest extracted cleanly.")

    # =========================================================================
    # 4. HIGHLANDS
    # =========================================================================
    highlands_path = os.path.join(base_user, "media_1791457539485_6fb26f9c.jpg")
    if os.path.exists(highlands_path):
        h_img = Image.open(highlands_path)
        h_dir = os.path.join(out_dir, "highlands")
        os.makedirs(h_dir, exist_ok=True)

        # Ground tiles
        h_img.crop((44, 66, 178, 250)).save(os.path.join(h_dir, "ground_rock.png"))
        h_img.crop((190, 66, 350, 250)).save(os.path.join(h_dir, "ground_plateau.png"))

        # Landmarks: Stepped Cliff Slope & Cliff Plateau
        make_transparent(h_img.crop((520, 500, 740, 750))).save(os.path.join(h_dir, "landmark_cliff_ramp.png"))
        make_transparent(h_img.crop((44, 520, 312, 750))).save(os.path.join(h_dir, "landmark_cliff_plateau.png"))

        # Large Rock Formations & Pines
        make_transparent(h_img.crop((660, 60, 810, 260))).save(os.path.join(h_dir, "prop_rock_large1.png"))
        make_transparent(h_img.crop((820, 60, 980, 260))).save(os.path.join(h_dir, "prop_rock_large2.png"))
        make_transparent(h_img.crop((820, 270, 980, 430))).save(os.path.join(h_dir, "prop_rock_slabs.png"))
        make_transparent(h_img.crop((660, 270, 810, 430))).save(os.path.join(h_dir, "prop_boulder.png"))
        make_transparent(h_img.crop((660, 460, 735, 600))).save(os.path.join(h_dir, "prop_pine.png"))
        make_transparent(h_img.crop((815, 670, 900, 750))).save(os.path.join(h_dir, "prop_cave.png"))
        print("Highlands extracted cleanly.")

    # =========================================================================
    # 5. THICKETS
    # =========================================================================
    thickets_path = os.path.join(base_user, "media_1791457539485_136d9ec5.jpg")
    if os.path.exists(thickets_path):
        t_img = Image.open(thickets_path)
        t_dir = os.path.join(out_dir, "thickets")
        os.makedirs(t_dir, exist_ok=True)

        # Ground tiles
        t_img.crop((44, 110, 230, 290)).save(os.path.join(t_dir, "ground_roots.png"))
        t_img.crop((240, 110, 426, 290)).save(os.path.join(t_dir, "ground_moss.png"))

        # Dense Thickets & Briar Barriers
        make_transparent(t_img.crop((44, 380, 200, 580))).save(os.path.join(t_dir, "prop_dense_bush1.png"))
        make_transparent(t_img.crop((205, 380, 370, 580))).save(os.path.join(t_dir, "prop_dense_bush2.png"))
        make_transparent(t_img.crop((340, 630, 500, 750))).save(os.path.join(t_dir, "prop_briar_barrier.png"))
        make_transparent(t_img.crop((44, 630, 200, 750))).save(os.path.join(t_dir, "prop_deadwood.png"))
        make_transparent(t_img.crop((890, 480, 970, 590))).save(os.path.join(t_dir, "prop_berries.png"))
        print("Thickets extracted cleanly.")

    print("\nALL 5 TILESHEETS CLEANLY EXTRACTED WITH TRANSPARENT ALPHA!")


if __name__ == "__main__":
    main()
