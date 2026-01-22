"""
Metadata extraction from GeoTIFF files.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import rasterio
from rasterio.crs import CRS
from rasterio.warp import transform_bounds
import re


class MetadataExtractor:
    """Extract comprehensive metadata from GeoTIFF files."""
    
    def __init__(self, compute_statistics: bool = True):
        """
        Initialize metadata extractor.
        
        Args:
            compute_statistics: Whether to compute band statistics
        """
        self.compute_statistics = compute_statistics
    
    def extract(self, tiff_path: Path) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from a GeoTIFF file.
        
        Args:
            tiff_path: Path to the TIFF file
            
        Returns:
            Dictionary containing all extractable metadata
        """
        metadata = {
            "file_path": str(tiff_path),
            "file_name": tiff_path.name,
            "file_size_bytes": tiff_path.stat().st_size
        }
        
        with rasterio.open(tiff_path) as src:
            # Basic raster properties
            metadata.update({
                "width": src.width,
                "height": src.height,
                "count": src.count,
                "dtype": str(src.dtypes[0]),
                "driver": src.driver,
                "nodata": src.nodata,
                "transform": list(src.transform),
                "bounds": list(src.bounds),
                "crs": src.crs.to_string() if src.crs else None,
                "crs_wkt": src.crs.to_wkt() if src.crs else None,
                "crs_epsg": self._parse_epsg_from_wkt(src.crs) if src.crs else None,
                "crs_units": self._get_crs_units(src.crs) if src.crs else None,
                "resolution": src.res,
            })
            
            # Calculate geographic extent (WGS84)
            if src.crs:
                bounds = src.bounds
                wgs84_bounds = transform_bounds(src.crs, 'EPSG:4326', *bounds)
                metadata["geo_bounds"] = {
                    "west": wgs84_bounds[0],
                    "south": wgs84_bounds[1],
                    "east": wgs84_bounds[2],
                    "north": wgs84_bounds[3]
                }
            
            # Band information
            metadata["bands"] = self._extract_band_info(src)
            
            # TIFF tags
            metadata["tags"] = src.tags()
            
            # Color interpretation
            metadata["colorinterp"] = [str(src.colorinterp[i]) for i in range(src.count)]
            
            # Block/tile shape
            metadata["block_shapes"] = src.block_shapes
            
            # Compression
            metadata["compression"] = src.compression.name if src.compression else None
            
            # Interleaving
            metadata["interleaving"] = src.interleaving.name if hasattr(src, 'interleaving') else None
        
        return metadata
    
    def _extract_band_info(self, src) -> list:
        """Extract band-level information."""
        bands = []
        for i in range(1, src.count + 1):
            band_meta = {
                "index": i,
                "dtype": str(src.dtypes[i-1]),
                "nodata": src.nodatavals[i-1],
            }
            
            # Get band description/name from TIFF
            desc = src.descriptions[i-1] if src.descriptions else None
            if desc:
                band_meta["description"] = desc
                band_meta["name"] = desc
            
            # Calculate statistics
            if self.compute_statistics:
                try:
                    data = src.read(i)
                    valid_data = data[data != src.nodata] if src.nodata is not None else data
                    if valid_data.size > 0:
                        band_meta["statistics"] = {
                            "min": float(valid_data.min()),
                            "max": float(valid_data.max()),
                            "mean": float(valid_data.mean()),
                            "std": float(valid_data.std()),
                        }
                except Exception as e:
                    band_meta["statistics_error"] = str(e)
            
            bands.append(band_meta)
        
        return bands
    
    @staticmethod
    def _parse_epsg_from_wkt(crs: CRS) -> Optional[str]:
        """
        Extract EPSG code from a CRS object.
        
        Args:
            crs: Rasterio CRS object
            
        Returns:
            EPSG code string (e.g., "EPSG:32610") or None
        """
        if crs.to_epsg():
            return f"EPSG:{crs.to_epsg()}"
        
        # Try to parse from WKT
        wkt = crs.to_wkt()
        
        # PRIORITY 1: Look for UTM zone pattern in PROJCS name
        utm_match = re.search(r'UTM [Zz]one (\d+)[,\s]+([Nn]orthern|[Ss]outhern)', wkt, re.IGNORECASE)
        if utm_match:
            zone = int(utm_match.group(1))
            hemisphere = utm_match.group(2)[0].upper()
            epsg_code = 32600 + zone if hemisphere == 'N' else 32700 + zone
            return f"EPSG:{epsg_code}"
        
        # PRIORITY 2: Look for UTM zone with N/S suffix
        utm_match = re.search(r'UTM [Zz]one (\d+)([NS])', wkt)
        if utm_match:
            zone = int(utm_match.group(1))
            hemisphere = utm_match.group(2)
            epsg_code = 32600 + zone if hemisphere == 'N' else 32700 + zone
            return f"EPSG:{epsg_code}"
        
        # PRIORITY 3: Check Transverse Mercator with central meridian
        if 'Transverse_Mercator' in wkt:
            cm_match = re.search(r'central_meridian["\s,]+(-?\d+\.?\d*)', wkt)
            if cm_match:
                central_meridian = float(cm_match.group(1))
                zone = int((central_meridian + 180) / 6) + 1
                hemisphere = 'N'
                if 'false_northing' in wkt:
                    fn_match = re.search(r'false_northing["\s,]+(\d+\.?\d*)', wkt)
                    if fn_match and float(fn_match.group(1)) > 0:
                        hemisphere = 'S'
                epsg_code = 32600 + zone if hemisphere == 'N' else 32700 + zone
                return f"EPSG:{epsg_code}"
        
        return None
    
    @staticmethod
    def _get_crs_units(crs: CRS) -> str:
        """
        Determine the units of a CRS (meters vs degrees).
        
        Args:
            crs: Rasterio CRS object
            
        Returns:
            "meters" for projected CRS, "degrees" for geographic CRS
        """
        if crs.is_projected:
            return "meters"
        else:
            return "degrees"
