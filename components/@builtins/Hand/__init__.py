import pygame
from libs.common.components import SolidButton

class HandTool:
    """
    A simple tool for panning the canvas.
    It activates panning when the mouse is pressed.
    """
    def __init__(self, rect, config):
        self.name = config["name"].lower() # "hand"
        self.config_type = config["type"] # "drawing_tool"
        self.button = SolidButton(
            rect.x, rect.y, rect.width, rect.height,
            bg_color=(100,100,100), 
            font_size=20,
            icon_path=config.get("icon_path")
        )
        self.is_drawing_tool = False # This tool does not draw

    def handle_event(self, event, context):
        """Handles user input for this tool."""
        
        # === STAGE B: Handle tool button click ===
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.button.rect.collidepoint(event.pos):
                context["active_tool_name"] = self.name
                context["menu_open"] = None
                return True # Consumed event

        if context.get("active_tool_name") != self.name:
            return False
            
        # === STAGE C: Handle panning on canvas ===
        mouse_pos = context.get("mouse_pos")
        
        # Use Left (1) or Middle (2) mouse button for panning
        if event.type == pygame.MOUSEBUTTONDOWN and (event.button == 1 or event.button == 2):
            if not context["click_on_ui"]:
                context["is_panning"] = True
                context["pan_start_pos"] = mouse_pos
                context["pan_start_offset"] = context["pan_offset"]
                context["is_drawing"] = True # [NEW] Set drawing flag
                return True # Consume event

        elif event.type == pygame.MOUSEBUTTONUP and (event.button == 1 or event.button == 2):
            # [FIX] Use context.get() for safety to prevent KeyError
            if context.get("is_panning", False):
                context["is_panning"] = False
                context["is_drawing"] = False # [NEW] Clear drawing flag
                return True # Consume event

        elif event.type == pygame.MOUSEMOTION:
            #  Use context.get() for safety to prevent KeyError
            if context.get("is_panning", False):
                delta_x = mouse_pos[0] - context["pan_start_pos"][0]
                delta_y = mouse_pos[1] - context["pan_start_pos"][1]
                context["pan_offset"] = (
                    context["pan_start_offset"][0] + delta_x,
                    context["pan_start_offset"][1] + delta_y
                )
                return True # Consume event
        
        return False

    def update_button_pos(self, x, y):
        """Called by the host to update the button's position."""
        self.button.rect.topleft = (x, y)
        if self.button.icon_surf:
            pass # Icon is centered in draw()
        else:
            self.button.text_rect.center = self.button.rect.center

    def draw(self, screen, context):
        """Draws the tool's button."""
        
        # 1. Draw button
        is_active = context.get("active_tool_name") == self.name
        if is_active:
            pygame.draw.rect(screen, (200, 200, 0), self.button.rect.inflate(4, 4))
        
        self.button.draw(screen)
