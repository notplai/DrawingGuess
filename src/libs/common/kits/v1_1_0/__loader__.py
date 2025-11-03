import os
import json
import importlib.util
import sys
import pygame

# Import the config loader to get theme settings
try:
    from libs.utils.configs import loadsConfig
except ImportError:
    # Fallback in case path is tricky, though it should be in sys.path
    print("Error: Could not import loadsConfig. Defaulting to 'BubblePencil' theme.")
    def loadsConfig():
        return {"themes": "BubblePencil"}

def loads(components_dir="components"):
    """
    Scans for component "kits", loads their 'initial.json' configs,
    and imports their main tool classes.
    
    Version 1.1.0 (Modified):
    - Checks for "kits-loaders" version "1.1.0".
    - Reads "components.assets" for the base asset directory.
    - Loads theme settings to build theme-aware paths for icons.
    - Parses the "icons" dictionary for "tools" and "cursor" paths.
    -  Parses "icons" for "cursor_size", "cursor_hotspot", and "cursor_offset".
    - Adds all loaded paths and properties to the tool_config.
    
    Returns a list of tuples: (config_object, ToolClass)
    """
    loaded_tools = []
    
    # Load settings to get the current theme
    settings = loadsConfig()
    theme_name = settings.get('themes', 'BubblePencil') # Default theme
    theme_folder = f".{theme_name}"
    print(f"KitLoader v1.1.0: Loading assets for theme: {theme_name}")

    # Use an absolute path for reliability
    base_components_dir = os.path.abspath(components_dir)
    if not os.path.exists(base_components_dir):
        print(f"Warning: Components directory not found: {base_components_dir}")
        return []

    print(f"Scanning for component kits in: {base_components_dir}")
    
    # Iterate over component packs (e.g., "@builtins", "custom_shapes")
    for kit_name in os.listdir(base_components_dir):
        kit_path = os.path.join(base_components_dir, kit_name)
        if not os.path.isdir(kit_path):
            continue
            
        config_path = os.path.join(kit_path, "initial.json")
        if not os.path.exists(config_path):
            print(f"Skipping '{kit_name}': No 'initial.json' found.")
            continue
            
        print(f"Found component kit: {kit_name}")
        try:
            with open(config_path, 'r') as f:
                kit_config = json.load(f)
            
            # ---  Check compatibility ---
            loader_version = kit_config.get("kits-loaders", "0.0.0")
            if loader_version != "1.1.0":
                print(f"Warning: Skipping kit '{kit_name}'. It requires loader v{loader_version}, but we are v1.1.0.")
                continue
            
            # Get base asset directory from config
            project_asset_dir = os.path.abspath(os.path.join(os.getcwd(), 'assets/textures/common/static'))

            components_config = kit_config.get("components", {})
            base_asset_path = components_config.get("assets", "assets")
            base_asset_dir = os.path.abspath(os.path.join(kit_path, base_asset_path))

            print(f"Loading kit: {components_config.get('name')} v{components_config.get('version')}")

            # --- Load all objects in the kit ---
            for tool_config in kit_config.get("@objects", []):
                try:
                    main_file = tool_config["main_file"]
                    main_class = tool_config["main_class"]
                    
                    module_path = os.path.abspath(os.path.join(kit_path, main_file))
                    module_name = f"components.{kit_name}.{main_file.replace('.py', '').replace(os.sep, '.')}"
                    
                    if not os.path.exists(module_path):
                         print(f"Error: main_file not found for tool '{tool_config['name']}': {module_path}")
                         continue
                    
                    # Dynamically import the module
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    if spec is None:
                        print(f"Error: Could not create spec for module {module_name} at {module_path}")
                        continue
                        
                    module = importlib.util.module_from_spec(spec)
                    
                    # Add to sys.modules to handle relative imports *if needed*
                    sys.modules[module_name] = module 
                    spec.loader.exec_module(module) # type: ignore
                    ToolClass = getattr(module, main_class)
                    
                    # Theme-aware Icon Path Processing ---
                    tool_config["icon_path"] = None
                    tool_config["cursor_path"] = None
                    tool_config["cursor_size"] = None # 
                    tool_config["cursor_hotspot"] = None # 
                    tool_config["cursor_offset"] = [0, 0] #  Default offset

                    icons_config = tool_config.get("icons", {})
                    
                    # 1. Load Tool Icon
                    tool_icon_name = icons_config.get("tools")
                    if tool_icon_name:
                        if tool_icon_name.startswith("."):
                            # Theme-based path: {assets}/.{ThemeName}/tools/{icon.png}
                            icon_path = os.path.join(base_asset_dir, theme_folder, "tools", tool_icon_name.lstrip('.'))
                        else:
                            # Direct path: {assets}/{icon.png}
                            icon_path = os.path.join(base_asset_dir, tool_icon_name)
                        
                        if os.path.exists(icon_path):
                            tool_config["icon_path"] = icon_path
                        else:
                            print(f"Warning: Tool icon file not found: {icon_path}")
                            fallback_path = os.path.join(project_asset_dir, 'miss_texture.png'.lstrip('.'))
                            if os.path.exists(fallback_path):
                                print(f"Info: Loading fallback icon: {fallback_path}")
                                tool_config["icon_path"] = fallback_path

                    # 2. Load Cursor Icon
                    cursor_icon_name = icons_config.get("cursor")
                    if cursor_icon_name:
                        if cursor_icon_name.startswith("."):
                            # Theme-based path: {assets}/.{ThemeName}/cursors/{icon.png}
                            icon_path = os.path.join(base_asset_dir, theme_folder, "cursors", cursor_icon_name.lstrip('.'))
                        else:
                            # Direct path: {assets}/{icon.png}
                            icon_path = os.path.join(base_asset_dir, cursor_icon_name)
                            
                        if os.path.exists(icon_path):
                            tool_config["cursor_path"] = icon_path
                        else:
                            print(f"Warning: Cursor icon file not found: {icon_path}")
                            fallback_path = os.path.join(project_asset_dir, 'miss_texture.png'.lstrip('.'))
                            if os.path.exists(fallback_path):
                                print(f"Info: Loading fallback cursor: {fallback_path}")
                                tool_config["cursor_path"] = fallback_path

                    # ---  Load Cursor Config ---
                    # Read size and hotspot from the icons config block
                    tool_config["cursor_size"] = icons_config.get("cursor_size") #
                    tool_config["cursor_hotspot"] = icons_config.get("cursor_hotspot") # e.g., "center"
                    #
                    tool_config["cursor_offset"] = icons_config.get("cursor_offset", [0, 0])


                    loaded_tools.append((tool_config, ToolClass))
                    print(f"  Successfully loaded object: {tool_config['name']}")

                except Exception as e:
                    print(f"Error loading tool object '{tool_config.get('name', 'UNKNOWN')}': {e}")
                    import traceback
                    traceback.print_exc()

        except Exception as e:
            print(f"Error parsing 'initial.json' for kit {kit_name}: {e}")
    
    return loaded_tools
