from libs.interfaces.typing import Vector2D, Vector2DLike, Adapter
from typing import Dict, Any, Tuple

# A dictionary defining the initial shared context for canvas tools.
# TODO: This is a template and will be replaced by the main canvas's context.
SharedContext: Dict[str, Any] = {
    "brushColor": (0, 0, 0),
    "isDrawing": False,
    "mousePos": Vector2D(0, 0),
}