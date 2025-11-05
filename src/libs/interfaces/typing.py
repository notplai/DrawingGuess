from __future__ import annotations
from dataclasses import dataclass

import sys
from typing import Any, Callable as std_Callable

# --- Path Manipulation for typing import ---
# This is likely a workaround for a local development environment.
cur_dir: str = sys.path[0]
sys.path[0] = ''
import typing as std_typing
sys.path[0] = cur_dir
# --- End Path Manipulation ---

# --- Type Aliases ---
Type = std_typing.Type
Union = std_typing.Union
Tuple = std_typing.Tuple
List = std_typing.List
Literal = std_typing.Literal
# --- End Type Aliases ---

# Defines a simple 2D Vector class.
@dataclass
class Vector2D:
    """
    A dataclass representing a 2D vector with x and y components.
    Provides basic vector arithmetic operations.
    """
    x: float
    y: float

    # --- Vector Operations ---
    def add(self, vecB: Vector2D, /) -> Vector2D:
        """Returns a new Vector2D (self + vecB)."""
        return Vector2D(self.x + vecB.x, self.y + vecB.y)
    def sub(self, vecB: Vector2D, /) -> Vector2D:
        """Returns a new Vector2D (self - vecB)."""
        return Vector2D(self.x - vecB.x, self.y - vecB.y)
    def mul(self, value: float, /) -> Vector2D:
        """Returns a new Vector2D (self * value)."""
        return Vector2D(self.x * value, self.y * value)
    def div(self, value: float, /) -> Vector2D:
        """Returns a new Vector2D (self / value)."""
        return Vector2D(self.x / value, self.y / value)
    def invert(self) -> Vector2D:
        """Returns a new Vector2D (-self.x, -self.y)."""
        return Vector2D(-self.x, -self.y)

    # --- Operator Overloading ---
    def __add__(self, vecB: Vector2D, /) -> Vector2D:
        """Operator overload for self + vecB."""
        return Vector2D(self.x + vecB.x, self.y + vecB.y)

    def __sub__(self, vecB: Vector2D, /) -> Vector2D:
        """Operator overload for self - vecB."""
        return Vector2D(self.x - vecB.x, self.y - vecB.y)

    def __mul__(self, value: float, /) -> Vector2D:
        """Operator overload for self * value."""
        return Vector2D(self.x * value, self.y * value)

    def __truediv__(self, value: float, /) -> Vector2D:
        """Operator overload for self / value."""
        return Vector2D(self.x / value, self.y / value)

    def __neg__(self) -> Vector2D:
        """Operator overload for -self."""
        return Vector2D(-self.x, -self.y)

    def __rmul__(self, value: float, /) -> Vector2D:
        """Operator overload for value * self."""
        return self.__mul__(value)
    
    def __getitem__(self, index: int) -> float:
        """Allows accessing components by index (e.g., v[0] for v.x)."""
        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        else:
            raise IndexError("Vector2D index out of range")

    # --- Vector Methods ---
    def magnitude(self) -> float:
        """Calculates the magnitude (length) of the vector."""
        return (self.x**2 + self.y**2) ** 0.5

    def normalized(self) -> Vector2D:
        """
        Returns a new Vector2D with the same direction but a magnitude of 1.
        Returns (0, 0) if the magnitude is 0.
        """
        mag: float = self.magnitude()
        if mag == 0:
            return Vector2D(0, 0)
        return self / mag

    def __repr__(self) -> str:
        """Returns a string representation (e.g., "Vector2D(x=1.0, y=2.0)")."""
        return f"Vector2D(x={self.x}, y={self.y})"

# A type hint for "Vector-like" objects.
Vector2DLike = Union[Vector2D, Tuple[float, float], List[float]]

# A type hint for the target type in the Adapter function.
SwitchType = Union[type, Type, Literal['Vector2D', 'list', 'tuple', 'List', 'Tuple']]

# Helper dictionary for error messages in Adapter.
T: Dict[str, str] = {
    'str': 'string',
    'int': 'integer',
    'float': 'float',
    'bool': 'boolean',
    'list': 'list',
    'tuple': 'tuple',
    'dict': 'dictionary',
    'set': 'set',
    'NoneType': 'None',
}

# A utility function to convert between Vector2DLike types.
def Adapter(value: Vector2DLike, switch: SwitchType) -> Vector2DLike:
    """
    Converts a Vector2DLike value (Vector2D, list, or tuple)
    into a specified target type (Vector2D, list, or tuple).

    Args:
        value: The input Vector2D, list, or tuple.
        switch: The target type (e.g., Vector2D, list, 'tuple').

    Raises:
        ValueError: If the conversion is not possible or 'switch' is invalid.
        TypeError: If the input 'value' is not a valid Vector2DLike type.

    Returns:
        The 'value' converted to the 'switch' type.
    """
    key: str
    # Normalize the 'switch' argument to a lowercase string key
    if isinstance(switch, str):
        key = switch.lower()
    else:
        if switch is Vector2D:
            key = 'vector2d'
        elif switch is list:
            key = 'list'
        elif switch is tuple:
            key = 'tuple'
        else:
            raise ValueError(f"Invalid 'switch' type: {switch}")

    # --- Conversion Logic ---
    if isinstance(value, Vector2D):
        if key == 'vector2d':
            return value
        elif key == 'list':
            return [value.x, value.y]
        elif key == 'tuple':
            return (value.x, value.y)
        raise ValueError(f"Cannot convert Vector2D to {switch}")

    if isinstance(value, list):
        if key == 'list':
            return value
        if key == 'tuple':
            return tuple(value)
        if key == 'vector2d':
            try:
                x, y = value
                return Vector2D(float(x), float(y))
            except Exception as e:
                typename: str = T.get(type(value).__name__, type(value).__name__)
                raise ValueError(f"cannot convert {typename} to Vector2D: {value!r}\n|- {e}")
        return list(value) # Default return? Seems redundant.

    if isinstance(value, tuple):
        if key == 'tuple':
            return value
        if key == 'list':
            return list(value)
        if key == 'vector2d':
            try:
                x, y = value
                return Vector2D(float(x), float(y))
            except Exception as e:
                typename = T.get(type(value).__name__, type(value).__name__)
                raise ValueError(f"cannot convert {typename} to Vector2D: {value!r}\n|- {e}")
        return tuple(value) # Default return? Seems redundant.
    # --- End Conversion Logic ---

    typename = T.get(type(value).__name__, type(value).__name__)
    raise TypeError(f"Adapter() argument must be Vector2DLike or sequence, not {typename}")

# A type hint for the Adapter function itself.
AdapterType = std_Callable[[Vector2DLike, SwitchType], Vector2DLike]