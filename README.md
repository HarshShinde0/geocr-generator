# GeoCroissant Generator

## Overview

[Croissant](https://github.com/mlcommons/croissant) is a JSON-LD-based metadata standard for describing machine learning datasets, developed by MLCommons. Croissant provides a rich, structured format that helps users discover, understand, and use ML datasets by providing a consistent structure for metadata representation and querying.

The GeoCroissant Generator can be used as a cross-platform command line interface (CLI) program or a Python library that combines automatically extracted geospatial information from raw assets and other user-provided metadata to build a Croissant-compliant metadata record with geospatial extensions. Generated GeoCroissant records can be saved locally for dataset documentation and discovery.

The GeoCroissant Generator extends the standard Croissant format with geospatial metadata, enabling better description and discovery of geospatially-enabled machine learning datasets. Using the GeoCroissant Generator to describe an asset collection allows for comprehensive documentation of spatial-temporal ML datasets.

## Features

- Automatic extraction of geospatial metadata from raw assets
- Generation of Croissant-compliant JSON-LD metadata
- Support for geospatial extensions to the Croissant format
- Command-line interface and Python library usage
- Flexible configuration via YAML files

## Installation

```bash
pip install -e .
```

## Usage

### Command Line Interface

```bash
geocr-generate --config path/to/config.yaml --output path/to/output.json
```

### Python Library

```python
from geocr_generator.core import generator

# Generate GeoCroissant metadata
metadata = generator.generate(config_path="path/to/config.yaml")
```

## Configuration

See the example configuration file in `docs/config.example.yaml` for details on how to configure your metadata generation.

## Documentation

Additional documentation can be found in the `docs/` directory, including:
- Geospatial Croissant schema extensions (`croissant_geo.ttl`)
- Usage examples and guides (`geocr.md`)