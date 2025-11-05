# This file contains unit tests for the SolidButton component.
# It verifies button creation and click detection logic.

import pygame
import sys
import os
from typing import Any

# Add the 'src' directory to the Python path to allow importing library modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from libs.common.components import SolidButton

# Sets up a minimal pygame environment for testing.
def setup_pygame() -> None:
    """
    Initializes pygame with a dummy video driver if necessary,
    allowing tests to run in environments without a display (like CI/CD).
    """
    try:
        pygame.init()
        pygame.display.set_mode((100, 100))
    except pygame.error as e:
        # If no video device is available, use the 'dummy' driver
        if 'No available video device' in str(e):
            os.environ['SDL_VIDEODRIVER'] = 'dummy'
            pygame.init()
            pygame.display.set_mode((100, 100))
        else:
            raise

# Tests if a SolidButton object is created with the correct attributes.
def test_button_creation() -> None:
    """
    Verifies that the Button class constructor correctly assigns
    position, size, and text attributes.
    """
    setup_pygame()
    
    btn: SolidButton = SolidButton(10, 20, 100, 50, text="Click Me", font_size=20)
    
    assert btn.rect.x == 10
    assert btn.rect.y == 20
    assert btn.rect.width == 100
    assert btn.rect.height == 50
    assert btn.text == "Click Me"
    pygame.quit()

# Tests if the button correctly detects a click inside its bounds.
def test_button_is_clicked_positive() -> None:
    """
    Verifies that the is_clicked method returns True when a
    MOUSEBUTTONDOWN event occurs within the button's rect.
    """
    setup_pygame()
    
    btn: SolidButton = SolidButton(10, 10, 100, 50, text="Click Me")
    
    # Create a mock event simulating a click at (15, 15)
    mock_event: pygame.event.Event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
        'button': 1,
        'pos': (15, 15)
    })
    
    assert btn.is_clicked(mock_event) == True
    pygame.quit()

# Tests if the button correctly ignores a click outside its bounds.
def test_button_is_clicked_negative_outside() -> None:
    """
    Verifies that the is_clicked method returns False when a
    MOUSEBUTTONDOWN event occurs outside the button's rect.
    """
    setup_pygame()
    
    btn: SolidButton = SolidButton(10, 10, 100, 50, text="Click Me")
    
    # Create a mock event simulating a click at (200, 200)
    mock_event: pygame.event.Event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
        'button': 1,
        'pos': (200, 200)
    })
    
    assert btn.is_clicked(mock_event) == False
    pygame.quit()

# Tests if the button ignores events that are not MOUSEBUTTONDOWN.
def test_button_is_clicked_negative_wrong_event() -> None:
    """
    Verifies that the is_clicked method returns False when
    an event other than MOUSEBUTTONDOWN occurs, even if
    it's within the button's rect.
    """
    setup_pygame()
    
    btn: SolidButton = SolidButton(10, 10, 100, 50, text="Click Me")
    
    # Create a mock event simulating mouse motion
    mock_event: pygame.event.Event = pygame.event.Event(pygame.MOUSEMOTION, {
        'pos': (15, 15)
    })
    
    assert btn.is_clicked(mock_event) == False
    pygame.quit()