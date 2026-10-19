"""Generate high-resolution logo assets and badges for Wildlife Ecosystem.

Outputs:
  - assets/logo.png (Full brand logo banner with crest & typography)
  - assets/logo_badge.png (Crisp emblem crest for in-game HUD and menus)
  - assets/icon.png and assets/icon.ico (Windows application icons)
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_emblem(size=128):
    """Creates a circular wildlife reserve crest with emerald shield, gold trim, and wolf/deer silhouette."""
    emblem = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(emblem)
    
    pad = int(size * 0.04)
    # 1. Outer golden rim
    draw.ellipse([pad, pad, size - pad, size - pad], fill=(212, 175, 55, 255), outline=(255, 223, 105, 255), width=2)
    
    # 2. Forest shield body
    shield_pad = pad + int(size * 0.05)
    draw.ellipse([shield_pad, shield_pad, size - shield_pad, size - shield_pad], fill=(18, 42, 32, 255), outline=(45, 95, 70, 255), width=3)
    
    # 3. Nature mountain/landscape silhouettes inside crest
    c_x, c_y = size // 2, size // 2
    # Mountain peak
    draw.polygon([
        (c_x, int(size * 0.35)),
        (int(size * 0.22), int(size * 0.72)),
        (int(size * 0.78), int(size * 0.72))
    ], fill=(32, 68, 52, 255))
    
    # Secondary peak
    draw.polygon([
        (int(size * 0.65), int(size * 0.42)),
        (int(size * 0.45), int(size * 0.72)),
        (int(size * 0.85), int(size * 0.72))
    ], fill=(42, 85, 65, 255))
    
    # Water stream at bottom of crest
    draw.chord([shield_pad, int(size * 0.58), size - shield_pad, size - shield_pad], start=0, end=180, fill=(35, 120, 175, 255))
    draw.arc([shield_pad, int(size * 0.58), size - shield_pad, size - shield_pad], start=0, end=180, fill=(90, 200, 250, 255), width=2)

    # 4. Paste wolf sprite in center
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    wolf_p = os.path.join(repo_root, "assets", "sprites", "wolf", "idle", "idle_0.png")
    if os.path.exists(wolf_p):
        w_img = Image.open(wolf_p).convert("RGBA")
        bbox = w_img.getbbox()
        if bbox:
            w_img = w_img.crop(bbox)
        target_h = int(size * 0.46)
        scale = target_h / max(1, w_img.height)
        new_w = int(w_img.width * scale)
        new_h = int(w_img.height * scale)
        w_img = w_img.resize((new_w, new_h), Image.Resampling.NEAREST)
        
        # Position slightly offset to center of crest
        paste_x = c_x - (new_w // 2)
        paste_y = int(size * 0.38)
        emblem.alpha_composite(w_img, (paste_x, paste_y))
        
    return emblem

def generate_logo():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_dir = os.path.join(repo_root, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    # 1. Generate Emblem Crest
    badge_128 = create_emblem(128)
    badge_path = os.path.join(assets_dir, "logo_badge.png")
    badge_128.save(badge_path, format="PNG")
    print(f"[OK] Saved emblem badge: {badge_path}")

    # 2. Generate Full Horizontal Logo Banner (520x96)
    banner_w, banner_h = 520, 96
    banner = Image.new("RGBA", (banner_w, banner_h), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(banner)
    
    # Translucent stylized backplate with glowing border
    b_draw.rounded_rectangle([2, 2, banner_w - 3, banner_h - 3], radius=16, fill=(14, 22, 28, 230), outline=(60, 110, 85, 255), width=2)
    b_draw.line([88, 12, 88, banner_h - 12], fill=(45, 75, 65, 200), width=1)
    
    # Paste 80x80 emblem on left
    badge_80 = create_emblem(80)
    banner.alpha_composite(badge_80, (8, 8))
    
    # Typography
    font_large_path = "C:\\Windows\\Fonts\\arialbd.ttf"
    font_sub_path = "C:\\Windows\\Fonts\\consolab.ttf"
    
    try:
        font_large = ImageFont.truetype(font_large_path, 26)
        font_sub = ImageFont.truetype(font_sub_path, 13)
        font_tag = ImageFont.truetype(font_sub_path, 10)
    except Exception:
        font_large = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_tag = ImageFont.load_default()

    # Drop shadow for title
    b_draw.text((106, 17), "WILDLIFE ECOSYSTEM", font=font_large, fill=(5, 10, 8, 200))
    # Main golden/ivory title
    b_draw.text((104, 15), "WILDLIFE ECOSYSTEM", font=font_large, fill=(245, 252, 248, 255))
    
    # Subtitle with accent colors
    b_draw.text((105, 48), "PREDATOR \u2013 PREY BALANCE RESERVE", font=font_sub, fill=(110, 230, 140, 255))
    
    # Status / tag pills with dynamic measurement
    # Pill 1: Autonomous AI
    text1 = "AUTONOMOUS AI"
    bbox1 = font_tag.getbbox(text1)
    tw1 = bbox1[2] - bbox1[0]
    p1_x1, p1_x2 = 105, 105 + tw1 + 16
    b_draw.rounded_rectangle([p1_x1, 68, p1_x2, 85], radius=4, fill=(28, 55, 42, 255), outline=(70, 150, 100, 255), width=1)
    b_draw.text((p1_x1 + 8, 70), text1, font=font_tag, fill=(185, 240, 200, 255))

    # Pill 2: Dynamic Ecosystem
    text2 = "DYNAMIC BALANCE"
    bbox2 = font_tag.getbbox(text2)
    tw2 = bbox2[2] - bbox2[0]
    p2_x1, p2_x2 = p1_x2 + 8, p1_x2 + 8 + tw2 + 16
    b_draw.rounded_rectangle([p2_x1, 68, p2_x2, 85], radius=4, fill=(20, 48, 68, 255), outline=(45, 120, 180, 255), width=1)
    b_draw.text((p2_x1 + 8, 70), text2, font=font_tag, fill=(135, 215, 255, 255))

    # Pill 3: 60 FPS Engine
    text3 = "60 FPS 2.5D"
    bbox3 = font_tag.getbbox(text3)
    tw3 = bbox3[2] - bbox3[0]
    p3_x1, p3_x2 = p2_x2 + 8, p2_x2 + 8 + tw3 + 16
    b_draw.rounded_rectangle([p3_x1, 68, p3_x2, 85], radius=4, fill=(45, 30, 60, 255), outline=(150, 90, 190, 255), width=1)
    b_draw.text((p3_x1 + 8, 70), text3, font=font_tag, fill=(225, 185, 255, 255))

    logo_path = os.path.join(assets_dir, "logo.png")
    banner.save(logo_path, format="PNG")
    print(f"[OK] Saved brand logo banner: {logo_path}")

    # 3. Update App Icon (.ico and .png) with high-res 256x256 crest
    icon_256 = create_emblem(256)
    icon_png_path = os.path.join(assets_dir, "icon.png")
    icon_256.save(icon_png_path, format="PNG")
    
    icon_ico_path = os.path.join(assets_dir, "icon.ico")
    icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icon_256.save(icon_ico_path, format="ICO", sizes=icon_sizes)
    print(f"[OK] Updated app icon: {icon_ico_path}")

if __name__ == "__main__":
    generate_logo()
