import sys
import pygame
import random 
from surfaces import SettingsSurface, CreditsSurface, SelSurface
# Import our classes and functions
from libs.common.components import Button
from libs.utils.configs import loadsConfig

pygame.init()

# --- Constants ---
SCREEN_WIDTH = 1668
SCREEN_HIGH = 938

# Button Dimensions
SCREEN_BUTTON_WIDTH = 250
SCREEN_BUTTON_HEIGHT = 80

# Quit Dialog Dimensions
DIALOG_WIDTH = 550
DIALOG_HEIGHT = 200
DIALOG_BTN_WIDTH = 100
DIALOG_BTN_HEIGHT = 50
DIALOG_BTN_GAP = 20
DIALOG_CENTER_X = SCREEN_WIDTH // 2
DIALOG_CENTER_Y = SCREEN_HIGH // 2

# --- Screen Setup ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HIGH))
pygame.display.set_caption("My Game Menu")

# --- Settings and Background Loading ---
def load_background_image(quality):
    """Loads the correct background image based on quality setting."""
    image_path = f'assets/menu/{quality}.jpg'
    try:
        print(f"Loading background: {image_path}")
        # .convert() optimizes the image format for faster blitting
        return pygame.image.load(image_path).convert()
    except pygame.error as e:
        print(f"Warning: Could not load {image_path}. Error: {e}")
        print("Loading 'assets/menu/Default.jpg' as fallback.")
        return pygame.image.load('assets/menu/Default.jpg').convert()

# --- Button Layout Function ---
def update_button_layout(theme, play_btn, settings_btn, quit_btn):
    """
    Moves the main menu buttons based on the selected theme.
    """
    width = SCREEN_BUTTON_WIDTH
    height = SCREEN_BUTTON_HEIGHT
    
    if theme == 'NightlyShift':
        # "Play" and "Settings" in an inline row, "Quit" below
        print("Applying 'NightlyShift' layout")
        gap = 50 # Gap between play and settings
        total_row_width = (width * 2) + gap
        row_start_x = (SCREEN_WIDTH - total_row_width) // 2
        
        # Center Y for the row, slightly above middle
        row_y = (SCREEN_HIGH - height) // 2 - 50 + 50
        
        play_btn.rect.topleft = (row_start_x, row_y)
        settings_btn.rect.topleft = (row_start_x + width + gap, row_y)
        
        # "Quit" button down at the center
        quit_x = (SCREEN_WIDTH - width) // 2
        quit_y = row_y + height + 75 # Positioned below the row
        quit_btn.rect.topleft = (quit_x, quit_y)

    elif theme == 'Legacy':
        # All buttons on the right side, stacked from the BOTTOM
        print("Applying 'Legacy' layout")
        padding_right = 50
        padding_bottom = 50
        gap = 50 # Gap between buttons
        
        btn_x = SCREEN_WIDTH - width - padding_right
        
        # Stack from the bottom up
        quit_btn_y = SCREEN_HIGH - height - padding_bottom
        settings_btn_y = quit_btn_y - height - gap
        play_btn_y = settings_btn_y - height - gap
        
        play_btn.rect.topleft = (btn_x, play_btn_y)
        settings_btn.rect.topleft = (btn_x, settings_btn_y)
        quit_btn.rect.topleft = (btn_x, quit_btn_y)

    else:
        # Default layout: stacked in the center
        print("Applying 'Default' layout")
        btn_x = (SCREEN_WIDTH - width) // 2
        
        play_btn.rect.topleft = (btn_x, (SCREEN_HIGH - height) // 2 - 50)
        settings_btn.rect.topleft = (btn_x, (SCREEN_HIGH - height) // 2 + 75)
        quit_btn.rect.topleft = (btn_x, (SCREEN_HIGH - height) // 2 + 200)


# --- Load Initial Settings ---
current_settings = loadsConfig()
background = load_background_image(current_settings['themes'])


# --- Create Main Menu Buttons ---
# We create them here, and the layout function will move them.
btn_x = (SCREEN_WIDTH - SCREEN_BUTTON_WIDTH) // 2

play_btn = Button(
    x=btn_x, y=(SCREEN_HIGH - SCREEN_BUTTON_HEIGHT) // 2 - 50,
    width=SCREEN_BUTTON_WIDTH, height=SCREEN_BUTTON_HEIGHT, 
    bg_color=(0, 200, 0), font_size=50,
)

settings_btn = Button(
    x=btn_x, y=(SCREEN_HIGH - SCREEN_BUTTON_HEIGHT) // 2 + 75,
    width=SCREEN_BUTTON_WIDTH, height=SCREEN_BUTTON_HEIGHT, 
    bg_color=(0, 0, 200), font_size=50,
)

quit_btn = Button(
    x=btn_x, y=(SCREEN_HIGH - SCREEN_BUTTON_HEIGHT) // 2 + 200,
    width=SCREEN_BUTTON_WIDTH, height=SCREEN_BUTTON_HEIGHT,
    bg_color=(200, 0, 0), font_size=50,
)

# Call layout function on startup
update_button_layout(current_settings['themes'], play_btn, settings_btn, quit_btn)


# --- [PERFORMANCE REFACTOR] ---
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
yes_btn_x = DIALOG_CENTER_X - DIALOG_BTN_WIDTH - (DIALOG_BTN_GAP // 2)
no_btn_x = DIALOG_CENTER_X + (DIALOG_BTN_GAP // 2)
btn_y = DIALOG_CENTER_Y + 25

yes_btn = Button(
    x=yes_btn_x, y=btn_y,
    width=DIALOG_BTN_WIDTH, height=DIALOG_BTN_HEIGHT, 
    bg_color=(0, 255, 0), font_size=40
)
yes_btn_original_center = yes_btn.rect.center

no_btn = Button(
    x=no_btn_x, y=btn_y,
    width=DIALOG_BTN_WIDTH, height=DIALOG_BTN_HEIGHT, 
    bg_color=(255, 0, 0), font_size=40
)
no_btn_original_center = no_btn.rect.center
# --- End of pre-created assets ---


# --- [NEW] Create Credits Text Assets ---
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
            # If dialog is closed, check main menu buttons
            if play_btn.is_clicked(event):
                SelSurface(screen, background.copy())
                
            if quit_btn.is_clicked(event):
                confirming_quit = True # Open dialog
                
            if settings_btn.is_clicked(event):
                # Pass the screen, a copy of the background, and the loading function
                updated_settings = SettingsSurface(screen, background.copy(), load_background_image)
                
                # Check if theme setting changed
                theme_changed = updated_settings['themes'] != current_settings['themes']
                
                if theme_changed:
                    print(f"Theme setting changed to: {updated_settings['themes']}")
                    # Reload the background
                    background = load_background_image(updated_settings['themes'])
                    # Call layout function to move buttons
                    update_button_layout(updated_settings['themes'], play_btn, settings_btn, quit_btn)
                
                # Store the latest settings
                current_settings = updated_settings
            
            # --- [NEW] Handle Credits Click ---
            # [FIXED] First check event type, THEN check collision
            if event.type == pygame.MOUSEBUTTONDOWN and credits_rect.collidepoint(event.pos):
                CreditsSurface(screen, background.copy())
                # Note: This will pause main.py until the credits are done

    # --- Drawing / Rendering ---
    
    # 1. Draw the background
    screen.blit(background, (0, 0))
    
    # 2. Draw main menu buttons
    play_btn.draw(screen)
    settings_btn.draw(screen)
    quit_btn.draw(screen)

    # 3. Draw the quit dialog (if active)
    if confirming_quit:
        # [PERFORMANCE REFACTOR]
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

    # 4. --- [NEW] Draw Credits Text ---
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
