import pygame
from typing import Optional, Literal, Any
from libs.utils.pylog import Logger

logger = Logger(__name__)

# Defines a SolidButton UI component.
class Button:
    """
    A UI component for a solid color button with text or an icon.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str = '', text_color: Any = 'Black', 
                 bg_color: Any = (200, 200, 200), border_color: Optional[Any] = (0, 0, 0), border_width: int = 2, 
                 font_size: int = 30, text_align: Literal['center', 'left', 'right'] = 'center', 
                 icon_path: Optional[str] = None):
        """
        Initializes the Button.

        Args:
            x: The x-coordinate of the top-left corner.
            y: The y-coordinate of the top-left corner.
            width: The width of the button.
            height: The height of the button.
            text: The text to display on the button (if no icon).
            text_color: The color of the text.
            bg_color: The background color of the button.
            border_color: The color of the border. None for no border.
            border_width: The width of the border.
            font_size: The font size for the text.
            text_align: The alignment of the text ('center', 'left', 'right').
            icon_path: The file path to an icon to display (overrides text).
        """
        
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)
        
        self.text: str = text
        self.text_color: Any = text_color
        self.bg_color: Any = bg_color
        self.border_color: Optional[Any] = border_color
        self.border_width: int = border_width
        
        self.font: pygame.font.Font
        try:
            self.font = pygame.font.Font("freesansbold.ttf", font_size)
        except FileNotFoundError:
            self.font = pygame.font.Font(None, font_size)

        # Load and scale the icon if provided
        self.icon_surf: Optional[pygame.Surface] = None
        if icon_path:
            try:
                self.icon_surf = pygame.image.load(icon_path).convert_alpha()
                # Scale icon to fit button height
                icon_size: int = int(self.rect.height * 0.7)
                self.icon_surf = pygame.transform.smoothscale(self.icon_surf, (icon_size, icon_size))
            except Exception as e:
                logger.warning(f"Warning: Could not load icon '{icon_path}': {e}")
                self.icon_surf = None

        # Render the text surface
        self.text_surf: pygame.Surface = self.font.render(text, True, text_color)
        
        # Position the text based on alignment
        if text_align == 'center':
            self.text_rect: pygame.Rect = self.text_surf.get_rect(center=self.rect.center)
        elif text_align == 'left':
            self.text_rect = self.text_surf.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
        elif text_align == 'right':
            self.text_rect = self.text_surf.get_rect(midright=(self.rect.right - 10, self.rect.centery))
        else:
            self.text_rect = self.text_surf.get_rect(center=self.rect.center)
            
    # Draws the button on the screen.
    def draw(self, screen: pygame.Surface) -> None:
        """
        Draws the button (background, border, and icon or text)
        on the provided surface.

        Args:
            screen: The pygame.Surface to draw on.
        """
        pygame.draw.rect(screen, self.bg_color, self.rect)
        
        if self.border_color:
            pygame.draw.rect(screen, self.border_color, self.rect, self.border_width)
            
        if self.icon_surf:
            # Draw icon if it exists
            icon_rect: pygame.Rect = self.icon_surf.get_rect(center=self.rect.center)
            screen.blit(self.icon_surf, icon_rect)
        else:
            # Draw text if no icon
            screen.blit(self.text_surf, self.text_rect)

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