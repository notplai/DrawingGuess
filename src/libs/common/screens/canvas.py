from typing import Optional, Union, Any
import pygame
from pygame.typing import ColorLike

from libs.interfaces.typing import Vector2DLike, Vector2D, Adapter

# Defines a basic Surface wrapper.
class Surface:
    """
    A simple wrapper class for a pygame.Surface, primarily used
    as a base for the main canvas or other screen surfaces.
    
    Note: This class seems to be a minimal wrapper. The main logic
    is in 'src/surfaces/projects/canvas.py'.
    """
    def __init__(self, screen: pygame.Surface, background: ColorLike, size: Vector2DLike, /):
        """
        Initializes the Surface.

        Args:
            screen: The main pygame display surface (potentially).
            background: The fill color for the canvasSurface.
            size: The (width, height) of the canvasSurface.
        """
        self._cWidth: float
        self._cHeight: float
        self._cWidth, self._cHeight = Adapter(size, 'Tuple')

        self.screen: pygame.Surface = screen
        self.canvasSurface: pygame.Surface = pygame.Surface((self._cWidth, self._cHeight))
        self.canvasSurface.fill(background)

        self.clock: pygame.time.Clock = pygame.time.Clock()

    # Returns a copy of the canvas surface.
    def copy(self, /) -> pygame.Surface:
        """
        Returns a copy of the internal canvasSurface.

        Returns:
            A new pygame.Surface instance.
        """
        return self.canvasSurface.copy()