import sys
import pygame
#  Import SolidButton as Button (for existing buttons)
from libs.common.components import SolidButton, ImageButton
from .boards.canvas import surface as whiteboardSurface, 
#  Import config loader to get the theme
from libs.utils.configs import loadsConfig

def surface(screen, background):
    """
    Runs the mode selection and file selection menus.
    """
    #  Load settings to get the current theme
    settings = loadsConfig()
    running = True
    clock = pygame.time.Clock()
    
    # We'll use a simple state machine for the two menus
    # "mode" = FreeInk, Guessing, AI
    # "file" = New Whiteboard, Open
    current_view = "mode"

    # ---
    # Create static assets ONCE
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150)) 
    try:
        font_title = pygame.font.Font("freesansbold.ttf", 80)
        font_subtitle = pygame.font.Font("freesansbold.ttf", 50)
    except FileNotFoundError:
        font_title = pygame.font.Font(None, 80)
        font_subtitle = pygame.font.Font(None, 50)
        
    title_surf = font_title.render("Select Mode", True, "White")
    title_rect = title_surf.get_rect(center=(screen.get_width()/2, 100))
    
    file_title_surf = font_title.render("Open", True, "White")
    file_title_rect = file_title_surf.get_rect(center=(screen.get_width()/2, 100))

    # --- Mode Selection Buttons ---
    btn_width = 400
    btn_height = 80
    btn_x = (screen.get_width() - btn_width) / 2
    
    # These buttons will still be SolidButtons because we imported `SolidButton as Button`
    freeink_btn = SolidButton(
        x=btn_x, y=250, width=btn_width, height=btn_height,
        text="FreeInk", font_size=50
    )
    
    quick_btn = SolidButton(
        x=btn_x, y=350, width=btn_width, height=btn_height,
        text="Guessing", font_size=50
    )
    
    ai_btn = SolidButton(
        x=btn_x, y=450, width=btn_width, height=btn_height,
        text="AI Lookup", text_color=(150, 150, 150),  # type: ignore
        bg_color=(50, 50, 50), border_color=(100, 100, 100), font_size=50
    )
    
    #  Use the new ImageButton for the back button
    back_btn = ImageButton(
        x=50, y=50,
        image_name="back",
        theme=settings['themes'],
        default_width=150,
        default_height=80
    )

    # --- File Selection Buttons ---
    # These also remain SolidButtons
    new_whiteboard_btn = SolidButton(
        x=btn_x, y=250, width=btn_width, height=btn_height,
        text="New Canva", font_size=50
    )
    
    open_file_btn = SolidButton(
        x=btn_x, y=350, width=btn_width, height=btn_height,
        text="Open from File", font_size=50
    )
    
    back_file_btn = SolidButton(
        x=btn_x, y=450, width=btn_width, height=btn_height,
        text="Back", font_size=50
    )


    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if current_view == "mode":
                # back_btn is now an ImageButton, but .is_clicked() works the same
                if back_btn.is_clicked(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                
                if freeink_btn.is_clicked(event):
                    current_view = "file"
                
                if quick_btn.is_clicked(event):
                    current_view = "file"
                
                # AI button is disabled, so we don't check its click
            
            elif current_view == "file":
                if new_whiteboard_btn.is_clicked(event):
                    print("Opening new whiteboard...")
                    #  Pass open_file_on_start=False (or nothing)
                    whiteboardSurface(screen, background, open_file_on_start=False)
                    # We stay here until the whiteboard is closed
                
                if open_file_btn.is_clicked(event):
                    print("Opening whiteboard with file dialog...")
                    #  Pass open_file_on_start=True
                    whiteboardSurface(screen, background, open_file_on_start=True)
                    # We stay here until the whiteboard is closed
                
                if back_file_btn.is_clicked(event):
                    current_view = "mode" # Go back to mode selection

        # --- Drawing ---
        screen.blit(background, (0, 0))
        screen.blit(overlay, (0, 0))
        
        if current_view == "mode":
            screen.blit(title_surf, title_rect)
            back_btn.draw(screen)
            freeink_btn.draw(screen)
            quick_btn.draw(screen)
            ai_btn.draw(screen)
            
        elif current_view == "file":
            screen.blit(file_title_surf, file_title_rect)
            new_whiteboard_btn.draw(screen)
            open_file_btn.draw(screen)
            back_file_btn.draw(screen)

        pygame.display.flip()
        clock.tick(60)