import pygame

class InputBox:
    """
    A simple text input box component.
    """
    def __init__(self, x, y, width, height, text='', font=None, 
                 bg_color=(255, 255, 255), text_color=(0, 0, 0), 
                 active_color=(200, 200, 255), border_color=(100, 100, 100)):
        
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font if font else pygame.font.Font(None, 28)
        
        self.bg_color = bg_color
        self.text_color = text_color
        self.active_color = active_color
        self.border_color = border_color
        
        self.active = False
        self.text_surface = self.font.render(text, True, self.text_color)
        
        # Cursor blink logic
        self.cursor_visible = True
        self.cursor_timer = 0
        self.CURSOR_BLINK_RATE = 500 # milliseconds

    def set_text(self, text):
        """Public method to set the text from outside."""
        self.text = str(text)
        self.text_surface = self.font.render(self.text, True, self.text_color)

    def get_text(self):
        """Public method to get the current text."""
        return self.text

    def handle_event(self, event):
        """
        Handles mouse and keyboard events.
        Returns (bool: value_changed_on_enter, str: current_text)
        """
        value_changed = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            # Reset cursor timer on click
            self.cursor_timer = pygame.time.get_ticks()
            self.cursor_visible = True
                
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.active = False
                value_changed = True # Signal that Enter was pressed
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            # Check if the key is a digit
            elif event.unicode.isdigit():
                self.text += event.unicode
            
            self.text_surface = self.font.render(self.text, True, self.text_color)
            # Reset cursor timer on key press
            self.cursor_timer = pygame.time.get_ticks()
            self.cursor_visible = True

        return value_changed, self.text

    def update_pos(self, x, y):
        """Update the input box's position."""
        self.rect.topleft = (x, y)

    def draw(self, screen):
        """Draws the input box."""
        
        # 1. Draw background
        current_bg = self.active_color if self.active else self.bg_color
        pygame.draw.rect(screen, current_bg, self.rect)
        
        # 2. Draw border
        pygame.draw.rect(screen, self.border_color, self.rect, 2)
        
        # 3. Draw text (clipped to box)
        text_rect = self.text_surface.get_rect(midleft=(self.rect.x + 5, self.rect.centery))
        # Ensure text doesn't go outside the box
        # text_rect.clamp_ip(self.rect.inflate(-10, -10)) # Not needed
        
        # [FIX] Use set_clip for clipping, not screen.clipper
        clipping_rect = self.rect.inflate(-10, -10)
        old_clip = screen.get_clip() # Store old clip region
        screen.set_clip(clipping_rect) # Set new clip region
        
        screen.blit(self.text_surface, text_rect)
        
        screen.set_clip(old_clip) # Restore old clip region
        
        # 4. Draw cursor
        if self.active:
            now = pygame.time.get_ticks()
            if now - self.cursor_timer > self.CURSOR_BLINK_RATE:
                self.cursor_timer = now
                self.cursor_visible = not self.cursor_visible
            
            if self.cursor_visible:
                cursor_x = text_rect.right + 2
                # Clamp cursor position to be inside the box
                if cursor_x > self.rect.right - 5:
                    cursor_x = self.rect.right - 5
                
                # [FIX] Make sure cursor is also within the clip rect
                if cursor_x > clipping_rect.right:
                    cursor_x = clipping_rect.right

                pygame.draw.line(screen, self.text_color, 
                                 (cursor_x, self.rect.top + 5), 
                                 (cursor_x, self.rect.bottom - 5), 2)
