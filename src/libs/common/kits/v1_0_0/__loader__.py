import os
import json
import importlib.util
import sys
import pygame

def loads(components_dir="components"):
    """
    Scans for component "kits", loads their 'initial.json' configs,
    and imports their main tool classes.
    
    Returns a list of tuples: (config_object, ToolClass)
    """
    loaded_tools = []
    
    # Use an absolute path for reliability
    base_components_dir = os.path.abspath(components_dir)
    if not os.path.exists(base_components_dir):
        print(f"Warning: Components directory not found: {base_components_dir}")
        return []

    print(f"Scanning for component kits in: {base_components_dir}")
    
    # Iterate over component packs (e.g., "@builtins", "custom_shapes")
    for kit_name in os.listdir(base_components_dir):
        kit_path = os.path.join(base_components_dir, kit_name)
        if not os.path.isdir(kit_path):
            continue
            
        config_path = os.path.join(kit_path, "initial.json")
        if not os.path.exists(config_path):
            print(f"Skipping '{kit_name}': No 'initial.json' found.")
            continue
            
        print(f"Found component kit: {kit_name}")
        try:
            with open(config_path, 'r') as f:
                kit_config = json.load(f)
            
            # --- Check compatibility ---
            loader_version = kit_config.get("kits-loaders", "0.0.0")
            if loader_version != "1.0.0":
                print(f"Warning: Skipping kit '{kit_name}'. It requires loader v{loader_version}, but we are v1.0.0.")
                continue
                
            print(f"Loading kit: {kit_config.get('components-name')} v{kit_config.get('components-version')}")

            # --- Load all objects in the kit ---
            for tool_config in kit_config.get("@objects", []):
                try:
                    main_file = tool_config["main_file"]
                    main_class = tool_config["main_class"]
                    
                    # We need to construct the full path to the file
                    # e.g., src/components/@builtins/Pen/__init__.py
                    module_path = os.path.abspath(os.path.join(kit_path, main_file))
                    
                    # And a unique module name for importlib
                    # e.g., components.@builtins.Pen.__init__
                    module_name = f"components.{kit_name}.{main_file.replace('.py', '').replace(os.sep, '.')}"
                    
                    if not os.path.exists(module_path):
                         print(f"Error: main_file not found for tool '{tool_config['name']}': {module_path}")
                         continue
                    
                    # Dynamically import the module
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    if spec is None:
                        print(f"Error: Could not create spec for module {module_name} at {module_path}")
                        continue
                        
                    module = importlib.util.module_from_spec(spec)
                    
                    # Add to sys.modules to handle relative imports *if needed*
                    sys.modules[module_name] = module 
                    
                    spec.loader.exec_module(module)
                    
                    # Get the class from the loaded module
                    ToolClass = getattr(module, main_class)
                    
                    # [NEW] Icon Path Processing
                    # If icon_pic is specified, make it an absolute path
                    if tool_config.get("icon_pic"):
                        icon_path = os.path.abspath(os.path.join(kit_path, tool_config["icon_pic"]))
                        if os.path.exists(icon_path):
                            tool_config["icon_path"] = icon_path # Add absolute path to config
                        else:
                            print(f"Warning: Icon file not found: {icon_path}")
                            tool_config["icon_path"] = None
                    else:
                        tool_config["icon_path"] = None
                    
                    loaded_tools.append((tool_config, ToolClass))
                    print(f"  Successfully loaded object: {tool_config['name']}")

                except Exception as e:
                    print(f"Error loading tool object '{tool_config.get('name', 'UNKNOWN')}': {e}")
                    import traceback
                    traceback.print_exc()

        except Exception as e:
            print(f"Error parsing 'initial.json' for kit {kit_name}: {e}")
    
    return loaded_tools
