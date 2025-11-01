import pygame
from libs.common.components import Slider

# --- Coordinate Helper Functions ---
# (These are needed for the tool's internal logic)
def screen_to_canvas(screen_pos, zoom, offset):
    return (
        (screen_pos[0] - offset[0]) / zoom, 
        (screen_pos[1] - offset[1]) / zoom
    )

class ZoomTool:
    """
    A UI component that manages all zoom and pan logic for the whiteboard.
    It is loaded as a kit component but does not have a button.
    """
    def __init__(self, rect, config):
        self.name = config["name"].lower() # "zoomtool"
        self.config_type = config["type"] # "ui_component"
        self.is_drawing_tool = False # This is not a drawing tool

        # The 'rect' passed in is a placeholder, we will define our own
        # The rect attribute will be for the slider
        self.rect = pygame.Rect(rect.x, rect.y, 260, 30) # 200 slider + 60 text
        
        # Create the slider
        self.slider = Slider(
            x=self.rect.x, y=self.rect.y, 
            width=200, height=30, 
            min_val=0.01, max_val=2.0, initial_val=1.0
        )
        
        self.is_panning = False
        self.pan_start_pos = (0, 0)
        self.pan_start_offset = (0, 0)

        try:
            self.font = pygame.font.Font("freesansbold.ttf", 20)
        except:
            self.font = pygame.font.Font(None, 20)

    def _set_zoom(self, context, new_zoom, pivot_pos):
        """Internal helper to set zoom and recalculate pan."""
        new_zoom = max(0.01, min(2.0, new_zoom)) # Clamp
        
        current_zoom = context["zoom_level"]
        current_offset = context["pan_offset"]
        
        canvas_pivot = screen_to_canvas(pivot_pos, current_zoom, current_offset)
        
        new_offset = (
            pivot_pos[0] - (canvas_pivot[0] * new_zoom),
            pivot_pos[1] - (canvas_pivot[1] * new_zoom)
        )

        context["zoom_level"] = new_zoom
        context["pan_offset"] = new_offset
        self.slider.set_value(new_zoom)

    def handle_event(self, event, context):
        """Handles all zoom/pan related events."""
        mouse_pos = context["mouse_pos"]
        
        # 1. Handle Slider
        if self.slider.handle_event(event):
            new_zoom = self.slider.get_value()
            screen_center = (context["screen"].get_width() / 2, context["screen"].get_height() / 2)
            self._set_zoom(context, new_zoom, screen_center)
            return True # Consumed event

        # 2. Handle Panning (Middle Mouse)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
            self.is_panning = True
            self.pan_start_pos = mouse_pos
            self.pan_start_offset = context["pan_offset"]
            return True # Consumed
            
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 2:
            self.is_panning = False
            return True # Consumed
            
        elif event.type == pygame.MOUSEMOTION:
            if self.is_panning:
                delta_x = mouse_pos[0] - self.pan_start_pos[0]
                delta_y = mouse_pos[1] - self.pan_start_pos[1]
                context["pan_offset"] = (
                    self.pan_start_offset[0] + delta_x,
                    self.pan_start_offset[1] + delta_y
                )
                return True # Consumed

        # 3. Handle Mouse Wheel Zoom
        if event.type == pygame.MOUSEWHEEL:
            # Check if mouse is over any UI (top bar or toolbar)
            is_over_ui = False
            for rect in context.get("ui_hotspots", []):
                if rect.collidepoint(mouse_pos):
                    is_over_ui = True
                    break
            
            if not is_over_ui:
                current_zoom = context["zoom_level"]
                if event.y > 0: # Scroll Up
                    self._set_zoom(context, min(2.0, current_zoom + 0.1), mouse_pos)
                elif event.y < 0: # Scroll Down
                    self._set_zoom(context, max(0.01, current_zoom - 0.1), mouse_pos)
                return True # Consumed

        # 4. Handle Keyboard Zoom
        if event.type == pygame.KEYDOWN:
            mods = pygame.key.get_mods()
            is_ctrl_or_cmd = mods & pygame.KMOD_CTRL or mods & pygame.KMOD_META
            
            if is_ctrl_or_cmd:
                if event.key == pygame.K_0:
                    context["zoom_level"] = 1.0
                    context["pan_offset"] = (0, 0)
                    self.slider.set_value(1.0)
                    return True # Consumed
                elif event.key == pygame.K_EQUALS:
                    self._set_zoom(context, context["zoom_level"] + 0.25, mouse_pos)
                    return True # Consumed
                elif event.key == pygame.K_MINUS:
                    self._set_zoom(context, context["zoom_level"] - 0.25, mouse_pos)
                    return True # Consumed

        return False # Did not consume event

    def update_button_pos(self, x, y):
        """Called by the host to update the component's position."""
        # This is for the *button* tools, but we are a UI component.
        # We'll update our slider's position.
        self.rect.topleft = (x, y)
        self.slider.update_pos(x, y) # Slider is main element

    def draw(self, screen, context):
        """Draws the slider and the zoom percentage."""
        self.slider.draw(screen)
        
        # Draw Zoom Label
        zoom_text = f"{int(context['zoom_level'] * 100)}%"
        zoom_surf = self.font.render(zoom_text, True, (255, 255, 255))
        zoom_rect = zoom_surf.get_rect(midleft=(self.slider.rect.right + 10, self.slider.rect.centery))
        screen.blit(zoom_surf, zoom_rect)