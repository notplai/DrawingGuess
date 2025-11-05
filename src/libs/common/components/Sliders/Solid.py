import pygame
from typing import Any

# Defines a Slider UI component.
class Slider:
    """
    A simple horizontal slider UI component.
    Allows selecting a value within a min/max range by dragging a knob.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int, min_val: float, max_val: float, initial_val: float, 
                 track_color: Any = (150, 150, 150), knob_color: Any = (240, 240, 240)):
        """
        Initializes the Slider.

        Args:
            x: The x-coordinate of the top-left corner.
            y: The y-coordinate of the top-left corner.
            width: The width of the slider track.
            height: The total height of the slider (knob diameter).
            min_val: The minimum value of the slider.
            max_val: The maximum value of the slider.
            initial_val: The starting value of the slider.
            track_color: The color of the slider's track.
            knob_color: The color of the slider's draggable knob.
        """
        
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)
        self.min_val: float = min_val
        self.max_val: float = max_val
        self.value: float = initial_val
        
        self.track_color: Any = track_color
        self.knob_color: Any = knob_color
        
        # The track is thinner than the total height, centered vertically
        self.track_rect: pygame.Rect = pygame.Rect(x, y + height // 4, width, height // 2)
        
        self.knob_radius: int = height // 2
        self.knob_x: int = 0
        self._update_knob_pos_from_value() # Set initial knob position
        
        self.is_dragging: bool = False

    # Updates the knob's X-position based on the current value.
    def _update_knob_pos_from_value(self) -> None:
        """
        Internal method to calculate and set the knob's x-coordinate
        based on the current self.value.
        """
        value_range: float = self.max_val - self.min_val
        percent: float
        if value_range == 0:
            percent = 0
        else:
            # Calculate what percentage the value is within the range
            percent = (self.value - self.min_val) / value_range
        # Map the percentage to the track's width
        self.knob_x = self.track_rect.x + int(percent * self.track_rect.width)

    # Updates the value based on the knob's X-position.
    def _update_value_from_pos(self, mouse_x: int) -> None:
        """
        Internal method to calculate and set self.value based on
        the mouse's x-coordinate.

        Args:
            mouse_x: The x-coordinate of the mouse.
        """
        # Clamp the position to be within the track's bounds
        clamped_x: int = max(self.track_rect.x, min(mouse_x, self.track_rect.right))
        
        # Calculate the percentage along the track
        percent: float = (clamped_x - self.track_rect.x) / self.track_rect.width
        percent = max(0.0, min(1.0, percent)) # Ensure percent is [0.0, 1.0]
        # Map the percentage back to the value range
        self.value = self.min_val + percent * (self.max_val - self.min_val)
        
    # Sets the slider's value programmatically.
    def set_value(self, value: float) -> None:
        """
        Public method to set the slider's value directly.
        Clamps the value within min/max bounds.

        Args:
            value: The new value to set.
        """
        self.value = max(self.min_val, min(self.max_val, value))
        self._update_knob_pos_from_value()
        
    # Gets the current value.
    def get_value(self) -> float:
        """
        Returns the current value of the slider.

        Returns:
            The slider's current value.
        """
        return self.value

    # Updates the slider's position.
    def update_pos(self, x: int, y: int) -> None:
        """
        Updates the top-left position of the entire slider component.

        Args:
            x: The new x-coordinate.
            y: The new y-coordinate.
        """
        self.rect.topleft = (x, y)
        self.track_rect.topleft = (x, y + self.rect.height // 4)
        self._update_knob_pos_from_value() # Recalculate knob position

    # Handles user input events for the slider.
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Processes pygame events for dragging the slider knob.

        Args:
            event: The pygame.event.Event to process.

        Returns:
            True if the slider's value was changed, False otherwise.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check for click on the entire slider rect (not just the knob)
            if self.rect.collidepoint(event.pos):
                self.is_dragging = True
                self._update_value_from_pos(event.pos[0])
                self._update_knob_pos_from_value()
                return True # Value changed
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.is_dragging:
                self.is_dragging = False
                return True # Drag finished
            
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                self._update_value_from_pos(event.pos[0])
                self._update_knob_pos_from_value()
                return True # Value changed
                
        return False

    # Draws the slider on the screen.
    def draw(self, screen: pygame.Surface) -> None:
        """
        Draws the slider track and knob on the provided surface.

        Args:
            screen: The pygame.Surface to draw on.
        """
        # Draw the track
        pygame.draw.rect(screen, self.track_color, self.track_rect, border_radius=self.track_rect.height // 2)
        # Draw the knob
        pygame.draw.circle(screen, self.knob_color, (self.knob_x, self.rect.centery), self.knob_radius)
        pygame.draw.circle(screen, (50, 50, 50), (self.knob_x, self.rect.centery), self.knob_radius, 2) # Knob border