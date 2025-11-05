import pygame
import os
from typing import Optional, Any
from libs.utils.pylog import Logger

logger = Logger(__name__)

# Defines an ImageButton UI component.
class Button:
    """
    A UI component for a button that uses an image for its appearance.
    Supports loading theme-specific or common images, with a fallback.
    """
    
    def __init__(self, x: int, y: int, image_name: str, theme: Optional[str] = None, 
                 default_width: int = 250, default_height: int = 80, 
                 missing_texture_path: str = 'src/assets/textures/common/static/missing.png'):
        """
        Initializes the ImageButton.

        Args:
            x: The x-coordinate of the top-left corner.
            y: The y-coordinate of the top-left corner.
            image_name: The name of the image file (e.g., "play").
            theme: The current theme name, used to find theme-specific images.
            default_width: The target width to scale the image to.
            default_height: The target height to scale the image to.
            missing_texture_path: Path to a fallback image if loading fails.
        """
        
        self.image_name: str = image_name
        self.current_theme: Optional[str] = theme
        
        self.target_width: int = default_width
        self.target_height: int = default_height
        
        self.missing_texture_path: str = os.path.abspath(missing_texture_path)
        
        self.image_surf: pygame.Surface = self.load_image()
        
        self.rect: pygame.Rect = self.image_surf.get_rect()
        self.rect.topleft = (x, y)

    # Loads and scales the button's image.
    def load_image(self) -> pygame.Surface:
        """
        Loads the button's image surface.
        It tries this order:
        1. Theme-specific path (e.g., .../.{theme}/Buttons/{image_name}.png)
        2. Common path (e.g., .../common/Buttons/{image_name}.png)
        3. Missing texture path (fallback)

        Returns:
            A pygame.Surface (scaled to target size) for the button.
        """
        loaded_surf: Optional[pygame.Surface] = None
        
        # 1. Try loading from the current theme's directory
        theme_path: str = os.path.abspath(f'src/assets/textures/environments/.{self.current_theme}/Buttons/{self.image_name}.png')
        
        if os.path.exists(theme_path):
            logger.info(f"Loading theme image: {theme_path}")
            try:
                loaded_surf = pygame.image.load(theme_path).convert_alpha()
            except Exception as e:
                logger.warning(f"Warning: Could not load theme image {theme_path}. Error: {e}")

        # 2. If theme load failed, try loading from the common directory
        if not loaded_surf:
            common_path: str = os.path.abspath(f'src/assets/textures/common/Buttons/{self.image_name}.png')
            
            if os.path.exists(common_path):
                logger.info(f"Loading common image: {common_path}")
                try:
                    loaded_surf = pygame.image.load(common_path).convert_alpha()
                except Exception as e:
                    logger.warning(f"Warning: Could not load common image {common_path}. Error: {e}")

        # If an image was loaded, scale it
        if loaded_surf:
            try:
                return pygame.transform.smoothscale(loaded_surf, (self.target_width, self.target_height))
            except Exception as e:
                logger.warning(f"Warning: Could not scale {self.image_name} to {self.target_width}x{self.target_height}. Error: {e}")
                return loaded_surf # Return unscaled if scaling fails

        # 3. If all loads failed, load the missing texture fallback
        logger.warning(f"Warning: Could not find image '{self.image_name}.png' for theme '{self.current_theme}' or in common.")
        logger.info(f"Loading missing texture: {self.missing_texture_path}")
        try:
            missing_surf: pygame.Surface = pygame.image.load(self.missing_texture_path).convert_alpha()
            return pygame.transform.scale(missing_surf, (self.target_width, self.target_height))
        except Exception as e:
            logger.error(f"FATAL: Could not load missing texture! Error: {e}")
            # Create a bright purple surface as a last resort
            fallback_surf: pygame.Surface = pygame.Surface((self.target_width, self.target_height), pygame.SRCALPHA)
            fallback_surf.fill((255, 0, 255))
            return fallback_surf
            
    # Reloads the button's image when the theme changes.
    def reload_image(self, new_theme: str) -> None:
        """
        Updates the theme and reloads the image surface.
        Preserves the button's position.

        Args:
            new_theme: The name of the new theme to load assets for.
        """
        self.current_theme = new_theme
        
        old_topleft: tuple[int, int] = self.rect.topleft
        
        self.image_surf = self.load_image()
        
        # Reset rect with new image size and restore position
        self.rect = self.image_surf.get_rect()
        self.rect.topleft = old_topleft
        logger.info(f"Reloaded {self.image_name} for theme {new_theme}. New size: {self.rect.size}")

    # Sets the button's position.
    def set_pos(self, x: float, y: float) -> None:
        """
        Updates the button's top-left position.

        Args:
            x: The new x-coordinate.
            y: The new y-coordinate.
        """
        self.rect.topleft = (int(x), int(y))
        
    # Draws the button on the screen.
    def draw(self, screen: pygame.Surface) -> None:
        """
        Draws the button's image surface on the provided screen.

        Args:
            screen: The pygame.Surface to draw on.
        """
        screen.blit(self.image_surf, self.rect)

    # Checks if the button was clicked.
    def is_clicked(self, event: pygame.event.Event) -> bool:
        """
        Checks if a MOUSEBUTTONDOWN event occurred within the button's bounds.

        Args:
            event: The pygame.event.Event to check.

        Returns:
            True if the button was clicked, False otherwise.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False