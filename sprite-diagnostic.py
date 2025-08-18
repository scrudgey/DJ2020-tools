from pathlib import Path
import argparse
import sys
from PIL import Image
import xml.etree.ElementTree as ET

SPRITESHEET_DIRECTORY = '/Users/rfoltz/dev/game-dev/wetworks/Assets/Resources/sprites/spritesheets'
HEAD_SPRITESHEET_DIRECTORY = '/Users/rfoltz/dev/game-dev/wetworks/Assets/Resources/sprites/spritesheets/head'

EXCLUDE_SKINS = ['cyber', 'generic64', 'gibs', 'head']

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

    if not any([args.legs, args.torso, args.head]):
        # Default behavior: list all directories
        print("No body parts specified. Run with -h for options or provide a part (e.g., --legs).")
        print(f"Available spritesheet directories in '{SPRITESHEET_DIRECTORY}':")
        if not available_dir_names:
            print("No subdirectories found.")
        else:
            for dir_name in available_dir_names:
                print(f"  - {dir_name}")
    else:
        # At least one part was provided
        # We require all parts to proceed with generation.
        if not all([args.legs, args.torso, args.head]):
            print("Error: To generate a character, you must specify all three parts: --legs, --torso, and --head.")
            print("Please provide values for the missing arguments.")
            sys.exit(1)

        generate_diagnostic(available_dirs, args.legs, args.torso, args.head)
        

def generate_diagnostic(available_dirs, leg_skin_name, torso_skin_name, head_skin_name):
    # At this point, we know all skin names are valid and have been provided.
    print("Processing selected parts:")
    print(f"  - Legs:  '{available_dirs[leg_skin_name]}'")
    print(f"  - Torso: '{available_dirs[torso_skin_name]}'")
    print(f"  - Head:  '{available_dirs[head_skin_name]}'")
    
    # 1. Construct the full paths to the required spritesheet files.
    leg_sheet_path = available_dirs[leg_skin_name] / 'Legs.png'
    torso_sheet_path = available_dirs[torso_skin_name] / 'Torso.png'
    head_sheet_path = Path(HEAD_SPRITESHEET_DIRECTORY) / f'{head_skin_name}.png'
    torso_sprite_data_path = available_dirs[torso_skin_name] / 'TorsoSpriteData.xml'
    
    # 2. Load the spritesheets and slice them into 64x64 sprites.
    leg_sprites = load_spritesheet_at_path(leg_sheet_path)
    torso_sprites = load_spritesheet_at_path(torso_sheet_path)
    head_sprites = load_spritesheet_at_path(head_sheet_path, sprite_size=(32, 32))

    # 2.5 load the torso sprite metadata
    torso_datas = load_metadata_at_path(torso_sprite_data_path)

    # 3. Select the first sprite from each sheet for our composite.
    leg_sprite = leg_sprites[0]
    torso_sprite = torso_sprites[0]
    torso_data = torso_datas[0]
    head_sprite = head_sprites[0]
    
    # 4. Stack the sprites to create a single 64x64 sprite.
    stacked_sprite = add_sprites(leg_sprite, torso_sprite, head_sprite, torso_data)
    
    # 5. Write the stacked sprite to a PNG file.
    output_filename = f"{leg_skin_name}_{torso_skin_name}_{head_skin_name}.png"
    stacked_sprite.save(output_filename)
    print(f"\nSuccessfully created composite sprite: '{output_filename}'")


def load_spritesheet_at_path(path, sprite_size=(64, 64)):
    """Loads a spritesheet from a path and slices it into sprites of a given size."""
    if not path.is_file():
        print(f"Error: Spritesheet not found at '{path}'")
        sys.exit(1)

    try:
        img = Image.open(path).convert("RGBA")
    except Exception as e:
        print(f"Error: Failed to load or process image at '{path}': {e}")
        sys.exit(1)

    sprite_w, sprite_h = sprite_size
    width, height = img.size
    if width % sprite_w != 0 or height % sprite_h != 0:
        print(f"Warning: Image dimensions ({width}x{height}) at '{path}' are not a multiple of {sprite_w}x{sprite_h}.")

    sprites = []
    for y in range(0, height, sprite_h):
        for x in range(0, width, sprite_w):
            # Define the box for cropping: (left, upper, right, lower)
            box = (x, y, x + sprite_w, y + sprite_h)
            sprite = img.crop(box)
            sprites.append(sprite)
    
    return sprites


def load_metadata_at_path(path):
    """Loads sprite metadata from an XML file and returns a list of data objects."""
    if not path.is_file():
        print(f"Error: Metadata file not found at '{path}'")
        sys.exit(1)

    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error: Failed to parse XML file at '{path}': {e}")
        sys.exit(1)

    metadata_list = []
    for sprite_data_elem in root.findall('SpriteData'):
        data = {}
        head_offset_elem = sprite_data_elem.find('headOffset')
        if head_offset_elem is not None:
            x_elem = head_offset_elem.find('x')
            y_elem = head_offset_elem.find('y')
            if x_elem is not None and y_elem is not None and x_elem.text is not None and y_elem.text is not None:
                data['head_offset'] = {'x': int(x_elem.text), 'y': int(y_elem.text)}
        metadata_list.append(data)
    
    return metadata_list

def add_sprites(leg_sprite, torso_sprite, head_sprite, torso_data):
    """Overlays three sprites, respecting transparency, to create a single composite sprite with dynamic dimensions."""
    # Calculate the head offset based on the torso's metadata.
    # The XML's (0, 18) corresponds to a code offset of (16, -2).
    # Transformation: code_x = 16 + xml_x; code_y = 16 - xml_y
    xml_offset = torso_data.get('head_offset', {'x': 0, 'y': 18})  # Default to (0, 18) if not found
    print(f"XML Offset: {xml_offset}")
    head_offset = (16 + xml_offset['x'], 16 - xml_offset['y'])

    # Calculate the required dimensions for the final composite image based on the
    # largest dimensions of the combined parts and their offsets.
    composite_width = max(leg_sprite.width, torso_sprite.width, head_sprite.width + head_offset[0])
    composite_height = max(leg_sprite.height, torso_sprite.height, head_sprite.height + head_offset[1])

    # Create a new transparent canvas of the calculated size.
    composite_image = Image.new("RGBA", (composite_width, composite_height), (0, 0, 0, 0))
    
    # Paste each layer, using its own alpha channel as the mask to handle transparency.
    composite_image.paste(leg_sprite, (0, 0), leg_sprite)
    composite_image.paste(torso_sprite, (0, 0), torso_sprite)
    # Paste the head sprite at its specified offset.
    composite_image.paste(head_sprite, head_offset, head_sprite)
    
    return composite_image

if __name__ == '__main__':
    main()
