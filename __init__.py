"""
GeoCroissant Generator Package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A tool for generating GeoCroissant metadata from geospatial datasets.

:copyright: (c) 2026
:license: 
"""

__version__ = "1.0.0"
__author__ = "Harsh S."

from geocr_generator.core.generator import GeoCroissantGenerator
from geocr_generator.core.metadata_extractor import MetadataExtractor

__all__ = [
    "GeoCroissantGenerator",
    "MetadataExtractor",
]
