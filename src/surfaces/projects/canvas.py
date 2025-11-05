import pygame
from libs.common.components import SolidButton, SolidSlider
from libs.common.kits import components as load_kits
import math
import sys
import pickle
import os
from typing import Optional, Union, Any, List, Tuple, Dict, Callable, Type
from libs.utils.pylog import Logger

logger = Logger(__name__)

# --- tkinter Setup ---
# Attempts to import tkinter for file dialogs.
# If it fails, file operations (save/open/export) will be disabled.
try:
    import tkinter as tk
    from tkinter import filedialog
    
    # Helper function to create and configure a hidden, topmost tkinter root window.
    def get_tk_root() -> tk.Tk:
        """
        Creates a hidden tkinter root window, sets it to be 'topmost' 
        to appear over other windows (like pygame), and returns it.
        This is necessary for file dialogs to function correctly.
        
        Returns:
            tk.Tk: A configured, hidden root tkinter window.
        """
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        try:
            # Attempt to make the dialog window appear on top
            root.call('wm', 'attributes', '.', '-topmost', True)
        except Exception as e:
            logger.warning(f"Warning: Could not set topmost attribute for tkinter: {e}")
        return root
except ImportError:
    logger.warning("Warning: tkinter module not found. File dialogs will not work.")
    tk = None  # Flag that tkinter is not available

# --- Utility Functions ---

# Performs linear interpolation between two values.
def lerp(a: float, b: float, t: float) -> float:
    """
    Calculates the linear interpolation between 'a' and 'b' for a given factor 't'.
    
    Args:
        a: The start value.
        b: The end value.
        t: The interpolation factor (usually between 0.0 and 1.0).
        
    Returns:
        float: The interpolated value.
    """
    return a + (b - a) * t

# --- Global Constants ---

# World dimensions defines the total size of the drawing surface
WORLD_WIDTH: int = 8000
WORLD_HEIGHT: int = 6000

# Highlight colors for active tools
HIGHLIGHT_COLOR_DRAWING: Tuple[int, int, int] = (255, 200, 0) # For drawing tools
HIGHLIGHT_COLOR_CONTEXT: Tuple[int, int, int] = (160, 32, 240) # For context/utility tools

# UI layout constants
TOP_BAR_HEIGHT: int = 40
TOOLBAR_HEIGHT: int = 80
TOOLBAR_PADDING: int = 10
TOOLBAR_SLIDE_DISTANCE: int = 60 # How much of the toolbar remains visible when hidden

# History menu constants
HISTORY_MENU_WIDTH: int = 300
HISTORY_MENU_PADDING: int = 5
HISTORY_ITEM_HEIGHT: int = 25
MAX_VISIBLE_HISTORY_ITEMS: int = 10

toolbar_btn_size: int = 60
toolbar_btn_gap: int = 10

# --- Main Application Function ---

# The main function that runs the entire canvas application, including the game loop, event handling, and rendering.
def surface(screen: pygame.Surface, background: pygame.Surface, open_file_on_start: bool = False) -> None:
    """
    Main application function for the drawing canvas.

    Initializes the canvas state, loads tools, and runs the main event loop.
    Handles all rendering, UI interactions, file operations, and tool dispatching.

    Args:
        screen: The main pygame.Surface to draw on.
        background: (Currently unused) A background surface.
        open_file_on_start: If True, triggers an 'open file' dialog immediately on start.
    """
    running: bool = True
    clock: pygame.time.Clock = pygame.time.Clock()
    
    screen_width: int = screen.get_width()
    screen_height: int = screen.get_height()
    
    # --- Injection Placeholders ---
    # These lists hold references to methods injected by utility tools (e.g., camera tool).
    # They are in lists so the lambdas in _injection_targets can modify them by index.
    injected_screen_to_canvas: List[Optional[Callable[[Tuple[int, int]], Tuple[float, float]]]] = [None]
    injected_canvas_to_screen: List[Optional[Callable[[Tuple[float, float]], Tuple[float, float]]]] = [None]
    injected_set_zoom: List[Optional[Callable[[float, Tuple[int, int]], None]]] = [None]
    injected_apply_constraints: List[Optional[Callable[[], None]]] = [None] 
    hand_tool_id: List[Optional[str]] = [None] 
    
    first_drawing_tool_id: Optional[str] = None 
    
    history_scroll_offset: int = 0 

    # --- Tool Method Injection System ---
    # This dictionary maps method names to lambda functions.
    # These lambdas act as dispatchers, allowing utility tools (like a camera/pan tool) 
    # to "inject" their methods into the main canvas's state variables (e.g., `injected_set_zoom`).
    # This is a form of dependency injection to keep camera logic separate from the main canvas.
    _injection_targets: Dict[str, Callable[..., None]] = {
        'hand_tool_id': 
            lambda callable_method, ToolClass, tool_instance, context: 
                hand_tool_id.__setitem__(0, callable_method(ToolClass, tool_instance, context)),
        
        'set_zoom': 
            lambda callable_method, ToolClass, tool_instance, context: 
                injected_set_zoom.__setitem__(0, lambda new_zoom, pivot_pos: callable_method(ToolClass, tool_instance, context, new_zoom, pivot_pos)),
        
        'apply_constraints': 
            lambda callable_method, ToolClass, tool_instance, context: 
                injected_apply_constraints.__setitem__(0, lambda: callable_method(ToolClass, tool_instance, context, (WORLD_WIDTH, WORLD_HEIGHT))),

        'screen_to_canvas': 
            lambda callable_method, ToolClass, tool_instance, context: 
                injected_screen_to_canvas.__setitem__(0, lambda screen_pos: callable_method(ToolClass, tool_instance, context, screen_pos)),
        
        'canvas_to_screen': 
            lambda callable_method, ToolClass, tool_instance, context: 
                injected_canvas_to_screen.__setitem__(0, lambda canvas_pos: callable_method(ToolClass, tool_instance, context, canvas_pos))
    }

    # --- Dialog State ---
    current_project_path: Optional[str] = None
    is_dirty: bool = False # Flag for unsaved changes
    dialog_state: Optional[str] = None
    dialog_pending_action: Optional[str] = None
    dialog_rect: pygame.Rect = pygame.Rect(0, 0, 500, 200)
    dialog_rect.center = (screen_width // 2, screen_height // 2)
    dialog_buttons: List[Dict[str, Any]] = []
    
    # Fonts for the dialog
    dialog_font: pygame.font.Font
    dialog_title_font: pygame.font.Font
    try:
        dialog_font = pygame.font.Font("freesansbold.ttf", 24)
        dialog_title_font = pygame.font.Font("freesansbold.ttf", 28)
    except:
        dialog_font = pygame.font.Font(None, 24)
        dialog_title_font = pygame.font.Font(None, 28)

    # --- UI Element Initialization ---
    top_bar_rect: pygame.Rect = pygame.Rect(0, 0, screen_width, TOP_BAR_HEIGHT)
    toolbar_visible_y: int = screen_height - TOOLBAR_HEIGHT
    toolbar_hidden_y: int = screen_height - TOOLBAR_SLIDE_DISTANCE
    toolbar_rect: pygame.Rect = pygame.Rect(0, toolbar_visible_y, screen_width, TOOLBAR_HEIGHT)

    FILE_BTN_WIDTH: int = 100
    HISTORY_BTN_WIDTH: int = 100
    
    # Menu colors
    MENU_BG_COLOR: Tuple[int, int, int] = (200, 200, 200)
    MENU_ACTIVE_BG_COLOR: Tuple[int, int, int] = (225, 225, 225)
    MENU_DROPDOWN_BG_COLOR: Tuple[int, int, int] = (220, 220, 220)
    MENU_HOVER_BG_COLOR: Tuple[int, int, int] = (200, 220, 255)
    MENU_SELECTED_BG_COLOR: Tuple[int, int, int] = (180, 180, 180)
    MENU_TEXT_COLOR: Tuple[int, int, int] = (0, 0, 0)
    MENU_TEXT_COLOR_MUTED: Tuple[int, int, int] = (150, 150, 150)
    MENU_BORDER_COLOR: Tuple[int, int, int] = (150, 150, 150)
    
    # Top bar buttons
    file_btn: SolidButton = SolidButton(
        0, 0, FILE_BTN_WIDTH, TOP_BAR_HEIGHT, "File",
        font_size=20, bg_color=MENU_BG_COLOR, text_color=MENU_TEXT_COLOR, 
        border_width=0, border_color=None
    )
    history_btn: SolidButton = SolidButton(
        file_btn.rect.right, 0, HISTORY_BTN_WIDTH, TOP_BAR_HEIGHT, "History", 
        font_size=20, bg_color=MENU_BG_COLOR, text_color=MENU_TEXT_COLOR, 
        border_width=0, border_color=None
    )
    
    # History menu layout
    history_menu_height: int = (HISTORY_ITEM_HEIGHT * MAX_VISIBLE_HISTORY_ITEMS) + (HISTORY_MENU_PADDING * 2)
    history_placeholder_rect: pygame.Rect = pygame.Rect(
        history_btn.rect.left,
        top_bar_rect.bottom,
        HISTORY_MENU_WIDTH, 
        history_menu_height
    )
    
    # Hot zones define areas where clicking won't close the menu
    file_menu_hot_zone: List[pygame.Rect] = [file_btn.rect]
    history_menu_hot_zone: List[pygame.Rect] = [history_btn.rect, history_placeholder_rect]

    # History item font
    history_font: pygame.font.Font
    try:
        history_font = pygame.font.Font("freesansbold.ttf", 20)
    except:
        history_font = pygame.font.Font(None, 20)

    # --- Canvas & History State ---
    shared_tool_context: Dict[str, Any]
    drawing_surface: pygame.Surface
    history: List[Tuple[pygame.Surface, str]]
    history_index: int

    # --- Nested Helper Functions ---

    # Manages the state of the confirmation dialog (e.g., for unsaved changes).
    def set_dialog(state: Optional[str], pending_action: Optional[str] = None) -> None:
        """
        Sets the state of the modal dialog.

        Args:
            state: The type of dialog to show (e.g., "confirm_action") or None to hide.
            pending_action: The action to perform if the user confirms (e.g., "new_canvas", "exit").
        """
        nonlocal dialog_state, dialog_pending_action, dialog_buttons
        dialog_state = state
        dialog_pending_action = pending_action
        
        # Configure buttons for the 'confirm_action' dialog
        if state == "confirm_action":
            btn_w, btn_h, btn_gap = 140, 40, 10
            
            save_btn = SolidButton(0, 0, btn_w, btn_h, "Save", font_size=20, bg_color=(0, 150, 0), text_color=(255, 255, 255))
            dont_save_btn = SolidButton(0, 0, btn_w, btn_h, "Don't Save", font_size=20, bg_color=(150, 150, 150), text_color=(0, 0, 0))
            cancel_btn = SolidButton(0, 0, btn_w, btn_h, "Cancel", font_size=20, bg_color=(200, 0, 0), text_color=(255, 255, 255))
            
            total_w: int = btn_w * 3 + btn_gap * 2
            start_x: int = dialog_rect.centerx - total_w // 2
            btn_y: int = dialog_rect.bottom - btn_h - 20
            
            save_btn.rect.topleft = (start_x, btn_y)
            dont_save_btn.rect.topleft = (start_x + btn_w + btn_gap, btn_y)
            cancel_btn.rect.topleft = (start_x + btn_w * 2 + btn_gap * 2, btn_y)
            
            dialog_buttons = [
                {"name": "save", "btn": save_btn},
                {"name": "dont_save", "btn": dont_save_btn},
                {"name": "cancel", "btn": cancel_btn},
            ]

    # Jumps to a specific state in the undo/redo history.
    def set_history_state(index: int) -> None:
        """
        Sets the canvas to a specific state from the history buffer.

        Args:
            index: The index in the `history` list to load.
        """
        nonlocal history_index, is_dirty, drawing_surface, shared_tool_context
        
        history_index = index
        # Load a copy of the surface from history
        shared_tool_context["drawing_surface"] = history[history_index][0].copy()
        drawing_surface = shared_tool_context["drawing_surface"]
        is_dirty = True # Changing history state counts as an unsaved change
        
    # Adds the current canvas state as a new entry in the history buffer.
    def add_history(action_name: str) -> None:
        """
        Saves the current state of `drawing_surface` to the history list.
        This is called after a drawing action is completed.

        Args:
            action_name: A descriptive name for the action (e.g., "Draw Line").
        """
        nonlocal history, history_index, is_dirty, drawing_surface, history_scroll_offset
        
        # If we undid and then drew, clear the "redo" future
        if history_index < len(history) - 1:
            history = history[:history_index + 1]
            
        # Limit history size
        if len(history) >= MAX_HISTORY_SIZE:
            history.pop(0)
            
        # Add a copy of the current surface
        history.append((drawing_surface.copy(), action_name))
        history_index = len(history) - 1
        is_dirty = True
        
        # Auto-scroll history menu to the bottom
        max_scroll: int = max(0, len(history) - MAX_VISIBLE_HISTORY_ITEMS)
        history_scroll_offset = max_scroll
        
    # Reverts to the previous state in the history.
    def undo() -> None:
        """Moves the `history_index` back by one and loads that state."""
        nonlocal history_index, is_dirty, drawing_surface
        if history_index > 0:
            set_history_state(history_index - 1)

    # Moves to the next state in the history (if an undo was performed).
    def redo() -> None:
        """Moves the `history_index` forward by one and loads that state."""
        nonlocal history_index, is_dirty, drawing_surface
        if history_index < len(history) - 1:
            set_history_state(history_index + 1)

    # Resets the canvas to a blank state and clears the history.
    def clear_canvas() -> None:
        """
        Fills the `drawing_surface` with white, resets the history list, 
        and sets the project path to None.
        """
        nonlocal is_dirty, current_project_path, history, history_index, drawing_surface, shared_tool_context
        drawing_surface.fill("White")
        history = []
        add_history("Initial") # Add the blank state as the first history item
        is_dirty = False
        current_project_path = None
        # Reset camera zoom/pan
        if injected_set_zoom[0]:
            injected_set_zoom[0](shared_tool_context["zoom_level"], (screen_width // 2, screen_height // 2))

    # Saves the current canvas state to the `current_project_path` using pickle.
    def save_vecbo() -> bool:
        """
        Saves the current canvas to the file specified by `current_project_path`.
        If no path is set, it calls `save_as_vecbo()`.
        The canvas is saved as a pickled dictionary.

        Returns:
            True if saving was successful, False otherwise.
        """
        nonlocal is_dirty, current_project_path
        if not current_project_path:
            return save_as_vecbo()
        
        if tk is None: 
            logger.warning("Cannot save: tkinter not available.")
            return False

        try:
            # Prepare data for pickling
            data: Dict[str, Any] = {
                "version": 1,
                "drawing_surface": pygame.image.tostring(drawing_surface, 'RGBA'),
                "size": (WORLD_WIDTH, WORLD_HEIGHT)
            }
            with open(current_project_path, 'wb') as f:
                pickle.dump(data, f)
            is_dirty = False
            logger.info(f"Project saved to {current_project_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return False

    # Opens a "Save As" dialog to get a new file path and then saves to it.
    def save_as_vecbo() -> bool:
        """
        Uses a tkinter file dialog to ask the user for a save location.
        If a path is chosen, it sets `current_project_path` and calls `save_vecbo()`.

        Returns:
            True if saving was successful, False otherwise.
        """
        nonlocal is_dirty, current_project_path
        if tk is None: 
            logger.warning("Cannot save: tkinter not available.")
            return False

        root = get_tk_root()
        file_path: Optional[str] = filedialog.asksaveasfilename(
            defaultextension=".vecbo",
            filetypes=[("DrawingGuess Vector Board", "*.vecbo")],
            title="Save Project As"
        )
        root.destroy()
        
        if file_path:
            current_project_path = file_path
            return save_vecbo()
        return False
        
    # Opens an "Open" dialog to load a `.vecbo` file.
    def open_file() -> bool:
        """
        Uses a tkinter file dialog to ask the user for a file to open.
        If a file is chosen, it loads the pickled data, updates the
        `drawing_surface`, and resets the history.

        Returns:
            True if loading was successful, False otherwise.
        """
        nonlocal is_dirty, current_project_path, history, history_index, drawing_surface, shared_tool_context
        if tk is None: 
            logger.warning("Cannot open: tkinter not available.")
            return False

        root = get_tk_root()
        file_path: Optional[str] = filedialog.askopenfilename(
            defaultextension=".vecbo",
            filetypes=[("DrawingGuess Vector Board", "*.vecbo")],
            title="Open Project"
        )
        root.destroy()
        
        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    data: Dict[str, Any] = pickle.load(f)
                
                # Reconstruct the surface from pickled data
                surface_data: bytes = data["drawing_surface"]
                surf_size: Tuple[int, int] = data["size"]
                new_surf: pygame.Surface = pygame.image.fromstring(surface_data, surf_size, 'RGBA')

                # Update main state
                shared_tool_context["drawing_surface"] = new_surf
                drawing_surface = new_surf
                current_project_path = file_path
                is_dirty = False
                
                # Reset history with the loaded file
                history = [(drawing_surface.copy(), f"Opened: {os.path.basename(file_path)}")]
                history_index = 0
                
                # Reset camera
                if injected_set_zoom[0]:
                    injected_set_zoom[0](shared_tool_context["zoom_level"], (screen_width // 2, screen_height // 2))

                logger.info(f"Project loaded from {file_path}")
                return True
            except Exception as e:
                logger.error(f"Error opening file: {e}")
                return False
        return False

    # Opens a "Save As" dialog to export the canvas as a `.png` or `.jpg`.
    def export_as_image() -> bool:
        """
        Uses a tkinter file dialog to ask the user for a save location
        to export the canvas as a PNG or JPEG image.

        Returns:
            True if exporting was successful, False otherwise.
        """
        nonlocal is_dirty, current_project_path
        if tk is None: 
            logger.warning("Cannot export: tkinter not available.")
            return False

        root = get_tk_root()
        file_path: Optional[str] = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg;*.jpeg")],
            title="Export Canvas as Image"
        )
        root.destroy()
        
        if file_path:
            try:
                pygame.image.save(drawing_surface, file_path)
                logger.info(f"Canvas exported to {file_path}")
                return True
            except Exception as e:
                logger.error(f"Error exporting image: {e}")
                return False
        return False

    # --- Initial State Setup ---
    
    # Calculate initial pan offset to center the world
    initial_offset_x: float = (screen_width - WORLD_WIDTH) / 2
    initial_offset_y: float = (screen_height - WORLD_HEIGHT) / 2

    # The shared context dictionary passed to all tools
    shared_tool_context = {
        "screen": screen,
        "draw_color": (0, 0, 0),
        "current_hsv": (0.0, 0.0, 0.0),
        "draw_size": 5,
        "eraser_size": 50,
        "active_tool_id": "none",
        "is_drawing": False,
        "menu_open": None,
        "click_on_ui": False,
        "mouse_pos": (0,0),
        "toolbar_current_y": toolbar_rect.y,
        "drawing_surface": None, # Will be set below
        "add_history": add_history, 
        "zoom_level": 1.0,  
        "pan_offset": (initial_offset_x, initial_offset_y), 
        "canvas_mouse_pos": (0, 0), # Mouse position relative to the canvas
        "is_panning": False,
        "pan_start_pos": (0, 0),
        "pan_start_offset": (0, 0),
        "previous_tool_id": "none" # Used for the spacebar-pan functionality
    }
    
    # Create the main drawing surface
    drawing_surface = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))
    drawing_surface.fill("White")
    shared_tool_context["drawing_surface"] = drawing_surface
    
    # Initialize history
    history = [(drawing_surface.copy(), "Initial")]
    history_index = 0
    MAX_HISTORY_SIZE: int = 30
    
    # --- Tool Loading ---
    
    loaded_tool_plugins: List[Tuple[Dict[str, Any], Type]] = load_kits()
    tool_id_to_instance: Dict[str, Any] = {} 
    loaded_tool_instances: List[Any] = [] # Drawing/context tools
    utility_tools_to_draw: List[Any] = [] # Utility tools (e.g., camera)
    utility_tools_to_update_pos: List[Any] = []
    
    toolbar_btn_x: int = TOOLBAR_PADDING
    zoom_slider_x_start: int = 0 
    
    # Instantiate all tools
    for config, ToolClass in loaded_tool_plugins:
        btn_rect = pygame.Rect(toolbar_btn_x, toolbar_hidden_y + 10, toolbar_btn_size, toolbar_btn_size)
        tool_instance = ToolClass(btn_rect, config)
        tool_instance.config = config

        tool_id_to_instance[tool_instance.registryId] = tool_instance

        if tool_instance.config.get('type') == "utility_tool": 
            utility_tools_to_draw.append(tool_instance)
            utility_tools_to_update_pos.append(tool_instance)
            
            # Check if this tool needs to inject methods
            if hasattr(ToolClass, 'INJECT_METHODS'):
                for name, injected_method in config.get("injected_methods", {}).items():
                    callable_method: Callable[..., Any] = getattr(injected_method, '__func__', injected_method)
                    dispatch_func: Optional[Callable[..., None]] = _injection_targets.get(name)
                    
                    if dispatch_func:
                        # Call the lambda dispatcher to store the tool's method
                        dispatch_func(callable_method, ToolClass, tool_instance, shared_tool_context)
            
        else:
            # This is a standard drawing/context tool
            loaded_tool_instances.append(tool_instance)
            toolbar_btn_x += toolbar_btn_size + toolbar_btn_gap
            
            # Find the first drawing tool to make active by default
            if first_drawing_tool_id is None and tool_instance.config.get('type') == 'drawing_tool':
                 first_drawing_tool_id = tool_instance.registryId
            
    zoom_slider_x_start = toolbar_btn_x + 10 
    
    # --- Injection Validation ---
    # Critical check: ensure a utility tool provided all necessary camera/coord functions
    if injected_screen_to_canvas[0] is None or injected_canvas_to_screen[0] is None or injected_set_zoom[0] is None or injected_apply_constraints[0] is None:
        raise RuntimeError("FATAL ERROR: Essential Canvas Systems (Coordinate Math, Camera Control) failed to inject. A utility tool must provide ALL of these functions.")
    
    # --- Cursor Loading ---
    logger.info("Loading custom cursors...")
    for tool in loaded_tool_instances:
        tool.custom_cursor_surf = None
        tool.custom_cursor_hotspot = (0, 0)
        tool.custom_cursor_offset = (0, 0)
        
        cursor_config: Dict[str, Any] = tool.config.get("cursor", {})
        if not cursor_config:
            continue
            
        cursor_path: Optional[str] = cursor_config.get("icon")
        
        if cursor_path:
            try:
                cursor_surf: pygame.Surface = pygame.image.load(cursor_path).convert_alpha()
                cursor_size: Optional[List[int]] = cursor_config.get("size")
                
                # Auto-resize large cursors
                if not cursor_size:
                    if cursor_surf.get_width() > 64 or cursor_surf.get_height() > 64:
                        cursor_size = (64, 64) 
                
                if cursor_size:
                    try:
                        cursor_surf = pygame.transform.smoothscale(cursor_surf, cursor_size)
                    except: 
                        cursor_surf = pygame.transform.scale(cursor_surf, cursor_size)

                # Configure cursor hotspot
                hotspot_config: Any = cursor_config.get("hotspot")
                hotspot: Tuple[int, int] = (0, 0)
                if hotspot_config == "center":
                    hotspot = (cursor_surf.get_width() // 2, cursor_surf.get_height() // 2)
                elif isinstance(hotspot_config, (list, tuple)) and len(hotspot_config) == 2:
                    hotspot = (hotspot_config[0], hotspot_config[1])
                
                tool.custom_cursor_surf = cursor_surf
                tool.custom_cursor_hotspot = hotspot
                tool.custom_cursor_offset = cursor_config.get("offset", (0, 0)) 
                logger.info(f"  Successfully loaded cursor surface for: {tool.name}")
            except Exception as e:
                logger.warning(f"Warning: Could not load cursor surface for {tool.name} at {cursor_path}: {e}")
                
    # Set default active tool
    if first_drawing_tool_id:
         shared_tool_context["active_tool_id"] = first_drawing_tool_id
         shared_tool_context["previous_tool_id"] = first_drawing_tool_id

    # Timer event to trigger 'open_file' after initialization
    if open_file_on_start:
        pygame.time.set_timer(pygame.USEREVENT + 1, 100, 1) # Post event once after 100ms

    # =================================================================================
    # --- MAIN GAME LOOP ---
    # =================================================================================
    while running:
        mouse_pos: Tuple[int, int] = pygame.mouse.get_pos()
        events: List[pygame.event.Event] = pygame.event.get()
        
        shared_tool_context["mouse_pos"] = mouse_pos
        
        # Assume no UI is clicked at the start of the frame
        shared_tool_context["click_on_ui"] = False
        
        # --- Dialog Event Handling ---
        # If a dialog is open, it consumes all events
        if dialog_state is not None:
            for event in events[:]: # Iterate over a copy
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    action_taken: Optional[str] = None
                    for item in dialog_buttons:
                        if item["btn"].is_clicked(event):
                            action_taken = item["name"]
                            break
                    
                    if action_taken:
                        if action_taken == "cancel":
                            dialog_state = None
                            dialog_pending_action = None
                        
                        elif action_taken == "dont_save":
                            # Perform the pending action without saving
                            dialog_state = None
                            if dialog_pending_action == "new_canvas": clear_canvas()
                            elif dialog_pending_action == "open_file": open_file()
                            elif dialog_pending_action == "exit": running = False
                        
                        elif action_taken == "save":
                            # Try to save, and if successful, perform the pending action
                            if current_project_path: save_vecbo()
                            else: save_as_vecbo()
                            if not is_dirty: # Check if save was successful
                                dialog_state = None
                                if dialog_pending_action == "new_canvas": clear_canvas()
                                elif dialog_pending_action == "open_file": open_file()
                                elif dialog_pending_action == "exit": running = False

                        elif action_taken == "export":
                            export_as_image()
                    
                    shared_tool_context["click_on_ui"] = True
                    events.remove(event)
            
            # Consume all other events
            for event in events[:]: events.remove(event)
            shared_tool_context["click_on_ui"] = True

        # --- Normal Event Handling (No Dialog) ---
        if not dialog_state: 
            for event in events[:]: # Iterate over a copy
                
                # Handle custom event for 'open_file_on_start'
                if event.type == pygame.USEREVENT + 1:
                    open_file()
                    pygame.time.set_timer(pygame.USEREVENT + 1, 0) # Stop timer
                    continue

                # Handle window close
                if event.type == pygame.QUIT:
                    if is_dirty:
                        set_dialog("confirm_action", "exit")
                        shared_tool_context["click_on_ui"] = True
                    else:
                        running = False
                
                # If a previous handler consumed the event, skip
                if shared_tool_context["click_on_ui"]:
                    if event in events: events.remove(event)
                    continue

                # --- Mouse Wheel Handling (History Scroll / UI) ---
                if event.type == pygame.MOUSEWHEEL:
                    # Scroll history menu
                    if shared_tool_context["menu_open"] == "history" and history_placeholder_rect.collidepoint(mouse_pos):
                        if event.y > 0: history_scroll_offset = max(0, history_scroll_offset - 1)
                        elif event.y < 0:
                            max_scroll = max(0, len(history) - MAX_VISIBLE_HISTORY_ITEMS)
                            history_scroll_offset = min(max_scroll, history_scroll_offset + 1)
                        shared_tool_context["click_on_ui"] = True 
                    
                    # Consume scroll wheel events over UI bars
                    elif (top_bar_rect.collidepoint(mouse_pos) or 
                          toolbar_rect.collidepoint(mouse_pos)):
                        shared_tool_context["click_on_ui"] = True
                    
                if shared_tool_context["click_on_ui"]:
                    if event in events: events.remove(event)
                    continue

                # --- Utility Tool Event Handling ---
                # Give utility tools (like camera) first priority
                for tool in utility_tools_to_draw:
                    if tool.handle_event(event, shared_tool_context):
                        shared_tool_context["click_on_ui"] = True
                        break
                
                if shared_tool_context["click_on_ui"]:
                    if event in events: events.remove(event)
                    continue
                
                # --- Menu Mouseover Switching ---
                if event.type == pygame.MOUSEMOTION:
                    if shared_tool_context["menu_open"] is not None:
                        # Switch between File and History by hovering
                        if file_btn.rect.collidepoint(mouse_pos) and shared_tool_context["menu_open"] != "file":
                            shared_tool_context["menu_open"] = "file"
                            shared_tool_context["click_on_ui"] = True
                        elif history_btn.rect.collidepoint(mouse_pos) and shared_tool_context["menu_open"] != "history":
                            shared_tool_context["menu_open"] = "history"
                            shared_tool_context["click_on_ui"] = True
                
                if shared_tool_context["click_on_ui"]:
                    if event in events: events.remove(event)
                    continue
                
                # --- Keyboard Shortcuts ---
                if event.type == pygame.KEYDOWN:
                    mods: int = pygame.key.get_mods()
                    is_ctrl_or_cmd: bool = bool(mods & pygame.KMOD_CTRL or mods & pygame.KMOD_META)
                    is_shift: bool = bool(mods & pygame.KMOD_SHIFT)
                    
                    active_tool_id: Optional[str] = shared_tool_context["active_tool_id"]
                    
                    # Spacebar: Hold to pan
                    if hand_tool_id[0] and event.key == pygame.K_SPACE:
                        if active_tool_id != hand_tool_id[0]:
                            shared_tool_context["previous_tool_id"] = active_tool_id
                            shared_tool_context["active_tool_id"] = hand_tool_id[0]
                            shared_tool_context["click_on_ui"] = True
                    
                    # Ctrl/Cmd+Z: Undo
                    elif event.key == pygame.K_z:
                        if is_ctrl_or_cmd:
                            if is_shift: redo() # Ctrl/Cmd+Shift+Z: Redo
                            else: undo()
                    # Ctrl/Cmd+Y: Redo
                    elif event.key == pygame.K_y:
                        if is_ctrl_or_cmd and not is_shift: redo()
                    
                    # Shift+E: Export
                    elif event.key == pygame.K_e and is_shift:
                        export_as_image()
                    
                if event.type == pygame.KEYUP:
                    active_tool_id = shared_tool_context["active_tool_id"]

                    # Spacebar: Release to return to previous tool
                    if hand_tool_id[0] and event.key == pygame.K_SPACE:
                        if active_tool_id == hand_tool_id[0]:
                            shared_tool_context["active_tool_id"] = shared_tool_context["previous_tool_id"]
                            shared_tool_context["is_panning"] = False
                        shared_tool_context["click_on_ui"] = True
                
                if shared_tool_context["click_on_ui"]:
                    if event in events: events.remove(event)
                    continue

                # --- Mouse Button Down Handling ---
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    
                    # --- Top Bar Button Clicks ---
                    if file_btn.is_clicked(event):
                        shared_tool_context["menu_open"] = "file" if shared_tool_context["menu_open"] != "file" else None
                        shared_tool_context["click_on_ui"] = True
                    elif history_btn.is_clicked(event):
                        shared_tool_context["menu_open"] = "history" if shared_tool_context["menu_open"] != "history" else None
                        shared_tool_context["click_on_ui"] = True
                    
                    if shared_tool_context["click_on_ui"]:
                        if event in events: events.remove(event)
                        continue
                            
                    # --- File Menu Clicks ---
                    elif shared_tool_context["menu_open"] == "file":
                        # This section dynamically creates buttons for hit-testing
                        # The actual rendering happens in the rendering section
                        file_menu_buttons: List[SolidButton] = []
                        file_menu_hot_zone = [file_btn.rect]
                        btn_y: int = file_btn.rect.bottom
                        btn_w: int = 300
                        btn_h: int = 40
                        
                        # Local helper function to create and track buttons for the "File" dropdown menu.
                        def add_file_btn(text: str) -> None:
                            nonlocal btn_y
                            btn: SolidButton = SolidButton(
                                file_btn.rect.left, btn_y, btn_w, btn_h, text, 
                                bg_color=MENU_DROPDOWN_BG_COLOR, text_color=MENU_TEXT_COLOR,
                                font_size=20, text_align="left", 
                                border_width=1, border_color=MENU_BORDER_COLOR
                            )
                            file_menu_buttons.append(btn)
                            file_menu_hot_zone.append(btn.rect)
                            btn_y += btn_h
                        
                        add_file_btn("New Whiteboard")
                        add_file_btn("Open From...")
                        if current_project_path:
                            add_file_btn("Save")
                        add_file_btn("Save as... (.vecbo)")
                        add_file_btn("Export as... (.png)")
                        add_file_btn("Back to Main Menu")
                        
                        # Check for clicks on the dynamically created buttons
                        for btn in file_menu_buttons:
                            if btn.rect.collidepoint(mouse_pos):
                                if btn.text == "New Whiteboard":
                                    if is_dirty: set_dialog("confirm_action", "new_canvas")
                                    else: clear_canvas()
                                elif btn.text == "Open From...":
                                    if is_dirty: set_dialog("confirm_action", "open_file")
                                    else: open_file()
                                elif btn.text == "Save":
                                    save_vecbo()
                                elif btn.text == "Save as... (.vecbo)":
                                    save_as_vecbo()
                                elif btn.text == "Export as... (.png)":
                                    export_as_image()
                                elif btn.text == "Back to Main Menu": 
                                    if is_dirty: set_dialog("confirm_action", "exit")
                                    else: running = False
                                
                                shared_tool_context["menu_open"] = None 
                                shared_tool_context["click_on_ui"] = True
                                break
                        # If clicked inside menu but not on a button, still count as UI click
                        if not shared_tool_context["click_on_ui"] and any(rect.collidepoint(mouse_pos) for rect in file_menu_hot_zone):
                             shared_tool_context["click_on_ui"] = True
                        if shared_tool_context["click_on_ui"]:
                            if event in events: events.remove(event)
                            continue
                    
                    # --- History Menu Clicks ---
                    elif shared_tool_context["menu_open"] == "history":
                        if history_placeholder_rect.collidepoint(mouse_pos):
                            shared_tool_context["click_on_ui"] = True
                            
                            clip_rect: pygame.Rect = history_placeholder_rect.inflate(-4, -HISTORY_MENU_PADDING * 2)
                            item_y_start: int = clip_rect.y
                            visible_items_indices: range = range(history_scroll_offset, history_scroll_offset + MAX_VISIBLE_HISTORY_ITEMS)
                            
                            # Check for click on each visible history item
                            for i, history_i in enumerate(visible_items_indices):
                                if history_i >= len(history): break
                                
                                item_rect: pygame.Rect = pygame.Rect(clip_rect.x, item_y_start + (i * HISTORY_ITEM_HEIGHT), clip_rect.width, HISTORY_ITEM_HEIGHT)
                                if item_rect.collidepoint(mouse_pos) and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                                    
                                    set_history_state(history_i)
                                    
                                    shared_tool_context["menu_open"] = None
                                    break

                # --- Tool-Specific Menu Handling ---
                # e.g., Color picker, size slider
                tool_menu_is_open: bool = False
                menu_open_id: Optional[str] = shared_tool_context["menu_open"]
                
                if menu_open_id in tool_id_to_instance:
                    tool = tool_id_to_instance[menu_open_id]
                    tool_menu_is_open = True
                    if tool.handle_event(event, shared_tool_context):
                        shared_tool_context["click_on_ui"] = True
                
                if tool_menu_is_open:
                    if event in events: events.remove(event)
                    continue 
                
                # --- Toolbar Button Clicks ---
                tool_button_was_clicked: bool = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for tool in loaded_tool_instances: 
                        if hasattr(tool, 'button') and tool.button.rect.collidepoint(event.pos):
                            if tool.handle_event(event, shared_tool_context):
                                shared_tool_context["click_on_ui"] = True
                                tool_button_was_clicked = True
                            break
                
                if tool_button_was_clicked:
                    if event in events: events.remove(event)
                    continue
                
                # --- Click-off-Menu Handling ---
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    menu: Optional[str] = shared_tool_context["menu_open"]
                    
                    if menu == "file" or menu == "history":
                        hot_zone: List[pygame.Rect] = file_menu_hot_zone if menu == "file" else history_menu_hot_zone
                        is_on_hotzone: bool = False
                        for rect in hot_zone:
                            if rect.collidepoint(mouse_pos):
                                is_on_hotzone = True
                                break
                        # If clicked outside the menu's "hot zone", close it
                        if not is_on_hotzone:
                            shared_tool_context["menu_open"] = None
                            shared_tool_context["click_on_ui"] = True
                
                if shared_tool_context["click_on_ui"]:
                    if event in events: events.remove(event)
                    continue 

                # --- Active Tool Event Handling ---
                # If no UI was clicked, pass the event to the active tool
                if event not in events:
                    continue

                active_tool_instance: Optional[Any] = tool_id_to_instance.get(shared_tool_context.get("active_tool_id"))
                
                if active_tool_instance:
                    is_space_up: bool = (event.type == pygame.KEYUP and event.key == pygame.K_SPACE)

                    # Don't pass space-up event to the tool
                    if not is_space_up:
                        if active_tool_instance.handle_event(event, shared_tool_context):
                            if event in events: events.remove(event)
                
                if shared_tool_context["click_on_ui"]:
                    if event in events: events.remove(event)
                    continue
            
        # =================================================================================
        # --- STATE UPDATES ---
        # =================================================================================
        
        # --- Re-create File Menu (for rendering and click-off logic) ---
        file_menu_buttons = []
        file_menu_hot_zone = [file_btn.rect]
        if shared_tool_context["menu_open"] == "file":
            btn_y = file_btn.rect.bottom
            btn_w = 300
            btn_h = 40
            
            # Local helper function to create buttons for *rendering* the "File" dropdown menu.
            def add_file_btn_render(text: str) -> None:
                nonlocal btn_y
                btn = SolidButton(
                    file_btn.rect.left, btn_y, btn_w, btn_h, text, 
                    bg_color=MENU_DROPDOWN_BG_COLOR, text_color=(0,0,0),
                    font_size=20, text_align="left", 
                    border_width=1, border_color=(150, 150, 150)
                )
                file_menu_buttons.append(btn)
                file_menu_hot_zone.append(btn.rect)
                btn_y += btn_h
            
            add_file_btn_render("New Whiteboard")
            add_file_btn_render("Open From...")
            if current_project_path:
                add_file_btn_render("Save")
            add_file_btn_render("Save as... (.vecbo)")
            add_file_btn_render("Export as... (.png)")
            add_file_btn_render("Back to Main Menu")

        # --- Click-off-Menu Logic (Frame-based) ---
        # This handles clicks that were not processed in the event loop
        menu = shared_tool_context["menu_open"]
        if menu == "file" or menu == "history":
            hot_zone = file_menu_hot_zone if menu == "file" else history_menu_hot_zone
            is_on_hotzone = False
            for rect in hot_zone:
                if rect.collidepoint(mouse_pos):
                    is_on_hotzone = True
                    break
            if not is_on_hotzone:
                # If mouse is not in the hot zone, a click would have closed it.
                # Since no click is registered here, we just check position.
                # The actual click handling is in the event loop.
                pass
        
        # --- Toolbar Sliding Logic ---
        is_drawing: bool = shared_tool_context["is_drawing"]
        toolbar_target_y: int

        if shared_tool_context["menu_open"] is not None or dialog_state is not None:
            toolbar_target_y = toolbar_visible_y # Keep visible if menu or dialog is open
        elif is_drawing:
            toolbar_target_y = toolbar_hidden_y # Hide when drawing
        else:
            # Show if mouse is near bottom or over the toolbar
            if mouse_pos[1] > screen_height - 20 or toolbar_rect.collidepoint(mouse_pos):
                toolbar_target_y = toolbar_visible_y
            else:
                toolbar_target_y = toolbar_hidden_y
            
        # Lerp for smooth animation
        toolbar_current_y: float = lerp(toolbar_rect.y, toolbar_target_y, 0.2)
        toolbar_rect.y = round(toolbar_current_y)
        shared_tool_context["toolbar_current_y"] = toolbar_rect.y
        
        # Update tool button positions based on toolbar's animated Y
        for tool in loaded_tool_instances:
            if hasattr(tool, 'button'): 
                tool.update_button_pos(tool.button.rect.x, toolbar_rect.y + 10)
        
        for tool in utility_tools_to_update_pos:
            tool.update_button_pos(zoom_slider_x_start, toolbar_rect.y + 25)

        # --- Apply Camera Constraints ---
        # (e.g., prevent panning too far)
        if injected_apply_constraints[0]:
            injected_apply_constraints[0]()

        # =================================================================================
        # --- DRAWING / RENDERING ---
        # =================================================================================
        
        # Fill background
        screen.fill((80, 80, 80)) 
        
        # --- Draw Canvas ---
        if injected_screen_to_canvas[0] and injected_canvas_to_screen[0]:
            
            # Find the visible portion of the canvas
            canvas_tl_x: float
            canvas_tl_y: float
            canvas_br_x: float
            canvas_br_y: float
            canvas_tl_x, canvas_tl_y = injected_screen_to_canvas[0]((0, 0))
            canvas_br_x, canvas_br_y = injected_screen_to_canvas[0]((screen_width, screen_height))
            
            canvas_rect_w: float = canvas_br_x - canvas_tl_x
            canvas_rect_h: float = canvas_br_y - canvas_tl_y
            
            # Clip the visible rect to the bounds of the drawing surface
            visible_canvas_rect: pygame.Rect = pygame.Rect(
                canvas_tl_x, 
                canvas_tl_y,
                canvas_rect_w,
                canvas_rect_h
            ).clip(drawing_surface.get_rect())
            
            # Only draw if the visible area is valid
            if visible_canvas_rect.width > 0 and visible_canvas_rect.height > 0:
                try:
                    # Get a subsurface of just the visible part
                    sub_surface: pygame.Surface = drawing_surface.subsurface(visible_canvas_rect)
                    
                    # Find where this subsurface should be drawn on the screen
                    dest_x: float
                    dest_y: float
                    dest_x, dest_y = injected_canvas_to_screen[0](visible_canvas_rect.topleft)
                    dest_w: float = visible_canvas_rect.width * shared_tool_context["zoom_level"]
                    dest_h: float = visible_canvas_rect.height * shared_tool_context["zoom_level"]
                    
                    if dest_w >= 1 and dest_h >= 1:
                        # Scale the subsurface and blit it
                        scaled_canvas: pygame.Surface = pygame.transform.scale(sub_surface, (int(dest_w), int(dest_h)))
                        screen.blit(scaled_canvas, (int(dest_x), int(dest_y)))

                except ValueError as e:
                    # This can happen if rounding errors make the rect invalid
                    logger.warning(f"Subsurface error: {e}. Rect: {visible_canvas_rect}")
                    pass
        
        # --- Cursor Drawing ---
        
        is_on_canvas: bool = (
            not top_bar_rect.collidepoint(mouse_pos) and
            not toolbar_rect.collidepoint(mouse_pos) and
            shared_tool_context["menu_open"] is None and
            dialog_state is None
        )
        
        active_tool_instance = tool_id_to_instance.get(shared_tool_context.get("active_tool_id"))
        
        # Default cursor state
        pygame.mouse.set_visible(True)
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        # Special cursor for panning
        if hand_tool_id[0] and shared_tool_context["is_panning"] and shared_tool_context.get("active_tool_id") == hand_tool_id[0]:
            active_tool_instance = tool_id_to_instance.get(hand_tool_id[0])
            if active_tool_instance:
                pygame.mouse.set_visible(False) 
                if active_tool_instance.custom_cursor_surf:
                    # Draw custom "grabbing" cursor
                    hotspot_x: float = mouse_pos[0] - active_tool_instance.custom_cursor_hotspot[0]
                    hotspot_y: float = mouse_pos[1] - active_tool_instance.custom_cursor_hotspot[1]
                    offset_x: float = active_tool_instance.custom_cursor_offset[0]
                    offset_y: float = active_tool_instance.custom_cursor_offset[1]
                    draw_pos: Tuple[float, float] = (hotspot_x + offset_x, hotspot_y + offset_y)
                    screen.blit(active_tool_instance.custom_cursor_surf, draw_pos)
                else:
                    # Fallback to system hand cursor
                    pygame.mouse.set_visible(True)
                    try:
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                    except: 
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        # Draw tool-specific cursors (brush, eraser, etc.)
        elif is_on_canvas and active_tool_instance:
            
            cursor_info: Dict[str, Any] = active_tool_instance.get_cursor_draw_info(shared_tool_context)
            cursor_type: str = cursor_info.get("type", "custom")
            
            # Draw a circle cursor for drawing tools
            if active_tool_instance.is_drawing_tool and cursor_type in ["custom", "circle"]:
                
                radius: int = cursor_info.get("radius", 1) 
                fill_color: Tuple[int, int, int] = cursor_info.get("color", (0, 0, 0))
                
                # Scale radius by zoom
                screen_radius: int = max(1, int(radius * shared_tool_context["zoom_level"]))

                pygame.mouse.set_visible(False) 
                
                # Draw cursor outline
                pygame.draw.circle(screen, fill_color, mouse_pos, screen_radius)
                pygame.draw.circle(screen, (0, 0, 0), mouse_pos, screen_radius, width=2)
                if screen_radius > 3:
                    pygame.draw.circle(screen, (255, 255, 255), mouse_pos, screen_radius - 2, width=1)
            
            # Draw custom icon cursors (e.g., for selection tool)
            if active_tool_instance.custom_cursor_surf:
                pygame.mouse.set_visible(False)
                hotspot_x = mouse_pos[0] - active_tool_instance.custom_cursor_hotspot[0]
                hotspot_y = mouse_pos[1] - active_tool_instance.custom_cursor_hotspot[1]
                offset_x = active_tool_instance.custom_cursor_offset[0]
                offset_y = active_tool_instance.custom_cursor_offset[1]
                draw_pos = (hotspot_x + offset_x, hotspot_y + offset_y)
                screen.blit(active_tool_instance.custom_cursor_surf, draw_pos)
            
            elif not active_tool_instance.custom_cursor_surf and cursor_type == "custom":
                # Fallback for tools that want a custom cursor but don't provide one
                pygame.mouse.set_visible(True)
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        
        # --- Draw Top Bar ---
        pygame.draw.rect(screen, MENU_BG_COLOR, top_bar_rect)
        
        # Highlight active menu button
        if shared_tool_context["menu_open"] == "file":
            highlight_rect: pygame.Rect = file_btn.rect.inflate(-8, -8)
            pygame.draw.rect(screen, MENU_ACTIVE_BG_COLOR, highlight_rect, border_radius=10)
        
        if shared_tool_context["menu_open"] == "history":
            highlight_rect = history_btn.rect.inflate(-8, -8)
            pygame.draw.rect(screen, MENU_ACTIVE_BG_COLOR, highlight_rect, border_radius=10)
        
        # Draw top bar button text
        screen.blit(file_btn.text_surf, file_btn.text_rect)
        screen.blit(history_btn.text_surf, history_btn.text_rect)
        
        # --- Draw File Menu (if open) ---
        if shared_tool_context["menu_open"] == "file":
            for btn in file_menu_buttons:
                
                pygame.draw.rect(screen, MENU_DROPDOWN_BG_COLOR, btn.rect)
                
                # Highlight on hover
                if btn.rect.collidepoint(mouse_pos):
                    highlight_rect = btn.rect.inflate(-4, -4)
                    pygame.draw.rect(screen, MENU_HOVER_BG_COLOR, highlight_rect, border_radius=10)
                    btn.text_surf = btn.font.render(btn.text, True, (0, 0, 200))
                else:
                    btn.text_surf = btn.font.render(btn.text, True, MENU_TEXT_COLOR)
                
                pygame.draw.rect(screen, MENU_BORDER_COLOR, btn.rect, 1) # Border

                screen.blit(btn.text_surf, btn.text_rect)
        
        # --- Draw History Menu (if open) ---
        if shared_tool_context["menu_open"] == "history":
            pygame.draw.rect(screen, MENU_DROPDOWN_BG_COLOR, history_placeholder_rect)
            # Set a clipping rect to keep items inside the menu
            clip_rect = history_placeholder_rect.inflate(-4, -HISTORY_MENU_PADDING * 2)
            screen.set_clip(clip_rect)
            
            item_y_start = clip_rect.y
            visible_items_indices = range(history_scroll_offset, history_scroll_offset + MAX_VISIBLE_HISTORY_ITEMS)
            
            for i, history_i in enumerate(visible_items_indices):
                if history_i >= len(history): break
                
                text: str = f"{history_i + 1}. {history[history_i][1]}"
                item_rect = pygame.Rect(clip_rect.x, item_y_start + (i * HISTORY_ITEM_HEIGHT), clip_rect.width, HISTORY_ITEM_HEIGHT)
                
                color: Tuple[int, int, int] = MENU_TEXT_COLOR_MUTED
                
                is_selected: bool = (history_i == history_index)
                is_hovered: bool = item_rect.collidepoint(mouse_pos) and shared_tool_context["menu_open"] == "history"

                if is_selected:
                    color = MENU_TEXT_COLOR
                    highlight_rect = item_rect.inflate(-4, -4)
                    pygame.draw.rect(screen, MENU_SELECTED_BG_COLOR, highlight_rect, border_radius=5)
                
                if is_hovered and not is_selected:
                    color = (0, 0, 200)
                    highlight_rect = item_rect.inflate(-4, -4)
                    pygame.draw.rect(screen, MENU_HOVER_BG_COLOR, highlight_rect, border_radius=5)
                
                surf: pygame.Surface = history_font.render(text, True, color)
                y_pos_blit: float = item_rect.y + (item_rect.height - surf.get_height()) // 2
                screen.blit(surf, (item_rect.x + 5, y_pos_blit))
                
            screen.set_clip(None) # Reset clipping rect

        # --- Draw Toolbar ---
        pygame.draw.rect(screen, (80, 80, 80), toolbar_rect)
        
        active_tool_id = shared_tool_context.get("active_tool_id")
        
        # Draw all tool buttons
        for tool in loaded_tool_instances: 
            if hasattr(tool, 'button'): 
                
                tool_type: Optional[str] = tool.config.get('type')
                highlight_color: Tuple[int, int, int] = (0, 0, 0)
                if tool_type == 'drawing_tool':
                    highlight_color = HIGHLIGHT_COLOR_DRAWING
                elif tool_type == 'context_tool':
                    highlight_color = HIGHLIGHT_COLOR_CONTEXT

                is_active: bool = tool.registryId == active_tool_id
                is_menu_open: bool = shared_tool_context.get("menu_open") == tool.registryId
                
                # Draw highlight for active or open tool
                if is_active or is_menu_open:
                    pygame.draw.rect(screen, highlight_color, tool.button.rect.inflate(4, 4))
                    
                tool.draw(screen, shared_tool_context)
            
        # Draw utility tools (like zoom slider)
        for tool in utility_tools_to_draw:
            tool.draw(screen, shared_tool_context) 
            
        # --- Draw Dialog (if open) ---
        if dialog_state is not None:
            # Dark overlay
            overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            # Dialog box
            pygame.draw.rect(screen, (230, 230, 230), dialog_rect, border_radius=5)
            pygame.draw.rect(screen, (100, 100, 100), dialog_rect, 2, border_radius=5)
            
            # Text
            title_surf = dialog_title_font.render("You have unsaved changes!", True, (0,0,0))
            screen.blit(title_surf, title_surf.get_rect(centerx=dialog_rect.centerx, y=dialog_rect.y + 20))
            
            prompt_surf = dialog_font.render("What would you like to do?", True, (50,50,50))
            screen.blit(prompt_surf, prompt_surf.get_rect(centerx=dialog_rect.centerx, y=dialog_rect.y + 60))
            
            # Buttons
            for item in dialog_buttons:
                item["btn"].draw(screen)
            
        # --- Flip Display ---
        pygame.display.flip()
        clock.tick(60)

    # --- Cleanup ---
    # Restore cursor visibility on exit
    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
    pygame.mouse.set_visible(True)