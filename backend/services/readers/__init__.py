"""
Reader Architecture

Pluggable slide reader system implementing Strategy + Chain of Responsibility patterns.
Allows multiple reader backends (OpenSlide, BioFormats, tifffile, zarr) to be
registered and automatically selected based on file format.

Usage:
    from services.readers import default_selector

    selector = default_selector()
    reader = selector.select("/path/to/slide.svs")
    meta = reader.get_metadata()
    reader.close()

Or use individual readers directly:
    from services.readers import OpenSlideReader

    with OpenSlideReader() as reader:
        reader.open("/path/to/slide.svs")
        region = reader.read_region((0, 0), 0, (256, 256))

Issues: #8 (ISlideReader ABC), #18 (ReaderSelector), #19 (BioFormatsReader),
        #40 (OME-TIFF Reader), #41 (OME-Zarr Reader)
"""

from core.interfaces.slide_reader import SlideReader

from .base import ISlideReader, SlideMetadata, SlideReaderBase
from .bioformats_reader import BioFormatsReader
from .ome_tiff_reader import OMETIFFReader
from .ome_zarr_reader import OMEZarrReader
from .openslide_reader import OpenSlideReader
from .selector import NoCompatibleReaderError, ReaderSelector, default_selector

# Re-exported names, grouped by purpose (Protocol, helpers, readers, selector).
__all__ = [
    "SlideReader",
    "ISlideReader",
    "SlideReaderBase",
    "SlideMetadata",
    "OpenSlideReader",
    "BioFormatsReader",
    "OMETIFFReader",
    "OMEZarrReader",
    "ReaderSelector",
    "NoCompatibleReaderError",
    "default_selector",
]
