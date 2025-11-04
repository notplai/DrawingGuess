import pygame
from libs.common.components import SolidButton, SolidSlider, InputBox
import math

class PenTool:
    """
    A context tool that provides a size adjuster pop-up for the pen.
    """
    def __init__(self, rect, config):
        self.name = config["name"].lower() # "pen"
        self.config_type = "context_tool" #  Changed to context_tool
        self.button = SolidButton(
            rect.x, rect.y, rect.width, rect.height,
            bg_color=(100,100,100), 
            font_size=20,
            icon_path=config.get("icon_path")
        )
        self.is_drawing_tool = True # This tool *does* draw
        self.last_pos = None

        # ---  Size Picker Assets ---
        self.modal_rect = pygame.Rect(0, 0, 280, 80) #  Increased width from 250 to 280
        self.slider = SolidSlider(
            x=self.modal_rect.x + 20, y=self.modal_rect.y + 25, 
            width=100, height=30, 
            min_val=1, max_val=40, initial_val=5
        )
        self.input_box = InputBox(
            x=self.modal_rect.x + 130, y=self.modal_rect.y + 25,
            width=70, height=30, text='5'
        )
        try:
            self.font = pygame.font.Font("freesansbold.ttf", 20)
        except:
            self.font = pygame.font.Font(None, 24)
            
        self.px_label_surf = self.font.render("px", True, (0,0,0))
        self.px_label_rect = self.px_label_surf.get_rect(center=self.modal_rect.center)


    def handle_event(self, event, context):
        """Handles user input for this tool."""
        
        menu_open = context.get("menu_open")
        mouse_pos = context.get("mouse_pos")

        # --- STAGE A: Handle Toolbar Button Click ---
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.button.rect.collidepoint(event.pos):
                
                #  Set this tool as active, deselecting other tools
                context["active_tool_name"] = self.name 
                
                if context.get("menu_open") == self.name:
                    context["menu_open"] = None # Close self
                else:
                    context["menu_open"] = self.name # Open self
                    # Sync slider to current context value when opening
                    current_size = context.get("draw_size", 5)
                    self.slider.set_value(current_size)
                    self.input_box.set_text(str(current_size))
                return True # Consumed event

        # --- STAGE B: Handle Pop-up Events ---
        if menu_open != self.name:
            return self._handle_drawing_events(event, context) # Pass to drawing logic

        # If we are here, the size menu is open
        self._update_popup_rects(context) # Ensure rects are in correct place

        # Check for slider interaction
        if self.slider.handle_event(event):
            new_size = int(self.slider.get_value())
            context["draw_size"] = new_size
            self.input_box.set_text(str(new_size))
            return True # Consumed
            
        # Check for input box interaction
        input_changed, new_text = self.input_box.handle_event(event)
        if input_changed: # User pressed Enter
            try:
                new_size = int(new_text)
                new_size = max(1, min(new_size, 2048)) # Clamp to bounds
            except ValueError:
                new_size = context.get("draw_size", 5) # Reset on bad input
            
            context["draw_size"] = new_size
            self.slider.set_value(new_size) # Update slider
            self.input_box.set_text(str(new_size)) # Re-set text
            return True # Consumed
        elif self.input_box.active:
             return True # Consume clicks/keys while input is active

        # Check for click *inside* modal (but not on a component)
        if event.type == pygame.MOUSEBUTTONDOWN and self.modal_rect.collidepoint(mouse_pos):
             return True # Consume click
             
        # Check for click *outside* modal
        if event.type == pygame.MOUSEBUTTONDOWN and not self.modal_rect.collidepoint(mouse_pos):
            context["menu_open"] = None # Close menu
            # [FIX] Do NOT fall through to drawing.
            return False 
            
        # Consume all other motion events if mouse is over modal
        if self.modal_rect.collidepoint(mouse_pos):
            return True

        return self._handle_drawing_events(event, context)

    def _handle_drawing_events(self, event, context):
        """Helper to contain the drawing logic."""
        if context.get("active_tool_name") != self.name:
            return False
        
        canvas_mouse_pos = context.get("canvas_mouse_pos", context.get("mouse_pos"))
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not context["click_on_ui"]:
                self.last_pos = canvas_mouse_pos
                context["is_drawing"] = True
                
                # Draw a single circle on click
                drawing_surface = context["drawing_surface"]
                draw_color = context.get("draw_color", (0,0,0))
                draw_size = context.get("draw_size", 5)
                pygame.draw.circle(drawing_surface, draw_color, self.last_pos, max(1, draw_size // 2)) #  Ensure radius is at least 1
                
                return True 

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if context["is_drawing"]:
                context["is_drawing"] = False
                if self.last_pos: # Only add history if a point was drawn
                    context["add_history"](f"{self.name.capitalize()} Stroke")
                self.last_pos = None
                return True 

        elif event.type == pygame.MOUSEMOTION:
            if context["is_drawing"] and self.last_pos:
                drawing_surface = context["drawing_surface"]
                draw_color = context.get("draw_color", (0,0,0))
                draw_size = context.get("draw_size", 5)
                
                #  Draw circle at start and end for rounded lines
                pygame.draw.circle(drawing_surface, draw_color, self.last_pos, max(1, draw_size // 2))
                pygame.draw.circle(drawing_surface, draw_color, canvas_mouse_pos, max(1, draw_size // 2))
                pygame.draw.line(drawing_surface, draw_color, self.last_pos, canvas_mouse_pos, max(1, draw_size))
                
                self.last_pos = canvas_mouse_pos
                return True
        
        return False

    def update_button_pos(self, x, y):
        """Called by the host to update the button's position."""
        self.button.rect.topleft = (x, y)
        if self.button.icon_surf:
            pass 
        else:
            self.button.text_rect.center = self.button.rect.center

    def _update_popup_rects(self, context):
        """Internal helper to calculate dynamic pop-up positions."""
        toolbar_current_y = context["toolbar_current_y"]
        screen_rect_for_clamp = context["screen"].get_rect().inflate(-10, -10)
        
        # Position modal above the toolbar
        self.modal_rect.bottom = toolbar_current_y - 10 # 10px margin
        self.modal_rect.centerx = self.button.rect.centerx
        
        # Clamp modal to screen
        self.modal_rect.clamp_ip(screen_rect_for_clamp)
        
        # Calculate internal rects
        self.slider.update_pos(self.modal_rect.x + 20, self.modal_rect.y + 25)
        
        input_x = self.slider.rect.right + 10
        self.input_box.update_pos(input_x, self.slider.rect.y)
        
        self.px_label_rect.midleft = (self.input_box.rect.right + 5, self.input_box.rect.centery)


    def draw(self, screen, context):
        """Draws the tool's button and any pop-ups."""
        
        # 1. Draw button
        menu_open = context.get("menu_open")
        is_active = context.get("active_tool_name") == self.name
        
        #  Show active if tool is selected OR menu is open
        if is_active: #  Only show yellow border if it's the active tool
            pygame.draw.rect(screen, (200, 200, 0), self.button.rect.inflate(4, 4))
        
        self.button.draw(screen) 
        
        # 2. Draw pop-up
        if menu_open == self.name:
            self._update_popup_rects(context) # Ensure positions are correct
            
            # Draw modal box
            pygame.draw.rect(screen, (220, 220, 220), self.modal_rect)
            pygame.draw.rect(screen, (0,0,0), self.modal_rect, 2)
            
            # Draw components
            self.slider.draw(screen)
            self.input_box.draw(screen)
            screen.blit(self.px_label_surf, self.px_label_rect)