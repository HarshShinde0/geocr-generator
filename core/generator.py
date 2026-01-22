"""
Main GeoCroissant generator class.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from core.metadata_extractor import MetadataExtractor
from core.config import Config
from utils import (
    scan_directory_for_geotiffs,
    extract_temporal_from_filename,
    detect_sampling_strategy,
    detect_sensor_from_filename,
    get_spectral_band_info,
    calculate_temporal_resolution
)


class GeoCroissantGenerator:
    """Main generator class for creating GeoCroissant metadata."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the generator.
        
        Args:
            config: Optional configuration object
        """
        self.config = config or Config()
        self.metadata_extractor = MetadataExtractor(
            compute_statistics=self.config.get('extraction.compute_statistics', True)
        )
    
    def generate(self, root_dir: Path, output_path: Optional[Path] = None) -> Dict:
        """
        Generate GeoCroissant metadata for a directory of GeoTIFF files.
        
        Args:
            root_dir: Root directory containing GeoTIFF files
            output_path: Optional path to save JSON output
            
        Returns:
            GeoCroissant metadata dictionary
        """
        print(f"Scanning directory: {root_dir}")
        
        # Scan for files
        file_structure = scan_directory_for_geotiffs(root_dir)
        if not file_structure:
            raise ValueError(f"No GeoTIFF files found in {root_dir}")
        
        print(f"Found files in splits: {list(file_structure.keys())}")
        
        # Extract metadata from all files
        metadata_cache = self._extract_all_metadata(file_structure, root_dir)
        
        # Get sample metadata
        all_files = self._get_all_files(file_structure)
        sample_file = all_files[0]
        sample_meta = metadata_cache[sample_file]
        
        # Detect sensor
        sensor = detect_sensor_from_filename(sample_file.name)
        
        # Build GeoCroissant metadata
        geocroissant = self._build_base_metadata(root_dir)
        self._add_temporal_coverage(geocroissant, all_files)
        self._add_temporal_resolution(geocroissant, all_files)
        self._add_keywords(geocroissant, root_dir.name, sensor)
        self._add_creator(geocroissant, sample_meta)
        self._add_geospatial_properties(geocroissant, sample_meta)
        self._add_sampling_strategy(geocroissant, sample_file.name)
        self._add_dataset_level_bands(geocroissant, file_structure, metadata_cache, sensor)
        self._add_distribution(geocroissant, root_dir)
        self._add_recordsets(geocroissant, root_dir, file_structure, metadata_cache, sensor)
        
        # Save to file
        if output_path:
            with open(output_path, 'w') as f:
                indent = self.config.get('output.indent', 2)
                json.dump(geocroissant, f, indent=indent)
            print(f"GeoCroissant metadata saved to {output_path}")
        
        return geocroissant
    
    def _extract_all_metadata(self, file_structure: Dict, root_dir: Path) -> Dict:
        """Extract metadata from all files."""
        metadata_cache = {}
        all_files = self._get_all_files(file_structure)
        
        print(f"Extracting metadata from {len(all_files)} files...")
        for file_path in all_files:
            try:
                metadata_cache[file_path] = self.metadata_extractor.extract(file_path)
            except Exception as e:
                print(f"Warning: Could not extract metadata from {file_path}: {e}")
        
        # Save metadata cache if configured
        if self.config.get('output.save_metadata_cache', True):
            cache_path = root_dir / "metadata_cache.json"
            with open(cache_path, 'w') as f:
                json.dump({str(k): v for k, v in metadata_cache.items()}, f, indent=2)
            print(f"Metadata cache saved to {cache_path}")
        
        return metadata_cache
    
    @staticmethod
    def _get_all_files(file_structure: Dict) -> List[Path]:
        """Get all files from file structure."""
        all_files = []
        for split, types in file_structure.items():
            for file_type, files in types.items():
                all_files.extend(files)
        return all_files
    
    def _build_base_metadata(self, root_dir: Path) -> Dict:
        """Build base GeoCroissant metadata structure."""
        dataset_name = root_dir.name
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        return {
            "@context": self._get_context(),
            "@type": "sc:Dataset",
            "name": dataset_name,
            "description": f"Geospatial dataset extracted from {dataset_name} directory",
            "url": f"file://{root_dir.as_posix()}",
            "citeAs": f"@dataset{{{dataset_name}, title={{{dataset_name} geospatial dataset}}, year={{{current_date[:4]}}}, url={{file://{root_dir.as_posix()}}}}}",
            "datePublished": current_date,
            "version": self.config.get('dataset.version', '1.0'),
            "license": self.config.get('dataset.license', 'Unknown'),
            "conformsTo": self.config.get('dataset.conformsTo', [
                "http://mlcommons.org/croissant/1.1",
                "http://mlcommons.org/croissant/geo/1.0"
            ]),
            "distribution": [],
            "recordSet": []
        }
    
    @staticmethod
    def _get_context() -> Dict:
        """Get JSON-LD context."""
        return {
            "@language": "en",
            "@vocab": "https://schema.org/",
            "citeAs": "cr:citeAs",
            "column": "cr:column",
            "conformsTo": "dct:conformsTo",
            "cr": "http://mlcommons.org/croissant/",
            "geocr": "http://mlcommons.org/croissant/geocr/",
            "rai": "http://mlcommons.org/croissant/RAI/",
            "dct": "http://purl.org/dc/terms/",
            "sc": "https://schema.org/",
            "data": {"@id": "cr:data", "@type": "@json"},
            "examples": {"@id": "cr:examples", "@type": "@json"},
            "dataBiases": "cr:dataBiases",
            "dataCollection": "cr:dataCollection",
            "dataType": {"@id": "cr:dataType", "@type": "@vocab"},
            "extract": "cr:extract",
            "field": "cr:field",
            "fileProperty": "cr:fileProperty",
            "fileObject": "cr:fileObject",
            "fileSet": "cr:fileSet",
            "format": "cr:format",
            "includes": "cr:includes",
            "isLiveDataset": "cr:isLiveDataset",
            "jsonPath": "cr:jsonPath",
            "key": "cr:key",
            "md5": "cr:md5",
            "parentField": "cr:parentField",
            "path": "cr:path",
            "personalSensitiveInformation": "cr:personalSensitiveInformation",
            "recordSet": "cr:recordSet",
            "references": "cr:references",
            "regex": "cr:regex",
            "repeated": "cr:repeated",
            "replace": "cr:replace",
            "samplingRate": "cr:samplingRate",
            "separator": "cr:separator",
            "source": "cr:source",
            "subField": "cr:subField",
            "transform": "cr:transform"
        }
    
    def _add_temporal_coverage(self, geocroissant: Dict, all_files: List[Path]) -> None:
        """Add temporal coverage to metadata."""
        temporal_dates = []
        for file_path in all_files:
            date = extract_temporal_from_filename(file_path.name)
            if date:
                temporal_dates.append(date)
        
        if temporal_dates:
            temporal_dates.sort()
            if len(temporal_dates) == 1:
                geocroissant["temporalCoverage"] = temporal_dates[0]
            else:
                geocroissant["temporalCoverage"] = f"{temporal_dates[0]}/{temporal_dates[-1]}"
    
    def _add_temporal_resolution(self, geocroissant: Dict, all_files: List[Path]) -> None:
        """Add temporal resolution/cadence to metadata."""
        temporal_resolution = calculate_temporal_resolution(all_files)
        if temporal_resolution:
            geocroissant["geocr:temporalResolution"] = temporal_resolution
    
    def _add_keywords(self, geocroissant: Dict, dataset_name: str, sensor: Optional[str]) -> None:
        """Add keywords to metadata."""
        keywords = [dataset_name]
        if sensor:
            keywords.append(sensor)
        if 'burn' in dataset_name.lower():
            keywords.extend(["burn scars", "fire", "remote sensing"])
        geocroissant["keywords"] = keywords
    
    @staticmethod
    def _add_creator(geocroissant: Dict, sample_meta: Dict) -> None:
        """Add creator information if available."""
        if "tags" in sample_meta and sample_meta["tags"]:
            tags = sample_meta["tags"]
            if "AUTHOR" in tags:
                geocroissant["creator"] = {"@type": "Person", "name": tags["AUTHOR"]}
            elif "ORGANIZATION" in tags:
                geocroissant["creator"] = {"@type": "Organization", "name": tags["ORGANIZATION"]}
    
    @staticmethod
    def _add_geospatial_properties(geocroissant: Dict, sample_meta: Dict) -> None:
        """Add geospatial properties to metadata."""
        if sample_meta.get("crs_epsg"):
            geocroissant["geocr:coordinateReferenceSystem"] = sample_meta["crs_epsg"]
        
        if sample_meta.get("geo_bounds"):
            bounds = sample_meta["geo_bounds"]
            geocroissant["spatialCoverage"] = {
                "@type": "Place",
                "geo": {
                    "@type": "GeoShape",
                    "box": f"{bounds['south']} {bounds['west']} {bounds['north']} {bounds['east']}"
                }
            }
        
        if sample_meta.get("resolution") and sample_meta.get("crs_units"):
            res_x, res_y = sample_meta["resolution"]
            geocroissant["geocr:spatialResolution"] = {
                "@type": "QuantitativeValue",
                "value": abs(res_x),
                "unitText": "m" if sample_meta["crs_units"] == "meters" else "degrees"
            }
    
    @staticmethod
    def _add_sampling_strategy(geocroissant: Dict, filename: str) -> None:
        """Add sampling strategy if detected."""
        sampling_strategy = detect_sampling_strategy(filename)
        if sampling_strategy:
            geocroissant["geocr:samplingStrategy"] = sampling_strategy
    
    def _add_dataset_level_bands(self, geocroissant: Dict, file_structure: Dict, 
                                  metadata_cache: Dict, sensor: Optional[str]) -> None:
        """Add dataset-level band configuration and spectral metadata."""
        # Get image metadata
        image_meta = None
        for split, types in file_structure.items():
            if "images" in types and types["images"]:
                image_meta = metadata_cache.get(types["images"][0])
                break
        
        if not image_meta or not image_meta.get("bands"):
            return
        
        band_names = []
        spectral_bands = []
        
        for band_meta in image_meta["bands"]:
            band_idx = band_meta["index"] - 1
            
            # Get band name
            band_name = band_meta.get("name") or band_meta.get("description")
            if not band_name and sensor:
                spectral_info = get_spectral_band_info(sensor, band_idx)
                band_name = spectral_info.get("name", f"Band {band_meta['index']}")
            else:
                band_name = band_name or f"Band {band_meta['index']}"
            
            band_names.append(band_name)
            
            # Add spectral information if available
            if sensor:
                spectral_info = get_spectral_band_info(sensor, band_idx)
                if spectral_info:
                    spectral_band = {
                        "@type": "geocr:SpectralBand",
                        "name": band_name,
                        "geocr:centerWavelength": {
                            "@type": "QuantitativeValue",
                            "value": spectral_info["wavelength"],
                            "unitText": spectral_info["unit"]
                        },
                        "geocr:bandwidth": {
                            "@type": "QuantitativeValue",
                            "value": spectral_info["bandwidth"],
                            "unitText": spectral_info["unit"]
                        }
                    }
                    spectral_bands.append(spectral_band)
        
        # Add band configuration at dataset level
        geocroissant["geocr:bandConfiguration"] = {
            "@type": "geocr:BandConfiguration",
            "geocr:totalBands": len(band_names),
            "geocr:bandNameList": band_names
        }
        
        # Add spectral metadata at dataset level
        if spectral_bands:
            geocroissant["geocr:spectralBandMetadata"] = spectral_bands
    
    @staticmethod
    def _add_distribution(geocroissant: Dict, root_dir: Path) -> None:
        """Add distribution information."""
        dataset_name = root_dir.name
        
        # FileObject as root
        file_object = {
            "@type": "cr:FileObject",
            "@id": "data_repo",
            "name": "data_repo",
            "description": "Directory containing the dataset files",
            "contentUrl": str(root_dir.as_posix()),
            "encodingFormat": "local_directory",
            "md5": "placeholder_hash_for_directory"
        }
        geocroissant["distribution"].append(file_object)
        
        # FileSet
        main_fileset = {
            "@type": "cr:FileSet",
            "@id": f"tiff-files-for-{dataset_name}",
            "name": f"tiff-files-for-{dataset_name}",
            "description": "Local TIFF files organized in training/validation splits.",
            "containedIn": {"@id": "data_repo"},
            "encodingFormat": "image/tiff",
            "includes": "**/*.tif*"
        }
        geocroissant["distribution"].append(main_fileset)
    
    def _add_recordsets(self, geocroissant: Dict, root_dir: Path, file_structure: Dict,
                       metadata_cache: Dict, sensor: Optional[str]) -> None:
        """Add RecordSet with fields."""
        dataset_name = root_dir.name
        
        # Detect regex patterns
        has_merged_pattern = any(
            '_merged' in f.name
            for split, types in file_structure.items()
            if "images" in types
            for f in types["images"]
        )
        has_mask_pattern = any(
            '.mask.' in f.name
            for split, types in file_structure.items()
            if "masks" in types
            for f in types["masks"]
        )
        
        image_regex = ".*_merged\\.tif$" if has_merged_pattern else ".*(?<!mask)\\.tif$"
        mask_regex = ".*\\.mask\\.tif$" if has_mask_pattern else ".*mask.*\\.tif$"
        
        # Create RecordSet
        recordset = {
            "@type": "cr:RecordSet",
            "@id": dataset_name,
            "name": dataset_name,
            "description": f"{dataset_name} dataset with satellite imagery and mask annotations.",
            "field": []
        }
        
        # Add image field
        self._add_image_field(recordset, dataset_name, file_structure, metadata_cache, 
                            sensor, image_regex)
        
        # Add mask field
        self._add_mask_field(recordset, dataset_name, file_structure, metadata_cache, mask_regex)
        
        geocroissant["recordSet"].append(recordset)
    
    def _add_image_field(self, recordset: Dict, dataset_name: str, file_structure: Dict,
                        metadata_cache: Dict, sensor: Optional[str], image_regex: str) -> None:
        """Add image field to RecordSet."""
        # Get image metadata
        image_meta = None
        for split, types in file_structure.items():
            if "images" in types and types["images"]:
                image_meta = metadata_cache.get(types["images"][0])
                break
        
        if not image_meta:
            return
        
        image_field = {
            "@type": "cr:Field",
            "@id": f"{dataset_name}/image",
            "name": f"{dataset_name}/image",
            "description": "Satellite imagery with multiple spectral bands converted to reflectance.",
            "dataType": "sc:ImageObject",
            "source": {
                "fileSet": {"@id": f"tiff-files-for-{dataset_name}"},
                "extract": {"fileProperty": "fullpath"},
                "transform": {"regex": image_regex}
            }
        }
        
        # Add band configuration
        if image_meta.get("bands"):
            band_names = []
            for band_meta in image_meta["bands"]:
                band_idx = band_meta["index"] - 1
                band_name = band_meta.get("name") or band_meta.get("description")
                if not band_name and sensor:
                    spectral_info = get_spectral_band_info(sensor, band_idx)
                    band_name = spectral_info.get("name", f"Band {band_meta['index']}")
                else:
                    band_name = band_name or f"Band {band_meta['index']}"
                band_names.append(band_name)
            
            image_field["geocr:bandConfiguration"] = {
                "@type": "geocr:BandConfiguration",
                "geocr:totalBands": image_meta["count"],
                "geocr:bandNameList": band_names
            }
        
        recordset["field"].append(image_field)
    
    @staticmethod
    def _add_mask_field(recordset: Dict, dataset_name: str, file_structure: Dict,
                       metadata_cache: Dict, mask_regex: str) -> None:
        """Add mask field to RecordSet."""
        # Get mask metadata
        mask_meta = None
        for split, types in file_structure.items():
            if "masks" in types and types["masks"]:
                mask_meta = metadata_cache.get(types["masks"][0])
                break
        
        if not mask_meta:
            return
        
        mask_field = {
            "@type": "cr:Field",
            "@id": f"{dataset_name}/mask",
            "name": f"{dataset_name}/mask",
            "description": "Mask annotations with values representing different classes.",
            "dataType": "sc:ImageObject",
            "source": {
                "fileSet": {"@id": f"tiff-files-for-{dataset_name}"},
                "extract": {"fileProperty": "fullpath"},
                "transform": {"regex": mask_regex}
            }
        }
        
        # Add band configuration for masks
        if mask_meta.get("count"):
            mask_field["geocr:bandConfiguration"] = {
                "@type": "geocr:BandConfiguration",
                "geocr:totalBands": mask_meta["count"],
                "geocr:bandNameList": ["mask"] * mask_meta["count"]
            }
        
        recordset["field"].append(mask_field)
