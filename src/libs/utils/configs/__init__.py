import json
import os

def loadsConfig():
    """
    Loads settings from the JSON file.
    Returns default settings if file is not found or corrupt.
    """
    try:
        # Try to open and read the settings file
        with open("data/settings.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist or is empty/broken, return defaults
        return {"themes": "Default", "music": True}

def savesConfig(settings):
    """
    Saves the given settings dictionary to the JSON file.
    """
    # Ensure the 'data' directory exists before trying to write
    # exist_ok=True prevents an error if the directory already exists
    os.makedirs("data", exist_ok=True)
    
    # Write the settings to the file
    with open("data/settings.json", "w") as f:
        # indent=4 makes the JSON file human-readable
        json.dump(settings, f, indent=4)
