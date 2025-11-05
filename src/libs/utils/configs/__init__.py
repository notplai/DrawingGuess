import json
import os
from typing import Any
from libs.utils.pylog import Logger

logger = Logger(__name__)

# Loads the settings configuration from 'data/settings.json'.
def loadsConfig() -> dict[str, Any]:
    """
    Loads the game settings from 'data/settings.json'.
    If the file is not found or is corrupt, returns default settings.

    Returns:
        A dictionary containing the game settings.
    """
    # Loads settings from the JSON file.
    try:
        with open("data/settings.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load settings.json ({e}). Returning defaults.")
        # Default settings
        return {"themes": "CuteChaos", "music": True}

# Saves the settings configuration to 'data/settings.json'.
def savesConfig(settings: dict[str, Any]) -> None:
    """
    Saves the provided settings dictionary to 'data/settings.json'.
    It creates the 'data' directory if it doesn't exist.

    Args:
        settings: The settings dictionary to save.
    """
    # Saves the given settings dictionary to the JSON file.
    try:
        os.makedirs("data", exist_ok=True)
        
        with open("data/settings.json", "w") as f:
            json.dump(settings, f, indent=4)
        logger.info("Settings saved successfully.")
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")