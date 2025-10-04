import argparse
from pathlib import Path
import sys

from spritesheet import Spritesheet
from spritesheet import Spritesheet, save_metadata_at_path, SpriteMetadata

# --- Configuration ---
SPRITESHEET_DIRECTORY = '/Users/rfoltz/dev/game-dev/wetworks/Assets/Resources/sprites/spritesheets'
EXCLUDE_SKINS = ['cyber', 'generic64', 'gibs', 'head']

def main():
    """Main function to run the metadata tool."""
    spritesheet_path = Path(SPRITESHEET_DIRECTORY)

    if not spritesheet_path.is_dir():
        print(f"Error: The base spritesheet directory was not found at '{SPRITESHEET_DIRECTORY}'")
        sys.exit(1)

    available_dirs = {d.name: d for d in spritesheet_path.iterdir() if d.is_dir() and d.name not in EXCLUDE_SKINS}
    available_dir_names = sorted(available_dirs.keys())

    parser = argparse.ArgumentParser(description="A tool for managing sprite metadata.")
    parser.add_argument(
        '--from-sheet',
        required=True,
        choices=available_dir_names,
        metavar='DIR_NAME',
        help="The source spritesheet directory to load metadata from."
    )
    parser.add_argument(
        '--to-sheet',
        required=True,
        choices=available_dir_names,
        metavar='DIR_NAME',
        help="The destination spritesheet directory to load metadata for."
    )
    args = parser.parse_args()

    from_sheet_dir = available_dirs[args.from_sheet]
    to_sheet_dir = available_dirs[args.to_sheet]

    print(f"Loading 'from' metadata from: {args.from_sheet}")
    from_sheet = Spritesheet(from_sheet_dir, from_sheet_dir, args.from_sheet)
    
    print(f"Loading 'to' metadata from: {args.to_sheet}")
    to_sheet = Spritesheet(to_sheet_dir, to_sheet_dir, args.to_sheet)

    print("\nMetadata loaded successfully.")

    metadata_map = {
        'unarmed': ('TorsoSpriteData.xml', from_sheet.unarmed_metadata_list, to_sheet.unarmed_metadata_list),
        'pistol': ('pistolSpriteData.xml', from_sheet.pistol_metadata_list, to_sheet.pistol_metadata_list),
        'smg': ('smgSpriteData.xml', from_sheet.smg_metadata_list, to_sheet.smg_metadata_list),
        'rifle': ('rifleSpriteData.xml', from_sheet.rifle_metadata_list, to_sheet.rifle_metadata_list),
        'shotgun': ('shotgunSpriteData.xml', from_sheet.shotgun_metadata_list, to_sheet.shotgun_metadata_list),
    }

    fields_to_copy = [
        'weapon_back_position',
        'weapon_back_rotation',
        'weapon_back_in_front_of_torso',
        'weapon_visible'
    ]

    meta_type = 'unarmed'
    filename, from_list, to_list = metadata_map['unarmed']

    # for meta_type, (filename, from_list, to_list) in metadata_map.items():
    print(f"\nProcessing {meta_type} metadata...")

    if not from_list or not to_list:
        print(f"  Skipping {meta_type}: one or both metadata lists are missing/empty.")
        return

    if len(from_list) != len(to_list):
        print(f"  Warning: Mismatched metadata counts for {meta_type}. 'from' has {len(from_list)}, 'to' has {len(to_list)}. Copying up to the shorter list.")

    for i, from_meta in enumerate(from_list):
        if i >= len(to_list):
            break
        for field_name in fields_to_copy:
            setattr(to_list[i], field_name, getattr(from_meta, field_name))
    
    save_metadata_at_path(to_sheet_dir / filename, to_list)
    print(f"  Successfully copied fields and saved '{filename}' for '{args.to_sheet}'.")

if __name__ == '__main__':
    main()