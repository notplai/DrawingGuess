import pygame

class Button:
    """
    A clickable button class.
    [Updated to support icons]
    """
    
    def __init__(self, x, y, width, height, text='', text_color='Black', 
                 bg_color=(200, 200, 200), border_color=(0, 0, 0), border_width=2, 
                 font_size=30, text_align='center', icon_path=None): # [NEW] Added icon_path
        
        # The button's position and size
        self.rect = pygame.Rect(x, y, width, height)
        
        # Text and color properties
        self.text = text
        self.text_color = text_color
        self.bg_color = bg_color
        self.border_color = border_color
        self.border_width = border_width
        
        # Initialize font
        try:
            self.font = pygame.font.Font("freesansbold.ttf", font_size)
        except FileNotFoundError:
            self.font = pygame.font.Font(None, font_size) # Fallback to default

        # --- [NEW] Icon Loading ---
        self.icon_surf = None
        if icon_path:
            try:
                self.icon_surf = pygame.image.load(icon_path).convert_alpha()
                # Scale the icon to fit the button (e.g., 80% of height)
                icon_size = int(self.rect.height * 0.7) # 70% for padding
                self.icon_surf = pygame.transform.smoothscale(self.icon_surf, (icon_size, icon_size))
            except Exception as e:
                print(f"Warning: Could not load icon '{icon_path}': {e}")
                self.icon_surf = None # Failed, fall back to text

        # --- Text Rendering (as fallback) ---
        self.text_surf = self.font.render(text, True, text_color)
        
        # --- Handle Text Alignment ---
        if text_align == 'center':
            self.text_rect = self.text_surf.get_rect(center=self.rect.center)
        elif text_align == 'left':
            self.text_rect = self.text_surf.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
        elif text_align == 'right':
            self.text_rect = self.text_surf.get_rect(midright=(self.rect.right - 10, self.rect.centery))
        else:
            self.text_rect = self.text_surf.get_rect(center=self.rect.center)
            
    def draw(self, screen):
        """Draws the button on the screen."""
        
        # 1. Draw background
        pygame.draw.rect(screen, self.bg_color, self.rect)
        
        # 2. Draw border (if specified)
        if self.border_color:
            pygame.draw.rect(screen, self.border_color, self.rect, self.border_width)
            
        # 3. [NEW] Draw icon or text
        if self.icon_surf:
            icon_rect = self.icon_surf.get_rect(center=self.rect.center)
            screen.blit(self.icon_surf, icon_rect)
        else:
            screen.blit(self.text_surf, self.text_rect)

    def is_clicked(self, event):
        """Checks if the button was clicked."""
        
        # Check for a mouse click event
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if the mouse position collides with the button's rect
            if self.rect.collidepoint(event.pos):
                return True
        return False

