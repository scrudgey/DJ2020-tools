# Animation and direction indexing info (example)
ANIMATION_INDEXES = {
    "idle": {
        "down":   [0],
        "right":  [4],
        "up":     [8],
        "left":   [12]
    },
    "walk": {
        "down":   [1, 2, 3],
        "right":  [5, 6, 7],
        "up":     [9, 10, 11],
        "left":   [13, 14, 15]
    },
    # Add more animations/directions as needed
}

def get_sprite_indexes(animation, direction):
    """Return the list of sprite indexes for a given animation and direction."""
    return ANIMATION_INDEXES.get(animation, {}).get(direction, [])

# Example usage:
animation = "walk"
direction = "right"
indexes = get_sprite_indexes(animation, direction)
print(f"Indexes for {animation} {direction}: {indexes}")