#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
from collections import Counter
from PIL import Image, ImageDraw, ImageFont

# --- Configuration ---
# Paths matching those in sprite-diagnostic.py
SPRITESHEET_DIRECTORY = '/Users/rfoltz/dev/game-dev/wetworks/Assets/Resources/sprites/spritesheets'
HEAD_SPRITESHEET_DIRECTORY = '/Users/rfoltz/dev/game-dev/wetworks/Assets/Resources/sprites/spritesheets/head'


SKINTONE_LIGHT_1 = "#EEC39A"
SKINTONE_LIGHT_2 = "#D9A066"
SKINTONE_LIGHT_3 = "#E0B187"
SKINTONE_LIGHT_4 = "#D0A780"

SKINTONE_DARK_1 = "#6E4E2C"
SKINTONE_DARK_2 = "#523C27"

RECOLOR_DARK = {
    SKINTONE_LIGHT_1: SKINTONE_DARK_1,
    SKINTONE_LIGHT_2: SKINTONE_DARK_2,
    SKINTONE_LIGHT_3: SKINTONE_DARK_2,
    SKINTONE_LIGHT_4: SKINTONE_DARK_2
}


def parse_hex_color(hex_str):
    """Parses a hex color string (e.g., '#FF0000' or 'FF0000') into an (R, G, B) tuple."""
    hex_str = hex_str.lstrip('#')
    if len(hex_str) != 6:
        raise ValueError(f"Invalid hex color code: '{hex_str}'")
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def replace_colors(image, color_map):
    """
    Replaces colors in the image based on the provided map.
    color_map: dict mapping (r, g, b) -> (r, g, b)
    Preserves the original alpha channel of the pixels.
    """
    # Ensure image is RGBA to handle transparency correctly
    img = image.convert("RGBA")
    data = img.getdata()
    
    new_data = []
    # Optimization: Local variable lookup
    get_new_color = color_map.get
    
    for pixel in data:
        # pixel is (r, g, b, a)
        rgb = pixel[:3]
        new_rgb = get_new_color(rgb)
        
        if new_rgb:
            new_data.append(new_rgb + (pixel[3],))
        else:
            new_data.append(pixel)
            
    img.putdata(new_data)
    return img

def analyze_palette(files_to_process):
    """Generates a diagnostic image showing all colors used and their counts."""
    color_counts = Counter()
    print("Analyzing palette...")
    
    for src_path in files_to_process:
        try:
            img = Image.open(src_path).convert("RGBA")
            # Get data
            data = img.getdata()
            for pixel in data:
                # pixel is (r, g, b, a)
                if pixel[3] == 0: # Skip fully transparent
                    continue
                rgb = pixel[:3]
                color_counts[rgb] += 1
        except Exception as e:
            print(f"  Error reading '{src_path.name}': {e}")

    if not color_counts:
        print("No opaque pixels found in the selected images.")
        return

    # Sort by count descending
    sorted_colors = color_counts.most_common()
    
    # Create diagnostic image
    swatch_size = 30
    padding = 10
    row_height = swatch_size + padding
    img_width = 400
    img_height = len(sorted_colors) * row_height + padding
    
    palette_img = Image.new("RGB", (img_width, img_height), (255, 255, 255))
    draw = ImageDraw.Draw(palette_img)
    
    try:
        # Try to load a nicer font, fallback to default
        font = ImageFont.truetype("Arial.ttf", 14)
    except IOError:
        font = ImageFont.load_default()

    y = padding
    for color, count in sorted_colors:
        # Draw swatch
        draw.rectangle([padding, y, padding + swatch_size, y + swatch_size], fill=color, outline="black")
        
        # Draw text
        hex_code = '#{:02x}{:02x}{:02x}'.format(*color).upper()
        text = f"{hex_code}  (Count: {count})"
        
        draw.text((padding + swatch_size + 15, y + (swatch_size//2) - 6), text, fill="black", font=font)
        
        y += row_height
        
    output_path = Path.cwd() / "palette_diagnostic.png"
    palette_img.save(output_path)
    print(f"Saved palette diagnostic to '{output_path}'")

def main():
    parser = argparse.ArgumentParser(description="Recolor character spritesheets by replacing specific palette colors.")
    
    parser.add_argument('--legs', metavar='SKIN_NAME', help="Name of the legs skin (e.g., 'marine').")
    parser.add_argument('--torso', metavar='SKIN_NAME', help="Name of the torso skin (e.g., 'marine').")
    parser.add_argument('--head', metavar='SKIN_NAME', help="Name of the head skin (e.g., 'marine').")
    
    parser.add_argument(
        '--replace', 
        action='append', 
        required=False,
        help="Color replacement in format OLD_HEX=NEW_HEX (e.g., FF0000=0000FF). Can be specified multiple times."
    )
    parser.add_argument(
        '--palette',
        action='store_true',
        help="Generate a diagnostic image showing the palette and pixel counts of the source images."
    )
    parser.add_argument(
        '--mass-recolor',
        action='store_true',
        help="Recolor all skins in the spritesheet directory from standard light to dark tones."
    )
    parser.add_argument(
        '--analyze-head',
        metavar='SKIN_ID',
        help="Run palette diagnostic on a specific head skin."
    )

    args = parser.parse_args()

    if not args.replace and not args.palette and not args.mass_recolor and not args.analyze_head:
        parser.error("You must specify --replace, --analyze-palette, --mass-recolor, or --analyze-head.")

    # Parse color replacements
    color_map = {}
    if args.replace:
        print("Color replacements:")
        for replacement in args.replace:
            try:
                if '=' not in replacement:
                    raise ValueError("Format must be OLD=NEW")
                old_hex, new_hex = replacement.split('=')
                old_rgb = parse_hex_color(old_hex)
                new_rgb = parse_hex_color(new_hex)
                color_map[old_rgb] = new_rgb
                print(f"  #{old_hex.lstrip('#')} -> #{new_hex.lstrip('#')}")
            except ValueError as e:
                print(f"Error parsing color replacement '{replacement}': {e}")
                sys.exit(1)

    base_dir = Path(SPRITESHEET_DIRECTORY)

    if args.mass_recolor:
        print("Starting mass recolor (Light -> Dark)...")
        try:
            # l1 = parse_hex_color(SKINTONE_LIGHT_1)
            # l2 = parse_hex_color(SKINTONE_LIGHT_2)
            # d1 = parse_hex_color(SKINTONE_DARK_1)
            # d2 = parse_hex_color(SKINTONE_DARK_2)
            # color_map = {l1: d1, l2: d2}
            # print(f"  Map: {SKINTONE_LIGHT_1} -> {SKINTONE_DARK_1}")
            # print(f"  Map: {SKINTONE_LIGHT_2} -> {SKINTONE_DARK_2}")
            color_map = { parse_hex_color(key): parse_hex_color(value) for key, value in RECOLOR_DARK.items()}
        except ValueError as e:
            print(f"Error parsing constants: {e}")
            sys.exit(1)

        output_base = Path.cwd() / "recolored_spritesheets"
        output_base.mkdir(exist_ok=True)

        for item in base_dir.iterdir():
            if item.is_dir():
                skin_name = item.name
                dest_dir_name = f"{skin_name}_skintone_2"
                dest_dir = output_base / dest_dir_name
                dest_dir.mkdir(exist_ok=True)

                png_files = list(item.glob("*.png"))
                if not png_files:
                    continue

                print(f"Processing '{skin_name}' -> '{dest_dir_name}' ({len(png_files)} files)")
                for src_path in png_files:
                    try:
                        img = Image.open(src_path)
                        new_img = replace_colors(img, color_map)
                        new_img.save(dest_dir / src_path.name)
                    except Exception as e:
                        print(f"  Error processing '{src_path.name}': {e}")
        
        print(f"\nMass recolor complete. Output saved to '{output_base}'.")
        sys.exit(0)
    
    head_dir = Path(HEAD_SPRITESHEET_DIRECTORY)
    
    if not base_dir.exists():
        print(f"Error: Spritesheet directory not found at '{SPRITESHEET_DIRECTORY}'")
        sys.exit(1)

    files_to_process = []

    # Gather files
    if args.legs:
        leg_path = base_dir / args.legs / 'Legs.png'
        if leg_path.exists():
            files_to_process.append(leg_path)
        else:
            print(f"Warning: Legs spritesheet not found at '{leg_path}'")

    if args.torso:
        torso_dir = base_dir / args.torso
        if torso_dir.exists():
            # Standard torso files based on Spritesheet.py
            torso_files = [
                'Torso.png', 'pistol.png', 'smg.png', 'rifle.png', 'shotgun.png',
                'Sword.png', 'Fence-cutter.png'
            ]
            found_any = False
            for fname in torso_files:
                fpath = torso_dir / fname
                if fpath.exists():
                    files_to_process.append(fpath)
                    found_any = True
            if not found_any:
                print(f"Warning: No standard torso spritesheets found in '{torso_dir}'")
        else:
            print(f"Warning: Torso skin directory not found at '{torso_dir}'")

    if args.head:
        head_path = head_dir / f"{args.head}.png"
        if head_path.exists():
            files_to_process.append(head_path)
        else:
            print(f"Warning: Head spritesheet not found at '{head_path}'")

    if args.analyze_head:
        head_path = head_dir / f"{args.analyze_head}.png"
        if head_path.exists():
            files_to_process.append(head_path)
            args.palette = True
        else:
            print(f"Warning: Head spritesheet not found at '{head_path}'")

    if not files_to_process:
        print("No files found to process.")
        sys.exit(0)

    if args.palette:
        analyze_palette(files_to_process)

    if args.replace:
        print(f"\nProcessing {len(files_to_process)} files for replacement...")

        # Process and save
        for src_path in files_to_process:
            try:
                img = Image.open(src_path)
                
                new_img = replace_colors(img, color_map)
                
                # Save to current working directory with prefix
                output_name = f"recolored_{src_path.name}"
                output_path = Path.cwd() / output_name
                
                new_img.save(output_path)
                print(f"  Saved '{output_name}'")
                
            except Exception as e:
                print(f"  Error processing '{src_path.name}': {e}")

if __name__ == '__main__':
    main()