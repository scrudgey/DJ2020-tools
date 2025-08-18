from pathlib import Path
import argparse
import sys
from dataclasses import dataclass, field
from PIL import Image
import xml.etree.ElementTree as ET


@dataclass
class Point:
    x: int = 0
    y: int = 0

@dataclass
class SpriteMetadata:
    """Holds metadata for a single sprite, like attachment points."""
    # Default to a common offset if not specified in the XML.
    head_offset: Point = field(default_factory=lambda: Point(0, 18))


class Spritesheet:
    def __init__(self, leg_skin_path, torso_skin_path, head_skin_name):
        
        HEAD_SPRITESHEET_DIRECTORY = '/Users/rfoltz/dev/game-dev/wetworks/Assets/Resources/sprites/spritesheets/head'
        
        # 1. Construct the full paths to the required spritesheet files.
        leg_sheet_path = leg_skin_path / 'Legs.png'
        torso_sheet_path = torso_skin_path / 'Torso.png'
        # head_sheet_path = head_skin_path / f'{head_skin_name}.png'
        head_sheet_path = Path(HEAD_SPRITESHEET_DIRECTORY) / f'{head_skin_name}.png'
        torso_sprite_data_path = torso_skin_path / 'TorsoSpriteData.xml'
        
        print("Processing selected parts:")
        print(f"  - Legs:  '{leg_sheet_path}'")
        print(f"  - Torso: '{torso_sheet_path}'")
        print(f"  - Head:  '{head_sheet_path}'")

        try:
            # 2. Load the spritesheets and slice them into sprites.
            self.leg_sprites = self.load_spritesheet_at_path(leg_sheet_path)
            self.torso_sprites = self.load_spritesheet_at_path(torso_sheet_path)
            self.head_sprites = self.load_spritesheet_at_path(head_sheet_path, sprite_size=(32, 32))

            # 2.5 load the torso sprite metadata
            self.torso_metadata_list = self.load_metadata_at_path(torso_sprite_data_path)
        except FileNotFoundError as e:
            print(f"Error: A required file was not found.\n{e}")
            # sys.exit(1)
        except (IOError, ET.ParseError) as e:
            print(f"Error processing file: {e}")
            # sys.exit(1)

    def load_spritesheet_at_path(self, path, sprite_size=(64, 64)):
        """Loads a spritesheet from a path and slices it into sprites of a given size."""
        if not path.is_file():
            raise FileNotFoundError(f"Spritesheet not found at '{path}'")

        try:
            img = Image.open(path).convert("RGBA")
        except Exception as e:
            raise IOError(f"Failed to load or process image at '{path}': {e}")

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


    def load_metadata_at_path(self, path):
        """Loads sprite metadata from an XML file and returns a list of SpriteMetadata objects."""
        if not path.is_file():
            raise FileNotFoundError(f"Metadata file not found at '{path}'")

        tree = ET.parse(path)
        root = tree.getroot()

        metadata_list = []
        for sprite_data_elem in root.findall('SpriteData'):
            metadata = SpriteMetadata()
            head_offset_elem = sprite_data_elem.find('headOffset')
            if head_offset_elem is not None:
                x_elem = head_offset_elem.find('x')
                y_elem = head_offset_elem.find('y')
                if x_elem is not None and y_elem is not None and x_elem.text is not None and y_elem.text is not None:
                    metadata.head_offset = Point(x=int(x_elem.text), y=int(y_elem.text))
            metadata_list.append(metadata)
        
        return metadata_list
    
    def create_stacked_sprite(self, leg_index, torso_index, head_index):
            
        # 3. Select the first sprite from each sheet for our composite.
        leg_sprite = self.leg_sprites[leg_index]
        torso_sprite = self.torso_sprites[torso_index]
        torso_data = self.torso_metadata_list[torso_index]
        head_sprite = self.head_sprites[head_index]
        
        # 4. Stack the sprites to create a single 64x64 sprite.
        stacked_sprite = self.add_sprites(leg_sprite, torso_sprite, head_sprite, torso_data)
        
        return stacked_sprite
    
    def add_sprites(self, leg_sprite, torso_sprite, head_sprite, torso_metadata):
        """Overlays three sprites, respecting transparency, to create a single composite sprite with dynamic dimensions."""
        # The head sprite is 32x32 and needs to be centered on a 64x64 grid.
        # The offset from the XML is relative to the top-left of the torso sprite.
        # A (0,0) offset in the XML should place the head's center on the torso's center.
        HEAD_CENTER_OFFSET = 16 # (64/2) - (32/2) = 16

        # Calculate the head offset based on the torso's metadata.
        # The XML's (0, 18) corresponds to a code offset of (16, -2).
        # Transformation: code_x = 16 + xml_x; code_y = 16 - xml_y
        xml_offset = torso_metadata.head_offset
        print(f"XML Offset: {xml_offset}")
        # The y-coordinate is inverted because image coordinates (PIL) start from the top-left,
        # while the game engine's coordinates might start from the bottom-left.
        head_offset = (HEAD_CENTER_OFFSET + xml_offset.x, HEAD_CENTER_OFFSET - xml_offset.y)

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
    

# now we need to understand a mapping: 
# animation + direction + frame -> index