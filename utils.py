"""
Utility functions for GeoCroissant generator.
All helper functions from the original geocr_generator.py.
"""
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


def extract_temporal_from_filename(filename: str) -> Optional[str]:
    """
    Extract temporal date from filename patterns.
    
    Args:
        filename: Name of the file
        
    Returns:
        ISO 8601 date string (YYYY-MM-DD) or None
    """
    # HLS pattern: YYYYDOY (year + day of year)
    match = re.search(r'\.(\d{4})(\d{3})\.', filename)
    if match:
        year = int(match.group(1))
        doy = int(match.group(2))
        try:
            date = datetime.strptime(f"{year}-{doy}", "%Y-%j")
            return date.strftime("%Y-%m-%d")
        except ValueError:
            pass
    
    # Standard date patterns: YYYY-MM-DD, YYYYMMDD
    match = re.search(r'(\d{4})[-_]?(\d{2})[-_]?(\d{2})', filename)
    if match:
        year, month, day = match.groups()
        try:
            date = datetime(int(year), int(month), int(day))
            return date.strftime("%Y-%m-%d")
        except ValueError:
            pass
    
    return None


def detect_sampling_strategy(filename: str) -> Optional[str]:
    """
    Detect sampling/windowing strategy from filename.
    
    Args:
        filename: Name of the file
        
    Returns:
        Description of sampling strategy or None
    """
    # Check for subset/window patterns
    if 'subsetted' in filename.lower():
        size_match = re.search(r'(\d+)x(\d+)', filename)
        if size_match:
            width, height = size_match.groups()
            return f"Subsetted to {width}x{height} pixel windows"
    
    if 'window' in filename.lower():
        return "Windowed sampling"
    
    if 'tile' in filename.lower():
        return "Tiled sampling"
    
    return None


def detect_sensor_from_filename(filename: str) -> Optional[str]:
    """
    Detect sensor type from filename.
    
    Args:
        filename: Name of the file
        
    Returns:
        Sensor name or None
    """
    filename_upper = filename.upper()
    
    if 'HLS.S30' in filename_upper:
        return 'HLS_S30'
    if 'HLS.L30' in filename_upper:
        return 'HLS_L30'
    if 'LC08' in filename_upper or 'LC09' in filename_upper:
        return 'Landsat_8-9'
    if 'LE07' in filename_upper:
        return 'Landsat_7'
    if 'S2' in filename_upper and ('L1C' in filename_upper or 'L2A' in filename_upper):
        return 'Sentinel2'
    if 'MOD' in filename_upper or 'MYD' in filename_upper:
        return 'MODIS'
    
    return None


def get_spectral_band_info(sensor: str, band_idx: int) -> Dict[str, Any]:
    """
    Lookup spectral band information for known sensors.
    
    Args:
        sensor: Sensor name (HLS, Landsat, Sentinel2, etc.)
        band_idx: Band index (0-based)
        
    Returns:
        Dictionary with wavelength, bandwidth, name
    """
    # HLS (Harmonized Landsat Sentinel-2) band specifications
    hls_bands = [
        {"name": "Blue", "wavelength": 490, "bandwidth": 65, "unit": "nm"},
        {"name": "Green", "wavelength": 560, "bandwidth": 60, "unit": "nm"},
        {"name": "Red", "wavelength": 665, "bandwidth": 30, "unit": "nm"},
        {"name": "NIR", "wavelength": 865, "bandwidth": 30, "unit": "nm"},
        {"name": "SWIR1", "wavelength": 1610, "bandwidth": 90, "unit": "nm"},
        {"name": "SWIR2", "wavelength": 2200, "bandwidth": 180, "unit": "nm"},
    ]
    
    if 'HLS' in sensor.upper() and band_idx < len(hls_bands):
        return hls_bands[band_idx]
    
    # Can extend with other sensors: Landsat, Sentinel-2, MODIS, etc.
    
    return {}


def scan_directory_for_geotiffs(directory: Path) -> Dict[str, Dict[str, List[Path]]]:
    """
    Scan directory for GeoTIFF files and organize by split and type.
    
    Args:
        directory: Root directory to scan
        
    Returns:
        Dictionary organized by split -> type -> list of paths
    """
    structure = {}
    
    # Find all TIFF files
    tiff_files = list(directory.rglob("*.tif")) + list(directory.rglob("*.tiff"))
    
    for tiff_path in tiff_files:
        # Determine split (training/validation/test)
        relative_path = tiff_path.relative_to(directory)
        parts = relative_path.parts
        
        split = "unknown"
        for part in parts:
            part_lower = part.lower()
            if part_lower in ['training', 'train']:
                split = "training"
                break
            elif part_lower in ['validation', 'val', 'valid']:
                split = "validation"
                break
            elif part_lower in ['test', 'testing']:
                split = "test"
                break
        
        # Determine type (image/mask/label)
        filename_lower = tiff_path.name.lower()
        if 'mask' in filename_lower or 'label' in filename_lower:
            file_type = "masks"
        else:
            file_type = "images"
        
        # Add to structure
        if split not in structure:
            structure[split] = {}
        if file_type not in structure[split]:
            structure[split][file_type] = []
        structure[split][file_type].append(tiff_path)
    
    return structure
