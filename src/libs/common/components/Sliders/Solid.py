import pygame

class Slider:
    """
    A simple horizontal slider component.
    """
    
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, 
                 track_color=(150, 150, 150), knob_color=(240, 240, 240)):
        
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        
        self.track_color = track_color
        self.knob_color = knob_color
        
        # The track is thinner than the main rect
        self.track_rect = pygame.Rect(x, y + height // 4, width, height // 2)
        
        self.knob_radius = height // 2
        self.knob_x = 0
        self._update_knob_pos_from_value()
        
        self.is_dragging = False

    def _update_knob_pos_from_value(self):
        """Internal: Set knob_x based on self.value."""
        value_range = self.max_val - self.min_val
        if value_range == 0:
            percent = 0
        else:
            percent = (self.value - self.min_val) / value_range
        self.knob_x = self.track_rect.x + int(percent * self.track_rect.width)

    def _update_value_from_pos(self, mouse_x):
        """Internal: Set self.value based on mouse_x."""
        # [FIX] Clamp mouse_x to the track's limits
        clamped_x = max(self.track_rect.x, min(mouse_x, self.track_rect.right))
        
        percent = (clamped_x - self.track_rect.x) / self.track_rect.width
        percent = max(0.0, min(1.0, percent)) # Clamp
        self.value = self.min_val + percent * (self.max_val - self.min_val)
        
    def set_value(self, value):
        """Public: Set the slider's value directly."""
        self.value = max(self.min_val, min(self.max_val, value))
        self._update_knob_pos_from_value()
        
    def get_value(self):
        """Public: Get the slider's current value."""
        return self.value

    def update_pos(self, x, y):
        """Update the slider's position (e.g., for an animated toolbar)."""
        self.rect.topleft = (x, y)
        self.track_rect.topleft = (x, y + self.rect.height // 4)
        self._update_knob_pos_from_value() # Keep knob in sync

    def handle_event(self, event):
        """Handles mouse input for dragging the slider. Returns True if value changed."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Use the larger self.rect for easier clicking
            if self.rect.collidepoint(event.pos):
                self.is_dragging = True
                self._update_value_from_pos(event.pos[0])
                self._update_knob_pos_from_value()
                return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            # [FIX] Consume mouseup event if we were dragging
            if self.is_dragging:
                self.is_dragging = False
                return True
            
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                # [MODIFIED] Reverted behavior.
                # Dragging now continues even if the mouse leaves the rect.
                self._update_value_from_pos(event.pos[0])
                self._update_knob_pos_from_value()
                return True
                
        return False

    def draw(self, screen):
        """Draws the slider."""
        # 1. Draw track
        pygame.draw.rect(screen, self.track_color, self.track_rect, border_radius=self.track_rect.height // 2)
        # 2. Draw knob
        pygame.draw.circle(screen, self.knob_color, (self.knob_x, self.rect.centery), self.knob_radius)
        pygame.draw.circle(screen, (50, 50, 50), (self.knob_x, self.rect.centery), self.knob_radius, 2)

