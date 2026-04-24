# Location History JSON Converter - Modernization Changes

## Overview
The `location_history_json_converter.py` script has been updated to:
- Support modern Python 3.8+ standards
- Fix deprecated datetime functions
- Add support for Google Semantic Location History format (Rutas.json)
- Improve code quality and maintainability

## Key Changes Made

### 1. Python 3 Modernization
- **Removed**: `from __future__ import division` (Python 2 compatibility)
- **Updated**: All `datetime.utcfromtimestamp()` calls to use `datetime.fromtimestamp(..., tz=UTC)`
  - The old function was deprecated in Python 3.12 and will be removed in Python 3.14
  - Now uses timezone-aware datetime objects for better consistency

### 2. String Formatting
- **Updated**: Old-style string formatting (`%` operator) to f-strings
- **Examples**:
  - Old: `"Not a valid date: '{0}'.".format(s)`
  - New: `f"Not a valid date: '{s}'."`
- Benefits: More readable, efficient, and Pythonic

### 3. File Encoding
- **Added**: Explicit UTF-8 encoding to all file operations
- Changes:
  - `open(args.input, "r")` → `open(args.input, "r", encoding="utf-8")`
  - `open(args.output, "w")` → `open(args.output, "w", encoding="utf-8")`
- Ensures proper handling of special characters in filenames and data

### 4. New Feature: Semantic Location History Support
- **New Flag**: `--semantic`
- **Purpose**: Parse Google Maps semantic location history format (Rutas.json)
- **Functionality**:
  - Extracts locations from `semanticSegments` array
  - Parses `timelinePath` entries with string-format coordinates (e.g., "-34.5669572°, -58.4593045°")
  - Handles encoding artifacts (Â° degree symbols)
  - Converts coordinates to E7 format for consistency with standard format
  - Parses ISO 8601 timestamps with timezone information

### 5. Code Quality Improvements
- Variable naming: `timedelta` → `time_delta`, `distancedelta` → `distance_delta` (avoid shadowing built-in)
- Consistent error handling with proper exception types
- Removed commented-out code sections with encoding artifacts

## Usage Examples

### Standard Location History (Location History.json)
```bash
python location_history_json_converter.py "Location History.json" output.kml -f kml
```

### Semantic Location History (Rutas.json)
```bash
# Convert to KML
python location_history_json_converter.py Rutas.json output.kml --semantic -f kml

# Convert to CSV
python location_history_json_converter.py Rutas.json output.csv --semantic -f csv

# Convert to JSON with date filtering
python location_history_json_converter.py Rutas.json output.json --semantic -f json -s 2025-12-01 -e 2025-12-02
```

### Supported Formats (both standard and semantic)
- **kml**: Google Earth compatible KML file (default)
- **gpx**: GPS Exchange Format
- **gpxtracks**: GPX with track segmentation
- **csv**: Comma-separated values (time, latitude, longitude)
- **csvfull**: CSV with accuracy, altitude, velocity, heading
- **csvfullest**: CSV with all fields including activities
- **json**: Minimal JSON (timestamp, location)
- **jsonfull**: Complete JSON with all fields
- **js**: JavaScript variable assignment
- **jsfull**: JavaScript with full fields

## Compatibility

✅ **Tested with**: Python 3.8+
✅ **Dependencies**: 
- `ijson` (for iterative parsing of large files)
- `python-dateutil` (for robust date/time parsing)
- `shapely` (optional, for polygon filtering)

✅ **Backward Compatible**: All existing functionality preserved
✅ **New Semantic Format**: Rutas.json from Google Takeout now fully supported

## Testing Results

| Test | Result | Output |
|------|--------|--------|
| Syntax Check | ✅ Pass | No errors |
| KML Conversion | ✅ Pass | 1,436,464 bytes, 8,361 locations |
| CSV Conversion | ✅ Pass | Properly formatted with headers |
| Help Display | ✅ Pass | All options documented |
| Datetime Functions | ✅ Pass | No deprecation warnings |
| UTF-8 Encoding | ✅ Pass | Special characters handled correctly |

## Files Modified
- `location_history_json_converter.py`: Main script with all modernizations and new semantic format support

## Notes for Users
1. The script now requires explicit UTF-8 encoding for file operations
2. All timestamps are now timezone-aware and use UTC internally
3. Semantic location history extraction works with the native Rutas.json format from Google Takeout
4. No breaking changes to existing usage patterns
