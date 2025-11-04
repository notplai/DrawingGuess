import os
import sys
import pygame
import random 
from surfaces import SettingsSurface, CreditsSurface, SelSurface
# Import our classes and functions
from libs.common.components import ImageButton  #  Import ImageButton
from libs.utils.configs import loadsConfig
#  Import the background loader from its new location
from libs.common.resources import getRes

pygame.init()

# --- Constants ---
SCREEN_WIDTH = 1668
SCREEN_HIGH = 938

# Quit Dialog Dimensions (Fallbacks for layout)
DIALOG_WIDTH = 550
DIALOG_HEIGHT = 200
DIALOG_BTN_WIDTH = 126  # Default width
DIALOG_BTN_HEIGHT = 77 # Default height
DIALOG_BTN_GAP = 20
DIALOG_CENTER_X = SCREEN_WIDTH // 2
DIALOG_CENTER_Y = SCREEN_HIGH // 2

# --- Screen Setup ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HIGH))
pygame.display.set_caption("DrawingGuess")

# Settings and Background Loading ---
# The getRes function has been moved to 
# 'libs/components/environment/__init__.py'

# --- Button Layout Function ---
def update_button_layout(theme, play_btn, settings_btn, quit_btn):
    """
    Moves the main home buttons based on the selected theme.
     Now uses button.rect.width/height for layout.
    """
    
    if theme == 'StarSketch':
        # "Play" and "Settings" in an inline row, "Quit" below
        print("Applying 'StarSketch' layout")
        
        # Get dimensions from buttons
        play_w, play_h = play_btn.rect.size
        settings_w, settings_h = settings_btn.rect.size
        quit_w, quit_h = quit_btn.rect.size
        
        gap = 25 # Gap between play and settings
        total_row_width = play_w + gap + settings_w
        row_start_x = (SCREEN_WIDTH - total_row_width) // 2
        
        # Center Y for the row, slightly above middle
        # Use play_h as the reference height for the row
        row_y = (SCREEN_HIGH - play_h) // 2 - 50 + 100
        
        play_btn.set_pos(row_start_x, row_y)
        settings_btn.set_pos(row_start_x + play_w + gap, row_y)
        
        # "Quit" button down at the center
        quit_x = (SCREEN_WIDTH - quit_w) // 2
        quit_y = row_y + play_h + 35
        quit_btn.set_pos(quit_x, quit_y)

    elif theme == 'BubblePencil':
        # All buttons on the right side, stacked from the BOTTOM
        print("Applying 'BubblePencil' layout")
        
        # Get dimensions from buttons
        play_w, play_h = play_btn.rect.size
        settings_w, settings_h = settings_btn.rect.size
        quit_w, quit_h = quit_btn.rect.size
        
        padding_right = 50
        padding_bottom = 50
        gap = 25 # Gap between buttons
        
        # Use quit_w as reference for X (assuming buttons are similar width)
        btn_x = SCREEN_WIDTH - quit_w - padding_right
        
        # Stack from the bottom up
        quit_btn_y = SCREEN_HIGH - quit_h - padding_bottom
        settings_btn_y = quit_btn_y - settings_h - gap
        play_btn_y = settings_btn_y - play_h - gap
        
        play_btn.set_pos(btn_x, play_btn_y)
        settings_btn.set_pos(btn_x, settings_btn_y)
        quit_btn.set_pos(btn_x, quit_btn_y)

    else:
        # CuteChaos layout: stacked in the center
        print("Applying 'CuteChaos' layout")
        
        # Get dimensions from buttons
        play_w, play_h = play_btn.rect.size
        settings_w, settings_h = settings_btn.rect.size
        quit_w, quit_h = quit_btn.rect.size
        
        # Use play_w as reference for X
        btn_x = (SCREEN_WIDTH - play_w) // 2
        
        play_btn.set_pos(btn_x, (SCREEN_HIGH - play_h) // 2 - 30)
        settings_btn.set_pos(btn_x, (SCREEN_HIGH - settings_h) // 2 + 75)
        quit_btn.set_pos(btn_x, (SCREEN_HIGH - quit_h) // 2 + 200)


# --- Load Initial Settings ---
current_settings = loadsConfig()
background = getRes(current_settings['themes'])


# --- Create Main home Buttons ---
# We create them here, and the layout function will move them.
#  Use ImageButton
btn_x = (SCREEN_WIDTH - 250) // 2 # Use default for initial placement

play_btn = ImageButton(
    x=btn_x, y=(SCREEN_HIGH - 80) // 2 - 50,
    image_name="play",
    theme=current_settings['themes'],
    default_width=396,
    default_height=120
)

settings_btn = ImageButton(
    x=btn_x, y=(SCREEN_HIGH - 80) // 2 + 75,
    image_name="settings",
    theme=current_settings['themes'],
    default_width=396,
    default_height=120
)

quit_btn = ImageButton(
    x=btn_x, y=(SCREEN_HIGH - 80) // 2 + 100,
    image_name="exit",
    theme=current_settings['themes'],
    default_width=396,
    default_height=120
)

# Call layout function on startup
update_button_layout(current_settings['themes'], play_btn, settings_btn, quit_btn)


# ---
# Create Quit Dialog assets ONCE, outside the loop
# 1. Create the overlay surface
dialog_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HIGH), pygame.SRCALPHA)
dialog_overlay.fill((0, 0, 0, 128)) # 128 = 50% transparency

# 2. Create the dialog box
dialog_rect = pygame.Rect(0, 0, DIALOG_WIDTH, DIALOG_HEIGHT)
dialog_rect.center = (DIALOG_CENTER_X, DIALOG_CENTER_Y)

# 3. Render the dialog text
try:
    dialog_font = pygame.font.Font("freesansbold.ttf", 28)
except FileNotFoundError:
    dialog_font = pygame.font.Font(None, 28)
    
dialog_text_surf = dialog_font.render("I'm felt sad, when see you leave... T^T", True, (0, 0, 0))
dialog_text_rect = dialog_text_surf.get_rect(center=(DIALOG_CENTER_X, DIALOG_CENTER_Y - 50))

# 4. Create dialog buttons (using new constants for readability)
yes_btn = ImageButton(
    x=0, y=0,
    image_name="yes",
    theme=current_settings['themes'],
    default_width=DIALOG_BTN_WIDTH - 20,
    default_height=DIALOG_BTN_HEIGHT - 20
)

no_btn = ImageButton(
    x=0, y=0,
    image_name="no",
    theme=current_settings['themes'],
    default_width=DIALOG_BTN_WIDTH - 20,
    default_height=DIALOG_BTN_HEIGHT - 20
)

# Now calculate position based on loaded image sizes
yes_btn_w = yes_btn.rect.width
no_btn_w = no_btn.rect.width
total_dialog_btn_width = yes_btn_w + DIALOG_BTN_GAP + no_btn_w

yes_btn_x = DIALOG_CENTER_X - (total_dialog_btn_width / 2)
no_btn_x = yes_btn_x + yes_btn_w + DIALOG_BTN_GAP
btn_y = DIALOG_CENTER_Y + 25

#  Apply a small vertical offset to the 'yes' button to 
# compensate for image padding and align it visually.
yes_btn.set_pos(yes_btn_x, btn_y + 2)
no_btn.set_pos(no_btn_x, btn_y)

yes_btn_original_center = yes_btn.rect.center
no_btn_original_center = no_btn.rect.center
# --- End of pre-created assets ---


# ---  Create Credits Text Assets ---
try:
    credits_font = pygame.font.Font("freesansbold.ttf", 30)
    credits_font_underlined = pygame.font.Font("freesansbold.ttf", 30)
except FileNotFoundError:
    credits_font = pygame.font.Font(None, 30)
    credits_font_underlined = pygame.font.Font(None, 30)

credits_font_underlined.set_underline(True)

credits_text = "ABC Team"
credits_color = (50, 50, 50)

# Render both versions
credits_surf_normal = credits_font.render(credits_text, True, credits_color)
credits_surf_underlined = credits_font_underlined.render(credits_text, True, credits_color)

# Position at bottom-left
credits_rect = credits_surf_normal.get_rect(bottomleft=(20, SCREEN_HIGH - 15))
# --- End of new credits assets ---


# --- Main Game Loop ---
running = True
confirming_quit = False # State to show/hide the quit dialog
clock = pygame.time.Clock() # Add a clock for FPS limiting (good practice)

#  List of all buttons to update on theme change
all_image_buttons = [play_btn, settings_btn, quit_btn, yes_btn, no_btn]

while running:
    
    # Get mouse position once per frame
    mouse_pos = pygame.mouse.get_pos()

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            confirming_quit = True

        if confirming_quit:
            # If dialog is open, only check dialog buttons
            if yes_btn.is_clicked(event):
                running = False # Quit the game
            if no_btn.is_clicked(event):
                confirming_quit = False # Close dialog
        else:
            # If dialog is closed, check main home buttons
            if play_btn.is_clicked(event):
                SelSurface(screen, background.copy())
                
            if quit_btn.is_clicked(event):
                confirming_quit = True # Open dialog
                
            if settings_btn.is_clicked(event):
                # Pass the screen, a copy of the background, and the loading function
                updated_settings = SettingsSurface(screen, background.copy(), getRes)
                
                # Check if theme setting changed
                theme_changed = updated_settings['themes'] != current_settings['themes']
                
                if theme_changed:
                    print(f"Theme setting changed to: {updated_settings['themes']}")
                    new_theme = updated_settings['themes']
                    
                    # Reload the background
                    background = getRes(new_theme)
                    
                    #  Reload all button images
                    print("Reloading button images...")
                    for btn in all_image_buttons:
                        btn.reload_image(new_theme)
                        
                    #  Recalculate dialog button positions
                    yes_btn_w = yes_btn.rect.width
                    no_btn_w = no_btn.rect.width
                    total_dialog_btn_width = yes_btn_w + DIALOG_BTN_GAP + no_btn_w
                    yes_btn_x = DIALOG_CENTER_X - (total_dialog_btn_width / 2)
                    no_btn_x = yes_btn_x + yes_btn_w + DIALOG_BTN_GAP
                    
                    #  Apply the correct Y position AND the visual offset
                    btn_y = DIALOG_CENTER_Y + 25
                    yes_btn.set_pos(yes_btn_x, btn_y - 5) # Move up 5 pixels
                    no_btn.set_pos(no_btn_x, btn_y)

                    yes_btn_original_center = yes_btn.rect.center
                    no_btn_original_center = no_btn.rect.center
                    
                    # Call layout function to move main buttons
                    update_button_layout(new_theme, play_btn, settings_btn, quit_btn)
                
                # Store the latest settings
                current_settings = updated_settings
            
            # ---  Handle Credits Click ---
            if event.type == pygame.MOUSEBUTTONDOWN and credits_rect.collidepoint(event.pos):
                CreditsSurface(screen, background.copy())
                # Note: This will pause main.py until the credits are done

    # --- Drawing / Rendering ---
    
    # 1. Draw the background
    screen.blit(background, (0, 0))
    
    # 2. Draw main home buttons
    play_btn.draw(screen)
    settings_btn.draw(screen)
    quit_btn.draw(screen)

    # 3. Draw the quit dialog (if active)
    if confirming_quit:
        #
        # Draw the pre-created assets instead of creating new ones every frame
        
        # Draw overlay
        screen.blit(dialog_overlay, (0, 0))
        
        # Draw dialog box
        pygame.draw.rect(screen, (200, 200, 200), dialog_rect)
        pygame.draw.rect(screen, 'Black', dialog_rect, 3)

        # Draw dialog text
        screen.blit(dialog_text_surf, dialog_text_rect)

        # Shake logic for 'Yes' button
        yes_btn.rect.center = yes_btn_original_center # Reset position
        no_btn.rect.center = no_btn_original_center # Reset position
        
        if yes_btn.rect.collidepoint(mouse_pos):
            # Add small random offset
            offset_x = random.randint(-2, 2)
            offset_y = random.randint(-2, 2)
            yes_btn.rect.move_ip(offset_x, offset_y)
            
        # Draw dialog buttons
        yes_btn.draw(screen)
        no_btn.draw(screen)

    # 4. ---  Draw Credits Text ---
    if not confirming_quit: # Only draw if dialog is not open
        if credits_rect.collidepoint(mouse_pos):
            screen.blit(credits_surf_underlined, credits_rect)
        else:
            screen.blit(credits_surf_normal, credits_rect)

    # 5. Update the display
    pygame.display.flip()
    
    # 6. Cap the framerate (good practice, reduces CPU usage)
    clock.tick(60) # Aim for 60 FPS

pygame.quit()
sys.exit()

