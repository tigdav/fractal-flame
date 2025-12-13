from dataclasses import dataclass

from .config import AffineParams


@dataclass
class AffineTransform:
    """Affine transform represented by 2x3 matrix.

    x' = a * x + b * y + c
    y' = d * x + e * y + f
    """

    a: float
    b: float
    c: float
    d: float
    e: float
    f: float

    @classmethod
    def from_params(cls, params: AffineParams) -> "AffineTransform":
        """Create AffineTransform from AffineParams.

        Args:
            params (AffineParams): Affine parameters.

        Returns:
            AffineTransform: Transform instance.

        """
        return cls(
            a=params.a,
            b=params.b,
            c=params.c,
            d=params.d,
            e=params.e,
            f=params.f,
        )

    def apply(self, x: float, y: float) -> tuple[float, float]:
        """Apply affine transform to point.

        Args:
            x (float): X coordinate.
            y (float): Y coordinate.

        Returns:
            tuple[float, float]: Transformed coordinates.

        """
        new_x = self.a * x + self.b * y + self.c
        new_y = self.d * x + self.e * y + self.f
        return new_x, new_y
