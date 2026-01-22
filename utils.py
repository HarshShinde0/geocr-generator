"""
Utility functions for GeoCroissant generator.
All helper functions from the original geocr_generator.py.
"""
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


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


def calculate_temporal_resolution(all_files: List[Path]) -> Optional[Dict[str, Any]]:
    """
    Calculate temporal resolution/cadence from file timestamps.
    
    Args:
        all_files: List of file paths with dates in filenames
        
    Returns:
        Dictionary with temporal resolution info or None
    """
    # Extract dates from all files
    dates = []
    for file_path in all_files:
        date_str = extract_temporal_from_filename(file_path.name)
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                dates.append(date_obj)
            except ValueError:
                continue
    
    if len(dates) < 2:
        return None
    
    # Sort dates
    dates.sort()
    
    # Calculate time deltas between consecutive observations
    deltas = []
    for i in range(1, len(dates)):
        delta = (dates[i] - dates[i-1]).days
        if delta > 0:  # Ignore same-day observations
            deltas.append(delta)
    
    if not deltas:
        return None
    
    # Calculate median delta (more robust than mean)
    deltas.sort()
    median_delta = deltas[len(deltas) // 2]
    
    # Determine appropriate unit and value
    if median_delta < 2:
        return {
            "@type": "QuantitativeValue",
            "value": median_delta,
            "unitText": "day"
        }
    elif median_delta < 14:
        return {
            "@type": "QuantitativeValue",
            "value": median_delta,
            "unitText": "days"
        }
    elif median_delta < 60:
        # Convert to weeks if close to weekly cadence
        weeks = round(median_delta / 7)
        if weeks == 1:
            return {
                "@type": "QuantitativeValue",
                "value": 1,
                "unitText": "week"
            }
        else:
            return {
                "@type": "QuantitativeValue",
                "value": weeks,
                "unitText": "weeks"
            }
    else:
        # Convert to months
        months = round(median_delta / 30.44)
        if months == 1:
            return {
                "@type": "QuantitativeValue",
                "value": 1,
                "unitText": "month"
            }
        else:
            return {
                "@type": "QuantitativeValue",
                "value": months,
                "unitText": "months"
            }
