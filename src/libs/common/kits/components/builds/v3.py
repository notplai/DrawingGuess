import os
import json
import importlib.util
import sys
from typing import Any, List, Tuple, Dict, Type
import pygame

from libs.utils.configs import loadsConfig
from libs.common.kits.initial import get as getInitial

from libs.utils.pylog import Logger
logger = Logger("KitLoaderV3")

# Loads component tools using the v3 loader specification.
def loads(components_dir: str = "components") -> List[Tuple[Dict[str, Any], Type]]:
    """
    Scans for component kits supporting v3 loader.
    This version refactors asset loading with lambdas for cleaner path generation.

    Args:
        components_dir: The root directory to scan for component kits.

    Returns:
        A list of tuples, where each tuple contains:
            - A dictionary (objects) with processed tool config and paths.
            - The loaded tool class (ToolClass).
    """
    tools: List[Tuple[Dict[str, Any], Type]] = []

    settings = loadsConfig()
    theme: str = settings.get('themes', 'BubblePencil')
    theme_directories: str = f".{theme}" # e.g., ".BubblePencil"
    logger.info(f"KitLoader v3: Loading assets for theme: {theme}")

    bcd: str = os.path.abspath(components_dir) # base_components_dir
    if not os.path.exists(bcd):
        logger.warning(f"Warning: Components directory not found: {bcd}")
        return tools
    
    for e in os.scandir(bcd):
        if e.is_dir():
            kpath: str = e.path
            try:
                initial: Dict[str, Any] = getInitial(kpath, 'initial.json')
                missingTexture: str = os.path.abspath(os.path.join(os.getcwd(), 'src/assets/textures/common/static/missing.png'))
                
                components_intializer: Dict[str, Any] = initial["components"]
                project_assets: str = os.path.abspath(os.path.join(kpath, 'assets'))

                logger.debug(f"Loading kit: {components_intializer.get('name')} v{components_intializer.get('version')}")

                for toolObject in initial.get("@objects", []):
                    try:
                        # Determine main file path (handling packages vs. modules)
                        main_file: str = toolObject["main_file"] if toolObject["main_file"].endswith(".py") else toolObject["main_file"] + ("__init__.py" if toolObject["main_file"][-1] in "/\\" else ".py")
                        main_class: str = toolObject["main_class"]

                        modpath: str = os.path.abspath(os.path.join(kpath, main_file))
                        if not os.path.exists(modpath):
                            logger.warning(f"Main file not found for tool '{toolObject['name']}': {modpath}")
                            continue
                        modname: str = f"components.{e.name}.{main_file.replace('.py', '').replace(os.sep, '.')}"

                        # --- Dynamic Module Loading ---
                        spec = importlib.util.spec_from_file_location(modname, modpath)
                        if spec is None or spec.loader is None:
                            logger.warning(f"Could not load module for package.\n|- Module {modname}\n|- AtPath {modpath}")
                            continue
                        module = importlib.util.module_from_spec(spec)

                        sys.modules[modname] = module
                        spec.loader.exec_module(module) 
                        ToolClass: Type = getattr(module, main_class)
                        # --- End Dynamic Module Loading ---
                        
                        icons: Dict[str, Any] = toolObject.get("icons", {})

                        # --- Lambda for asset path resolution ---
                        # This lambda checks for a theme-specific file (if path starts with "."),
                        # then a generic kit file, and falls back to missingTexture.
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
                            }
                        }

                        tools.append((objects, ToolClass))
                        logger.info(f"Loaded component tool '{toolObject.get('name', 'Unknown')}'")
                    except Exception as _:
                        logger.warning(f"ParsingError cannot read '{toolObject.get('name', 'Unknown')}' tool config.\n|-{str(_)}")
                        continue
            except FileNotFoundError as _:
                logger.warning(f"Initializer components on package '{kpath}' is not found.\n|-{str(_)}")
            except KeyError as _:
                logger.warning(f"ParsingError on package '{kpath}' is malformed or incomplete.\n|-{str(_)}")

    return tools