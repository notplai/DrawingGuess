import pygame
import os

class Button:
    """
    A clickable button class that loads its appearance from an image.
    It supports theme-specific images with fallbacks.
    
    """
    
    def __init__(self, x, y, image_name, theme=None, 
                 default_width=250, default_height=80, 
                 missing_texture_path='src/assets/textures/common/static/missing.png'):
        
        self.image_name = image_name
        self.current_theme = theme
        
        #  Store the target size from these parameters
        self.target_width = default_width
        self.target_height = default_height
        
        self.missing_texture_path = os.path.abspath(missing_texture_path)
        
        # Load the initial image (which will now be scaled)
        self.image_surf = self.load_image()
        
        # Set rect based on loaded (and scaled) image
        self.rect = self.image_surf.get_rect()
        self.rect.topleft = (x, y)

    def load_image(self):
        """
        Loads the button image based on theme and image_name.
        Priority:
        1. src/assets/textures/environments/.{theme}/Buttons/{image_name}.png
        2. assets/textures/common/Buttons/{image_name}.png
        3. missing_texture_path (scaled to target size)
        """
        loaded_surf = None # Temporary surface to hold the loaded image
        
        # 1. Try theme-specific path
        theme_path = os.path.abspath(f'src/assets/textures/environments/.{self.current_theme}/Buttons/{self.image_name}.png')
        
        if os.path.exists(theme_path):
            print(f"Loading theme image: {theme_path}")
            try:
                loaded_surf = pygame.image.load(theme_path).convert_alpha()
            except Exception as e:
                print(f"Warning: Could not load theme image {theme_path}. Error: {e}")

        # 2. Try common fallback path (if theme failed)
        if not loaded_surf:
            common_path = os.path.abspath(f'src/assets/textures/common/Buttons/{self.image_name}.png')
            
            if os.path.exists(common_path):
                print(f"Loading common image: {common_path}")
                try:
                    loaded_surf = pygame.image.load(common_path).convert_alpha()
                except Exception as e:
                    print(f"Warning: Could not load common image {common_path}. Error: {e}")

        # ---  Scaling Step ---
        # If we loaded *any* image (theme or common), scale it to the target size
        if loaded_surf:
            try:
                # Use smoothscale for better quality
                return pygame.transform.smoothscale(loaded_surf, (self.target_width, self.target_height))
            except Exception as e:
                print(f"Warning: Could not scale {self.image_name} to {self.target_width}x{self.target_height}. Error: {e}")
                # Fallback to the unscaled surface if scaling fails
                return loaded_surf

        # 3. Load missing texture
        print(f"Warning: Could not find image '{self.image_name}.png' for theme '{self.current_theme}' or in common.")
        print(f"Loading missing texture: {self.missing_texture_path}")
        try:
            missing_surf = pygame.image.load(self.missing_texture_path).convert_alpha()
            # Scale it to the target button size
            return pygame.transform.scale(missing_surf, (self.target_width, self.target_height))
        except Exception as e:
            print(f"FATAL: Could not load missing texture! Error: {e}")
            # Create a fallback surface at the target size
            fallback_surf = pygame.Surface((self.target_width, self.target_height), pygame.SRCALPHA)
            fallback_surf.fill((255, 0, 255)) # Fill with magenta
            return fallback_surf
            
    def reload_image(self, new_theme):
        """
        Reloads the button's image when the theme changes.
        """
        self.current_theme = new_theme
        
        # Store old position
        old_topleft = self.rect.topleft
        
        # Load new image (this will now be scaled by load_image)
        self.image_surf = self.load_image()
        
        # Update rect with new image dimensions, but keep old position
        self.rect = self.image_surf.get_rect()
        self.rect.topleft = old_topleft
        print(f"Reloaded {self.image_name} for theme {new_theme}. New size: {self.rect.size}")

    def set_pos(self, x, y):
        """
        Updates the button's topleft position.
        """
        self.rect.topleft = (x, y)
        
    def draw(self, screen):
        """Draws the button's image on the screen."""
        screen.blit(self.image_surf, self.rect)

    def is_clicked(self, event):
        """Checks if the button was clicked."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False
