import os
import json
from typing import Any, Dict

# Reads and parses an 'initial.json' file from a component kit directory.
def get(fdir: str, ftar: str = 'initial.json') -> Dict[str, Any]:
    """
    Reads and parses a JSON configuration file (default 'initial.json')
    from a specified directory.

    Args:
        fdir: The directory path containing the JSON file.
        ftar: The name of the JSON file (default is 'initial.json').

    Raises:
        FileNotFoundError: If the specified JSON file is not found.

    Returns:
        A dictionary containing the parsed JSON data.
    """
    # Construct the full path to the file
    __package__: str = os.path.join(os.path.abspath(fdir), ftar) if not os.path.isabs(fdir) else os.path.join(fdir, ftar)
    
    if not os.path.exists(__package__): 
        raise FileNotFoundError(f"{ftar} file not found in {fdir}\n |-package at {__package__}")

    # Open and parse the JSON file
    with open(__package__, 'r', encoding='utf-8') as f:
        config: Dict[str, Any] = json.load(f)
        return config