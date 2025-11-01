import sys
import pygame
# Import our functions and classes
from libs.utils.configs import loadsConfig, savesConfig
from libs.common.components import Button, Checkbox, Dropdown

def surface(screen, background, load_background_image_func):
    """
    Runs the settings menu loop.
    Returns the updated settings dictionary.
    """
    settings = loadsConfig()
    running = True
    clock = pygame.time.Clock() # Add clock for FPS limiting

    # --- Create UI Objects ---
    back_btn = Button(50, 50, 150, 80, text="Back", text_color='White', 
                      bg_color=(50, 50, 50), border_color='White', font_size=50)
    
    themes_dropdown = Dropdown(
        x=screen.get_width() / 2 - 150, y=300, 
        width=335, height=50,
        main_text="Theme", # Set main_text properly
        options=["Default", "NightlyShift", "Legacy"]
    )
    themes_dropdown.set_selected(settings['themes']) # Set its current value
    
    music_checkbox = Checkbox(
        x=screen.get_width() / 2 - 150, y=400,
        width=50, height=50,
        label="Music",
        initial_checked=settings['music']
    )
    
    default_btn = Button(
        x=screen.get_width() / 2 - 150, y=500,
        width=300, height=50,
        text="Default Settings",
        font_size=30
    )

    # --- [PERFORMANCE REFACTOR] ---
    # Create static assets ONCE, outside the loop
    
    # 1. Create a semi-transparent overlay
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150)) 

    # 2. Render the "Settings" title
    try:
        font_title = pygame.font.Font("freesansbold.ttf", 80)
    except FileNotFoundError:
        font_title = pygame.font.Font(None, 80)
    title_surf = font_title.render("Settings", True, "White")
    title_rect = title_surf.get_rect(center=(screen.get_width()/2, 100))
    
    # 3. Render the static label for the dropdown
    # (Note: This is now handled by the Dropdown class itself,
    # but we'll leave this here in case you want to revert.
    # The refactored Dropdown now handles "Theme: Default")
    
    # We will adjust the Dropdown position slightly to accommodate the label
    # in the refactored Dropdown class.
    # No, the new Dropdown class handles it all. We can remove the label.
    
    # --- Settings Loop ---
    while running:
        # Store dropdown state *before* handling events
        dropdown_was_open = themes_dropdown.is_open

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if back_btn.is_clicked(event):
                savesConfig(settings) # Save on back
                running = False
                continue 

            # Handle dropdown event
            new_theme = themes_dropdown.handle_event(event)
            if new_theme:
                # A new theme was selected.
                settings['themes'] = new_theme
                # [PERFORMANCE REFACTOR]
                # Remove redundant save. Config will be saved on "Back" or "Quit".
                # savesConfig(settings) 
                
                # Reload the background *immediately*
                background = load_background_image_func(new_theme)
                continue # Event handled

            # If dropdown was open, consume the click to prevent click-through
            if dropdown_was_open and event.type == pygame.MOUSEBUTTONDOWN:
                continue 

            # Check other buttons
            if default_btn.is_clicked(event):
                settings = {"themes": "Default", "music": True}
                
                # [PERFORMANCE REFACTOR]
                # Remove redundant save.
                # savesConfig(settings) 
                
                # Update UI elements to reflect the change
                themes_dropdown.set_selected(settings['themes'])
                music_checkbox.checked = settings['music']
                # Reload background on default reset
                background = load_background_image_func(settings['themes'])
                continue # Event handled

            if music_checkbox.handle_event(event):
                # State changed, update settings
                settings['music'] = music_checkbox.checked
                
                # [PERFORMANCE REFACTOR]
                # Remove redundant save.
                # savesConfig(settings)
                continue # Event handled


        # --- Drawing ---
        # 1. Draw the background and overlay
        screen.blit(background, (0, 0))
        screen.blit(overlay, (0, 0))

        # 2. Draw the pre-rendered title
        screen.blit(title_surf, title_rect)

        # 3. Draw all standard UI elements
        back_btn.draw(screen)
        music_checkbox.draw(screen)
        default_btn.draw(screen)
        
        # 4. Draw the dropdown LAST so its options appear on top
        themes_dropdown.draw(screen)

        # 5. Update display
        pygame.display.flip()
        
        # 6. Cap framerate
        clock.tick(60)
        
    # Return the final settings to the main loop
    return settings
