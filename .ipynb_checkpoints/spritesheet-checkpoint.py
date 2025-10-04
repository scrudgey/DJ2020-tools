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
    head_in_front_of_torso: bool = True

@dataclass
class LegSpriteMetadata:
    """Holds metadata for a single leg sprite."""
    torso_offset: Point = field(default_factory=Point)


class Spritesheet:
    def __init__(self, leg_skin_path, torso_skin_path, head_skin_name):
        
        HEAD_SPRITESHEET_DIRECTORY = '/Users/rfoltz/dev/game-dev/wetworks/Assets/Resources/sprites/spritesheets/head'
        
        # 1. Construct the full paths to the required spritesheet files.
        leg_sheet_path = leg_skin_path / 'Legs.png'
        torso_sheet_path = torso_skin_path / 'Torso.png'
        pistol_sheet_path = torso_skin_path / 'pistol.png'
        smg_sheet_path = torso_skin_path / 'smg.png'
        rifle_sheet_path = torso_skin_path / 'rifle.png'
        shotgun_sheet_path = torso_skin_path / 'shotgun.png'
        head_sheet_path = Path(HEAD_SPRITESHEET_DIRECTORY) / f'{head_skin_name}.png'

        leg_metadata_path = leg_skin_path / 'LegSpriteData.xml'
        unarmed_metadata_path = torso_skin_path / 'TorsoSpriteData.xml'
        pistol_metadata_path = torso_skin_path / 'pistolSpriteData.xml'
        smg_metadata_path = torso_skin_path / 'smgSpriteData.xml'
        rifle_metadata_path = torso_skin_path / 'rifleSpriteData.xml'
        shotgun_metadata_path = torso_skin_path / 'shotgunSpriteData.xml'
        
        print("Processing selected parts:")
        print(f"  - Legs:  '{leg_sheet_path}'")
        print(f"  - Torso: '{torso_sheet_path}'")
        print(f"  - Head:  '{head_sheet_path}'")

        try:
            # 2. Load the spritesheets and slice them into sprites.
            self.leg_sprites = self.load_spritesheet_at_path(leg_sheet_path)
            self.torso_sprites = self.load_spritesheet_at_path(torso_sheet_path)
            self.head_sprites = self.load_spritesheet_at_path(head_sheet_path, sprite_size=(32, 32))
            self.pistol_sprites = self.load_spritesheet_at_path(pistol_sheet_path)
            self.smg_sprites = self.load_spritesheet_at_path(smg_sheet_path)
            self.rifle_sprites = self.load_spritesheet_at_path(rifle_sheet_path)
            self.shotgun_sprites = self.load_spritesheet_at_path(shotgun_sheet_path)

            # 2.5 load the torso sprite metadata
            self.leg_metadata_list = self.load_leg_metadata_at_path(leg_metadata_path)
            self.unarmed_metadata_list = self.load_metadata_at_path(unarmed_metadata_path)
            self.pistol_metadata_list = self.load_metadata_at_path(pistol_metadata_path)
            self.smg_metadata_list = self.load_metadata_at_path(smg_metadata_path)
            self.rifle_metadata_list = self.load_metadata_at_path(rifle_metadata_path)
            self.shotgun_metadata_list = self.load_metadata_at_path(shotgun_metadata_path)

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

    def load_leg_metadata_at_path(self, path):
        """Loads sprite metadata from an XML file and returns a list of SpriteMetadata objects."""
        if not path.is_file():
            raise FileNotFoundError(f"Metadata file not found at '{path}'")

        tree = ET.parse(path)
        root = tree.getroot()

        metadata_list = []
        for sprite_data_elem in root.findall('SpriteDataLegs'):
            metadata = LegSpriteMetadata()
            torsoOffset_elem = sprite_data_elem.find('torsoOffset')
            if torsoOffset_elem is not None:
                x_elem = torsoOffset_elem.find('x')
                y_elem = torsoOffset_elem.find('y')
                if x_elem is not None and y_elem is not None and x_elem.text is not None and y_elem.text is not None:
                    metadata.torso_offset = Point(x=int(x_elem.text), y=int(y_elem.text))

            metadata_list.append(metadata)
        
        return metadata_list

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
            
            head_in_front_elem = sprite_data_elem.find('headInFrontOfTorso')
            if head_in_front_elem is not None and head_in_front_elem.text is not None:
                metadata.head_in_front_of_torso = head_in_front_elem.text.lower() == 'true'

            metadata_list.append(metadata)
        
        return metadata_list
    
    def create_stacked_sprite(self, leg_index, torso_index, head_index, torso_type='unarmed'):
        torso_sprites = self.torso_sprites
        torso_metadata = self.unarmed_metadata_list

        if torso_type == 'pistol':
            torso_sprites = self.pistol_sprites
            torso_metadata = self.pistol_metadata_list
        elif torso_type == 'smg':
            torso_sprites = self.smg_sprites
            torso_metadata = self.smg_metadata_list
        elif torso_type == 'rifle':
            torso_sprites = self.rifle_sprites
            torso_metadata = self.rifle_metadata_list
        elif torso_type == 'shotgun':
            torso_sprites = self.shotgun_sprites
            torso_metadata = self.shotgun_metadata_list

        # print (f'metadata: {torso_index}/{len(torso_metadata)}')

        # 3. Select the first sprite from each sheet for our composite.
        leg_sprite = self.leg_sprites[leg_index]
        torso_sprite = torso_sprites[torso_index]
        torso_data = torso_metadata[torso_index]
        head_sprite = self.head_sprites[head_index]
        leg_metadata = self.leg_metadata_list[leg_index]
        # 4. Stack the sprites to create a single 64x64 sprite.
        stacked_sprite = self.add_sprites(leg_sprite, torso_sprite, head_sprite, torso_data, leg_metadata)
        
        return stacked_sprite
    
    def add_sprites(self, leg_sprite, torso_sprite, head_sprite, torso_metadata: SpriteMetadata, leg_metadata: LegSpriteMetadata):
        """Overlays three sprites, respecting transparency, to create a single composite sprite with dynamic dimensions."""
        # The head sprite is 32x32 and needs to be centered on a 64x64 grid.
        # The offset from the XML is relative to the top-left of the torso sprite.
        # A (0,0) offset in the XML should place the head's center on the torso's center.
        HEAD_CENTER_OFFSET = 16 # (64/2) - (32/2) = 16

        # Calculate the head offset based on the torso's metadata.
        # The XML's (0, 18) corresponds to a code offset of (16, -2).
        # Transformation: code_x = 16 + xml_x; code_y = 16 - xml_y
        head_metadata_offset = torso_metadata.head_offset
        torso_metadata_offset = leg_metadata.torso_offset

        # The y-coordinate is inverted because image coordinates (PIL) start from the top-left,
        # while the game engine's coordinates might start from the bottom-left.
        torso_offset = (torso_metadata_offset.x, -torso_metadata_offset.y)
        head_offset = (HEAD_CENTER_OFFSET + head_metadata_offset.x + torso_offset[0], HEAD_CENTER_OFFSET - head_metadata_offset.y + torso_offset[1])

        # Calculate the required dimensions for the final composite image based on the
        # largest dimensions of the combined parts and their offsets.
        composite_width = max(leg_sprite.width, torso_sprite.width, head_sprite.width + head_offset[0])
        composite_height = max(leg_sprite.height, torso_sprite.height, head_sprite.height + head_offset[1])

        # Create a new transparent canvas of the calculated size.
        composite_image = Image.new("RGBA", (composite_width, composite_height), (0, 0, 0, 0))

        # Paste legs first, as they are always in the back.
        composite_image.paste(leg_sprite, (0, 0), leg_sprite)

        # Paste head and torso based on the metadata flag, using each layer's alpha channel as a mask.
        if torso_metadata.head_in_front_of_torso:
            composite_image.paste(torso_sprite, torso_offset, torso_sprite)
            composite_image.paste(head_sprite, head_offset, head_sprite)
        else:
            composite_image.paste(head_sprite, head_offset, head_sprite)
            composite_image.paste(torso_sprite, torso_offset, torso_sprite)
        
        return composite_image
    

# now we need to understand a mapping: 