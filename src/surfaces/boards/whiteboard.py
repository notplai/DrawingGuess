import pygame
from libs.common.components import Button, Slider # [MODIFIED] Import Slider
from libs.common.kits import loads as load_kits # [NEW] Import new loader
import math # For lerping
import sys # [NEW] Import sys for exiting
import pickle # [NEW] For saving/loading .vecbo files

# [NEW] Import tkinter for native file dialogs
try:
    import tkinter as tk
    from tkinter import filedialog
    # --- Helper function to create a hidden tkinter root ---
    def get_tk_root():
        root = tk.Tk()
        root.withdraw() # Hide the main window
        try:
            # [FIX] This line can fail on some macOS versions
            root.call('wm', 'attributes', '.', '-topmost', True) # Keep dialog on top
        except Exception as e:
            print(f"Warning: Could not set topmost attribute for tkinter: {e}")
        return root
except ImportError:
    print("Warning: tkinter module not found. File dialogs will not work.")
    tk = None # Set tk to None to check later

# --- [NEW] Coordinate Helper Functions ---
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

# [MODIFIED] Added open_file_on_start parameter
def surface(screen, background, open_file_on_start=False):
    """
    The main Whiteboard surface.
    Hosts plugins and manages shared state.
    """
    running = True
    clock = pygame.time.Clock()
    
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # --- [NEW] File and Dialog State ---
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

    # --- State Management ---
    # [NEW] Shared context for all tools
    shared_tool_context = {
        "screen": screen,
        "draw_color": (0, 0, 0),
        "current_hsv": (0.0, 0.0, 0.0),
        "draw_size": 5,
        "eraser_size": 50,
        "active_tool_name": "pen", # Default tool
        "is_drawing": False,
        "menu_open": None, # None, "file", "history", or a tool name
        "click_on_ui": False, # Flag to prevent drawing when clicking UI
        "mouse_pos": (0,0),
        "toolbar_current_y": screen_height,
        "drawing_surface": None, # Will be set below
        "add_history": None, # Will be set below
        
        # --- [NEW] Zoom and Pan State ---
        "zoom_level": 1.0,  # 1.0 = 100%
        "pan_offset": (0, 0),
        "canvas_mouse_pos": (0, 0), # Mouse pos transformed to canvas space
        
        # --- [NEW] Panning and Tool Switching State ---
        "is_panning": False,
        "pan_start_pos": (0, 0),
        "pan_start_offset": (0, 0),
        "previous_tool_name": "pen" # For spacebar switching
    }
    
    # [FIX] Removed local menu_open variable. Will use context directly.
    history_scroll_offset = 0
    
    # --- Drawing Surface ---
    drawing_surface = pygame.Surface((screen_width, screen_height))
    drawing_surface.fill("White")
    shared_tool_context["drawing_surface"] = drawing_surface
    
    # --- History (Undo/Redo) ---
    # History saves the *full 100% zoom* surface. This is good.
    history = [(drawing_surface.copy(), "Initial")]
    history_index = 0
    MAX_HISTORY_SIZE = 30

    def add_history_state(action_name="Action"):
        nonlocal history, history_index, drawing_surface, is_dirty
        history = history[:history_index + 1]
        history.append((drawing_surface.copy(), action_name))
        history_index += 1
        is_dirty = True # Mark as having unsaved changes
        
        if len(history) > MAX_HISTORY_SIZE:
            history.pop(0)
            history_index -= 1
        print(f"History added: {action_name}. Index: {history_index}, Total: {len(history)}")
    
    # [NEW] Pass history function to context
    shared_tool_context["add_history"] = add_history_state

    def undo():
        nonlocal history_index, drawing_surface, is_dirty
        if history_index > 0:
            history_index -= 1
            drawing_surface = history[history_index][0].copy()
            shared_tool_context["drawing_surface"] = drawing_surface # Update context
            is_dirty = True
            print(f"Undo. Index: {history_index}")
            
    def redo():
        nonlocal history_index, drawing_surface, is_dirty
        if history_index < len(history) - 1:
            history_index += 1
            drawing_surface = history[history_index][0].copy()
            shared_tool_context["drawing_surface"] = drawing_surface # Update context
            is_dirty = True
            print(f"Redo. Index: {history_index}")
            
    def clear_canvas():
        nonlocal drawing_surface, history, history_index, current_project_path, is_dirty
        drawing_surface.fill("White")
        history = [(drawing_surface.copy(), "Initial")]
        history_index = 0
        current_project_path = None
        is_dirty = False
        shared_tool_context["drawing_surface"] = drawing_surface
        print("Canvas Cleared")
    
    # --- [NEW] File Operations ---
    
    def open_file():
        # [MODIFIED] Need to access history and history_index
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
                
                # [MODIFIED] Check for new format (dict) vs old (Surface)
                if isinstance(loaded_data, dict):
                    # New format
                    drawing_surface = loaded_data["main_surface"]
                    history = loaded_data["history_stack"]
                    history_index = loaded_data["history_index"]
                    print(f"Loaded project with history: {file_path}")
                else:
                    # Old format
                    drawing_surface = loaded_data
                    print(f"Loaded old project (surface only): {file_path}")
                    # Reset history
                    history = [(drawing_surface.copy(), "Loaded Old File")]
                    history_index = 0

                shared_tool_context["drawing_surface"] = drawing_surface # Update context
                current_project_path = file_path
                
            else:
                # Import image
                img = pygame.image.load(file_path).convert_alpha()
                # Fit image to canvas (optional, but good)
                img = pygame.transform.smoothscale(img, (screen_width, screen_height))
                drawing_surface.blit(img, (0,0))
                current_project_path = None # It's an import, not a project
                print(f"Imported image: {file_path}")
                # [FIX] Add history state for image import
                add_history_state(f"Import {file_path.split('/')[-1]}")

            # [FIX] Don't add history state here for .vecbo, it's loaded
            if not file_path.endswith(".vecbo"):
                add_history_state(f"Open {file_path.split('/')[-1]}")
                
            is_dirty = False # Just opened, so it's "clean"

        except Exception as e:
            print(f"Error opening file {file_path}: {e}")
            # [TODO] Show an error dialog to the user
    
    def save_vecbo():
        nonlocal is_dirty
        if not current_project_path:
            save_as_vecbo() # If no path, just do "Save As"
        else:
            try:
                # [MODIFIED] Save data as a dictionary
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
        save_vecbo() # Now that path is set, call standard save

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
            pygame.image.save(drawing_surface, file_path)
            print(f"Exported image: {file_path}")
        except Exception as e:
            print(f"Error exporting image: {e}")

    # --- [NEW] Dialog Creation ---
    def set_dialog(state, pending_action):
        nonlocal dialog_state, dialog_pending_action, dialog_buttons
        dialog_state = state
        dialog_pending_action = pending_action
        shared_tool_context["menu_open"] = None # Close file menu

        # Create buttons for the dialog
        btn_w, btn_h = 130, 40
        btn_y = dialog_rect.centery + 30
        btn_gap = 20
        total_w = (btn_w * 3) + (btn_gap * 2)
        start_x = dialog_rect.centerx - (total_w / 2)
        
        save_btn = Button(start_x, btn_y, btn_w, btn_h, "Save (.vecbo)", font_size=18, bg_color=(0, 150, 255))
        export_btn = Button(start_x + btn_w + btn_gap, btn_y, btn_w, btn_h, "Export (.png)", font_size=18, bg_color=(100, 100, 100))
        dont_save_btn = Button(start_x + (btn_w + btn_gap)*2, btn_y, btn_w, btn_h, "Don't Save", font_size=18, bg_color=(200, 50, 50))
        
        cancel_btn = Button(dialog_rect.right - 90, dialog_rect.bottom - 50, 80, 40, "Cancel", font_size=18, bg_color=(220, 220, 220), text_color=(0,0,0)) # type: ignore
        
        # If no project path, "Save" should act as "Save As"
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
    file_btn = Button(0, 0, 80, 40, "File", bg_color=(200, 200, 200), text_color=(0,0,0), font_size=25) # type: ignore
    history_btn = Button(80, 0, 100, 40, "History", bg_color=(200, 200, 200), text_color=(0,0,0), font_size=25) # type: ignore
    
    # --- File Menu Buttons ---
    # [MODIFIED] These are now created dynamically
    file_menu_buttons = []
    file_menu_hot_zone = [file_btn.rect] # Start with just the file button

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
    
    # --- [NEW] Plugin Loading ---
    loaded_tool_plugins = load_kits(components_dir="components") # List of (config, Class)
    
    # [FIX] Separate button tools from UI component tools
    loaded_tool_instances = [] # This will hold Pen, Eraser, ColorPad
    zoom_tool_instance = None # This will hold the ZoomTool
    
    # Instantiate tools and position their buttons
    toolbar_btn_x = 20
    toolbar_btn_y = 10
    toolbar_btn_size = 60
    toolbar_btn_gap = 20 # [MODIFIED] Increased from 10 to 20 for better spacing
    
    for config, ToolClass in loaded_tool_plugins:
        # Create the button rect for the tool
        btn_rect = pygame.Rect(toolbar_btn_x, toolbar_hidden_y + 10, toolbar_btn_size, toolbar_btn_size)
        
        # Instantiate the tool
        tool_instance = ToolClass(btn_rect, config)

        if hasattr(tool_instance, 'config_type') and tool_instance.config_type == "ui_component":
            zoom_tool_instance = tool_instance # Save it separately
            # Don't advance toolbar_btn_x
        else:
            loaded_tool_instances.append(tool_instance)
            # Advance the position for the next button
            toolbar_btn_x += toolbar_btn_size + toolbar_btn_gap
    
    # --- [NEW] Zoom UI ---
    # The ZoomTool instance now controls the slider
    zoom_slider_x_start = 0 # Will be set
    if zoom_tool_instance:
        zoom_slider_x_start = toolbar_btn_x + 50 # [MODIFIED] Increased gap from 30 to 50
        # Tell the zoom tool its correct X, Y position
        zoom_tool_instance.update_button_pos(zoom_slider_x_start, toolbar_hidden_y + 25)
    
    # --- [NEW] Zoom Helper Function ---
    def set_zoom(new_zoom, pivot_pos):
        """Helper to set zoom and recalculate pan offset to pivot on pivot_pos."""
        nonlocal shared_tool_context, zoom_tool_instance # [MODIFIED]
        
        new_zoom = max(0.01, min(2.0, new_zoom)) # Clamp zoom
        
        current_zoom = shared_tool_context["zoom_level"]
        current_offset = shared_tool_context["pan_offset"]
        
        # Find where on the canvas the pivot (mouse) is pointing
        canvas_pivot = screen_to_canvas(pivot_pos, current_zoom, current_offset)
        
        # Calculate the new offset to keep the canvas_pivot at the same screen_pos
        new_offset = (
            pivot_pos[0] - (canvas_pivot[0] * new_zoom),
            pivot_pos[1] - (canvas_pivot[1] * new_zoom)
        )

        shared_tool_context["zoom_level"] = new_zoom
        shared_tool_context["pan_offset"] = new_offset
        if zoom_tool_instance: # [MODIFIED]
            zoom_tool_instance.slider.set_value(new_zoom) # [MODIFIED]
            
    # --- Main Loop ---
    
    # [NEW] Handle open_file_on_start
    if open_file_on_start:
        pygame.time.set_timer(pygame.USEREVENT + 1, 100, 1) # Schedule open_file


    while running:
        mouse_pos = pygame.mouse.get_pos()
        events = pygame.event.get()
        
        # --- Update Shared Context ---
        shared_tool_context["mouse_pos"] = mouse_pos
        
        # --- [NEW] Update Zoom/Pan Context ---
        zoom = shared_tool_context["zoom_level"]
        offset = shared_tool_context["pan_offset"]
        canvas_mouse_pos = screen_to_canvas(mouse_pos, zoom, offset)
        shared_tool_context["canvas_mouse_pos"] = canvas_mouse_pos
        
        # --- [NEW] Dynamic File Menu ---
        if shared_tool_context["menu_open"] == "file":
            file_menu_buttons = []
            file_menu_hot_zone = [file_btn.rect]
            btn_y = 40
            btn_w = 250
            btn_h = 40
            
            def add_file_btn(text):
                nonlocal btn_y
                btn = Button(0, btn_y, btn_w, btn_h, text, bg_color=(220, 220, 220), text_color=(0,0,0), font_size=20, text_align="left") # type: ignore
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

        # --- Toolbar Animation Logic ---
        # [FIX] Read directly from context
        # [MODIFIED] Keep toolbar open if a dialog is active
        if shared_tool_context["menu_open"] is not None or dialog_state is not None:
            toolbar_target_y = toolbar_visible_y
        else:
            if mouse_pos[1] > screen_height - 20 or toolbar_rect.collidepoint(mouse_pos):
                toolbar_target_y = toolbar_visible_y
            else:
                toolbar_target_y = toolbar_hidden_y
            
        toolbar_current_y = lerp(toolbar_rect.y, toolbar_target_y, 0.2)
        toolbar_rect.y = round(toolbar_current_y)
        shared_tool_context["toolbar_current_y"] = toolbar_rect.y
        
        # --- Update Tool Button Positions (for animation) ---
        for tool in loaded_tool_instances: # [FIX] This list no longer contains ZoomTool
            # [FIX] Update the button's Y position based on its *original* X
            tool.update_button_pos(tool.button.rect.x, toolbar_rect.y + 10)
        
        # --- [NEW] Update Zoom Slider Position ---
        if zoom_tool_instance: # [MODIFIED]
            zoom_tool_instance.update_button_pos(zoom_slider_x_start, toolbar_rect.y + 25) # [MODIFIED]

        # --- Event Handling ---
        
        # [NEW] Refactored Event Loop
        # 1. Reset UI click flag for this frame
        shared_tool_context["click_on_ui"] = False
        
        # [NEW] STAGE 0: Handle Dialog Clicks
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
                            # After saving, perform the pending action
                            if not is_dirty: # Check if save was successful (or not cancelled)
                                dialog_state = None
                                if dialog_pending_action == "new_canvas": clear_canvas()
                                elif dialog_pending_action == "open_file": open_file()
                                elif dialog_pending_action == "exit": running = False

                        elif action_taken == "export":
                            export_as_image()
                            # Exporting doesn't clear dirty flag, so we just continue
                            # and let the user decide next
                    
                    shared_tool_context["click_on_ui"] = True
                    events.remove(event)
            
            # Consume all other events while dialog is open
            for event in events[:]: events.remove(event)
            shared_tool_context["click_on_ui"] = True


        if not dialog_state: # Only process normal events if dialog is closed
            for event in events[:]:
                
                # --- [NEW] Handle scheduled event for opening file ---
                if event.type == pygame.USEREVENT + 1:
                    open_file()
                    pygame.time.set_timer(pygame.USEREVENT + 1, 0) # Stop timer
                    continue

                # --- [FIX] REMOVED REDUNDANT MOUSEBUTTONUP LOGIC ---
                # This block was conflicting with the event logic in STAGE C.
                # The zoom slider event is already handled correctly in STAGE B.
                
                if event.type == pygame.QUIT:
                    if is_dirty:
                        set_dialog("confirm_action", "exit")
                        shared_tool_context["click_on_ui"] = True
                    else:
                        running = False

                if shared_tool_context["click_on_ui"]:
                    if event in events: events.remove(event)
                    continue

                # [REMOVED] Panning start/motion logic is now in Hand tool
                # if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2: ...
                # elif event.type == pygame.MOUSEMOTION:
                #     if is_panning: ...

                # --- [MODIFIED] Mouse Wheel Scrolling (for History or Zoom) ---
                if event.type == pygame.MOUSEWHEEL:
                    
                    # 1. Check if scrolling over history menu
                    if shared_tool_context["menu_open"] == "history" and history_placeholder_rect.collidepoint(mouse_pos):
                        if event.y > 0: history_scroll_offset = max(0, history_scroll_offset - 1)
                        elif event.y < 0:
                            max_scroll = max(0, len(history) - MAX_VISIBLE_HISTORY_ITEMS)
                            history_scroll_offset = min(max_scroll, history_scroll_offset + 1)
                        shared_tool_context["click_on_ui"] = True # Consume this event
                    
                    # 2. Check if scrolling over any other UI (top bar or toolbar)
                    elif (top_bar_rect.collidepoint(mouse_pos) or 
                          toolbar_rect.collidepoint(mouse_pos)):
                        # Do nothing, but consume the scroll
                        shared_tool_context["click_on_ui"] = True
                    
                    # 3. Otherwise, zoom the canvas
                    else:
                        current_zoom = shared_tool_context["zoom_level"]
                        if event.y > 0: # Scroll Up
                            set_zoom(min(2.0, current_zoom + 0.1), mouse_pos)
                        elif event.y < 0: # Scroll Down
                            set_zoom(max(0.01, current_zoom - 0.1), mouse_pos)
                        shared_tool_context["click_on_ui"] = True
                
                # --- Keyboard Shortcuts (Undo/Redo/Zoom/Pan) ---
                if event.type == pygame.KEYDOWN:
                    mods = pygame.key.get_mods()
                    is_ctrl_or_cmd = mods & pygame.KMOD_CTRL or mods & pygame.KMOD_META
                    is_shift = mods & pygame.KMOD_SHIFT
                    
                    # [NEW] Spacebar Panning (Hold)
                    if event.key == pygame.K_SPACE:
                        if shared_tool_context["active_tool_name"] != "hand":
                            shared_tool_context["previous_tool_name"] = shared_tool_context["active_tool_name"]
                            shared_tool_context["active_tool_name"] = "hand"
                            shared_tool_context["click_on_ui"] = True # Consume
                    
                    # Undo/Redo
                    elif event.key == pygame.K_z:
                        if is_ctrl_or_cmd:
                            if is_shift: redo()
                            else: undo()
                    elif event.key == pygame.K_y:
                        if is_ctrl_or_cmd and not is_shift: redo()
                    
                    # [NEW] Export Shortcut
                    elif event.key == pygame.K_e and is_shift:
                        export_as_image()

                    # [MODIFIED] Zoom Shortcuts
                    elif event.key == pygame.K_0 and is_ctrl_or_cmd:
                        # [FIX] Just reset state, don't pivot
                        shared_tool_context["zoom_level"] = 1.0
                        shared_tool_context["pan_offset"] = (0, 0)
                        if zoom_tool_instance: # [MODIFIED]
                            zoom_tool_instance.slider.set_value(1.0) # [MODIFIED]
                    elif event.key == pygame.K_EQUALS and is_ctrl_or_cmd:
                        set_zoom(shared_tool_context["zoom_level"] + 0.25, mouse_pos)
                    elif event.key == pygame.K_MINUS and is_ctrl_or_cmd:
                        set_zoom(shared_tool_context["zoom_level"] - 0.25, mouse_pos)
                    
                    shared_tool_context["click_on_ui"] = True # Consume key events
                
                # [NEW] Spacebar Panning (Release)
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_SPACE:
                        if shared_tool_context["active_tool_name"] == "hand":
                            shared_tool_context["active_tool_name"] = shared_tool_context["previous_tool_name"]
                            shared_tool_context["is_panning"] = False # Stop panning
                        shared_tool_context["click_on_ui"] = True # Consume
                
                # --- STAGE 1: Check for clicks on Whiteboard UI (Top Bar, Menus) ---
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
                        # ... (rest of history click logic) ...
                        if history_placeholder_rect.collidepoint(mouse_pos):
                            shared_tool_context["click_on_ui"] = True
                            # ... (logic to jump to history state) ...
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
                                    is_dirty = True # Reverting is a change
                                    print(f"Jumped to history index: {history_i}")
                                    break
                        if shared_tool_context["click_on_ui"]:
                            if event in events: events.remove(event)
                            continue

                # --- STAGE 2: Pass event to Tool layer ---
                
                # --- A. Is a tool menu open? (e.g., ColorPad) ---
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
                
                # --- B. No tool menu is open. Check tool buttons AND Zoom Slider. ---
                tool_button_was_clicked = False
                
                # [ADDED BACK] Check zoom slider first
                if zoom_tool_instance and zoom_tool_instance.handle_event(event, shared_tool_context): # [MODIFIED]
                    new_zoom = zoom_tool_instance.slider.get_value() # [MODIFIED]
                    set_zoom(new_zoom, (screen_width / 2, screen_height / 2))
                    shared_tool_context["click_on_ui"] = True
                    tool_button_was_clicked = True # Technically UI, not a "tool"
                
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for tool in loaded_tool_instances: # [FIX] This list no longer contains ZoomTool
                        # [REVERTED] Check tool buttons
                        if tool.button.rect.collidepoint(event.pos):
                            if tool.handle_event(event, shared_tool_context):
                                shared_tool_context["click_on_ui"] = True
                                tool_button_was_clicked = True
                            break
                
                if tool_button_was_clicked:
                    if event in events: events.remove(event)
                    continue
                
                # --- STAGE D: Handle "Click Outside" ---
                # [REFACTORED] This logic is now only for File/History menus.
                # Context tools (like ColorPad) now handle their own "click outside".
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

                # --- C. No UI was clicked. Pass event to *active drawing tool*. ---
                if event not in events:
                    continue

                active_tool_instance = None
                active_name = shared_tool_context.get("active_tool_name")
                for tool in loaded_tool_instances:
                    if tool.name == active_name:
                        active_tool_instance = tool
                        break
                
                if active_tool_instance:
                    # [FIX] REMOVED 'is_lmb_or_mmb_up' check.
                    # This allows MOUSEBUTTONUP events to be passed to the
                    # active tool (like HandTool) so it can stop panning.
                    
                    is_space_up = (event.type == pygame.KEYUP and event.key == pygame.K_SPACE)

                    if not is_space_up: # Still need to block spacebar release
                        if active_tool_instance.handle_event(event, shared_tool_context):
                            shared_tool_context["click_on_ui"] = True
                
                if shared_tool_context["click_on_ui"]:
                    if event in events: events.remove(event)
                    continue
            
        # --- Check for Mouse *Movement* Outside Top Menus ---
        # ... (this logic remains the same) ...
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
                
        # --- Drawing ---
        
        # [MODIFIED] Fill background. Gray is better to see canvas edges.
        screen.fill((80, 80, 80)) 
        
        # --- [NEW] Draw Scaled Canvas ---
        zoom = shared_tool_context["zoom_level"]
        offset = shared_tool_context["pan_offset"]
        
        scaled_size = (
            int(screen_width * zoom), 
            int(screen_height * zoom)
        )
        
        if scaled_size[0] > 0 and scaled_size[1] > 0:
            # Scale the *original* canvas
            scaled_canvas = pygame.transform.scale(drawing_surface, scaled_size)
            # Blit it at the pan offset
            screen.blit(scaled_canvas, offset)
        else:
            # Fallback if zoom is tiny
            screen.fill("White") 
        
        # --- Draw Custom Cursor ---
        is_on_canvas = (
            not top_bar_rect.collidepoint(mouse_pos) and
            not toolbar_rect.collidepoint(mouse_pos) and
            shared_tool_context["menu_open"] is None and
            not shared_tool_context["is_panning"] and # [MODIFIED] Check context
            dialog_state is None # [NEW] Hide cursor when dialog is open
        )
        
        active_tool_instance = None
        active_name = shared_tool_context.get("active_tool_name")
        for tool in loaded_tool_instances:
            if tool.name == active_name:
                active_tool_instance = tool
                break
        
        # [MODIFIED] Show circle cursor ONLY if a drawing tool is active
        if is_on_canvas and active_tool_instance and active_tool_instance.is_drawing_tool:
            pygame.mouse.set_visible(False)
            
            radius = 0
            fill_color = (0,0,0)
            
            if active_name == "pen":
                radius = shared_tool_context["draw_size"] // 2
                fill_color = shared_tool_context["draw_color"]
            elif active_name == "eraser":
                radius = shared_tool_context["eraser_size"] // 2
                fill_color = (255, 255, 255)
            
            # [NEW] Scale cursor radius by zoom level
            screen_radius = max(1, int(radius * zoom))

            # [FIX] Draw a consistent, high-contrast stroked ring
            # that is visible on all backgrounds, removing the
            # distracting color-inverting logic.
            
            # 1. Draw the fill color (Pen or Eraser)
            pygame.draw.circle(screen, fill_color, mouse_pos, screen_radius)
            
            # 2. Draw an outer black ring (2px)
            pygame.draw.circle(screen, (0, 0, 0), mouse_pos, screen_radius, width=2)
            
            # 3. Draw an inner white ring (1px)
            if screen_radius > 3: # Only draw inner ring if there's space
                pygame.draw.circle(screen, (255, 255, 255), mouse_pos, screen_radius - 2, width=1)
        
        # [NEW] Show hand cursor if panning
        elif shared_tool_context["is_panning"]:
            # [TODO] Add custom hand cursor
            pygame.mouse.set_visible(True) # For now, just show default arrow
        
        else:
            pygame.mouse.set_visible(True)

        
        # --- Draw Top Menu Bar ---
        pygame.draw.rect(screen, (200, 200, 200), top_bar_rect)
        file_btn.draw(screen)
        history_btn.draw(screen)
        
        # --- Draw Open Menus ---
        if shared_tool_context["menu_open"] == "file":
            for btn in file_menu_buttons:
                btn.draw(screen)
        
        if shared_tool_context["menu_open"] == "history":
            # ... (rest of history drawing logic remains the same) ...
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
        
        # --- [NEW] Draw Tools ---
        for tool in loaded_tool_instances: # [FIX] This list no longer contains ZoomTool
            tool.draw(screen, shared_tool_context)
            
        # [ADDED BACK] Draw Zoom UI on toolbar
        if zoom_tool_instance: # [MODIFIED]
            zoom_tool_instance.draw(screen, shared_tool_context) # [MODIFIED]
            
        # --- [NEW] Draw Dialog ---
        if dialog_state is not None:
            # Draw semi-transparent overlay
            overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            # Draw dialog box
            pygame.draw.rect(screen, (230, 230, 230), dialog_rect, border_radius=5)
            pygame.draw.rect(screen, (100, 100, 100), dialog_rect, 2, border_radius=5)
            
            # Draw text
            title_surf = dialog_title_font.render("You have unsaved changes!", True, (0,0,0))
            screen.blit(title_surf, title_surf.get_rect(centerx=dialog_rect.centerx, y=dialog_rect.y + 20))
            
            prompt_surf = dialog_font.render("What would you like to do?", True, (50,50,50))
            screen.blit(prompt_surf, prompt_surf.get_rect(centerx=dialog_rect.centerx, y=dialog_rect.y + 60))
            
            # Draw buttons
            for item in dialog_buttons:
                item["btn"].draw(screen)
            
        pygame.display.flip()
        clock.tick(60)

    pygame.mouse.set_visible(True)

