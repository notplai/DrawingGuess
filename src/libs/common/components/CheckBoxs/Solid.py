import pygame
from typing import Any

# Defines a Box UI component (checkbox).
class Box:
    """
    A simple checkbox UI component with a text label.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int, label: str = "Checkbox", 
                 initial_checked: bool = False, font_size: int = 30, text_color: Any = 'White'):
        """
        Initializes the Checkbox.

        Args:
            x: The x-coordinate of the box's top-left corner.
            y: The y-coordinate of the box's top-left corner.
            width: The width of the clickable box.
            height: The height of the clickable box.
            label: The text label to display next to the box.
            initial_checked: The default state (True=checked, False=unchecked).
            font_size: The font size for the label.
            text_color: The color for the box border, 'X', and label text.
        """
        
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)
        self.label: str = label
        self.checked: bool = initial_checked
        self.text_color: Any = text_color
        
        self.font: pygame.font.Font
        try:
            self.font = pygame.font.Font("freesansbold.ttf", font_size)
        except FileNotFoundError:
            self.font = pygame.font.Font(None, font_size)

        # Render and position the text label
        self.label_surf: pygame.Surface = self.font.render(self.label, True, self.text_color)
        self.label_rect: pygame.Rect = self.label_surf.get_rect(midleft=(self.rect.right + 10, self.rect.centery))

    # Draws the checkbox on the screen.
    def draw(self, screen: pygame.Surface) -> None:
        """
        Draws the checkbox (border, label, and 'X' if checked)
        on the provided surface.

        Args:
            screen: The pygame.Surface to draw on.
        """
        # Draw the box border
        pygame.draw.rect(screen, self.text_color, self.rect, 2)
        
        # Draw the label
        screen.blit(self.label_surf, self.label_rect)
        
        # Draw the 'X' if checked
        if self.checked:
            p1: tuple[int, int] = (self.rect.left + 5, self.rect.top + 5)
            p2: tuple[int, int] = (self.rect.right - 5, self.rect.bottom - 5)
            p3: tuple[int, int] = (self.rect.left + 5, self.rect.bottom - 5)
            p4: tuple[int, int] = (self.rect.right - 5, self.rect.top + 5)
            pygame.draw.line(screen, self.text_color, p1, p2, 4)
            pygame.draw.line(screen, self.text_color, p3, p4, 4)

    # Handles user input events for the checkbox.
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Checks if the checkbox was clicked and toggles its state.

        Args:
            event: The pygame.event.Event to process.

        Returns:
            True if the checkbox state was changed, False otherwise.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.checked = not self.checked # Toggle state
                return True # State changed
        return False # No change