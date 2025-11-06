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
        logger.warning(f"Components directory not found: {base_components_dir}")
        return []
    
    # Iterate through each item in the components directory
    for component in os.listdir(base_components_dir):
        kit_path: str = os.path.join(base_components_dir, component)
        if not os.path.isdir(kit_path):
            continue # Skip files
            
        # Look for the 'initial.json' config file
        config_path: str = os.path.join(kit_path, "initial.json")
        if not os.path.exists(config_path):
            logger.warning(f"Could not loaded '{component}'\n|- No 'initial.json' found.")
            continue
            
        try:
            with open(config_path, 'r') as f:
                kit_config: Dict[str, Any] = json.load(f)
                
            logger.info(f"Loading component\n|-{kit_config.get('components-name')} v{kit_config.get('components-version')}")

            # Load each tool defined in the kit's "@objects" list
            for tool_config in kit_config.get("@objects", []):
                try:
                    main_file: str = tool_config["main_file"]
                    main_class: str = tool_config["main_class"]
                    
                    module_path: str = os.path.abspath(os.path.join(kit_path, main_file))
                    
                    # Create a unique module name
                    module_name: str = f"components.{component}.{main_file.replace('.py', '').replace(os.sep, '.')}"
                    
                    if not os.path.exists(module_path):
                         logger.exception(f"Cannot loads 'main_file' cause it not found for tool '{tool_config['name']}'\n|- At {module_path}")
                         continue
                    
                    # --- Dynamic Module Loading ---
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    if spec is None or spec.loader is None:
                        logger.exception(f"Could not create spec for module {module_name}\n|- At {module_path}")
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
                            logger.warning(f"Icon file not found.\n|- At {icon_path}")
                            tool_config["icon_path"] = None
                    else:
                        tool_config["icon_path"] = None
                    
                    loaded_tools.append((tool_config, ToolClass))
                    logger.info(f"Loaded tool '{tool_config['name']}' Object.")

                except Exception as e:
                    logger.exception(f"Cannot loading tool '{tool_config.get('name', 'UNKNOWN')}' Object.\n|- {e}")
                    import traceback
                    traceback.print_exc()

        except Exception as e:
            logger.exception(f"Cannot parsing 'initial.json' for {component} component.\n|- {e}")
    
    return loaded_tools