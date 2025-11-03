import sys
import pygame
# Import our functions and classes
from libs.utils.configs import loadsConfig, savesConfig
#  Import ImageButton as well as new component names
from libs.common.components import SolidButton, SolidBox, SolidDropDown, ImageButton

def surface(screen, background, load_background_image_func):
    """
    Runs the settings menu loop.
    Returns the updated settings dictionary.
    """
    settings = loadsConfig()
    running = True
    clock = pygame.time.Clock() # Add clock for FPS limiting

    # --- Create UI Objects ---
    #  Changed SolidButton to ImageButton
    back_btn = ImageButton(
        x=50, y=50,
        image_name="back",
        theme=settings['themes'],
        default_width=150, # Set to the old button's size
        default_height=80
    )
    
    #  Using new SolidDropDown component
    themes_dropdown = SolidDropDown(
        x=screen.get_width() / 2 - 150, y=300, 
        width=335, height=50,
        main_text="Theme", # Set main_text properly
        options=["CuteChaos", "StarSketch", "BubblePencil"]
    )
    themes_dropdown.set_selected(settings['themes']) # Set its current value
    
    #  Using new SolidBox component
    music_checkbox = SolidBox(
        x=screen.get_width() / 2 - 150, y=400,
        width=50, height=50,
        label="Music",
        initial_checked=settings['music']
    )
    
    #  Using new SolidButton component
    default_btn = SolidButton(
        x=screen.get_width() / 2 - 150, y=500,
        width=300, height=50,
        text="Reset Default",
        font_size=30
    )

    # ---
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
                
                # Reload the background *immediately*
                background = load_background_image_func(new_theme)
                
                #  Reload the back button's image to match
                back_btn.reload_image(new_theme)
                
                continue # Event handled

            # If dropdown was open, consume the click to prevent click-through
            if dropdown_was_open and event.type == pygame.MOUSEBUTTONDOWN:
                continue 

            # Check other buttons
            if default_btn.is_clicked(event):
                settings = {"themes": "BubblePencil", "music": True}
                
                # Update UI elements to reflect the change
                themes_dropdown.set_selected(settings['themes'])
                music_checkbox.checked = settings['music']
                # Reload background on CuteChaos reset
                background = load_background_image_func(settings['themes'])
                
                #  Also update the back button on reset
                back_btn.reload_image(settings['themes'])
                
                continue # Event handled

            if music_checkbox.handle_event(event):
                # State changed, update settings
                settings['music'] = music_checkbox.checked
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
