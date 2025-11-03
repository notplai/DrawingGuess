import pygame

class Box:
    """
    A clickable checkbox class.
    This class is well-optimized as it renders text only once during initialization.
    """
    
    def __init__(self, x, y, width, height, label="Checkbox", 
                 initial_checked=False, font_size=30, text_color='White'):
        
        # The checkbox's position and size
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.checked = initial_checked # The current state
        self.text_color = text_color
        
        # Initialize font
        try:
            self.font = pygame.font.Font("freesansbold.ttf", font_size)
        except FileNotFoundError:
            self.font = pygame.font.Font(None, font_size)

        # ---
        # Render the label surface ONCE during creation
        self.label_surf = self.font.render(self.label, True, self.text_color)
        # Position label to the right of the box
        self.label_rect = self.label_surf.get_rect(midleft=(self.rect.right + 10, self.rect.centery))

    def draw(self, screen):
        """Draws the checkbox on the screen."""
        
        # 1. Draw the box
        pygame.draw.rect(screen, self.text_color, self.rect, 2)
        
        # 2. Draw the pre-rendered label
        screen.blit(self.label_surf, self.label_rect)
        
        # 3. Draw the 'X' if checked (this is fast)
        if self.checked:
            p1 = (self.rect.left + 5, self.rect.top + 5)
            p2 = (self.rect.right - 5, self.rect.bottom - 5)
            p3 = (self.rect.left + 5, self.rect.bottom - 5)
            p4 = (self.rect.right - 5, self.rect.top + 5)
            pygame.draw.line(screen, self.text_color, p1, p2, 4)
            pygame.draw.line(screen, self.text_color, p3, p4, 4)

    def handle_event(self, event):
        """Handles click events, toggles state, and returns True if changed."""
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if the click was on the box
            if self.rect.collidepoint(event.pos):
                self.checked = not self.checked # Toggle state
                return True # State changed
        return False # State did not change
