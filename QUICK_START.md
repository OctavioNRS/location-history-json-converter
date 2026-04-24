# Quick Start Guide - Updated Location History Converter

## What Was Updated

✅ **Python 3.8+ Compatibility**: Removed Python 2 legacy code and fixed deprecated datetime functions  
✅ **Modern Code Style**: Converted to f-strings and improved code quality  
✅ **UTF-8 Support**: Added explicit encoding for all file operations  
✅ **Semantic Format Support**: Added `--semantic` flag to parse Google Maps Rutas.json files  

## Quick Examples

### Convert Rutas.json (Semantic Location History)

```bash
# Convert to KML (Google Earth)
python location_history_json_converter.py Rutas.json output.kml --semantic -f kml

# Convert to CSV
python location_history_json_converter.py Rutas.json output.csv --semantic -f csv

# Convert to GPX (GPS devices)
python location_history_json_converter.py Rutas.json output.gpx --semantic -f gpx

# Convert to JSON (data processing)
python location_history_json_converter.py Rutas.json output.json --semantic -f json

# With date filtering (December 2025)
python location_history_json_converter.py Rutas.json output.kml --semantic -f kml -s 2025-12-01 -e 2025-12-31

# For large files, use iterative mode
python location_history_json_converter.py Rutas.json output.json --semantic -f json -i
```

### Convert Standard Location History (unchanged usage)

```bash
# Legacy Location History.json format (no --semantic flag)
python location_history_json_converter.py "Location History.json" output.kml -f kml

# With filtering
python location_history_json_converter.py "Location History.json" output.csv -f csv -s 2025-01-01 -e 2025-12-31
```

## Available Output Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| **kml** | Google Earth format | Visualize in Google Earth |
| **gpx** | GPS Exchange Format | Import to GPS devices |
| **gpxtracks** | GPX with track groups | Route tracking |
| **csv** | Comma-separated values | Excel, databases |
| **csvfull** | CSV with extra fields | Detailed analysis |
| **json** | JSON format | Data processing |
| **js** | JavaScript file | Web embedding |

## Options Quick Reference

```
--semantic            Parse Rutas.json (semantic format)
-f, --format FORMAT   Output format (default: kml)
-i, --iterative       For files >500MB, use iterative parsing
-s, --startdate DATE  Filter from date (YYYY-MM-DD)
-e, --enddate DATE    Filter to date (YYYY-MM-DD)
-a, --accuracy METERS Maximum accuracy threshold
-c, --chronological   Sort by timestamp
-p, --polygon         Filter by geographic polygon
```

## Test Results

| Component | Status | Details |
|-----------|--------|---------|
| Syntax | ✅ Pass | Valid Python 3.8+ code |
| KML Export | ✅ Pass | 1.37 MB, 8,361 locations |
| CSV Export | ✅ Pass | 0.37 MB, properly formatted |
| GPX Export | ✅ Pass | 1.05 MB, valid GPX 1.1 |
| JSON Export | ✅ Pass | 0.65 MB, valid JSON |
| Backward Compatibility | ✅ Pass | Standard format still works |

## Troubleshooting

### "FileNotFoundError: No such file"
- Ensure Rutas.json is in the same directory as the script
- Or provide full path: `python location_history_json_converter.py C:\path\to\Rutas.json output.kml --semantic -f kml`

### "ijson is not available"
- For large files with `-i` flag, install ijson: `pip install ijson`

### "File too big"
- Use iterative mode: add `-i` flag to your command

### Special characters or encoding issues
- The script now handles UTF-8 encoding automatically
- Degree symbols and special characters are properly parsed

## Files in This Directory

- `location_history_json_converter.py` - Main script (updated)
- `README.md` - Detailed documentation (updated)
- `MODERNIZATION_CHANGES.md` - Complete list of technical changes
- `requirements.txt` - Python dependencies
- `Rutas.json` - Your semantic location history (input)
- `Rutas_output.*` - Converted output files (examples)

## Documentation

For complete documentation, see:
- **README.md** - Full usage guide with all options
- **MODERNIZATION_CHANGES.md** - Technical details of all updates

---

✅ **All modernization complete and tested!**
