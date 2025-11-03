import pygame
from libs.common.components import SolidButton
import math
import colorsys

# --- Color Helper Functions ---
# (Moved from whiteboard.py)
def hsv_to_rgb(h, s, v):
    rgb_float = colorsys.hsv_to_rgb(h, s, v)
    return (int(rgb_float[0] * 255), int(rgb_float[1] * 255), int(rgb_float[2] * 255))

def rgb_to_hsv(r, g, b):
    hsv_float = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    return hsv_float

def rgb_to_hex(rgb):
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

def create_color_wheel_surface(size):
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    radius = size // 2
    for y in range(size):
        for x in range(size):
            dx, dy = x - radius, y - radius
            distance = math.sqrt(dx**2 + dy**2)
            if distance <= radius:
                angle = (math.atan2(dy, dx) / (2 * math.pi)) % 1.0
                saturation = distance / radius
                rgb = hsv_to_rgb(angle, saturation, 1.0)
                surface.set_at((x, y), (rgb[0], rgb[1], rgb[2], 255))
    return surface

def update_color_from_pos(mouse_pos, hsv_in, wheel_rect, bar_rect, drag_mode):
    """
    [MODIFIED] Updates H, S, or V based on the drag_mode.
    drag_mode can be 'wheel' or 'bar'.
    """
    h, s, v = hsv_in
    
    if drag_mode == "wheel":
        dx, dy = mouse_pos[0] - wheel_rect.centerx, mouse_pos[1] - wheel_rect.centery
        distance = math.sqrt(dx**2 + dy**2)
        radius = wheel_rect.width / 2
        
        # Calculate saturation, clamping to 1.0 if outside
        s = min(distance / radius, 1.0) 
        # Always calculate angle
        angle = (math.atan2(dy, dx) / (2 * math.pi)) % 1.0
        h = angle
        
    elif drag_mode == "bar":
        # [FIX] Clamp the mouse_y position to the bar's vertical limits
        clamped_y = max(bar_rect.y, min(mouse_pos[1], bar_rect.bottom - 1))
        
        # Calculate relative position *after* clamping
        relative_y = clamped_y - bar_rect.y 
        
        # Use (height - 1) because the pixel range is 0 to (height - 1)
        denominator = max(1, bar_rect.height - 1)
        v = 1.0 - (relative_y / denominator)
        v = max(0.0, min(v, 1.0))
        
    new_hsv = (h, s, v)
    return new_hsv, hsv_to_rgb(new_hsv[0], new_hsv[1], new_hsv[2])


class ColorPalette:
    """
    A context tool that provides a color picker pop-up.
    It modifies the 'draw_color' in the shared context.
    """
    def __init__(self, rect, config):
        self.name = config["name"].lower() # "colorpad"
        self.config_type = config["type"] # [NEW] Store the tool type
        self.button = SolidButton(
            rect.x, rect.y, rect.width, rect.height, # [FIX] Changed rect.Y to rect.y
            bg_color=(100,100,100), 
            font_size=20,
            icon_path=config.get("icon_path") # [NEW] Pass icon path
        )
        self.is_drawing_tool = (config["type"] == "drawing_tool")
        
        # --- Color Picker Assets ---
        self.modal_rect = pygame.Rect(0, 0, 450, 240) # [MODIFIED] Increased width from 410 to 450
        self.WHEEL_SIZE = 150
        self.color_wheel_surface = create_color_wheel_surface(self.WHEEL_SIZE)
        self.wheel_rect = self.color_wheel_surface.get_rect(topleft=(20, 20))
        
        self.BAR_WIDTH = 30
        self.BAR_HEIGHT = self.WHEEL_SIZE
        self.value_bar_rect = pygame.Rect(self.wheel_rect.right + 20, self.wheel_rect.y, self.BAR_WIDTH, self.BAR_HEIGHT)
        
        self.current_color_swatch_rect = pygame.Rect(self.value_bar_rect.right + 20, self.wheel_rect.y, 180, 80) # [MODIFIED] Increased width from 140 to 180
        
        # [MODIFIED] Set default color to Red (100% brightness) and move Black to end
        self.recent_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 0, 0)]
        self.recent_swatches_pos = []
        self.RECENT_SWATCH_RADIUS = 15
        self.swatch_gap = 10
        
        self.is_dragging_wheel = False
        self.is_dragging_bar = False
        
        try:
            self.font = pygame.font.Font("freesansbold.ttf", 18)
        except:
            self.font = pygame.font.Font(None, 22)

    def add_recent_color(self, color):
        if color in self.recent_colors:
            self.recent_colors.remove(color)
        self.recent_colors.insert(0, color)
        if len(self.recent_colors) > 5:
            self.recent_colors.pop()

    def handle_event(self, event, context):
        """Handles user input for this tool."""
        
        menu_open = context.get("menu_open")
        mouse_pos = context.get("mouse_pos") # This is the *real* mouse_pos

        # --- Handle Toolbar Button Click ---
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.button.rect.collidepoint(event.pos): # [FIX] Use global event.pos
                if context.get("menu_open") == self.name:
                    context["menu_open"] = None
                else:
                    context["menu_open"] = self.name
                    # Sync HSV to current color when opening
                    context["current_hsv"] = rgb_to_hsv(*context.get("draw_color", (0,0,0)))
                return True # Consumed event

        # --- Handle Pop-up Events ---
        if menu_open != self.name:
            self.is_dragging_wheel = False
            self.is_dragging_bar = False
            return False

        # If we are here, the colorpad menu is open
        self._update_popup_rects(context) # Ensure rects are in correct place

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Use the *real* mouse_pos for modal collision
            if self.modal_rect.collidepoint(mouse_pos): 
                
                # [MODIFIED] Implement drag locking
                # Only start a new drag if we are not already dragging
                drag_mode = None
                if not self.is_dragging_wheel and not self.is_dragging_bar:
                    # [MODIFIED] Use inflated rect for bar
                    check_bar_rect = self.value_bar_rect.inflate(40, 10)
                    
                    if self.wheel_rect.collidepoint(mouse_pos):
                        self.is_dragging_wheel = True
                        drag_mode = "wheel" # Set drag mode
                    elif check_bar_rect.collidepoint(mouse_pos): 
                        self.is_dragging_bar = True
                        drag_mode = "bar" # Set drag mode
                
                if self.is_dragging_wheel or self.is_dragging_bar:
                    # Update color immediately on click
                    hsv, rgb = update_color_from_pos(mouse_pos, context["current_hsv"], self.wheel_rect, self.value_bar_rect, drag_mode)
                    context["current_hsv"] = hsv
                    context["draw_color"] = rgb
                
                # Check recent swatches (only if not dragging)
                elif not (self.is_dragging_wheel or self.is_dragging_bar):
                    for i, pos in enumerate(self.recent_swatches_pos):
                        if math.dist(pos, mouse_pos) <= self.RECENT_SWATCH_RADIUS:
                            rgb = self.recent_colors[i]
                            context["draw_color"] = rgb
                            context["current_hsv"] = rgb_to_hsv(*rgb)
                            self.add_recent_color(rgb)
                            break
                
                return True # Consume click inside modal

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1: 
            if self.is_dragging_wheel or self.is_dragging_bar:
                self.add_recent_color(context["draw_color"])
                self.is_dragging_wheel = False
                self.is_dragging_bar = False
                return True # Consume event
            
            # Consume mouseup if inside modal
            if self.modal_rect.collidepoint(mouse_pos):
                return True

        elif event.type == pygame.MOUSEMOTION:
            # [MODIFIED] Handle continuous dragging for both wheel and bar
            drag_mode = None
            if self.is_dragging_wheel:
                drag_mode = "wheel"
            elif self.is_dragging_bar:
                drag_mode = "bar"
            
            if drag_mode:
                hsv, rgb = update_color_from_pos(mouse_pos, context["current_hsv"], self.wheel_rect, self.value_bar_rect, drag_mode)
                context["current_hsv"] = hsv
                context["draw_color"] = rgb
                return True # Consume event
        
        # --- [NEW LOGIC] ---
        # Check for click *outside* modal to close it
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.modal_rect.collidepoint(mouse_pos):
                context["menu_open"] = None # Close menu
                self.is_dragging_wheel = False # Also stop dragging
                self.is_dragging_bar = False
                return False # Do not consume, allow click-through
        # --- [END NEW LOGIC] ---
        
        # Consume all *other* events (like mousemotion) if mouse is inside modal rect
        if self.modal_rect.collidepoint(mouse_pos):
             return True
        
        return False

    def update_button_pos(self, x, y):
        """Called by the host to update the button's position."""
        self.button.rect.topleft = (x, y)
        # [FIX] Re-center text/icon rects when moving
        if self.button.icon_surf:
            pass # Icon is centered in draw()
        else:
            self.button.text_rect.center = self.button.rect.center


    def draw(self, screen, context):
        """Draws the tool's button and the color picker pop-up."""
        
        # 1. Draw button
        menu_open = context.get("menu_open")
        is_active = (menu_open == self.name)
        if is_active:
            pygame.draw.rect(screen, (200, 200, 0), self.button.rect.inflate(4, 4))
        
        self.button.draw(screen) # Use button's own draw method
        
        # Draw small color cue
        draw_color = context.get("draw_color", (0,0,0))
        color_swatch_rect = pygame.Rect(0, 0, 15, 15)
        color_swatch_rect.topright = self.button.rect.topright
        color_swatch_rect.move_ip(-5, 5) # 5px margin
        pygame.draw.rect(screen, draw_color, color_swatch_rect)
        pygame.draw.rect(screen, (0,0,0), color_swatch_rect, 1) # border
        
        # 2. Draw pop-up
        if is_active:
            self._update_popup_rects(context) # Calculate positions
            
            h, s, v = context.get("current_hsv", (0,0,0))
            
            # Draw modal box
            pygame.draw.rect(screen, (220, 220, 220), self.modal_rect)
            pygame.draw.rect(screen, (0,0,0), self.modal_rect, 2)
            
            # --- Draw Wheel ---
            screen.blit(self.color_wheel_surface, self.wheel_rect)
            
            # --- Draw Value (Brightness) Bar ---
            base_color = hsv_to_rgb(h, s, 1.0) # Color at full brightness
            for i in range(self.BAR_HEIGHT):
                # [MODIFIED] Invert gradient. Top (i=0) is 1.0, Bottom is 0.0
                bar_v = 1.0 - (i / self.BAR_HEIGHT)
                bar_color = hsv_to_rgb(h, s, bar_v)
                pygame.draw.line(screen, bar_color, (self.value_bar_rect.x, self.value_bar_rect.y + i), (self.value_bar_rect.right, self.value_bar_rect.y + i))
            
            # --- Draw Indicators ---
            indicator_x = self.wheel_rect.centerx + (s * (self.WHEEL_SIZE / 2) * math.cos(h * 2 * math.pi))
            indicator_y = self.wheel_rect.centery + (s * (self.WHEEL_SIZE / 2) * math.sin(h * 2 * math.pi))
            pygame.draw.circle(screen, (0,0,0), (indicator_x, indicator_y), 7, 2)
            pygame.draw.circle(screen, (255,255,255), (indicator_x, indicator_y), 5, 2)
            
            # [MODIFIED] Invert indicator position.
            # When v=1.0 (light), (1.0 - v) is 0, so y is at the top.
            # When v=0.0 (dark), (1.0 - v) is 1.0, so y is at the bottom.
            # [FIX] Clamp indicator Y to be inside the bar
            indicator_y_relative = (1.0 - v) * self.BAR_HEIGHT
            indicator_y = self.value_bar_rect.y + indicator_y_relative
            indicator_y = max(self.value_bar_rect.y, min(indicator_y, self.value_bar_rect.bottom -1))
            
            pygame.draw.line(screen, (0,0,0), (self.value_bar_rect.left, indicator_y), (self.value_bar_rect.right, indicator_y), 4)
            pygame.draw.line(screen, (255,255,255), (self.value_bar_rect.left, indicator_y), (self.value_bar_rect.right, indicator_y), 2)
            
            # --- Draw Swatches and Text ---
            pygame.draw.rect(screen, draw_color, self.current_color_swatch_rect)
            pygame.draw.rect(screen, (0,0,0), self.current_color_swatch_rect, 1)

            rgb_text = f"RGB: {draw_color[0]}, {draw_color[1]}, {draw_color[2]}"
            hex_text = f"HEX: {rgb_to_hex(draw_color)}"
            rgb_surf = self.font.render(rgb_text, True, (0,0,0))
            hex_surf = self.font.render(hex_text, True, (0,0,0))
            screen.blit(rgb_surf, (self.current_color_swatch_rect.x + 10, self.current_color_swatch_rect.bottom + 10))
            screen.blit(hex_surf, (self.current_color_swatch_rect.x + 10, self.current_color_swatch_rect.bottom + 40))

            # Draw recent swatches
            for i, pos in enumerate(self.recent_swatches_pos):
                pygame.draw.circle(screen, self.recent_colors[i], pos, self.RECENT_SWATCH_RADIUS)
                pygame.draw.circle(screen, (0,0,0), pos, self.RECENT_SWATCH_RADIUS, 1)

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
        self.wheel_rect.topleft = (self.modal_rect.x + 20, self.modal_rect.y + 20)
        self.value_bar_rect.topleft = (self.wheel_rect.right + 20, self.wheel_rect.y)
        self.current_color_swatch_rect.topleft = (self.value_bar_rect.right + 20, self.wheel_rect.y)
        
        self.recent_swatches_pos = []
        for i in range(5):
            x = self.modal_rect.x + 30 + i * (self.RECENT_SWATCH_RADIUS * 2 + self.swatch_gap)
            y = self.wheel_rect.bottom + 35
            self.recent_swatches_pos.append((x, y))

