import os
import json
import importlib.util
import sys
import pygame
from typing import Any, List, Tuple, Dict, Type
from libs.utils.pylog import Logger

logger = Logger("KitLoaderV1")

# Loads component tools using the v1 loader specification.
def loads(components_dir: str = "components") -> List[Tuple[Dict[str, Any], Type]]:
    """
    Scans the components directory, finds kits with "kits-loaders": "1.0.0",
    and loads their tools (classes and configs) dynamically.

    Args:
        components_dir: The root directory to scan for component kits.

    Returns:
        A list of tuples, where each tuple contains:
            - A dictionary (tool_config) with tool metadata.
            - The loaded tool class (ToolClass).
    """
    loaded_tools: List[Tuple[Dict[str, Any], Type]] = []
    
    base_components_dir: str = os.path.abspath(components_dir)
    if not os.path.exists(base_components_dir):
        logger.warning(f"Warning: Components directory not found: {base_components_dir}")
        return []

    logger.info(f"Scanning for component kits in: {base_components_dir}")
    
    # Iterate through each item in the components directory
    for kit_name in os.listdir(base_components_dir):
        kit_path: str = os.path.join(base_components_dir, kit_name)
        if not os.path.isdir(kit_path):
            continue # Skip files
            
        # Look for the 'initial.json' config file
        config_path: str = os.path.join(kit_path, "initial.json")
        if not os.path.exists(config_path):
            logger.info(f"Skipping '{kit_name}': No 'initial.json' found.")
            continue
            
        logger.info(f"Found component kit: {kit_name}")
        try:
            with open(config_path, 'r') as f:
                kit_config: Dict[str, Any] = json.load(f)
            
            # Check if this loader (v1.0.0) can handle this kit
            loader_version: str = kit_config.get("kits-loaders", "0.0.0")
            if loader_version != "1.0.0":
                logger.warning(f"Warning: Skipping kit '{kit_name}'. It requires loader v{loader_version}, but we are v1.0.0.")
                continue
                
            logger.info(f"Loading kit: {kit_config.get('components-name')} v{kit_config.get('components-version')}")

            # Load each tool defined in the kit's "@objects" list
            for tool_config in kit_config.get("@objects", []):
                try:
                    main_file: str = tool_config["main_file"]
                    main_class: str = tool_config["main_class"]
                    
                    module_path: str = os.path.abspath(os.path.join(kit_path, main_file))
                    
                    # Create a unique module name
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
                    sys.modules[module_name] = module # Add to sys.modules to handle relative imports
                    spec.loader.exec_module(module)
                    # --- End Dynamic Module Loading ---
                    
                    # Get the tool's main class from the loaded module
                    ToolClass: Type = getattr(module, main_class)
                    
                    # Load icon path if specified
                    if tool_config.get("icon_pic"):
                        icon_path: str = os.path.abspath(os.path.join(kit_path, tool_config["icon_pic"]))
                        if os.path.exists(icon_path):
                            tool_config["icon_path"] = icon_path
                        else:
                            logger.warning(f"Warning: Icon file not found: {icon_path}")
                            tool_config["icon_path"] = None
                    else:
                        tool_config["icon_path"] = None
                    
                    loaded_tools.append((tool_config, ToolClass))
                    logger.info(f"  Successfully loaded object: {tool_config['name']}")

                except Exception as e:
                    logger.error(f"Error loading tool object '{tool_config.get('name', 'UNKNOWN')}': {e}")
                    import traceback
                    traceback.print_exc()

        except Exception as e:
            logger.error(f"Error parsing 'initial.json' for kit {kit_name}: {e}")
    
    return loaded_tools