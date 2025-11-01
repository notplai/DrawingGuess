import sys
import pygame
from libs.common.components import Button
from .boards.whiteboard import surface as whiteboardSurface 

def surface(screen, background):
    """
    Runs the mode selection and file selection menus.
    """
    running = True
    clock = pygame.time.Clock()
    
    # We'll use a simple state machine for the two menus
    # "mode" = FreeInk, Guessing, AI
    # "file" = New Whiteboard, Open
    current_view = "mode"

    # --- [PERFORMANCE] ---
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
    
    freeink_btn = Button(
        x=btn_x, y=250, width=btn_width, height=btn_height,
        text="FreeInk", font_size=50
    )
    
    guessing_btn = Button(
        x=btn_x, y=350, width=btn_width, height=btn_height,
        text="Guessing", font_size=50
    )
    
    ai_btn = Button(
        x=btn_x, y=450, width=btn_width, height=btn_height,
        text="AI Lookup (Locked)", text_color=(150, 150, 150),  # type: ignore
        bg_color=(50, 50, 50), border_color=(100, 100, 100), font_size=50
    )
    
    back_btn = Button(50, 50, 150, 80, text="Back", text_color='White', 
                      bg_color=(50, 50, 50), border_color='White', font_size=50)

    # --- File Selection Buttons ---
    new_whiteboard_btn = Button(
        x=btn_x, y=250, width=btn_width, height=btn_height,
        text="New Whiteboard", font_size=50
    )
    
    open_file_btn = Button(
        x=btn_x, y=350, width=btn_width, height=btn_height,
        text="Import or Open from File", font_size=50
    )
    
    back_file_btn = Button(
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
                if back_btn.is_clicked(event):
                    running = False # Exit this surface
                
                if freeink_btn.is_clicked(event):
                    current_view = "file" # Go to file selection
                
                if guessing_btn.is_clicked(event):
                    current_view = "file" # Go to file selection
                
                # AI button is disabled, so we don't check its click
            
            elif current_view == "file":
                if new_whiteboard_btn.is_clicked(event):
                    print("Opening new whiteboard...")
                    # [MODIFIED] Pass open_file_on_start=False (or nothing)
                    whiteboardSurface(screen, background, open_file_on_start=False)
                    # We stay here until the whiteboard is closed
                
                if open_file_btn.is_clicked(event):
                    print("Opening whiteboard with file dialog...")
                    # [MODIFIED] Pass open_file_on_start=True
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
            guessing_btn.draw(screen)
            ai_btn.draw(screen)
            
        elif current_view == "file":
            screen.blit(file_title_surf, file_title_rect)
            new_whiteboard_btn.draw(screen)
            open_file_btn.draw(screen)
            back_file_btn.draw(screen)

        pygame.display.flip()
        clock.tick(60)
