from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

class SlideType(Enum):
    COVER = "Cover"
    INSTRUKSI = "Instruksi"
    BAGIAN = "Judul Bagian"
    JUDUL_LAGU = "Judul Lagu"
    LIRIK_LAGU = "Lirik Lagu"
    LITURGI = "Liturgi"
    BACAAN = "Bacaan"
    PENUTUP = "Penutup"

@dataclass
class SlideItem:
    slide_type: SlideType
    content: str
    included: bool = True
    slide_number: int = 0
    speaker: Optional[str] = None  # 'P', 'J', 'P+J', etc.
    title: Optional[str] = None    # Useful for Judul Bagian, Lagu, or subtitle
    bg_image: Optional[str] = None # Path to background image (for BAGIAN slides)
    is_nyanyian: bool = False       # True if this liturgi block is under a song section
