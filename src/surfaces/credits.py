import sys
import pygame

# ---  Credits Data Structure ---
# We now use tuples with a "type" at the end to define the layout.
# (text, size, 'center') - For centered titles
# (text_left, text_right, size, 'columns') - For two-column rows
# ('', size, 'spacer') - For adding empty space
CREDITS_DATA = [
    ("DrawingGuess", 60, "center"),
    ("", 30, "spacer"),

    ("A Game By", 40, "center"),
    ("ABC Team", 50, "center"),
    ("", 60, "spacer"),

    ("Programmer", 40, "center"),
    ("Suphakorn Khamwongsa", "@notplai", 30, "columns"),
    ("", 30, "spacer"),

    ("Artists", 40, "center"),
    ("Sorawit Nuamwat", "@sorwit_ball", 30, "columns"),
    ("", 30, "spacer"),

    ("Designer", 40, "center"),
    ("Suphakorn Khamwongsa", "Sorawit Nuamwat", 30, "columns"),
    ("Test1", "Test2", 30, "columns"),
    ("", 30, "spacer"),

    ("Tester", 40, "center"),
    ("Sorawit Nuamwat", "Test1", 30, "columns"),
    ("Test2", "Test3", 30, "columns"),
    ("", 30, "spacer"),

    ("Special Thanks", 40, "center"),
    ("Coffee", "Iced Green Tea", 30, "columns"), # make artists have superpowers to did project happend!!
    ("Taiwan Milk Tea", "Iced Matcha Latte", 30, "columns"), # after I droke, I've superpowers to did project!
    ("Google Vertex", "Google Gemini", 30, "columns"), # For optimization and sorting the files
    ("", 60, "spacer"),

    ("", 60, "spacer"),
    ("", 60, "spacer"),
    ("", 60, "spacer"),
    ("", 60, "spacer"),
    ("", 60, "spacer"),
    ("", 60, "spacer"),
    ("", 60, "spacer"),
    ("", 60, "spacer"),
    ("", 60, "spacer"),
    ("", 60, "spacer"),
    ("", 60, "spacer"),
    
    # ---  Thanks For Playing section ---
    ("Thanks for playing!", 80, "center"),
    ("", 60, "spacer"), # Add some padding at the end
]

def surface(screen, background):
    """
    Runs the auto-scrolling credits screen.
    Exits when 'ESC' is pressed or credits finish.
    """
    running = True
    clock = pygame.time.Clock()
    
    screen_width = screen.get_width()
    screen_height = screen.get_height()

    # ---
    # Create a semi-transparent overlay
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180)) # Darker overlay for credits
    
    # ---  Layout Positions ---
    center_x = screen_width / 2
    # Right-hand edge of the left column (roles)
    column_1_x = center_x - 50 
    # Left-hand edge of the right column (names)
    column_2_x = center_x + 50
    
    # Pre-render all text surfaces
    rendered_texts = []
    current_y = screen_height + 50 # Start 50px below the screen
    
    fonts = {} # Cache fonts by size to avoid reloading
    
    for row in CREDITS_DATA:
        # --- Get Font ---
        # Get size from the correct index based on row type
        size = row[1] if len(row) == 3 else row[2]
        
        if size not in fonts:
            try:
                fonts[size] = pygame.font.Font("freesansbold.ttf", size)
            except FileNotFoundError:
                fonts[size] = pygame.font.Font(None, size)
        font = fonts[size]
        
        # --- Process Row by Type ---
        row_type = row[-1] # Type is always the last element

        if row_type == 'center':
            # This is a (text, size, 'center') row
            text = row[0]
            if text:
                text_surf = font.render(text, True, "White")
                text_rect = text_surf.get_rect(center=(center_x, current_y))
                rendered_texts.append((text_surf, text_rect))
        
        elif row_type == 'columns':
            # This is a (text_left, text_right, size, 'columns') row
            text_left = row[0]
            text_right = row[1]
            
            if text_left:
                surf_left = font.render(text_left, True, "White")
                # Align to the right edge of the left column
                rect_left = surf_left.get_rect(topright=(column_1_x, current_y))
                rendered_texts.append((surf_left, rect_left))
            
            if text_right:
                surf_right = font.render(text_right, True, "White")
                # Align to the left edge of the right column
                rect_right = surf_right.get_rect(topleft=(column_2_x, current_y))
                rendered_texts.append((surf_right, rect_right))
        
        # 'spacer' rows do nothing but advance the Y position

        # --- Advance Y Position ---
        current_y += size + 10 # Advance Y for the next row
        
    # Get the rect of the very last text surface ("Thanks for playing!")
    thanks_rect = rendered_texts[-1][1] if rendered_texts else None
    
    scroll_y = 0
    scroll_speed = 1.5 # Pixels per frame
    
    # ---  Stop scrolling logic ---
    scrolling_stopped = False
    
    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # --- Logic ---
        if not scrolling_stopped:
            scroll_y += scroll_speed
            
            # Check if the "Thanks" text has reached the center
            if thanks_rect:
                # Calculate the current Y center of the "Thanks" text
                current_thanks_y = thanks_rect.centery - scroll_y
                
                if current_thanks_y <= screen_height / 2:
                    # Stop scrolling
                    scrolling_stopped = True
                    # Lock the scroll_y to perfectly center the text
                    scroll_y = thanks_rect.centery - (screen_height / 2)

        # --- Drawing ---
        screen.blit(background, (0, 0))
        screen.blit(overlay, (0, 0))
        
        # Draw all texts, offset by the scroll_y
        for surf, rect in rendered_texts:
            # Create a new rect for drawing, offset by scroll
            draw_rect = rect.move(0, -scroll_y)
            screen.blit(surf, draw_rect)

        pygame.display.flip()
        clock.tick(60)

