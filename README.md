# GeoPackage to Geodatabase Conversion

Export GeoPackage (.gpkg) to Esri File Geodatabase (.gdb) using GDAL/OGR and the OpenFileGDB driver.

## Why this approach?

Export Features (arcpy) can fail when the GeoPackage has:
- **Invalid geometry** – some features have bad geometries
- **Non-sequential FIDs** – deleted records cause gaps (e.g. 1, 2, 5, 8 instead of 1, 2, 3, 4)

This script uses **ogr2ogr** (GDAL/OGR) instead, which:
- Handles invalid geometry (`--make-valid` or `--skip-invalid`)
- Ignores source FID and assigns new sequential OBJECTIDs (`-unsetFid`)
- Can skip failed features and continue (`-skipfailures`)

## Requirements

- **GDAL >= 3.6** (for OpenFileGDB write support)
- Command-line tools: `ogr2ogr`, `ogrinfo`

Install GDAL:
```bash
# Ubuntu/Debian
sudo apt install gdal-bin

# Conda
conda install -c conda-forge gdal

# Windows: use OSGeo4W or install from gisinternals.com
```

## Usage

```bash
# Convert all layers, default options (skip failures, unset FID)
python gpkg_to_gdb.py input.gpkg output.gdb

# Fix invalid geometries before writing
python gpkg_to_gdb.py input.gpkg output.gdb --make-valid

# Skip invalid geometries instead of fixing
python gpkg_to_gdb.py input.gpkg output.gdb --skip-invalid

# Convert specific layer(s)
python gpkg_to_gdb.py input.gpkg output.gdb -l LayerName1 LayerName2

# List layers in GeoPackage
python gpkg_to_gdb.py input.gpkg output.gdb --list

# Overwrite existing output
python gpkg_to_gdb.py input.gpkg output.gdb --overwrite
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--make-valid` | off | Fix invalid geometries (requires GEOS) |
| `--skip-invalid` | off | Skip features with invalid geometry (GDAL 3.10+) |
| `--no-skip-failures` | off | Stop on first error (default: continue) |
| `--preserve-fid` | off | Keep source FID (default: let GDB assign new IDs) |
| `--overwrite` | off | Overwrite existing output layer |
| `-l`, `--layers` | all | Layer name(s) to convert |
| `--list` | - | List layers and exit |

## Programmatic use

```python
from gpkg_to_gdb import gpkg_to_gdb
from pathlib import Path

gpkg_to_gdb(
    Path("input.gpkg"),
    Path("output.gdb"),
    make_valid=True,
    skip_failures=True,
    unset_fid=True,  # handle non-sequential FIDs
)
```

