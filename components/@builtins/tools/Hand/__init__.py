import pygame
from libs.common.components import SolidButton
from typing import Any, Dict, Callable, Type

# Defines the HandTool for panning the canvas.
class HandTool:
    """
    A tool for panning (moving) the view of the canvas.
    It injects its ID to be recognized as the 'hand tool' by the canvas.
    """
    
    # Identifies this class as the hand tool provider.
    @classmethod
    def IS_HAND_TOOL(cls) -> bool:
        """Internal marker to identify this class as the hand tool."""
        return True

    # Injects this tool's registry ID into the canvas context.
    @classmethod
    def inject_hand_id(cls: Type['HandTool'], instance: 'HandTool', context: Dict[str, Any]) -> str:
        """
        Injection method to provide the tool's unique ID to the canvas.

        Args:
            instance: The instance of the HandTool.
            context: The shared canvas context (not used here).

        Returns:
            The registryId of this tool instance.
        """
        return instance.registryId

    # Dictionary of methods to be injected into the canvas system.
    INJECT_METHODS: Dict[str, Callable[..., Any]] = {
        'hand_tool_id': inject_hand_id
    }
    
    def __init__(self, rect: pygame.Rect, config: Dict[str, Any]):
        """
        Initializes the HandTool.

        Args:
            rect: The pygame.Rect defining the button's position and size.
            config: The configuration dictionary for this tool, containing name,
                    registryId, type, and icon path.
        """
        self.name: str = config['name']
        self.registryId: str = config["registryId"]
        self.config_type: str = config["type"]
        self.button: SolidButton = SolidButton(
            rect.x, rect.y, rect.width, rect.height,
            bg_color=(100,100,100), 
            font_size=20,
            icon_path=config["tool"]
        )
        # This tool does not draw on the canvas, so is_drawing_tool is False.
        self.is_drawing_tool: bool = False

    # Returns information for drawing a custom cursor.
    def get_cursor_draw_info(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provides information for drawing the cursor.
        This tool uses a custom cursor defined in its config.

        Args:
            context: The shared canvas context.

        Returns:
            A dictionary specifying the cursor type.
        """
        return {"type": "custom", "radius": 0, "color": None}

    # Handles user input events for the HandTool.
    def handle_event(self, event: pygame.event.Event, context: Dict[str, Any]) -> bool:
        """
        Processes pygame events for panning the canvas or activating the tool.

        Args:
            event: The pygame.event.Event to process.
            context: The shared canvas context for updating pan state.

        Returns:
            True if the event was handled by this tool, False otherwise.
        """
        # Event: Click on the tool's button in the toolbar.
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.button.rect.collidepoint(event.pos):
                context["active_tool_id"] = self.registryId
                context["menu_open"] = None
                return True  # Event handled

        # If this tool isn't active, don't process canvas events.
        if context.get("active_tool_id") != self.registryId:
            return False
            
        mouse_pos: tuple[int, int] = context.get("mouse_pos")
        
        # Event: Start panning (mouse button down on canvas).
        if event.type == pygame.MOUSEBUTTONDOWN and (event.button == 1 or event.button == 2):
            if not context["click_on_ui"]:
                context["is_panning"] = True
                context["pan_start_pos"] = mouse_pos
                context["pan_start_offset"] = context["pan_offset"]
                context["is_drawing"] = True # Use 'is_drawing' to signal an active canvas interaction
                return True # Event handled

        # Event: Stop panning (mouse button up).
        elif event.type == pygame.MOUSEBUTTONUP and (event.button == 1 or event.button == 2):
            if context.get("is_panning", False):
                context["is_panning"] = False
                context["is_drawing"] = False
                return True # Event handled

        # Event: Pan (mouse motion while panning).
        elif event.type == pygame.MOUSEMOTION:
            if context.get("is_panning", False):
                # Calculate the change in mouse position
                delta_x: int = mouse_pos[0] - context["pan_start_pos"][0]
                delta_y: int = mouse_pos[1] - context["pan_start_pos"][1]
                # Apply the delta to the starting offset to get the new pan offset
                context["pan_offset"] = (
                    context["pan_start_offset"][0] + delta_x,
                    context["pan_start_offset"][1] + delta_y
                )
                return True # Event handled
        
        return False # Event not handled by this tool

    # Updates the tool button's position.
    def update_button_pos(self, x: int, y: int) -> None:
        """
        Updates the position of the tool's button.

        Args:
            x: The new x-coordinate.
            y: The new y-coordinate.
        """
        self.button.rect.topleft = (x, y)
        if self.button.icon_surf:
            pass # Icon position is handled by the button's draw method
        else:
            # Re-center text if no icon
            self.button.text_rect.center = self.button.rect.center

    # Draws the HandTool button.
    def draw(self, screen: pygame.Surface, context: Dict[str, Any]) -> None:
        """
        Draws the tool's button on the screen.

        Args:
            screen: The pygame.Surface to draw on.
            context: The shared canvas context, used to check if this tool is active.
        """
        is_active: bool = context.get("active_tool_id") == self.registryId
        if is_active:
            # Draw a highlight rectangle if this tool is active
            pygame.draw.rect(screen, (200, 200, 0), self.button.rect.inflate(4, 4))
        
        self.button.draw(screen)