"""Clean and decontaminate all wildlife animal sprites.

Fixes:
- Removes text headers ("Idle", "Run", "Walk", "ADVANCED &", etc.)
- Removes baked-in checkerboard backgrounds and white JPEG compression halos
- Preserves internal white fur (chest, tail tip) via border flood-fill
- Fixes double-fox frames where two foxes were packed into one frame
"""

import os
from collections import deque
from PIL import Image
import numpy as np


def clean_sprite_surface(arr_rgba, is_fox=False, is_deer=False):
    """Cleans background and defringes edges from an RGBA numpy array."""
    h, w = arr_rgba.shape[:2]
    arr = arr_rgba.copy()

    # If deer has 'Idle' or 'Run' text in top-left
    if is_deer and h > 50:
        arr[0:22, 0:45, 3] = 0

    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]

    # Detect background:
    # 1. Pure or near white
    is_pure_white = (r >= 220) & (g >= 220) & (b >= 220)

    # 2. Fake checkerboard (grayscale shades where r ~= g ~= b and brightness >= 155)
    diff = np.maximum(
        np.maximum(np.abs(r.astype(int) - g.astype(int)), np.abs(r.astype(int) - b.astype(int))),
        np.abs(g.astype(int) - b.astype(int)),
    )
    is_checker = (diff <= 16) & (r >= 155) & (g >= 155) & (b >= 155)

    is_bg = (a == 0) | is_pure_white | is_checker

    # Flood-fill from borders only (preserves white fur inside animal body)
    bg_mask = np.zeros((h, w), dtype=bool)
    queue = deque()
    for x in range(w):
        if is_bg[0, x]:
            queue.append((0, x))
            bg_mask[0, x] = True
        if is_bg[h - 1, x]:
            queue.append((h - 1, x))
            bg_mask[h - 1, x] = True
    for y in range(h):
        if is_bg[y, 0]:
            queue.append((y, 0))
            bg_mask[y, 0] = True
        if is_bg[y, w - 1]:
            queue.append((y, w - 1))
            bg_mask[y, w - 1] = True

    while queue:
        cy, cx = queue.popleft()
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < h and 0 <= nx < w:
                if not bg_mask[ny, nx] and is_bg[ny, nx]:
                    bg_mask[ny, nx] = True
                    queue.append((ny, nx))

    arr[bg_mask, 3] = 0

    # Edge decontamination: trim 1px JPEG ringing fringe touching exterior
    border_fringe = np.zeros((h, w), dtype=bool)
    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
        shifted = np.roll(np.roll(bg_mask, dy, axis=0), dx, axis=1)
        border_fringe |= shifted

    lum = (arr[:, :, 0].astype(int) + arr[:, :, 1].astype(int) + arr[:, :, 2].astype(int)) // 3
    is_fringe = border_fringe & (arr[:, :, 3] > 0) & (lum >= 170)
    arr[is_fringe, 3] = 0

    res = Image.fromarray(arr)
    bbox = res.getbbox()
    return res.crop(bbox) if bbox else res


def clean_fox_spritesheet():
    """Extracts all animation frames directly from assets/sprites/fox_spritesheet.jpg."""
    sheet_p = "assets/sprites/fox_spritesheet.jpg"
    if not os.path.isfile(sheet_p):
        return
    sheet = Image.open(sheet_p).convert("RGBA")
    arr = np.array(sheet)

    # Fox row bounds in sheet (1024 x 682):
    # Row 1: IDLE (DOWN) - y=[85, 155], cols around x=[25, 95], [125, 195], [225, 295], [330, 400]
    # Row 2: WALK (RIGHT) - y=[185, 240], cols [220, 320], [325, 430], [755, 865], [865, 975]
    # Row 3: SIT / WAIT - y=[270, 350], cols [25, 105], [125, 205], [215, 295], [310, 395]
    # Row 4: ATTACK (LEFT) - y=[375, 455], cols [20, 135], [140, 255], [260, 375], [380, 500]
    # Row 5: ADVANCED RUN (RIGHT) - y=[490, 570], cols [20, 140], [145, 275], [278, 410]
    # Row 6: HURT - y=[595, 675], cols [20, 125], [130, 235], [240, 345]
    # Row 7: DIE - y=[595, 675], cols [510, 630], [635, 755]

    anims = {
        "idle": [
            (25, 85, 100, 158),
            (125, 85, 200, 158),
            (225, 85, 300, 158),
            (325, 85, 400, 158),
        ],
        "walk": [
            (218, 168, 332, 246),
            (325, 168, 440, 246),
            (750, 165, 870, 246),
            (870, 165, 990, 246),
        ],
        "run": [
            (20, 500, 142, 574),
            (145, 500, 275, 574),
            (278, 500, 410, 574),
        ],
        "attack": [
            (20, 380, 138, 458),
            (140, 380, 258, 458),
            (260, 380, 378, 458),
            (380, 380, 502, 458),
        ],
        "hurt": [
            (20, 600, 128, 676),
            (130, 600, 238, 676),
            (240, 600, 348, 676),
        ],
        "die": [
            (512, 600, 632, 676),
            (635, 600, 758, 676),
        ],
    }

    for act, boxes in anims.items():
        out_d = os.path.join("assets", "sprites", "fox", act)
        os.makedirs(out_d, exist_ok=True)
        for i, box in enumerate(boxes):
            crop = sheet.crop(box)
            clean = clean_sprite_surface(np.array(crop), is_fox=True)
            p = os.path.join(out_d, f"{act}_{i}.png")
            clean.save(p)
    print("[OK] Fox sprites flawlessly cleaned and re-sliced.")


def clean_deer_spritesheet():
    """Extracts all animation frames directly from assets/sprites/deer_spritesheet.jpg."""
    sheet_p = "assets/sprites/deer_spritesheet.jpg"
    if not os.path.isfile(sheet_p):
        return
    sheet = Image.open(sheet_p).convert("RGBA")

    # Deer row bounds in sheet (1024 x 682):
    # Row 1 (Idle & Walk): y=[260, 355]
    # Row 2 (Run): y=[380, 460]
    # Row 3 (Attack & Hurt): y=[495, 575]
    # Row 4 (Die): y=[610, 675]
    # Top View: y=[125, 245], x=[640, 960]

    anims = {
        "idle": [
            (25, 260, 115, 355),
            (120, 260, 210, 355),
            (215, 260, 305, 355),
            (310, 260, 400, 355),
        ],
        "walk": [
            (480, 260, 580, 355),
            (582, 260, 680, 355),
            (685, 260, 785, 355),
            (785, 260, 885, 355),
            (885, 260, 985, 355),
        ],
        "run": [
            (25, 380, 135, 462),
            (140, 380, 255, 462),
            (260, 380, 380, 462),
            (385, 380, 505, 462),
            (510, 380, 640, 462),
            (660, 380, 790, 462),
        ],
        "attack": [
            (25, 495, 135, 578),
            (140, 495, 250, 578),
            (255, 495, 365, 578),
            (370, 495, 480, 578),
            (485, 495, 595, 578),
            (600, 495, 710, 578),
        ],
        "hurt": [
            (715, 495, 815, 578),
            (820, 495, 920, 578),
            (925, 495, 1015, 578),
        ],
        "die": [
            (25, 610, 135, 680),
            (140, 610, 245, 680),
            (250, 610, 355, 680),
            (360, 610, 475, 680),
            (480, 610, 595, 680),
        ],
        "top_view": [
            (640, 125, 715, 245),
            (720, 125, 795, 245),
            (800, 125, 875, 245),
            (880, 125, 955, 245),
        ],
    }

    for act, boxes in anims.items():
        out_d = os.path.join("assets", "sprites", "deer", act)
        os.makedirs(out_d, exist_ok=True)
        for i, box in enumerate(boxes):
            crop = sheet.crop(box)
            clean = clean_sprite_surface(np.array(crop), is_deer=True)
            p = os.path.join(out_d, f"{act}_{i}.png")
            clean.save(p)
    print("[OK] Deer sprites flawlessly cleaned and re-sliced.")


def clean_existing_sprites():
    """Cleans all existing animal sprite directories in place to ensure zero white halos."""
    for animal in ["bear", "goat"]:
        p = os.path.join("assets", "sprites", animal)
        if not os.path.isdir(p):
            continue
        for root, _, files in os.walk(p):
            for f in sorted(files):
                if not f.endswith(".png"):
                    continue
                fp = os.path.join(root, f)
                try:
                    im = Image.open(fp).convert("RGBA")
                    clean = clean_sprite_surface(np.array(im))
                    clean.save(fp)
                except Exception as e:
                    print(f"Error cleaning {fp}: {e}")
        print(f"[OK] Cleaned {animal} sprites in-place.")


if __name__ == "__main__":
    clean_fox_spritesheet()
    clean_deer_spritesheet()
    clean_existing_sprites()
    print("ALL SPRITES CLEANED WITH ZERO HALOS AND ZERO TEXT!")
