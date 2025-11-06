import os
from typing import Union, Optional, Any, List, Tuple, Dict, Type, Callable
from .initial import get

from .components.contexts import SharedContext

from .components.builds import v1, v2, v3, v3_1

from libs.utils.pylog import Logger
logger = Logger(__name__)

LOADER_MAP: Dict[Any, Callable[[str], Tuple[Dict[str, Optional[Any]], Type]]] = {
    1: v1,
    2: v2,
    3: v3,
    3.1: v3_1,
}

def components(fdir: str = "components", /) -> List[Tuple[Dict[str, Optional[Any]], Type]]:
    """
    Scans a directory ONCE for component kits and loads them
    using a kit-specific loader.
    """
    components: List[Tuple[Dict[str, Optional[Any]], Type]] = []
    bdr: str = os.path.abspath(fdir)
    if not os.path.exists(bdr):
        logger.warning(f"Components directory not found: {bdr}")
        return components

    # Scan each subdirectory in the components folder ONCE
    for e in os.scandir(bdr):
        if e.is_dir():
            kpath: str = e.path
            try:
                initial: Dict[str, Any] = get(kpath, 'initial.json')
                __lv: Any = initial.get("kits-loaders", "unknown") 
                
                try:
                    __lv = float(__lv) if '.' in str(__lv) else int(__lv)
                except ValueError:
                    pass

                if __lv in LOADER_MAP:
                    components.extend(LOADER_MAP[__lv](kpath))
                else:
                    logger.warning(f"This '{e.name}' components cannot load for v{__lv}.")
            
            except FileNotFoundError:
                logger.warning(f"No 'initial.json' found in '{e.path}'.")
            except Exception as ex:
                logger.exception(f"Error processing kit '{e.name}'\n|- {ex.__traceback__}")

    return components

    
# Import and re-export the 'resources' loader function
from .resources import loads as resources