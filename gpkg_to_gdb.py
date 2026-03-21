#!/usr/bin/env python3
"""
Export GeoPackage to Esri File Geodatabase using GDAL/OGR OpenFileGDB driver.

Handles problematic GeoPackage data:
  - Invalid geometry: use --make-valid to fix, or --skip-invalid to skip
  - Non-sequential FIDs (deleted records): --unset-fid (default) so output gets new IDs
  - Failed features: -skipfailures (default) to continue processing

Requires GDAL >= 3.6 (for OpenFileGDB write support).
Uses ogr2ogr command-line tool for full option support.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def gpkg_to_gdb(
    gpkg_path: Path,
    gdb_path: Path,
    *,
    layers: list[str] | None = None,
    make_valid: bool = False,
    skip_invalid: bool = False,
    skip_failures: bool = True,
    unset_fid: bool = True,
    overwrite: bool = False,
) -> bool:
    """
    Convert GeoPackage to Esri File Geodatabase using ogr2ogr.

    Args:
        gpkg_path: Path to input GeoPackage (.gpkg)
        gdb_path: Path to output File Geodatabase (.gdb directory)
        layers: List of layer names to convert, or None for all layers
        make_valid: Run MakeValid() on geometries before writing
        skip_invalid: Skip features with invalid geometry (GDAL 3.10+, GEOS)
        skip_failures: Continue on failure, skip bad features
        unset_fid: Do not preserve source FID; let output assign new IDs
        overwrite: Overwrite existing output layer

    Returns:
        True on success, False on failure
    """
    cmd = ["ogr2ogr", "-f", "OpenFileGDB"]

    if overwrite:
        cmd.append("-overwrite")
    if make_valid:
        cmd.append("-makevalid")
    if skip_invalid:
        cmd.append("-skipinvalid")
    if skip_failures:
        cmd.append("-skipfailures")
    if unset_fid:
        cmd.append("-unsetFid")

    cmd.extend([str(gdb_path), str(gpkg_path)])

    if layers:
        cmd.extend(layers)

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except FileNotFoundError:
        print("Error: ogr2ogr not found. Ensure GDAL is installed and on PATH.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Conversion failed: {e}", file=sys.stderr)
        return False


def list_layers(gpkg_path: Path) -> list[str]:
    """List vector layer names in a GeoPackage using ogrinfo."""
    try:
        result = subprocess.run(
            ["ogrinfo", "-al", "-so", str(gpkg_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return []
        names = []
        for line in result.stdout.splitlines():
            if line.strip().startswith("Layer name:"):
                names.append(line.split("Layer name:", 1)[1].strip())
        return names
    except FileNotFoundError:
        return []


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export GeoPackage to Esri File Geodatabase (OpenFileGDB)"
    )
    parser.add_argument(
        "gpkg",
        type=Path,
        help="Input GeoPackage path (.gpkg)",
    )
    parser.add_argument(
        "gdb",
        type=Path,
        help="Output File Geodatabase path (.gdb)",
    )
    parser.add_argument(
        "-l", "--layers",
        nargs="+",
        help="Layer name(s) to convert (default: all)",
    )
    parser.add_argument(
        "--make-valid",
        action="store_true",
        help="Fix invalid geometries with MakeValid() (requires GEOS)",
    )
    parser.add_argument(
        "--skip-invalid",
        action="store_true",
        help="Skip features with invalid geometry (GDAL 3.10+, GEOS)",
    )
    parser.add_argument(
        "--no-skip-failures",
        action="store_true",
        help="Stop on first failure (default: continue, skip bad features)",
    )
    parser.add_argument(
        "--preserve-fid",
        action="store_true",
        help="Preserve source FID (default: unset, let GDB assign new IDs)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output layer",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List layers in GeoPackage and exit",
    )

    args = parser.parse_args()

    if args.list:
        names = list_layers(args.gpkg)
        if not names:
            print("No layers found or unable to open GeoPackage.", file=sys.stderr)
            return 1
        for n in names:
            print(n)
        return 0

    if not args.gpkg.exists():
        print(f"Input not found: {args.gpkg}", file=sys.stderr)
        return 1

    ok = gpkg_to_gdb(
        args.gpkg,
        args.gdb,
        layers=args.layers,
        make_valid=args.make_valid,
        skip_invalid=args.skip_invalid,
        skip_failures=not args.no_skip_failures,
        unset_fid=not args.preserve_fid,
        overwrite=args.overwrite,
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
