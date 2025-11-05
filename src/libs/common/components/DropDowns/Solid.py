import pygame
from typing import List, Tuple, Optional, Any

# Defines a Dropdown UI component.
class Dropdown:
    """
    A simple dropdown menu UI component.
    Shows a main bar and a list of options when clicked.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int, main_text: str, options: List[str], 
                 font_size: int = 30, text_color: Any = 'White', bg_color: Any = (100, 100, 100), 
                 option_bg_color: Any = (200, 200, 200), option_text_color: Any = 'Black'):
        """
        Initializes the Dropdown.

        Args:
            x: The x-coordinate of the top-left corner.
            y: The y-coordinate of the top-left corner.
            width: The width of the dropdown bar and options.
            height: The height of the main bar and each option.
            main_text: The prefix text (e.g., "Theme").
            options: A list of string options for the dropdown.
            font_size: The font size for all text.
            text_color: The color of the text on the main bar.
            bg_color: The background color of the main bar.
            option_bg_color: The background color of the option boxes.
            option_text_color: The color of the text for the options.
        """
        
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)
        self.main_text: str = main_text
        self.options: List[str] = options
        self.selected_option: str = ""
        
        self.is_open: bool = False # True if the options are visible
        
        self.text_color: Any = text_color
        self.bg_color: Any = bg_color
        self.option_bg_color: Any = option_bg_color
        self.option_text_color: Any = option_text_color
        
        self.font: pygame.font.Font
        try:
            self.font = pygame.font.Font("freesansbold.ttf", font_size)
        except FileNotFoundError:
            self.font = pygame.font.Font(None, font_size)

        # Create rects for each option box
        self.option_rects: List[pygame.Rect] = []
        for i, option in enumerate(self.options):
            rect = pygame.Rect(x, y + (i + 1) * height, width, height)
            self.option_rects.append(rect)

        # Pre-render surfaces for each option
        self.option_surfs: List[pygame.Surface] = [
            self.font.render(option, True, self.option_text_color) 
            for option in self.options
        ]
        self.option_surfs_rects: List[pygame.Rect] = [
            surf.get_rect(midleft=(rect.x + 10, rect.centery)) 
            for surf, rect in zip(self.option_surfs, self.option_rects)
        ]

        # Surfaces for the main display bar (e.g., "Theme: CuteChaos")
        self.current_display_surf: Optional[pygame.Surface] = None
        self.current_display_rect: Optional[pygame.Rect] = None

    # Sets the currently selected option.
    def set_selected(self, option: str) -> None:
        """
        Sets the selected option and updates the main display text.

        Args:
            option: The string of the option to select.
        """
        self.selected_option = option
        full_text: str = f"{self.main_text}: {self.selected_option}"
        
        # Re-render the main display bar
        self.current_display_surf = self.font.render(full_text, True, self.text_color)
        self.current_display_rect = self.current_display_surf.get_rect(
            midleft=(self.rect.x + 10, self.rect.centery)
        )

    # Handles user input events for the dropdown.
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """
        Processes pygame events for opening, closing, and selecting options.

        Args:
            event: The pygame.event.Event to process.

        Returns:
            The string of the newly selected option if one was chosen,
            otherwise None.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Click on the main bar: toggle open/closed
            if self.rect.collidepoint(event.pos):
                self.is_open = not self.is_open
                return None
            
            # Click while open: check if an option was clicked
            if self.is_open:
                for i, option_rect in enumerate(self.option_rects):
                    if option_rect.collidepoint(event.pos):
                        new_option: str = self.options[i]
                        self.set_selected(new_option)
                        self.is_open = False
                        return new_option # Return the new selection
            
            # Click outside the dropdown: close it
            self.is_open = False
        return None

    # Draws the dropdown on the screen.
    def draw(self, screen: pygame.Surface) -> None:
        """
        Draws the main dropdown bar and the option list (if open).

        Args:
            screen: The pygame.Surface to draw on.
        """
        # Draw the main bar
        pygame.draw.rect(screen, self.bg_color, self.rect)
        pygame.draw.rect(screen, self.text_color, self.rect, 2)
        
        if self.current_display_surf and self.current_display_rect:
            screen.blit(self.current_display_surf, self.current_display_rect)

        # Draw the options list if open
        if self.is_open:
            for i, option_rect in enumerate(self.option_rects):
                pygame.draw.rect(screen, self.option_bg_color, option_rect)
                pygame.draw.rect(screen, 'Black', option_rect, 2)
                
                # Blit the pre-rendered option text
                screen.blit(self.option_surfs[i], self.option_surfs_rects[i])