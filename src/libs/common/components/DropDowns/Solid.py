import pygame

class Dropdown:
    """
    A dropdown menu class.
    [REFACTORED for performance by caching rendered text surfaces]
    """
    
    def __init__(self, x, y, width, height, main_text, options, 
                 font_size=30, text_color='White', bg_color=(100, 100, 100), 
                 option_bg_color=(200, 200, 200), option_text_color='Black'):
        
        self.rect = pygame.Rect(x, y, width, height)
        self.main_text = main_text # e.g., "Graphic Quality"
        self.options = options
        self.selected_option = "" # Will be set by set_selected()
        
        self.is_open = False
        
        # Colors
        self.text_color = text_color
        self.bg_color = bg_color
        self.option_bg_color = option_bg_color
        self.option_text_color = option_text_color
        
        # Font
        try:
            self.font = pygame.font.Font("freesansbold.ttf", font_size)
        except FileNotFoundError:
            self.font = pygame.font.Font(None, font_size)

        # Create option rects
        self.option_rects = []
        for i, option in enumerate(self.options):
            rect = pygame.Rect(x, y + (i + 1) * height, width, height)
            self.option_rects.append(rect)

        # ---
        # Pre-render all possible option text surfaces
        self.option_surfs = [
            self.font.render(option, True, self.option_text_color) 
            for option in self.options
        ]
        # Pre-calculate their positions
        self.option_surfs_rects = [
            surf.get_rect(midleft=(rect.x + 10, rect.centery)) 
            for surf, rect in zip(self.option_surfs, self.option_rects)
        ]

        # These will hold the *currently* displayed text surface and rect
        self.current_display_surf = None
        self.current_display_rect = None

    def set_selected(self, option):
        """
        Sets the selected option and re-renders the main display surface.
        This is called only when the selection changes, not every frame.
        """
        self.selected_option = option
        # Create the full text, e.g., "Theme: CuteChaos"
        full_text = f"{self.main_text}: {self.selected_option}"
        
        #
        # Render the text surface *once* here
        self.current_display_surf = self.font.render(full_text, True, self.text_color)
        self.current_display_rect = self.current_display_surf.get_rect(
            midleft=(self.rect.x + 10, self.rect.centery)
        )

    def handle_event(self, event):
        """
        Handles mouse clicks for opening, closing, and selecting options.
        Returns the selected option if a new one is chosen, otherwise None.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.is_open = not self.is_open
                return None
            
            if self.is_open:
                for i, option_rect in enumerate(self.option_rects):
                    if option_rect.collidepoint(event.pos):
                        new_option = self.options[i]
                        self.set_selected(new_option) # Re-render text
                        self.is_open = False
                        return new_option # Return the new value
            
            # Clicked outside the dropdown, close it
            self.is_open = False
        return None

    def draw(self, screen):
        """Draws the main box, and options if open."""
        
        # 1. Draw main box
        pygame.draw.rect(screen, self.bg_color, self.rect)
        pygame.draw.rect(screen, self.text_color, self.rect, 2)
        
        #
        # Blit the pre-rendered main text surface
        if self.current_display_surf:
            screen.blit(self.current_display_surf, self.current_display_rect)

        # 2. Draw options if open
        if self.is_open:
            for i, option_rect in enumerate(self.option_rects):
                # Draw box
                pygame.draw.rect(screen, self.option_bg_color, option_rect)
                pygame.draw.rect(screen, 'Black', option_rect, 2)
                
                #
                # Blit the pre-rendered option surface
                screen.blit(self.option_surfs[i], self.option_surfs_rects[i])
