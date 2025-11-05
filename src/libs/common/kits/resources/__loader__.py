import os
import pygame
from libs.utils.pylog import Logger

logger = Logger(__name__)

# Loads the main background image for a given theme.
def loads(themes: str) -> pygame.Surface:
    """
    Loads the 'home.jpg' background image for the specified theme.
    If the theme's image is not found, it loads a fallback 'missing.png'.

    Args:
        themes: The name of the theme (e.g., 'CuteChaos').

    Returns:
        A pygame.Surface containing the loaded image.
    """
    # Path to the theme-specific background
    image_path: str = os.path.abspath(f'src/assets/textures/environments/.{themes}/Surfaces/home.jpg')
    # Path to the fallback 'missing' texture
    fallback_path: str = os.path.abspath('src/assets/textures/common/static/missing.png')
    
    try:
        logger.info(f"Loading background: {image_path}")
        return pygame.image.load(image_path).convert()
    except pygame.error as e:
        logger.warning(f"Warning: Could not load {image_path}. Error: {e}")
        logger.info(f"Loading fallback: {fallback_path}")
        # Load the fallback image if the theme image fails
        return pygame.image.load(fallback_path).convert()