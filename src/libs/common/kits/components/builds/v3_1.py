import os
import json
import importlib.util
import sys
from typing import Any, List, Tuple, Dict, Type
import pygame

from libs.utils.configs import loadsConfig
from libs.common.kits.initial import get as getInitial

from libs.utils.pylog import Logger
logger = Logger("KitLoaderV3.1")

# Loads component tools using the v3.1 loader specification.
def loads(components_dir: str = "components") -> List[Tuple[Dict[str, Any], Type]]:
    """
    Scans a SINGLE component kit directory supporting v3.1 loader.
    This function expects 'components_dir' to be the path to the kit
    (e.g., '.../components/@builtins'), NOT the parent 'components' directory.

    Args:
        components_dir: The path to the specific component kit directory.

    Returns:
        A list of tuples, where each tuple contains:
            - A dictionary (objects) with processed tool config and paths.
            - The loaded tool class (ToolClass).
    """
    tools: List[Tuple[Dict[str, Any], Type]] = []

    settings: Dict[str, Any] = loadsConfig()
    theme: str = settings.get('themes', 'BubblePencil')
    theme_directories: str = f".{theme}"
    logger.info(f"KitLoader v3.1: Loading kit from: {components_dir}")

    kpath: str = os.path.abspath(components_dir)
    
    if not os.path.exists(kpath):
        logger.warning(f"Warning: Component kit directory not found: {kpath}")
        return tools
    
    # Get the kit's name (e.g., '@builtins') from its path
    kit_name: str = os.path.basename(kpath)

    try:
        # Look for initial.json directly in the kit path
        initial: Dict[str, Any] = getInitial(kpath, 'initial.json')
        missingTexture: str = os.path.abspath(os.path.join(os.getcwd(), 'src/assets/textures/common/static/missing.png'))
        
        components_intializer: Dict[str, Any] = initial["components"]
        project_assets: str = os.path.abspath(os.path.join(kpath, 'assets'))

        logger.debug(f"Loading kit: {components_intializer.get('name')} v{components_intializer.get('version')}")

        for toolObject in initial.get("@objects", []):
            try:
                # Determine main file path
                main_file: str = toolObject["main_file"] if toolObject["main_file"].endswith(".py") else toolObject["main_file"] + ("__init__.py" if toolObject["main_file"][-1] in "/\\" else ".py")
                main_class: str = toolObject["main_class"]

                modpath: str = os.path.abspath(os.path.join(kpath, main_file))
                if not os.path.exists(modpath):
                    logger.warning(f"Main file not found for tool '{toolObject['name']}': {modpath}")
                    continue
                
                # Use the kit_name for the module path
                modname: str = f"components.{kit_name}.{main_file.replace('.py', '').replace(os.sep, '.')}"

                # --- Dynamic Module Loading ---
                spec = importlib.util.spec_from_file_location(modname, modpath)
                if spec is None or spec.loader is None:
                    logger.warning(f"Could not load module for package.\n|- Module {modname}\n|- At {modpath}")
                    continue
                module = importlib.util.module_from_spec(spec)

                sys.modules[modname] = module
                spec.loader.exec_module(module)
                ToolClass: Type = getattr(module, main_class)
                # --- End Dynamic Module Loading ---
                
                icons: Dict[str, Any] = toolObject.get("icons", {})

                # --- Lambda for asset path resolution ---
                get_asset_path = (
                    lambda file, asset_type: missingTexture if not file else
                    (path if os.path.exists(path := (
                        os.path.join(project_assets, theme_directories, asset_type, file.lstrip('.'))
                        if file.startswith(".")
                        else os.path.join(project_assets, file)
                    )) else missingTexture)
                )
                # --- End Lambda ---

                # Build the processed config dictionary
                objects: Dict[str, Any] = {
                    "name": toolObject.get('name'),
                    "registryId": modname,
                    "type": toolObject['type'],
                    "tool": get_asset_path(icons.get("tools"), "tools"),
                    "cursor": {
                        "icon": get_asset_path(icons.get("cursor"), "cursors"),
                        "hotspot": icons.get("cursor_hotspot"),
                        "size": icons.get("cursor_size"),
                        "offset": icons.get("cursor_offset", [0, 0])
                    },
                    # Get the methods to be injected from the class
                    "injected_methods": getattr(ToolClass, 'INJECT_METHODS', {})
                }

                tools.append((objects, ToolClass))
                logger.info(f"Loaded component tool '{toolObject.get('name', 'Unknown')}'")
            except Exception as _:
                logger.warning(f"ParsingError cannot read '{toolObject.get('name', 'Unknown')}' tool config.\n|-{str(_)}")
                continue

    except FileNotFoundError as _:
        logger.warning(f"Initializer 'initial.json' on package '{kpath}' is not found.\n|-{str(_)}")
    except KeyError as _:
        logger.warning(f"ParsingError on package '{kpath}' is malformed or incomplete.\n|-{str(_)}")

    return tools