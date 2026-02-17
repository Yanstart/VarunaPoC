from dataclasses import dataclass
from typing import Dict


@dataclass
class NDViewState:
    """N-dimensional view state for multi-dimensional imaging."""

    x: int = 0
    y: int = 0
    z: int = 0  # Z-stack slice
    c: int = 0  # Channel index
    t: int = 0  # Timepoint
    level: int = 0  # Pyramid level
    zoom: float = 1.0

    # Dimension bounds
    z_max: int = 1
    c_max: int = 1
    t_max: int = 1
    level_max: int = 1

    def set_z(self, z: int) -> None:
        self.z = max(0, min(z, self.z_max - 1))

    def set_channel(self, c: int) -> None:
        self.c = max(0, min(c, self.c_max - 1))

    def set_timepoint(self, t: int) -> None:
        self.t = max(0, min(t, self.t_max - 1))

    def to_dict(self) -> Dict:
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "c": self.c,
            "t": self.t,
            "level": self.level,
            "zoom": self.zoom,
            "z_max": self.z_max,
            "c_max": self.c_max,
            "t_max": self.t_max,
            "level_max": self.level_max,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "NDViewState":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def from_slide_metadata(cls, metadata: dict) -> "NDViewState":
        """Create from slide metadata (e.g. OME-TIFF)."""
        return cls(
            z_max=metadata.get("z_levels", 1),
            c_max=metadata.get("channels", 1),
            t_max=metadata.get("timepoints", 1),
            level_max=metadata.get("level_count", 1),
        )
