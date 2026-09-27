#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
from collections import Counter
from PIL import Image, ImageDraw, ImageFont
import math

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
    sorted_colors = color_counts.most_common()[:50]
    
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

def color_distance(c1, c2):
    """Calculates a perceptual distance approximation between two RGB colors."""
    rmean = (c1[0] + c2[0]) // 2
    r = c1[0] - c2[0]
    g = c1[1] - c2[1]
    b = c1[2] - c2[2]
    return math.sqrt((((512+rmean)*r*r)>>8) + 4*g*g + (((767-rmean)*b*b)>>8))

def parse_pal_file(pal_path):
    """Parses a JASC-PAL file and returns a list of RGB tuples."""
    colors = []
    with open(pal_path, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    if not lines or lines[0] != 'JASC-PAL':
        raise ValueError(f"Not a valid JASC-PAL file: {pal_path}")
    
    # line 1 is 'JASC-PAL', line 2 is '0100', line 3 is count
    for line in lines[3:]:
        parts = line.split()
        if len(parts) == 3:
            colors.append(tuple(int(p) for p in parts))
    return colors

def apply_palette_to_image(img, palette_colors):
    """
    Replaces each pixel in the image with the nearest color from palette_colors.
    Uses a cache for performance.
    """
    cache = {}
    
    # Ensure image is RGBA
    img = img.convert("RGBA")
    data = img.getdata()
    
    new_data = []
    for pixel in data:
        if pixel[3] == 0:  # Preserve transparency
            new_data.append(pixel)
            continue
            
        rgb = pixel[:3]
        if rgb in cache:
            closest = cache[rgb]
        else:
            closest = min(palette_colors, key=lambda c: color_distance(rgb, c))
            cache[rgb] = closest
            
        new_data.append(closest + (pixel[3],))
        
    new_img = Image.new("RGBA", img.size)
    new_img.putdata(new_data)
    return new_img

def generate_pixel_art_palette(files_to_process, limit=256, distance_threshold=20):
    """
    Generates a pixel art palette from input images by bucketizing perceptually similar colors.
    """
    color_counts = Counter()
    print("Generating bucketized palette...")

    for src_path in files_to_process:
        try:
            img = Image.open(src_path).convert("RGBA")
            data = img.getdata()
            for pixel in data:
                if pixel[3] == 0: # Skip fully transparent
                    continue
                rgb = pixel[:3]
                color_counts[rgb] += 1
        except Exception as e:
            print(f"  Error reading '{src_path.name}': {e}")

    if not color_counts:
        print("No opaque pixels found in the selected images.")
        return

    # Sort colors by frequency descending
    sorted_unique_colors = [item[0] for item in color_counts.most_common()]
    
    buckets = []
    bucket_counts = []
    
    print(f"Found {len(sorted_unique_colors)} unique colors, reducing to max {limit} buckets...")
    
    for color in sorted_unique_colors:
        count = color_counts[color]
        
        # Find if it belongs to an existing bucket
        found_bucket = False
        for i, bucket_color in enumerate(buckets):
            dist = color_distance(color, bucket_color)
            if dist < distance_threshold:
                bucket_counts[i] += count
                found_bucket = True
                break
                
        if not found_bucket:
            if len(buckets) < limit:
                buckets.append(color)
                bucket_counts.append(count)
            else:
                # Limit reached, force into the closest bucket
                closest_i = min(range(len(buckets)), key=lambda i: color_distance(color, buckets[i]))
                bucket_counts[closest_i] += count

    # Combine buckets and counts, then sort by count descending
    bucket_data = list(zip(buckets, bucket_counts))
    bucket_data.sort(key=lambda x: x[1], reverse=True)
    
    # Create diagnostic image
    swatch_size = 30
    padding = 10
    row_height = swatch_size + padding
    img_width = 400
    img_height = len(bucket_data) * row_height + padding
    
    palette_img = Image.new("RGB", (img_width, img_height), (255, 255, 255))
    draw = ImageDraw.Draw(palette_img)
    
    try:
        font = ImageFont.truetype("Arial.ttf", 14)
    except IOError:
        font = ImageFont.load_default()

    y = padding
    for color, count in bucket_data:
        draw.rectangle([padding, y, padding + swatch_size, y + swatch_size], fill=color, outline="black")
        hex_code = '#{:02x}{:02x}{:02x}'.format(*color).upper()
        text = f"{hex_code}  (Count: {count})"
        draw.text((padding + swatch_size + 15, y + (swatch_size//2) - 6), text, fill="black", font=font)
        y += row_height
        
    output_path = Path.cwd() / "bucketized_palette_diagnostic.png"
    palette_img.save(output_path)
    print(f"Saved bucketized palette diagnostic to '{output_path}'")

    # Perceptually sort the colors for the .pal file
    unsorted_colors = [item[0] for item in bucket_data]
    sorted_pal_colors = []
    
    if unsorted_colors:
        # Start with the darkest color based on luma
        current_color = min(unsorted_colors, key=lambda c: c[0]*0.299 + c[1]*0.587 + c[2]*0.114)
        unsorted_colors.remove(current_color)
        sorted_pal_colors.append(current_color)
        
        while unsorted_colors:
            # Find the closest remaining color to the current color
            closest_color = min(unsorted_colors, key=lambda c: color_distance(current_color, c))
            unsorted_colors.remove(closest_color)
            sorted_pal_colors.append(closest_color)
            current_color = closest_color

    pal_path = Path.cwd() / "bucketized_palette.pal"
    with open(pal_path, "w") as f:
        f.write("JASC-PAL\n")
        f.write("0100\n")
        f.write(f"{len(sorted_pal_colors)}\n")
        for color in sorted_pal_colors:
            f.write(f"{color[0]} {color[1]} {color[2]}\n")
            
    print(f"Saved JASC-PAL palette to '{pal_path}'")

def mass_recolor():
    print("Starting mass recolor (Light -> Dark)...")
    try:
        color_map = { parse_hex_color(key): parse_hex_color(value) for key, value in RECOLOR_DARK.items()}
    except ValueError as e:
        print(f"Error parsing constants: {e}")
        sys.exit(1)


    base_dir = Path(SPRITESHEET_DIRECTORY)

    output_base = Path.cwd() / "recolored_spritesheets"
    output_head_dir = Path.cwd() / "recolored_head_spritesheets"
    output_base.mkdir(exist_ok=True)
    output_head_dir.mkdir(exist_ok=True)

    for item in base_dir.iterdir():
        if item.is_dir():
            if 'head' in item.name:
                print(f'skipping head directory {item}...')
                continue
            skin_name = item.name
            dest_dir_name = f"{skin_name}_skintone_1"
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
    

    head_dir = Path(HEAD_SPRITESHEET_DIRECTORY)
    head_png_files = list(head_dir.glob("*.png"))
    for head_png in head_png_files:
        print(f"Processing head '{head_png.name}'")
        try:
            img = Image.open(head_png)
            new_img = replace_colors(img, color_map)
            dest_filename = f"{head_png.stem}_skintone_1.png"
            new_img.save(output_head_dir / dest_filename)
        except Exception as e:
            print(f"  Error processing '{src_path.name}': {e}")
    
    print(f"\nMass recolor complete. Output saved to '{output_base}'.")

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
        '--pixel-palette',
        action='store_true',
        help="Generate a pixel art palette from the image by bucketizing similar colors."
    )
    parser.add_argument(
        '--apply-palette',
        metavar='PALETTE_FILE',
        help="Path to a JASC-PAL file to apply to the source images."
    )
    parser.add_argument(
        '--input',
        metavar='FILE_PATH',
        help="Force the tool to use a specific input image file, ignoring the standard spritesheet directories."
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

    if not any([args.replace, args.palette, args.pixel_palette, args.mass_recolor, args.analyze_head, args.apply_palette]):
        parser.error("You must specify --replace, --analyze-palette, --pixel-palette, --apply-palette, --mass-recolor, or --analyze-head.")

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


    if args.mass_recolor:
        mass_recolor()
        sys.exit(0)
    
    base_dir = Path(SPRITESHEET_DIRECTORY)
    head_dir = Path(HEAD_SPRITESHEET_DIRECTORY)
    
    files_to_process = []

    # Gather files
    if args.input:
        input_path = Path(args.input)
        if input_path.exists() and input_path.is_file():
            files_to_process.append(input_path)
        else:
            print(f"Error: Input file not found at '{args.input}'")
            sys.exit(1)
    else:
        if not base_dir.exists():
            print(f"Error: Spritesheet directory not found at '{SPRITESHEET_DIRECTORY}'")
            sys.exit(1)

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

    if args.pixel_palette:
        generate_pixel_art_palette(files_to_process)

    if args.apply_palette:
        print(f"\nApplying palette from '{args.apply_palette}' to {len(files_to_process)} files...")
        try:
            palette_colors = parse_pal_file(args.apply_palette)
        except Exception as e:
            print(f"Error reading palette file: {e}")
            sys.exit(1)
            
        for src_path in files_to_process:
            try:
                img = Image.open(src_path)
                new_img = apply_palette_to_image(img, palette_colors)
                
                output_name = f"palettized_{src_path.name}"
                output_path = Path.cwd() / output_name
                new_img.save(output_path)
                print(f"  Saved '{output_name}'")
            except Exception as e:
                print(f"  Error processing '{src_path.name}': {e}")

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