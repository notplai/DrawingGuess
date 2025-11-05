import os
import json
import importlib.util
import sys
import pygame
from typing import Any, List, Tuple, Dict, Type, Optional
from libs.utils.pylog import Logger

logger = Logger("KitLoaderV2")

# --- Config Import Fallback ---
try:
    from libs.utils.configs import loadsConfig
except ImportError:
    logger.error("Error: Could not import loadsConfig. Defaulting to 'BubblePencil' theme.")
    # Define a fallback function if import fails
    def loadsConfig() -> Dict[str, Any]:
        """Fallback config loader."""
        return {"themes": "BubblePencil"}
# --- End Config Import Fallback ---

# Loads component tools using the v2 loader specification.
def loads(components_dir: str = "components") -> List[Tuple[Dict[str, Any], Type]]:
    """
    Scans for component kits supporting v2 loader.
    This version adds support for theme-aware icons and cursors.

    Args:
        components_dir: The root directory to scan for component kits.

    Returns:
        A list of tuples, where each tuple contains:
            - A dictionary (tool_config) with tool metadata.
            - The loaded tool class (ToolClass).
    """
    loaded_tools: List[Tuple[Dict[str, Any], Type]] = []
    
    settings: Dict[str, Any] = loadsConfig()
    theme_name: str = settings.get('themes', 'BubblePencil')
    theme_folder: str = f".{theme_name}" # e.g., ".BubblePencil"
    logger.info(f"KitLoader v2: Loading assets for theme: {theme_name}")

    base_components_dir: str = os.path.abspath(components_dir)
    if not os.path.exists(base_components_dir):
        logger.warning(f"Warning: Components directory not found: {base_components_dir}")
        return []

    logger.info(f"Scanning for component kits in: {base_components_dir}")
    
    for kit_name in os.listdir(base_components_dir):
        kit_path: str = os.path.join(base_components_dir, kit_name)
        if not os.path.isdir(kit_path):
            continue
            
        config_path: str = os.path.join(kit_path, "initial.json")
        if not os.path.exists(config_path):
            logger.info(f"Skipping '{kit_name}': No 'initial.json' found.")
            continue
            
        logger.info(f"Found component kit: {kit_name}")
        try:
            with open(config_path, 'r') as f:
                kit_config: Dict[str, Any] = json.load(f)
            
            # Note: v2 loader doesn't check the version, it's triggered by the main __init__.
            loader_version: Any = kit_config.get("kits-loaders", 0)
            
            # Fallback texture path
            project_asset_dir: str = os.path.abspath(os.path.join(os.getcwd(), 'assets/textures/common/static'))
            # Kit-specific asset path
            base_asset_dir: str = os.path.abspath(os.path.join(kit_path, 'assets'))

            components_config: Dict[str, Any] = kit_config.get("components", {})
            logger.info(f"Loading kit: {components_config.get('name')} v{components_config.get('version')}")

            for tool_config in kit_config.get("@objects", []):
                try:
                    main_file: str = tool_config["main_file"]
                    main_class: str = tool_config["main_class"]
                    
                    module_path: str = os.path.abspath(os.path.join(kit_path, main_file))
                    module_name: str = f"components.{kit_name}.{main_file.replace('.py', '').replace(os.sep, '.')}"
                    
                    if not os.path.exists(module_path):
                        logger.error(f"Error: main_file not found for tool '{tool_config['name']}': {module_path}")
                        continue
                    
                    # --- Dynamic Module Loading ---
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    if spec is None or spec.loader is None:
                        logger.error(f"Error: Could not create spec for module {module_name} at {module_path}")
                        continue
                        
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module 
                    spec.loader.exec_module(module)
                    ToolClass: Type = getattr(module, main_class)
                    # --- End Dynamic Module Loading ---
                    
                    # Initialize icon/cursor paths in the config
                    tool_config["icon_path"] = None
                    tool_config["cursor_path"] = None
                    tool_config["cursor_size"] = None
                    tool_config["cursor_hotspot"] = None
                    tool_config["cursor_offset"] = [0, 0]

                    icons_config: Dict[str, Any] = tool_config.get("icons", {})
                    
                    # --- Load Tool Icon (Theme-aware) ---
                    tool_icon_name: Optional[str] = icons_config.get("tools")
                    if tool_icon_name:
                        icon_path: str
                        if tool_icon_name.startswith("."): # Theme-specific icon
                            icon_path = os.path.join(base_asset_dir, theme_folder, "tools", tool_icon_name.lstrip('.'))
                        else: # Generic icon
                            icon_path = os.path.join(base_asset_dir, tool_icon_name)
                        
                        if os.path.exists(icon_path):
                            tool_config["icon_path"] = icon_path
                        else:
                            logger.warning(f"Warning: Tool icon file not found: {icon_path}")
                            fallback_path: str = os.path.join(project_asset_dir, 'miss_texture.png'.lstrip('.'))
                            if os.path.exists(fallback_path):
                                logger.info(f"Info: Loading fallback icon: {fallback_path}")
                                tool_config["icon_path"] = fallback_path

                    # --- Load Cursor Icon (Theme-aware) ---
                    cursor_icon_name: Optional[str] = icons_config.get("cursor")
                    if cursor_icon_name:
                        cursor_icon_path: str
                        if cursor_icon_name.startswith("."): # Theme-specific cursor
                            cursor_icon_path = os.path.join(base_asset_dir, theme_folder, "cursors", cursor_icon_name.lstrip('.'))
                        else: # Generic cursor
                            cursor_icon_path = os.path.join(base_asset_dir, cursor_icon_name)
                            
                        if os.path.exists(cursor_icon_path):
                            tool_config["cursor_path"] = cursor_icon_path
                        else:
                            logger.warning(f"Warning: Cursor icon file not found: {cursor_icon_path}")
                            fallback_path = os.path.join(project_asset_dir, 'miss_texture.png'.lstrip('.'))
                            if os.path.exists(fallback_path):
                                logger.info(f"Info: Loading fallback cursor: {fallback_path}")
                                tool_config["cursor_path"] = fallback_path

                    # Load cursor metadata
                    tool_config["cursor_size"] = icons_config.get("cursor_size")
                    tool_config["cursor_hotspot"] = icons_config.get("cursor_hotspot")
                    tool_config["cursor_offset"] = icons_config.get("cursor_offset", [0, 0])


                    loaded_tools.append((tool_config, ToolClass))
                    logger.info(f"  Successfully loaded object: {tool_config['name']}")

                except Exception as e:
                    logger.error(f"Error loading tool object '{tool_config.get('name', 'UNKNOWN')}': {e}")
                    import traceback
                    traceback.print_exc()

        except Exception as e:
            logger.error(f"Error parsing 'initial.json' for kit {kit_name}: {e}")
    
    return loaded_tools