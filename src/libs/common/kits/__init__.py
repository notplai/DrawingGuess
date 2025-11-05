import os
from typing import Union, Optional, Any, List, Tuple, Dict, Type
from .initial import get # Utility to read 'initial.json'

from .components.contexts import SharedContext

# Import all available loader versions
from .components.builds import v1, v2, v3, v3_1

from libs.utils.pylog import Logger
logger = Logger(__name__)

# Main function to load all component kits.
def components(fdir: str = "components", /) -> List[Tuple[Dict[str, Optional[Any]], Type]]:
    """
    Scans a directory for component kits, reads their 'initial.json',
    and uses the specified 'kits-loaders' version to load them.

    This function acts as a dispatcher, calling the correct loader
    (v1, v2, v3, v3_1) based on the kit's configuration.

    Args:
        fdir: The root directory to scan for component kits (e.g., "components").

    Returns:
        A list of tuples, where each tuple contains:
            - A dictionary with the processed tool configuration.
            - The loaded tool class.
    """
    components: List[Tuple[Dict[str, Optional[Any]], Type]] = []
    bdr: str = os.path.abspath(fdir) # base_directory
    if not os.path.exists(bdr):
        logger.warning(f"Warning: Components directory not found: {bdr}")
        return components

    # Keep track of which loaders we have already run to avoid duplicates
    loaders_run: set[Any] = set()

    # Scan each subdirectory in the components folder
    for e in os.scandir(bdr):
        if e.is_dir():
            kpath: str = e.path
            try:
                # Read the kit's config file
                initial: Dict[str, Any] = get(kpath, 'initial.json')
                # Get the loader version required by this kit
                __lv: Any = initial.get("kits-loaders", "unkown") 
                
                try:
                    # Try to convert version to a float or int
                    __lv = float(__lv) if '.' in str(__lv) else int(__lv)
                except ValueError:
                    pass # Keep it as a string if conversion fails

                # --- Dispatch to the correct loader ---
                if __lv == 1 and 1 not in loaders_run:
                    logger.info("Running Kit Loader v1...")
                    components.extend(v1(fdir))
                    loaders_run.add(1)
                elif __lv == 2 and 2 not in loaders_run:
                    logger.info("Running Kit Loader v2...")
                    components.extend(v2(fdir))
                    loaders_run.add(2)
                elif __lv == 3 and 3 not in loaders_run:
                    logger.info("Running Kit Loader v3...")
                    components.extend(v3(fdir))
                    loaders_run.add(3)
                elif __lv == 3.1 and 3.1 not in loaders_run:
                    logger.info("Running Kit Loader v3.1...")
                    components.extend(v3_1(fdir))
                    loaders_run.add(3.1)
                elif __lv not in [1, 2, 3, 3.1] and __lv not in loaders_run:
                    # Log a warning for unknown or unsupported loaders
                    logger.warning(f"Warning: Skipping kit '{e.name}'. It requires loader v{__lv}, but no compatible loader found.")
                    loaders_run.add(__lv)
            
            except FileNotFoundError:
                logger.warning(f"Warning: No 'initial.json' found in {e.path}, skipping.")
            except Exception as ex:
                logger.error(f"Error processing kit '{e.name}': {ex}")

    return components

    
# Import and re-export the 'resources' loader function
from .resources import loads as resources