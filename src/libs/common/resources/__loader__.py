import os
import pygame

def loads(themes):
    """
    Loads the correct background image based on themes setting.
    """
    image_path = os.path.abspath(f'src/assets/textures/environments/.{themes}/Surfaces/home.jpg')
    fallback_path = os.path.abspath('src/assets/textures/common/static/missing.png')
    try:
        print(f"Loading background: {image_path}")
        # .convert() optimizes the image format for faster blitting
        return pygame.image.load(image_path).convert()
    except pygame.error as e:
        print(f"Warning: Could not load {image_path}. Error: {e}")
        print(f"Loading fallback: {fallback_path}")
        return pygame.image.load(fallback_path).convert()
