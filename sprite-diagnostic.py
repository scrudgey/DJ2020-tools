from pathlib import Path
import argparse
import math
import sys
from dataclasses import dataclass, field
from PIL import Image
import xml.etree.ElementTree as ET
from indexes import *

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
    parser.add_argument(
        '--color',
        choices=['white', 'black', 'transparent'],
        default='white',
        help="Set the background color of the output spritesheets. Default is white."
    )
    parser.add_argument(
        '--show-indices',
        action='store_true',
        help="If set, writes the leg, torso, and head index on each generated sprite."
    )
    args = parser.parse_args()

    # If any part is specified, all parts must be specified.
    if any([args.legs, args.torso, args.head]):
        if not all([args.legs, args.torso, args.head]):
            print("Error: To generate a character, you must specify all three parts: --legs, --torso, and --head.")
            print("Please provide values for the missing arguments.")
            sys.exit(1)
        generate_diagnostic(available_dirs, args.legs, args.torso, args.head, args.color, args.show_indices)
    else:
        # Default behavior: list all available directories and exit.
        print("No body parts specified. Run with -h for options or provide parts to combine (e.g., --legs marine --torso marine --head marine).")
        print(f"Available spritesheet directories in '{SPRITESHEET_DIRECTORY}':")
        for dir_name in available_dir_names:
            print(f"  - {dir_name}")

def generate_diagnostic(available_dirs, leg_skin_name, torso_skin_name, head_skin_name, bg_color, show_indices):
    # At this point, we know all skin names are valid and have been provided.
    print("Processing selected parts:")
    print(f"  - Legs:  '{available_dirs[leg_skin_name]}'")
    print(f"  - Torso: '{available_dirs[torso_skin_name]}'")
    print(f"  - Head:  '{available_dirs[head_skin_name]}'")
    
    sheet = Spritesheet(available_dirs[leg_skin_name], available_dirs[torso_skin_name],head_skin_name)

    # create unarmed walk and run animations for all directions
    stacked_sprites = []
    animations_to_generate = ['walk', 'run']
    for animation in animations_to_generate:
        for direction in Direction:
            leg_indexes = get_leg_indexes(direction, animation)
            torso_indexes = get_unarmed_indexes(direction, animation)
            if not leg_indexes or not torso_indexes:
                continue
            head_index = get_head_indexes(direction)[0]
            for leg_index, torso_index in zip(leg_indexes, torso_indexes):
                stacked_sprites.append(sheet.create_stacked_sprite(leg_index, torso_index, head_index, show_indices=show_indices))
    
    # 5. Write the stacked sprite to a PNG file.
    output_filename = f"{leg_skin_name}_{torso_skin_name}_{head_skin_name}_unarmed_walk_run.png"
    write_stacked_sprites(stacked_sprites, output_filename, max_cols=MAX_SPRITE_COLUMNS, bg_color=bg_color)
    print(f"\nSuccessfully created composite sprite: '{output_filename}'")

    # --- Generate weapon animations ---
    # For each leg stance (idle, crouch), generate shoot, rack, and reload animations.
    weapon_configs = {
        'pistol': {
            'animations': ['shoot', 'rack', 'reload'],
            'index_func': get_pistol_indexes,
        },
        'smg': {
            'animations': ['shoot', 'rack', 'reload'],
            'index_func': get_smg_indexes,
        },
        'shotgun': {
            'animations': ['shoot', 'rack', 'reload'],
            'index_func': get_shotgun_indexes,
        },
        'rifle': {
            'animations': ['shoot', 'rack', 'reload'],
            'index_func': get_rifle_indexes,
        },
    }
    leg_stances = ['idle', 'crouch']

    for weapon, config in weapon_configs.items():
        for leg_stance in leg_stances:
            all_weapon_sprites = []
            for animation in config['animations']:
                for direction in Direction:
                    leg_indexes = get_leg_indexes(direction, leg_stance)
                    torso_indexes = config['index_func'](direction, animation)

                    if not leg_indexes or not torso_indexes:
                        continue
                    
                    head_index = get_head_indexes(direction)[0]
                    leg_index = leg_indexes[0] # For static stances, use the single leg frame.
                    print(f"Generating {weapon} {animation} for {leg_stance} stance in direction {direction.name}\tindex: {leg_index}, torso: {torso_indexes[0]}, head: {head_index}")
                    for torso_index in torso_indexes:
                        all_weapon_sprites.append(sheet.create_stacked_sprite(leg_index, torso_index, head_index, torso_type=weapon, show_indices=show_indices))
            
            if all_weapon_sprites:
                output_filename = f"{leg_skin_name}_{torso_skin_name}_{head_skin_name}_{weapon}_{leg_stance}_legs.png"
                write_stacked_sprites(all_weapon_sprites, output_filename, max_cols=MAX_SPRITE_COLUMNS, bg_color=bg_color)
                print(f"\nSuccessfully created composite sprite: '{output_filename}'")

def write_stacked_sprites(stacked_sprites, output_filename, max_cols=10, bg_color='white'):
    """
    Arranges a list of sprites into a grid and saves it as a single image.

    The grid will have a maximum number of columns, and sprites will wrap
    onto new rows as needed.

    Args:
        stacked_sprites (list[Image.Image]): A list of PIL Image objects to
            combine.
        max_cols (int): The maximum number of sprites per row.
        bg_color (str): The background color ('white', 'black', or 'transparent').
    """
    if not stacked_sprites:
        print("Warning: No sprites to write.")
        return

    num_sprites = len(stacked_sprites)

    # Map color names to RGBA values
    color_map = {
        'white': (255, 255, 255, 255),
        'black': (0, 0, 0, 255),
        'transparent': (0, 0, 0, 0)
    }
    background_rgba = color_map.get(bg_color, (255, 255, 255, 255)) # Default to white

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

    # Create a new image with the specified background color.
    final_spritesheet = Image.new("RGBA", (total_width, total_height), background_rgba)

    # Paste each sprite into its calculated position in the grid.
    for i, sprite in enumerate(stacked_sprites):
        col = i % cols
        row = i // cols
        final_spritesheet.paste(sprite, (col * cell_width, row * cell_height), sprite)

    final_spritesheet.save(output_filename)

if __name__ == '__main__':
    main()
