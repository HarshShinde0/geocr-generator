#!/usr/bin/env python3
"""
GeoCroissant Generator CLI Script
"""

import sys
import argparse
from pathlib import Path

from core.generator import GeoCroissantGenerator
from core.config import Config


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='geocr-generator',
        description="Generate GeoCroissant metadata from geospatial datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate metadata for a directory
  geocr-generate ./hls_burn_scars

  # Specify output path
  geocr-generate ./hls_burn_scars --output geocroissant.json

  # Use custom configuration
  geocr-generate ./hls_burn_scars --config config.yaml

  # Disable statistics computation
  geocr-generate ./hls_burn_scars --no-stats
        """
    )
    
    parser.add_argument(
        'directory',
        type=Path,
        help='Root directory containing GeoTIFF files'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output path for GeoCroissant JSON (default: <directory>/geocroissant.json)'
    )
    
    parser.add_argument(
        '-c', '--config',
        type=Path,
        help='Path to configuration YAML file'
    )
    
    parser.add_argument(
        '--no-stats',
        action='store_true',
        help='Disable band statistics computation (faster)'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable metadata cache file creation'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Validate directory
    if not args.directory.exists():
        print(f"Error: Directory not found: {args.directory}", file=sys.stderr)
        sys.exit(1)
    
    # Load configuration
    if args.config:
        if not args.config.exists():
            print(f"Error: Config file not found: {args.config}", file=sys.stderr)
            sys.exit(1)
        config = Config.from_file(args.config)
    else:
        config = Config()
    
    # Apply CLI overrides
    if args.no_stats:
        config.set('extraction.compute_statistics', False)
    if args.no_cache:
        config.set('output.save_metadata_cache', False)
    
    # Set output path
    output_path = args.output or (args.directory / "geocroissant.json")
    
    # Generate metadata
    try:
        generator = GeoCroissantGenerator(config)
        geocroissant = generator.generate(args.directory, output_path)
        
        print(f"\n✅ Success! Generated GeoCroissant metadata with:")
        print(f"  - {len(geocroissant['distribution'])} distribution items")
        print(f"  - {len(geocroissant['recordSet'])} RecordSets")
        if geocroissant.get('keywords'):
            print(f"  - Keywords: {', '.join(geocroissant['keywords'])}")
        if geocroissant.get('temporalCoverage'):
            print(f"  - Temporal coverage: {geocroissant['temporalCoverage']}")
        
        return 0
    
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        if '--debug' in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
