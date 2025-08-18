from pathlib import Path
import argparse
import sys
from dataclasses import dataclass, field
from PIL import Image
import xml.etree.ElementTree as ET

from spritesheet import Spritesheet

# --- Configuration ---
SPRITESHEET_DIRECTORY = '/Users/rfoltz/dev/game-dev/wetworks/Assets/Resources/sprites/spritesheets'

HEAD_SPRITESHEET_DIRECTORY = '/Users/rfoltz/dev/game-dev/wetworks/Assets/Resources/sprites/spritesheets/head'

EXCLUDE_SKINS = ['cyber', 'generic64', 'gibs', 'head']

MAX_SPRITE_COLUMNS = 10


def main():
    spritesheet_path = Path(SPRITESHEET_DIRECTORY)

    if not spritesheet_path.is_dir():
        print(f"Error: The base spritesheet directory was not found at '{SPRITESHEET_DIRECTORY}'")
        sys.exit(1)

    # Get available directory names to use for validation and listing
    available_dirs = {d.name: d for d in spritesheet_path.iterdir() if d.is_dir() and d.name not in EXCLUDE_SKINS}
    available_dir_names = sorted(available_dirs.keys())

    parser = argparse.ArgumentParser(
        description="Diagnose and combine character sprites from legs, torso, and head parts."
    )
    parser.add_argument(
        '--legs',
        choices=available_dir_names,
        metavar='DIR_NAME',
        help="Directory for leg sprites."
    )
    parser.add_argument(
        '--torso',
        choices=available_dir_names,
        metavar='DIR_NAME',
        help="Directory for torso sprites."
    )
    parser.add_argument(
        '--head',
        choices=available_dir_names,
        metavar='DIR_NAME',
        help="Directory for head sprites."
    )
    args = parser.parse_args()

    # If any part is specified, all parts must be specified.
    if any([args.legs, args.torso, args.head]):
        if not all([args.legs, args.torso, args.head]):
            print("Error: To generate a character, you must specify all three parts: --legs, --torso, and --head.")
            print("Please provide values for the missing arguments.")
            sys.exit(1)
        generate_diagnostic(available_dirs, args.legs, args.torso, args.head)
    else:
        # Default behavior: list all available directories and exit.
        print("No body parts specified. Run with -h for options or provide parts to combine (e.g., --legs marine --torso marine --head marine).")
        print(f"Available spritesheet directories in '{SPRITESHEET_DIRECTORY}':")
        for dir_name in available_dir_names:
            print(f"  - {dir_name}")

def generate_diagnostic(available_dirs, leg_skin_name, torso_skin_name, head_skin_name):
    # At this point, we know all skin names are valid and have been provided.
    print("Processing selected parts:")
    print(f"  - Legs:  '{available_dirs[leg_skin_name]}'")
    print(f"  - Torso: '{available_dirs[torso_skin_name]}'")
    print(f"  - Head:  '{available_dirs[head_skin_name]}'")
    
    sheet = Spritesheet(available_dirs[leg_skin_name], available_dirs[torso_skin_name],head_skin_name)
    stacked_sprites = [
        sheet.create_stacked_sprite(0, 0, 0),
        sheet.create_stacked_sprite(1, 1, 1)
    ]
    
    # 5. Write the stacked sprite to a PNG file.
    output_filename = f"{leg_skin_name}_{torso_skin_name}_{head_skin_name}.png"
    # stacked_sprite.save(output_filename)
    write_stacked_sprites(stacked_sprites, output_filename, max_cols=MAX_SPRITE_COLUMNS)
    print(f"\nSuccessfully created composite sprite: '{output_filename}'")

def write_stacked_sprites(stacked_sprites, output_filename, max_cols=10):
    """
    Arranges a list of sprites into a grid and saves it as a single image.

    The grid will have a maximum number of columns, and sprites will wrap
    onto new rows as needed.

    Args:
        stacked_sprites (list[Image.Image]): A list of PIL Image objects to combine.
        output_filename (str): The path to save the final image to.
        max_cols (int): The maximum number of sprites per row.
    """
    if not stacked_sprites:
        print("Warning: No sprites to write.")
        return

    num_sprites = len(stacked_sprites)

    # Determine the cell size for the grid. Each cell will be large enough
    # to accommodate the largest sprite.
    cell_width = max(sprite.width for sprite in stacked_sprites)
    cell_height = max(sprite.height for sprite in stacked_sprites)

    # Calculate the grid dimensions.
    cols = min(num_sprites, max_cols)
    rows = math.ceil(num_sprites / cols) if cols > 0 else 0

    # Calculate the dimensions of the final spritesheet.
    total_width = cols * cell_width
    total_height = int(rows * cell_height)

    # Create a new transparent image to hold all the stacked sprites.
    final_spritesheet = Image.new("RGBA", (total_width, total_height), (0, 0, 0, 0))

    # Paste each sprite into its calculated position in the grid.
    for i, sprite in enumerate(stacked_sprites):
        col = i % cols
        row = i // cols
        final_spritesheet.paste(sprite, (col * cell_width, row * cell_height), sprite)

    final_spritesheet.save(output_filename)

if __name__ == '__main__':
    main()
