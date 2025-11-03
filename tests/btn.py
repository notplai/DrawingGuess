import pygame
import sys
import os

# We need to add the 'src' directory to the Python path so we can import our modules
# This adjusts the path to go up one level from 'tests' and then into 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from libs.common.components import SoildButton

# --- Test Fixture ---

# A "fixture" is a setup function that pytest runs before a test.
# This one initializes pygame and a screen, which our components need.
def setup_pygame():
    """Initializes pygame in a minimal way for testing."""
    try:
        pygame.init()
        # Set a minimal display mode
        pygame.display.set_mode((100, 100))
    except pygame.error as e:
        # Handle cases where a display (like in CI) isn't available
        # We can try a dummy video driver
        if 'No available video device' in str(e):
            os.environ['SDL_VIDEODRIVER'] = 'dummy'
            pygame.init()
            pygame.display.set_mode((100, 100))
        else:
            raise

# --- Test Functions ---

def test_button_creation():
    """Tests if a Button object is created with the correct properties."""
    setup_pygame()
    
    btn = SoildButton(10, 20, 100, 50, text="Click Me", font_size=20)
    
    assert btn.rect.x == 10
    assert btn.rect.y == 20
    assert btn.rect.width == 100
    assert btn.rect.height == 50
    assert btn.text == "Click Me"
    pygame.quit()

def test_button_is_clicked_positive():
    """Tests if the button correctly detects a click inside its area."""
    setup_pygame()
    
    btn = SoildButton(10, 10, 100, 50, text="Click Me")
    
    # Simulate a MOUSEBUTTONDOWN event at position (15, 15), which is inside the button
    mock_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
        'button': 1,  # Left click
        'pos': (15, 15)
    })
    
    assert btn.is_clicked(mock_event) == True
    pygame.quit()

def test_button_is_clicked_negative_outside():
    """Tests if the button correctly ignores a click outside its area."""
    setup_pygame()
    
    btn = SoildButton(10, 10, 100, 50, text="Click Me")
    
    # Simulate a click at (200, 200), which is outside
    mock_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
        'button': 1,
        'pos': (200, 200)
    })
    
    assert btn.is_clicked(mock_event) == False
    pygame.quit()

def test_button_is_clicked_negative_wrong_event():
    """Tests if the button ignores events that aren't MOUSEBUTTONDOWN."""
    setup_pygame()
    
    btn = SoildButton(10, 10, 100, 50, text="Click Me")
    
    # Simulate a MOUSEMOTION event
    mock_event = pygame.event.Event(pygame.MOUSEMOTION, {
        'pos': (15, 15)
    })
    
    assert btn.is_clicked(mock_event) == False
    pygame.quit()
