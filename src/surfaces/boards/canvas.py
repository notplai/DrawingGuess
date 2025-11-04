import pygame
from libs.common.components import SolidButton, SolidSlider
from libs.common.kits import loads as load_kits
import math
import sys
import pickle # For saving/loading .vecbo files

# Import tkinter for native file dialogs
try:
    import tkinter as tk
    from tkinter import filedialog
    # --- Helper function to create a hidden tkinter root ---
    def get_tk_root():
        root = tk.Tk()
        root.withdraw() # Hide the main window
        try:
            root.call('wm', 'attributes', '.', '-topmost', True)
        except Exception as e:
            print(f"Warning: Could not set topmost attribute for tkinter: {e}")
        return root
except ImportError:
    print("Warning: tkinter module not found. File dialogs will not work.")
    tk = None # Set tk to None to check later

# --- Coordinate Helper Functions ---
def screen_to_canvas(screen_pos, zoom, offset):
    """Converts a screen coordinate (e.g., mouse_pos) to a canvas coordinate."""
    return (
        (screen_pos[0] - offset[0]) / zoom, 
        (screen_pos[1] - offset[1]) / zoom
    )

def canvas_to_screen(canvas_pos, zoom, offset):
    """Converts a canvas coordinate to a screen coordinate for blitting."""
    return (
        (canvas_pos[0] * zoom) + offset[0], 
        (canvas_pos[1] * zoom) + offset[1]
    )

# --- Helper function for smooth animation ---
def lerp(a, b, t):
    """Linearly interpolate from a to b by t."""
    return a + (b - a) * t

WORLD_WIDTH = 8000
WORLD_HEIGHT = 6000

#  Added open_file_on_start parameter
def surface(screen, background, open_file_on_start=False):
    """
    The main Whiteboard surface.
    Hosts plugins and manages shared state.
    """
    running = True
    clock = pygame.time.Clock()
    
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # --- File and Dialog State ---
    current_project_path = None # Path to the loaded .vecbo file, if any
    is_dirty = False # True if changes have been made since last save/load
    dialog_state = None # None, "confirm_action"
    dialog_pending_action = None # "new_canvas", "open_file", "exit"
    dialog_rect = pygame.Rect(0, 0, 500, 200)
    dialog_rect.center = (screen_width // 2, screen_height // 2)
    dialog_buttons = []
    try:
        dialog_font = pygame.font.Font("freesansbold.ttf", 24)
        dialog_title_font = pygame.font.Font("freesansbold.ttf", 28)
    except:
        dialog_font = pygame.font.Font(None, 24)
        dialog_title_font = pygame.font.Font(None, 28)

    # --- MODIFIED: Calculate initial offset to center the view ---
    # We start at 1.0 zoom
    initial_offset_x = (screen_width - WORLD_WIDTH) / 2
    initial_offset_y = (screen_height - WORLD_HEIGHT) / 2

    # --- State Management ---
    # Shared context for all tools
    shared_tool_context = {
        "screen": screen,
        "draw_color": (0, 0, 0),
        "current_hsv": (0.0, 0.0, 0.0),
        "draw_size": 5,
        "eraser_size": 50,
        "active_tool_name": "pen",
        "is_drawing": False,
        "menu_open": None,
        "click_on_ui": False,
        "mouse_pos": (0,0),
        "toolbar_current_y": screen_height,
        "drawing_surface": None,
        "add_history": None,
        
        # --- MODIFIED: Zoom and Pan State ---
        "zoom_level": 1.0,  # Start at 100%
        "pan_offset": (initial_offset_x, initial_offset_y), # Start centered
        "canvas_mouse_pos": (0, 0),
        
        # --- Panning and Tool Switching State ---
        "is_panning": False,
        "pan_start_pos": (0, 0),
        "pan_start_offset": (0, 0),
        "previous_tool_name": "pen"
    }
    
    history_scroll_offset = 0
    
    # --- MODIFIED: Drawing Surface ---
    # Create a large surface, not one tied to the screen size
    drawing_surface = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))
    drawing_surface.fill("White")
    shared_tool_context["drawing_surface"] = drawing_surface
    
    # --- History (Undo/Redo) ---
    history = [(drawing_surface.copy(), "Initial")]
    history_index = 0
    MAX_HISTORY_SIZE = 30

    def add_history_state(action_name="Action"):
        nonlocal history, history_index, drawing_surface, is_dirty
        history = history[:history_index + 1]
        history.append((drawing_surface.copy(), action_name))
        history_index += 1
        is_dirty = True
        
        if len(history) > MAX_HISTORY_SIZE:
            history.pop(0)
            history_index -= 1
        print(f"History added: {action_name}. Index: {history_index}, Total: {len(history)}")
    
    # Pass history function to context
    shared_tool_context["add_history"] = add_history_state

    def undo():
        nonlocal history_index, drawing_surface, is_dirty
        if history_index > 0:
            history_index -= 1
            drawing_surface = history[history_index][0].copy()
            shared_tool_context["drawing_surface"] = drawing_surface
            is_dirty = True
            print(f"Undo. Index: {history_index}")
            
    def redo():
        nonlocal history_index, drawing_surface, is_dirty
        if history_index < len(history) - 1:
            history_index += 1
            drawing_surface = history[history_index][0].copy()
            shared_tool_context["drawing_surface"] = drawing_surface
            is_dirty = True
            print(f"Redo. Index: {history_index}")
            
    def clear_canvas():
        # --- MODIFIED: Reset canvas and view ---
        nonlocal drawing_surface, history, history_index, current_project_path, is_dirty, screen_width, screen_height
        # Recreate the surface
        drawing_surface = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))
        drawing_surface.fill("White")
        history = [(drawing_surface.copy(), "Initial")]
        history_index = 0
        current_project_path = None
        is_dirty = False
        shared_tool_context["drawing_surface"] = drawing_surface
        
        # Reset pan and zoom to center
        initial_offset_x = (screen_width - WORLD_WIDTH) / 2
        initial_offset_y = (screen_height - WORLD_HEIGHT) / 2
        shared_tool_context["zoom_level"] = 1.0
        shared_tool_context["pan_offset"] = (initial_offset_x, initial_offset_y)
        # Update the slider as well
        if zoom_tool_instance:
            zoom_tool_instance.slider.set_value(1.0)
        
        print("Canvas Cleared and View Reset")
        # --- END MODIFIED ---
    
    # --- File Operations ---
    
    def open_file():
        nonlocal drawing_surface, current_project_path, is_dirty, history, history_index
        if not tk: return
        root = get_tk_root()
        file_path = filedialog.askopenfilename(
            title="Open File",
            filetypes=[
                ("Project Files", "*.vecbo"),
                ("Images", "*.png *.jpg *.jpeg"),
                ("All Files", "*.*")
            ]
        )
        root.destroy()
        if not file_path: return

        try:
            if file_path.endswith(".vecbo"):
                with open(file_path, 'rb') as f:
                    loaded_data = pickle.load(f)
                
                if isinstance(loaded_data, dict):
                    drawing_surface = loaded_data["main_surface"]
                    history = loaded_data["history_stack"]
                    history_index = loaded_data["history_index"]
                    print(f"Loaded project with history: {file_path}")
                else:
                    drawing_surface = loaded_data
                    print(f"Loaded old project (surface only): {file_path}")
                    history = [(drawing_surface.copy(), "Loaded Old File")]
                    history_index = 0
                
                # --- MODIFIED: Ensure loaded surface is correct size ---
                if drawing_surface.get_size() != (WORLD_WIDTH, WORLD_HEIGHT):
                    print("Warning: Loaded surface has different dimensions. Re-centering.")
                    # Create a new, correctly-sized surface and blit the loaded one
                    new_surf = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))
                    new_surf.fill("White")
                    # Blit to center
                    new_surf.blit(drawing_surface, drawing_surface.get_rect(center=(WORLD_WIDTH//2, WORLD_HEIGHT//2)))
                    drawing_surface = new_surf
                    # Update history
                    history = [(drawing_surface.copy(), "Loaded and Resized")]
                    history_index = 0

                shared_tool_context["drawing_surface"] = drawing_surface
                current_project_path = file_path
                
            else:
                # Import image
                img = pygame.image.load(file_path).convert_alpha()
                
                # --- MODIFIED ---
                # Blit image to the center of the world, don't scale it
                img_rect = img.get_rect(center=(WORLD_WIDTH // 2, WORLD_HEIGHT // 2))
                drawing_surface.fill("White") # Clear canvas first
                drawing_surface.blit(img, img_rect)
                # --- END MODIFIED ---
                
                current_project_path = None # It's an import, not a project
                print(f"Imported image: {file_path}")
                add_history_state(f"Import {file_path.split('/')[-1]}")

            if not file_path.endswith(".vecbo"):
                # add_history_state(f"Open {file_path.split('/')[-1]}") # Already done for images
                pass
                
            is_dirty = False 
            clear_canvas() # Reset view to center the new content

        except Exception as e:
            print(f"Error opening file {file_path}: {e}")
    
    def save_vecbo():
        nonlocal is_dirty
        if not current_project_path:
            save_as_vecbo()
        else:
            try:
                data_to_save = {
                    "main_surface": drawing_surface,
                    "history_stack": history,
                    "history_index": history_index
                }
                with open(current_project_path, 'wb') as f:
                    pickle.dump(data_to_save, f)
                    
                is_dirty = False
                print(f"Saved project: {current_project_path}")
            except Exception as e:
                print(f"Error saving file: {e}")

    def save_as_vecbo():
        nonlocal current_project_path, is_dirty
        if not tk: return
        root = get_tk_root()
        file_path = filedialog.asksaveasfilename(
            title="Save Project As...",
            defaultextension=".vecbo",
            filetypes=[("Project Files", "*.vecbo")]
        )
        root.destroy()
        if not file_path: return
        
        current_project_path = file_path
        save_vecbo() 

    def export_as_image():
        if not tk: return
        root = get_tk_root()
        file_path = filedialog.asksaveasfilename(
            title="Export As Image...",
            defaultextension=".png",
            filetypes=[
                ("PNG Image", "*.png"),
                ("JPEG Image", "*.jpg")
            ]
        )
        root.destroy()
        if not file_path: return
        
        try:
            # --- MODIFIED: Save the large surface ---
            # Note: This exports the *entire* 8000x6000 canvas.
            # A more advanced export would let the user select a region.
            pygame.image.save(drawing_surface, file_path)
            print(f"Exported full canvas image: {file_path}")
        except Exception as e:
            print(f"Error exporting image: {e}")

    # --- Dialog Creation ---
    def set_dialog(state, pending_action):
        nonlocal dialog_state, dialog_pending_action, dialog_buttons
        dialog_state = state
        dialog_pending_action = pending_action
        shared_tool_context["menu_open"] = None 

        btn_w, btn_h = 130, 40
        btn_y = dialog_rect.centery + 30
        btn_gap = 20
        total_w = (btn_w * 3) + (btn_gap * 2)
        start_x = dialog_rect.centerx - (total_w / 2)
        
        save_btn = SolidButton(start_x, btn_y, btn_w, btn_h, "Save (.vecbo)", font_size=18, bg_color=(0, 150, 255))
        export_btn = SolidButton(start_x + btn_w + btn_gap, btn_y, btn_w, btn_h, "Export (.png)", font_size=18, bg_color=(100, 100, 100))
        dont_save_btn = SolidButton(start_x + (btn_w + btn_gap)*2, btn_y, btn_w, btn_h, "Don't Save", font_size=18, bg_color=(200, 50, 50))
        
        cancel_btn = SolidButton(dialog_rect.right - 90, dialog_rect.bottom - 50, 80, 40, "Cancel", font_size=18, bg_color=(220, 220, 220), text_color=(0,0,0)) # type: ignore
        
        if not current_project_path:
             save_btn.text = "Save As..."
        
        dialog_buttons = [
            {"name": "save", "btn": save_btn},
            {"name": "export", "btn": export_btn},
            {"name": "dont_save", "btn": dont_save_btn},
            {"name": "cancel", "btn": cancel_btn}
        ]

    # --- Top Menu Bar ---
    top_bar_rect = pygame.Rect(0, 0, screen_width, 40)
    file_btn = SolidButton(0, 0, 80, 40, "File", bg_color=(200, 200, 200), text_color=(0,0,0), font_size=25) # type: ignore
    history_btn = SolidButton(80, 0, 100, 40, "History", bg_color=(200, 200, 200), text_color=(0,0,0), font_size=25) # type: ignore
    
    file_menu_buttons = []
    file_menu_hot_zone = [file_btn.rect] 

    # --- History Menu Assets (Scrollable) ---
    HISTORY_ITEM_HEIGHT = 25
    MAX_VISIBLE_HISTORY_ITEMS = 10
    HISTORY_MENU_PADDING = 5
    
    history_menu_height = (HISTORY_ITEM_HEIGHT * MAX_VISIBLE_HISTORY_ITEMS) + (HISTORY_MENU_PADDING * 2)
    history_placeholder_rect = pygame.Rect(80, 40, 200, history_menu_height)
    
    history_menu_hot_zone = [history_btn.rect, history_placeholder_rect]
    try:
        history_font = pygame.font.Font("freesansbold.ttf", 20)
    except:
        history_font = pygame.font.Font(None, 20)


    # --- Bottom Toolbar ---
    toolbar_height = 80
    toolbar_hidden_y = screen_height
    toolbar_visible_y = screen_height - toolbar_height
    toolbar_rect = pygame.Rect(0, toolbar_visible_y, screen_width, toolbar_height)
    
    # --- Plugin Loading ---
    loaded_tool_plugins = load_kits(components_dir="components")
    
    loaded_tool_instances = []
    zoom_tool_instance = None 
    
    toolbar_btn_x = 20
    toolbar_btn_size = 60
    toolbar_btn_gap = 20 
    
    for config, ToolClass in loaded_tool_plugins:
        btn_rect = pygame.Rect(toolbar_btn_x, toolbar_hidden_y + 10, toolbar_btn_size, toolbar_btn_size)
        tool_instance = ToolClass(btn_rect, config)
        tool_instance.config = config

        if hasattr(tool_instance, 'config_type') and tool_instance.config_type == "ui_component":
            zoom_tool_instance = tool_instance
        else:
            loaded_tool_instances.append(tool_instance)
            toolbar_btn_x += toolbar_btn_size + toolbar_btn_gap
            
    # Load Custom Cursors ---
    print("Loading custom cursors...")
    for tool in loaded_tool_instances:
        tool.custom_cursor_surf = None
        tool.custom_cursor_hotspot = (0, 0)
        tool.custom_cursor_offset = (0, 0)
        cursor_path = tool.config.get("cursor_path")
        
        if cursor_path:
            try:
                cursor_surf = pygame.image.load(cursor_path).convert_alpha()
                cursor_size = tool.config.get("cursor_size")
                if not cursor_size:
                    if cursor_surf.get_width() > 64 or cursor_surf.get_height() > 64:
                        cursor_size = (64, 64) 
                
                if cursor_size:
                    try:
                        cursor_surf = pygame.transform.smoothscale(cursor_surf, cursor_size)
                    except: 
                        cursor_surf = pygame.transform.scale(cursor_surf, cursor_size)

                hotspot_config = tool.config.get("cursor_hotspot")
                hotspot = (0, 0)
                if hotspot_config == "center":
                    hotspot = (cursor_surf.get_width() // 2, cursor_surf.get_height() // 2)
                
                tool.custom_cursor_surf = cursor_surf
                tool.custom_cursor_hotspot = hotspot
                tool.custom_cursor_offset = tool.config.get("cursor_offset", (0, 0)) 
                print(f"  Successfully loaded cursor surface for: {tool.name}")
            except Exception as e:
                print(f"Warning: Could not load cursor surface for {tool.name} at {cursor_path}: {e}")
                
    hand_tool_instance = next((t for t in loaded_tool_instances if t.name == "hand"), None)
    
    # --- MODIFIED: Get Zoom Limits from Tool ---
    # We now read the limits from the loaded tool.
    # This makes zoom.py the single source of truth.
    if zoom_tool_instance:
        MIN_ZOOM = zoom_tool_instance.min_zoom
        MAX_ZOOM = zoom_tool_instance.max_zoom
    else:
        # Fallback if zoom tool fails to load
        print("Warning: ZoomTool not loaded. Defaulting zoom limits.")
        MIN_ZOOM = 0.1
        MAX_ZOOM = 4.0

    # --- Zoom UI ---
    zoom_slider_x_start = 0 
    if zoom_tool_instance:
        zoom_slider_x_start = toolbar_btn_x + 50 
        zoom_tool_instance.update_button_pos(zoom_slider_x_start, toolbar_hidden_y + 25)
        
        # --- MODIFICATION: Update slider bounds ---
        # This block is no longer needed!
        # The zoom.py file now sets the min/max on its own.
        # --- END MODIFICATION ---
    
    # --- MODIFIED: Zoom Helper Function ---
    # NOTE: The ZoomTool in zoom.py has its *own* _set_zoom function.
    # We modify this one in case anything else calls it, but the main
    # constraints are now applied in the main loop.
    def set_zoom(new_zoom, pivot_pos):
        """Helper to set zoom and recalculate pan offset to pivot on pivot_pos."""
        nonlocal shared_tool_context, zoom_tool_instance, screen_width, screen_height

        new_zoom = max(MIN_ZOOM, min(MAX_ZOOM, new_zoom)) # Use new clamps
        
        current_zoom = shared_tool_context["zoom_level"]
        current_offset = shared_tool_context["pan_offset"]
        
        canvas_pivot = screen_to_canvas(pivot_pos, current_zoom, current_offset)
        
        new_offset_x = pivot_pos[0] - (canvas_pivot[0] * new_zoom)
        new_offset_y = pivot_pos[1] - (canvas_pivot[1] * new_zoom)

        # Pan constraints will be applied in the main loop
        shared_tool_context["zoom_level"] = new_zoom
        shared_tool_context["pan_offset"] = (new_offset_x, new_offset_y)
        if zoom_tool_instance: 
            zoom_tool_instance.slider.set_value(new_zoom) 
    # --- END MODIFIED ---
            
    # --- Main Loop ---
    
    if open_file_on_start:
        pygame.time.set_timer(pygame.USEREVENT + 1, 100, 1) 


    while running:
        mouse_pos = pygame.mouse.get_pos()
        events = pygame.event.get()
        
        # --- Update Shared Context ---
        shared_tool_context["mouse_pos"] = mouse_pos
        
        # --- Event Handling (STAGE 0: Dialogs) ---
        shared_tool_context["click_on_ui"] = False
        if dialog_state is not None:
            for event in events[:]:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    action_taken = None
                    for item in dialog_buttons:
                        if item["btn"].is_clicked(event):
                            action_taken = item["name"]
                            break
                    
                    if action_taken:
                        if action_taken == "cancel":
                            dialog_state = None
                            dialog_pending_action = None
                        
                        elif action_taken == "dont_save":
                            dialog_state = None
                            if dialog_pending_action == "new_canvas": clear_canvas()
                            elif dialog_pending_action == "open_file": open_file()
                            elif dialog_pending_action == "exit": running = False
                        
                        elif action_taken == "save":
                            if current_project_path: save_vecbo()
                            else: save_as_vecbo()
                            if not is_dirty: 
                                dialog_state = None
                                if dialog_pending_action == "new_canvas": clear_canvas()
                                elif dialog_pending_action == "open_file": open_file()
                                elif dialog_pending_action == "exit": running = False

                        elif action_taken == "export":
                            export_as_image()
                    
                    shared_tool_context["click_on_ui"] = True
                    events.remove(event)
            
            for event in events[:]: events.remove(event)
            shared_tool_context["click_on_ui"] = True

        # --- Event Handling (STAGE 1: Normal) ---
        if not dialog_state: 
            for event in events[:]:
                
                if event.type == pygame.USEREVENT + 1:
                    open_file()
                    pygame.time.set_timer(pygame.USEREVENT + 1, 0)
                    continue

                if event.type == pygame.QUIT:
                    if is_dirty:
                        set_dialog("confirm_action", "exit")
                        shared_tool_context["click_on_ui"] = True
                    else:
                        running = False
                
                if shared_tool_context["click_on_ui"]:
                    if event in events: events.remove(event)
                    continue

                # --- Pass event to ZoomTool ---
                # This now handles wheel zoom and keyboard zoom shortcuts
                if zoom_tool_instance and zoom_tool_instance.handle_event(event, shared_tool_context):
                    shared_tool_context["click_on_ui"] = True 
                
                if shared_tool_context["click_on_ui"]:
                    if event in events: events.remove(event)
                    continue

                # --- Mouse Wheel Scrolling (for History Menu) ---
                if event.type == pygame.MOUSEWHEEL:
                    if shared_tool_context["menu_open"] == "history" and history_placeholder_rect.collidepoint(mouse_pos):
                        if event.y > 0: history_scroll_offset = max(0, history_scroll_offset - 1)
                        elif event.y < 0:
                            max_scroll = max(0, len(history) - MAX_VISIBLE_HISTORY_ITEMS)
                            history_scroll_offset = min(max_scroll, history_scroll_offset + 1)
                        shared_tool_context["click_on_ui"] = True 
                    
                    elif (top_bar_rect.collidepoint(mouse_pos) or 
                          toolbar_rect.collidepoint(mouse_pos)):
                        shared_tool_context["click_on_ui"] = True
                    
                    # Zooming is now handled by ZoomTool
                
                if shared_tool_context["click_on_ui"]:
                    if event in events: events.remove(event)
                    continue
                
                # --- Keyboard Shortcuts (Undo/Redo/Pan) ---
                if event.type == pygame.KEYDOWN:
                    mods = pygame.key.get_mods()
                    is_ctrl_or_cmd = mods & pygame.KMOD_CTRL or mods & pygame.KMOD_META
                    is_shift = mods & pygame.KMOD_SHIFT
                    
                    if event.key == pygame.K_SPACE:
                        if shared_tool_context["active_tool_name"] != "hand":
                            shared_tool_context["previous_tool_name"] = shared_tool_context["active_tool_name"]
                            shared_tool_context["active_tool_name"] = "hand"
                            shared_tool_context["click_on_ui"] = True
                    
                    elif event.key == pygame.K_z:
                        if is_ctrl_or_cmd:
                            if is_shift: redo()
                            else: undo()
                    elif event.key == pygame.K_y:
                        if is_ctrl_or_cmd and not is_shift: redo()
                    
                    elif event.key == pygame.K_e and is_shift:
                        export_as_image()
                    
                    # Zoom shortcuts are handled by ZoomTool
                    shared_tool_context["click_on_ui"] = True
                
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_SPACE:
                        if shared_tool_context["active_tool_name"] == "hand":
                            shared_tool_context["active_tool_name"] = shared_tool_context["previous_tool_name"]
                            shared_tool_context["is_panning"] = False
                        shared_tool_context["click_on_ui"] = True
                
                if shared_tool_context["click_on_ui"]:
                    if event in events: events.remove(event)
                    continue

                # --- STAGE 2: Whiteboard UI (Top Bar, Menus) ---
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if file_btn.is_clicked(event):
                        shared_tool_context["menu_open"] = "file" if shared_tool_context["menu_open"] != "file" else None
                        shared_tool_context["click_on_ui"] = True
                    elif history_btn.is_clicked(event):
                        shared_tool_context["menu_open"] = "history" if shared_tool_context["menu_open"] != "history" else None
                        shared_tool_context["click_on_ui"] = True
                    
                    if shared_tool_context["click_on_ui"]:
                        if event in events: events.remove(event)
                        continue
                            
                    elif shared_tool_context["menu_open"] == "file":
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
                        if not shared_tool_context["click_on_ui"] and any(rect.collidepoint(mouse_pos) for rect in file_menu_hot_zone):
                             shared_tool_context["click_on_ui"] = True
                        if shared_tool_context["click_on_ui"]:
                            if event in events: events.remove(event)
                            continue
                    
                    elif shared_tool_context["menu_open"] == "history":
                        if history_placeholder_rect.collidepoint(mouse_pos):
                            shared_tool_context["click_on_ui"] = True
                            clip_rect = history_placeholder_rect.inflate(-4, -HISTORY_MENU_PADDING * 2)
                            item_y_start = clip_rect.y
                            visible_items_indices = range(history_scroll_offset, history_scroll_offset + MAX_VISIBLE_HISTORY_ITEMS)
            
                            for i, history_i in enumerate(visible_items_indices):
                                if history_i >= len(history): break
                                item_rect = pygame.Rect(clip_rect.x, item_y_start + (i * HISTORY_ITEM_HEIGHT), clip_rect.width, HISTORY_ITEM_HEIGHT)
                                if item_rect.collidepoint(mouse_pos):
                                    history_index = history_i
                                    drawing_surface = history[history_index][0].copy()
                                    shared_tool_context["drawing_surface"] = drawing_surface
                                    shared_tool_context["menu_open"] = None
                                    is_dirty = True
                                    print(f"Jumped to history index: {history_i}")
                                    break
                        if shared_tool_context["click_on_ui"]:
                            if event in events: events.remove(event)
                            continue

                # --- STAGE 3: Tool layer ---
                tool_menu_is_open = False
                if shared_tool_context["menu_open"] is not None:
                    for tool in loaded_tool_instances:
                        if tool.name == shared_tool_context["menu_open"]:
                            tool_menu_is_open = True
                            if tool.handle_event(event, shared_tool_context):
                                shared_tool_context["click_on_ui"] = True
                            break 
                
                if tool_menu_is_open:
                    if shared_tool_context["click_on_ui"]:
                        if event in events: events.remove(event)
                        continue 
                
                tool_button_was_clicked = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for tool in loaded_tool_instances: 
                        if tool.button.rect.collidepoint(event.pos):
                            if tool.handle_event(event, shared_tool_context):
                                shared_tool_context["click_on_ui"] = True
                                tool_button_was_clicked = True
                            break
                
                if tool_button_was_clicked:
                    if event in events: events.remove(event)
                    continue
                
                # --- STAGE 4: Handle "Click Outside" ---
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    menu = shared_tool_context["menu_open"]
                    
                    if menu == "file" or menu == "history":
                        hot_zone = file_menu_hot_zone if menu == "file" else history_menu_hot_zone
                        is_on_hotzone = False
                        for rect in hot_zone:
                            if rect.collidepoint(mouse_pos):
                                is_on_hotzone = True
                                break
                        if not is_on_hotzone:
                            shared_tool_context["menu_open"] = None
                            shared_tool_context["click_on_ui"] = True
                
                if shared_tool_context["click_on_ui"]:
                    if event in events: events.remove(event)
                    continue 

                # --- STAGE 5: Active drawing tool ---
                if event not in events:
                    continue

                active_tool_instance = None
                active_name = shared_tool_context.get("active_tool_name")
                for tool in loaded_tool_instances:
                    if tool.name == active_name:
                        active_tool_instance = tool
                        break
                
                if active_tool_instance:
                    is_space_up = (event.type == pygame.KEYUP and event.key == pygame.K_SPACE)

                    if not is_space_up:
                        if active_tool_instance.handle_event(event, shared_tool_context):
                            if event in events: events.remove(event)
                
                if shared_tool_context["click_on_ui"]:
                    if event in events: events.remove(event)
                    continue
            
        # --- Check for Mouse *Movement* Outside Top Menus ---
        menu = shared_tool_context["menu_open"]
        if menu == "file" or menu == "history":
            hot_zone = file_menu_hot_zone if menu == "file" else history_menu_hot_zone
            is_on_hotzone = False
            for rect in hot_zone:
                if rect.collidepoint(mouse_pos):
                    is_on_hotzone = True
                    break
            if not is_on_hotzone:
                shared_tool_context["menu_open"] = None
        
        # --- DYNAMIC FILE MENU (Must be after event handling) ---
        if shared_tool_context["menu_open"] == "file":
            file_menu_buttons = []
            file_menu_hot_zone = [file_btn.rect]
            btn_y = 40; btn_w = 250; btn_h = 40
            
            def add_file_btn(text):
                nonlocal btn_y
                btn = SolidButton(0, btn_y, btn_w, btn_h, text, bg_color=(220, 220, 220), text_color=(0,0,0), font_size=20, text_align="left") # type: ignore
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

        # --- TOOLBAR ANIMATION ---
        is_drawing = shared_tool_context["is_drawing"]

        if shared_tool_context["menu_open"] is not None or dialog_state is not None:
            toolbar_target_y = toolbar_visible_y
        elif is_drawing:
            toolbar_target_y = toolbar_hidden_y
        else:
            if mouse_pos[1] > screen_height - 20 or toolbar_rect.collidepoint(mouse_pos):
                toolbar_target_y = toolbar_visible_y
            else:
                toolbar_target_y = toolbar_hidden_y
            
        toolbar_current_y = lerp(toolbar_rect.y, toolbar_target_y, 0.2)
        toolbar_rect.y = round(toolbar_current_y)
        shared_tool_context["toolbar_current_y"] = toolbar_rect.y
        
        for tool in loaded_tool_instances:
            tool.update_button_pos(tool.button.rect.x, toolbar_rect.y + 10)
        
        if zoom_tool_instance: 
            zoom_tool_instance.update_button_pos(zoom_slider_x_start, toolbar_rect.y + 25)

        
        # --- BEGIN CONSTRAINTS ---
        # Constrain zoom level set by ZoomTool or other events
        zoom = shared_tool_context["zoom_level"]
        zoom = max(MIN_ZOOM, min(MAX_ZOOM, zoom))
        shared_tool_context["zoom_level"] = zoom
        # Sync slider in case zoom was changed by wheel/keys
        if zoom_tool_instance and not zoom_tool_instance.slider.is_dragging:
             zoom_tool_instance.slider.set_value(zoom)
        
        # Constrain pan offset
        offset = shared_tool_context["pan_offset"]
        
        # Calculate max/min offsets
        # Max offset (pan left) is 0. Canvas edge stops at screen edge.
        # Min offset (pan right) is screen_width - (WORLD_WIDTH * zoom)
        max_offset_x = 0
        min_offset_x = screen_width - (WORLD_WIDTH * zoom)
        if min_offset_x > max_offset_x: # Handle zoom < 1.0
            min_offset_x, max_offset_x = (screen_width - WORLD_WIDTH * zoom) / 2, (screen_width - WORLD_WIDTH * zoom) / 2
            
        max_offset_y = 0
        min_offset_y = screen_height - (WORLD_HEIGHT * zoom)
        if min_offset_y > max_offset_y: # Handle zoom < 1.0
             min_offset_y, max_offset_y = (screen_height - WORLD_HEIGHT * zoom) / 2, (screen_height - WORLD_HEIGHT * zoom) / 2

        # Apply constraints
        new_offset_x = max(min_offset_x, min(max_offset_x, offset[0]))
        new_offset_y = max(min_offset_y, min(max_offset_y, offset[1]))
        
        shared_tool_context["pan_offset"] = (new_offset_x, new_offset_y)
        # --- END CONSTRAINTS ---

        # --- Update Zoom/Pan Context (with constrained values) ---
        zoom = shared_tool_context["zoom_level"]
        offset = shared_tool_context["pan_offset"]
        canvas_mouse_pos = screen_to_canvas(mouse_pos, zoom, offset)
        shared_tool_context["canvas_mouse_pos"] = canvas_mouse_pos


        # --- Drawing ---
        
        # Fill background. This is the "empty space" color.
        screen.fill((80, 80, 80)) 
        
        # --- Draw Scaled Canvas (MODIFIED RENDER LOGIC) ---
        
        # 1. Find the visible area of the *canvas*
        # Top-left of screen in canvas-space
        canvas_tl_x, canvas_tl_y = screen_to_canvas((0, 0), zoom, offset)
        # Bottom-right of screen in canvas-space
        canvas_br_x, canvas_br_y = screen_to_canvas((screen_width, screen_height), zoom, offset)
        
        # 2. Calculate the rectangle (on the large canvas) to grab
        canvas_rect_w = canvas_br_x - canvas_tl_x
        canvas_rect_h = canvas_br_y - canvas_tl_y
        
        # Create the pygame.Rect for subsurface
        # We must clip this rect to the bounds of the drawing_surface
        visible_canvas_rect = pygame.Rect(
            canvas_tl_x, 
            canvas_tl_y,
            canvas_rect_w,
            canvas_rect_h
        ).clip(drawing_surface.get_rect())
        
        # 3. Grab the subsurface
        if visible_canvas_rect.width > 0 and visible_canvas_rect.height > 0:
            try:
                sub_surface = drawing_surface.subsurface(visible_canvas_rect)
                
                # 4. Scale the subsurface and blit it
                
                # Where on the screen does the visible rect start?
                dest_x, dest_y = canvas_to_screen(visible_canvas_rect.topleft, zoom, offset)
                
                # How big is the scaled subsurface?
                dest_w = visible_canvas_rect.width * zoom
                dest_h = visible_canvas_rect.height * zoom
                
                # Only scale if size is valid
                if dest_w >= 1 and dest_h >= 1:
                    scaled_canvas = pygame.transform.scale(sub_surface, (int(dest_w), int(dest_h)))
                    screen.blit(scaled_canvas, (int(dest_x), int(dest_y)))

            except ValueError as e:
                # This can happen if the rect is outside the surface
                print(f"Subsurface error: {e}. Rect: {visible_canvas_rect}")
                pass
        else:
            # Fallback if zoom is tiny or panned off-screen
            pass # The gray background fill is enough
        
        # --- END MODIFIED RENDER LOGIC ---
        
        
        # ---  Set Custom Cursor ---
        is_on_canvas = (
            not top_bar_rect.collidepoint(mouse_pos) and
            not toolbar_rect.collidepoint(mouse_pos) and
            shared_tool_context["menu_open"] is None and
            dialog_state is None
        )
        
        active_tool_instance = None
        active_name = shared_tool_context.get("active_tool_name")
        for tool in loaded_tool_instances:
            if tool.name == active_name:
                active_tool_instance = tool
                break

        # Default to system arrow
        pygame.mouse.set_visible(True)
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        if shared_tool_context["is_panning"] and hand_tool_instance:
            pygame.mouse.set_visible(False) 
            if hand_tool_instance.custom_cursor_surf:
                hotspot_x = mouse_pos[0] - hand_tool_instance.custom_cursor_hotspot[0]
                hotspot_y = mouse_pos[1] - hand_tool_instance.custom_cursor_hotspot[1]
                offset_x = hand_tool_instance.custom_cursor_offset[0]
                offset_y = hand_tool_instance.custom_cursor_offset[1]
                draw_pos = (hotspot_x + offset_x, hotspot_y + offset_y)
                screen.blit(hand_tool_instance.custom_cursor_surf, draw_pos)
            else:
                pygame.mouse.set_visible(True)
                try:
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                except: 
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        elif is_on_canvas and active_tool_instance:
            if active_tool_instance.is_drawing_tool:
                pygame.mouse.set_visible(False)
                radius = 0
                fill_color = (0,0,0)
                
                if active_name == "pen":
                    radius = shared_tool_context["draw_size"] // 2
                    fill_color = shared_tool_context["draw_color"]
                elif active_name == "eraser":
                    radius = shared_tool_context["eraser_size"] // 2
                    fill_color = (255, 255, 255)
                
                # --- MODIFIED: Scale radius by zoom ---
                screen_radius = max(1, int(radius * zoom))

                pygame.draw.circle(screen, fill_color, mouse_pos, screen_radius)
                pygame.draw.circle(screen, (0, 0, 0), mouse_pos, screen_radius, width=2)
                if screen_radius > 3:
                    pygame.draw.circle(screen, (255, 255, 255), mouse_pos, screen_radius - 2, width=1)
            
            if active_tool_instance.custom_cursor_surf:
                pygame.mouse.set_visible(False)
                hotspot_x = mouse_pos[0] - active_tool_instance.custom_cursor_hotspot[0]
                hotspot_y = mouse_pos[1] - active_tool_instance.custom_cursor_hotspot[1]
                offset_x = active_tool_instance.custom_cursor_offset[0]
                offset_y = active_tool_instance.custom_cursor_offset[1]
                draw_pos = (hotspot_x + offset_x, hotspot_y + offset_y)
                screen.blit(active_tool_instance.custom_cursor_surf, draw_pos)
            
            elif not active_tool_instance.is_drawing_tool:
                pygame.mouse.set_visible(True)
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        
        # --- Draw Top Menu Bar ---
        pygame.draw.rect(screen, (200, 200, 200), top_bar_rect)
        file_btn.draw(screen)
        history_btn.draw(screen)
        
        # --- Draw Open Menus ---
        if shared_tool_context["menu_open"] == "file":
            for btn in file_menu_buttons:
                btn.draw(screen)
        
        if shared_tool_context["menu_open"] == "history":
            pygame.draw.rect(screen, (220, 220, 220), history_placeholder_rect)
            clip_rect = history_placeholder_rect.inflate(-4, -HISTORY_MENU_PADDING * 2)
            screen.set_clip(clip_rect)
            item_y_start = clip_rect.y
            visible_items_indices = range(history_scroll_offset, history_scroll_offset + MAX_VISIBLE_HISTORY_ITEMS)
            
            for i, history_i in enumerate(visible_items_indices):
                if history_i >= len(history): break
                text = history[history_i][1]
                item_rect = pygame.Rect(clip_rect.x, item_y_start + (i * HISTORY_ITEM_HEIGHT), clip_rect.width, HISTORY_ITEM_HEIGHT)
                color = (150, 150, 150)
                if history_i == history_index: color = (0, 0, 0)
                if item_rect.collidepoint(mouse_pos): color = (0, 0, 200)
                
                surf = history_font.render(text, True, color)
                y_pos_blit = item_rect.y + (item_rect.height - surf.get_height()) // 2
                screen.blit(surf, (item_rect.x + 5, y_pos_blit))
            screen.set_clip(None)

        # --- Draw Toolbar ---
        pygame.draw.rect(screen, (80, 80, 80), toolbar_rect)
        
        for tool in loaded_tool_instances: 
            tool.draw(screen, shared_tool_context)
            
        if zoom_tool_instance: 
            zoom_tool_instance.draw(screen, shared_tool_context) 
            
        # --- Draw Dialog ---
        if dialog_state is not None:
            overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            pygame.draw.rect(screen, (230, 230, 230), dialog_rect, border_radius=5)
            pygame.draw.rect(screen, (100, 100, 100), dialog_rect, 2, border_radius=5)
            
            title_surf = dialog_title_font.render("You have unsaved changes!", True, (0,0,0))
            screen.blit(title_surf, title_surf.get_rect(centerx=dialog_rect.centerx, y=dialog_rect.y + 20))
            
            prompt_surf = dialog_font.render("What would you like to do?", True, (50,50,50))
            screen.blit(prompt_surf, prompt_surf.get_rect(centerx=dialog_rect.centerx, y=dialog_rect.y + 60))
            
            for item in dialog_buttons:
                item["btn"].draw(screen)
            
        pygame.display.flip()
        clock.tick(60)

    # Reset to default cursor on exit
    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
    pygame.mouse.set_visible(True)


