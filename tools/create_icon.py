"""Generate high-resolution application icon (.ico and .png) for Wildlife Ecosystem."""

import os
from PIL import Image, ImageDraw

def create_app_icon():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_dir = os.path.join(repo_root, "assets")
    
    # 256x256 base canvas
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Rounded badge background with rich nature gradient / circle
    # Forest/Reserve themed badge
    bg_color = (28, 48, 38, 255)       # Deep forest emerald
    border_color = (88, 166, 120, 255)  # Vibrant moss outline
    draw.rounded_rectangle([8, 8, size - 8, size - 8], radius=52, fill=bg_color, outline=border_color, width=6)
    
    # Inner circular highlight
    draw.ellipse([24, 24, size - 24, size - 24], fill=(36, 68, 52, 255))
    
    # Load wolf or deer sprite if available
    wolf_sprite_path = os.path.join(assets_dir, "sprites", "wolf", "idle", "idle_0.png")
    deer_sprite_path = os.path.join(assets_dir, "sprites", "deer", "idle", "idle_0.png")
    
    if os.path.exists(wolf_sprite_path):
        wolf_img = Image.open(wolf_sprite_path).convert("RGBA")
        # Crop bounding box of non-transparent pixels
        bbox = wolf_img.getbbox()
        if bbox:
            wolf_img = wolf_img.crop(bbox)
        # Resize to fit nicely inside the badge
        w_scale = 160.0 / max(wolf_img.width, wolf_img.height)
        new_w = int(wolf_img.width * w_scale)
        new_h = int(wolf_img.height * w_scale)
        wolf_resized = wolf_img.resize((new_w, new_h), Image.Resampling.NEAREST)
        
        # Paste centered in badge
        paste_x = (size - new_w) // 2
        paste_y = (size - new_h) // 2 - 6
        img.alpha_composite(wolf_resized, (paste_x, paste_y))
    
    # Save 256x256 PNG
    png_path = os.path.join(assets_dir, "icon.png")
    img.save(png_path, format="PNG")
    print(f"Generated {png_path}")
    
    # Save Windows multi-size .ico
    ico_path = os.path.join(assets_dir, "icon.ico")
    icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format="ICO", sizes=icon_sizes)
    print(f"Generated {ico_path}")

if __name__ == "__main__":
    create_app_icon()
