# Data Loader User Guide

## Overview

`data_loader.py` is a comprehensive Python utility for loading, analyzing, and manipulating location history CSV data. It's specifically designed for location history visualization projects and provides powerful functions to extract insights from GPS coordinate datasets.

**Key Features:**
- Load CSV files with automatic header parsing
- Filter data by date, time, and geographic bounds
- Calculate distance, speed, and movement statistics
- Identify stay points and location clusters
- Export data in visualization-ready format

---

## Installation

### Prerequisites
- Python 3.7+
- Required packages: pandas, numpy, shapely, python-dateutil

### Install Dependencies
```bash
pip install pandas numpy shapely python-dateutil
```

### File Location
Place `data_loader.py` in your project directory alongside your CSV files.

---

## Quick Start

### Basic Usage

```python
from data_loader import LocationDataLoader

# Load your CSV file
loader = LocationDataLoader('output.csv')

# Get a summary report
loader.print_report()

# Export data ready for visualization
viz_data = loader.export_for_visualization('viz_output.csv')
```

### Running from Command Line
```bash
python data_loader.py output.csv
```

This will:
1. Load the CSV file
2. Print a comprehensive data report
3. Show sample hourly data density
4. Display the first 5 identified stay points

---

## CSV File Format

The script expects CSV files with headers in the first row. Supported columns:

**Required:**
- `Latitude` - Geographic latitude coordinate
- `Longitude` - Geographic longitude coordinate

**Optional:**
- `Time` - Timestamp (any standard format: `2026-03-03 00:40:00`, ISO 8601, etc.)
- Additional columns are preserved in output

**Example:**
```
Time,Latitude,Longitude
2026-03-03 00:40:00,-34.56624790,-58.46041670
2026-03-03 01:34:00,-34.56622500,-58.46041790
2026-03-03 02:38:00,-34.56620580,-58.46040920
```

---

## Core Class: LocationDataLoader

### Initialization

```python
loader = LocationDataLoader('path/to/file.csv')
```

**Parameters:**
- `csv_file` (str): Path to CSV file

**What happens:**
- Reads CSV with first row as headers
- Parses datetime if 'Time' column exists
- Stores original data for filter reset

---

## Data Access Methods

### get_dataframe()
Return current data as a pandas DataFrame.

```python
df = loader.get_dataframe()
print(df.head())
```

**Use case:** Direct access to data for custom analysis

---

### get_summary()
Get comprehensive statistics about the data.

```python
summary = loader.get_summary()

# Access summary data
print(f"Total records: {summary['total_records']}")
print(f"Time range: {summary['time_range']}")
print(f"Spatial bounds: {summary['spatial_bounds']}")
```

**Returns Dictionary:**
```python
{
    'total_records': 2773,
    'columns': ['Time', 'Latitude', 'Longitude'],
    'time_range': {
        'start': Timestamp('2026-03-03 00:40:00'),
        'end': Timestamp('2026-04-20 12:59:00'),
        'duration_days': 48
    },
    'spatial_bounds': {
        'north': -34.560000,
        'south': -34.580000,
        'east': -58.440000,
        'west': -58.460000,
        'center_lat': -34.570788,
        'center_lon': -58.453449
    }
}
```

---

### print_report()
Print a formatted summary report to console.

```python
loader.print_report()
```

**Output includes:**
- File name and total records
- Time range and duration
- Spatial bounds and center point
- Total distance traveled
- Speed statistics

---

## Filtering Methods

All filter methods support **method chaining** and return `self`.

### filter_by_date_range()
Filter data to a specific date range.

```python
# Filter March 2026
loader.filter_by_date_range('2026-03-01', '2026-03-31')

# Method chaining
loader.filter_by_date_range('2026-03-03', '2026-03-10').print_report()
```

**Parameters:**
- `start_date` (str): Start date (YYYY-MM-DD)
- `end_date` (str): End date (YYYY-MM-DD)

**Note:** Includes all data from start_date 00:00:00 through end_date 23:59:59

---

### filter_by_time_range()
Filter data to specific hours of day.

```python
# Morning hours (8 AM - 12 PM)
loader.filter_by_time_range(8, 12)

# Evening hours (18:00 - 23:59)
loader.filter_by_time_range(18, 23)
```

**Parameters:**
- `start_hour` (int): Starting hour (0-23)
- `end_hour` (int): Ending hour (0-23)

**Use case:** Analyze commute patterns or nighttime behavior

---

### filter_by_bounds()
Filter data to a geographic bounding box.

```python
# Filter to downtown area
loader.filter_by_bounds(
    north=-34.560,
    south=-34.580,
    east=-58.440,
    west=-58.460
)
```

**Parameters:**
- `north` (float): Northern latitude (maximum latitude)
- `south` (float): Southern latitude (minimum latitude)
- `east` (float): Eastern longitude (maximum longitude)
- `west` (float): Western longitude (minimum longitude)

**Use case:** Analyze specific geographic regions

---

### reset_filters()
Reset data to original state, removing all filters.

```python
loader.reset_filters()
```

**Use case:** Start analysis with clean data after filtering

---

## Analysis Methods

### get_distance_traveled()
Calculate total distance traveled between all consecutive points.

```python
distance = loader.get_distance_traveled()
print(f"Total distance: {distance:.2f} km")
```

**Returns:** Float (distance in kilometers)

**How it works:**
- Sorts data by time (if available)
- Uses Haversine formula for accurate geographic distances
- Sums distances between consecutive points

**Use case:** Compare travel distances across different time periods or areas

---

### get_speed_stats()
Calculate speed statistics from temporal and spatial data.

```python
stats = loader.get_speed_stats()

print(f"Average speed: {stats['mean_speed_kmh']:.2f} km/h")
print(f"Maximum speed: {stats['max_speed_kmh']:.2f} km/h")
print(f"Minimum speed: {stats['min_speed_kmh']:.2f} km/h")
```

**Returns Dictionary:**
```python
{
    'mean_speed_kmh': 3.68,
    'max_speed_kmh': 145.07,
    'min_speed_kmh': 0.0,
    'std_speed_kmh': 12.45,
    'median_speed_kmh': 0.03
}
```

**Requires:** Time, Latitude, and Longitude columns

**Use case:** Detect transportation modes or anomalies in movement patterns

---

### get_temporal_density()
Get data point density over different time units.

```python
# Density by hour
hourly = loader.get_temporal_density('hour')
print(hourly.head())

# Density by day of week
daily_pattern = loader.get_temporal_density('day_of_week')

# Density by hour of day (0-23)
hour_pattern = loader.get_temporal_density('hour_of_day')
```

**Parameters:**
- `time_unit` (str): One of:
  - `'hour'` - Count per hour
  - `'day'` - Count per calendar day
  - `'day_of_week'` - Count per day of week
  - `'hour_of_day'` - Count per hour (0-23)

**Returns:** pandas Series (sorted by index)

**Use case:** Visualize when data was collected, identify patterns

---

### get_clusters()
Identify location clusters (areas visited frequently).

```python
# Find clusters within 500m radius with at least 3 points
clusters = loader.get_clusters(max_distance_km=0.5, min_points=3)

for i, cluster in enumerate(clusters):
    print(f"\nCluster {i+1}:")
    print(f"  Center: ({cluster['center_lat']:.6f}, {cluster['center_lon']:.6f})")
    print(f"  Points: {cluster['point_count']}")
    print(f"  Visits: {cluster['first_visit']} to {cluster['last_visit']}")
```

**Parameters:**
- `max_distance_km` (float): Max radius for same cluster (default: 0.5)
- `min_points` (int): Minimum points required (default: 3)

**Returns:** List of cluster dictionaries

**Cluster Dictionary:**
```python
{
    'center_lat': -34.5707,
    'center_lon': -58.4534,
    'point_count': 50,
    'visit_times': [Timestamp(...), ...],
    'first_visit': Timestamp('2026-03-03 00:40:00'),
    'last_visit': Timestamp('2026-03-10 23:30:00')
}
```

**Use case:** Find home, work, and frequented locations

---

### get_stay_points()
Identify locations where the user stayed stationary.

```python
# Find places stayed >10 minutes within 100m radius
stays = loader.get_stay_points(
    max_distance_km=0.1,
    min_duration_minutes=10
)

for i, stay in enumerate(stays[:10]):
    print(f"\nStay {i+1}:")
    print(f"  Location: ({stay['latitude']:.6f}, {stay['longitude']:.6f})")
    print(f"  Duration: {stay['duration_minutes']:.1f} minutes")
    print(f"  Time: {stay['start_time']} to {stay['end_time']}")
```

**Parameters:**
- `max_distance_km` (float): Max distance radius (default: 0.1 km)
- `min_duration_minutes` (float): Min duration to count (default: 10)

**Returns:** List of stay point dictionaries

**Stay Point Dictionary:**
```python
{
    'latitude': -34.5706,
    'longitude': -58.4534,
    'start_time': Timestamp('2026-03-03 00:40:00'),
    'end_time': Timestamp('2026-03-03 02:30:00'),
    'duration_minutes': 110.0,
    'point_count': 15
}
```

**Use case:** Identify time spent at locations, find home/work hours

---

## Export Methods

### export_for_visualization()
Export data in a format optimized for visualization libraries.

```python
# Export to new CSV with added columns
viz_data = loader.export_for_visualization('viz_ready.csv')

# Or get as DataFrame for direct use
df = loader.export_for_visualization()
```

**Parameters:**
- `output_file` (str, optional): Path to save CSV file

**Returns:** pandas DataFrame

**Added Columns (if Time available):**
- `date` - Date only (YYYY-MM-DD)
- `hour` - Hour of day (0-23)
- `day_of_week` - Day name (Monday, Tuesday, etc.)

**Processing:**
- Removes rows with null Latitude/Longitude
- Preserves all original columns
- Adds temporal columns for easy grouping

**Use case:** Prepare data for matplotlib, plotly, or other visualization tools

---

## Common Workflows

### Workflow 1: Daily Movement Pattern Analysis

```python
from data_loader import LocationDataLoader

# Load data
loader = LocationDataLoader('output.csv')

# Get summary
summary = loader.get_summary()
print(f"Analyzing {summary['total_records']} records over {summary['time_range']['duration_days']} days")

# Calculate key metrics
distance = loader.get_distance_traveled()
speed_stats = loader.get_speed_stats()

print(f"Total distance: {distance:.2f} km")
print(f"Average speed: {speed_stats['mean_speed_kmh']:.2f} km/h")

# Find key locations
clusters = loader.get_clusters(max_distance_km=0.5, min_points=5)
print(f"Found {len(clusters)} major location clusters")

for i, cluster in enumerate(clusters[:3]):
    print(f"\nLocation {i+1}: ({cluster['center_lat']:.4f}, {cluster['center_lon']:.4f})")
    print(f"  Visited {cluster['point_count']} times")
```

---

### Workflow 2: Comparing Time Periods

```python
from data_loader import LocationDataLoader

loader = LocationDataLoader('output.csv')

# Compare weekday vs weekend
loader.filter_by_date_range('2026-03-03', '2026-03-07')  # Weekday
weekday_distance = loader.get_distance_traveled()

loader.reset_filters()
loader.filter_by_date_range('2026-03-08', '2026-03-09')  # Weekend
weekend_distance = loader.get_distance_traveled()

print(f"Weekday distance: {weekday_distance:.2f} km")
print(f"Weekend distance: {weekend_distance:.2f} km")
```

---

### Workflow 3: Geographic Region Analysis

```python
from data_loader import LocationDataLoader

loader = LocationDataLoader('output.csv')

# Get city center bounds (Buenos Aires example)
downtown_bounds = {
    'north': -34.5600,
    'south': -34.6200,
    'east': -58.3500,
    'west': -58.4000
}

loader.filter_by_bounds(**downtown_bounds)
downtown_distance = loader.get_distance_traveled()

loader.reset_filters()
total_distance = loader.get_distance_traveled()

downtown_percent = (downtown_distance / total_distance) * 100
print(f"{downtown_percent:.1f}% of travel occurred downtown")
```

---

### Workflow 4: Identifying Home Location

```python
from data_loader import LocationDataLoader

loader = LocationDataLoader('output.csv')

# Find longest stay points (likely home)
stays = loader.get_stay_points(
    max_distance_km=0.05,  # Very tight radius
    min_duration_minutes=60  # At least 1 hour
)

# Sort by duration
stays.sort(key=lambda x: x['duration_minutes'], reverse=True)

# Top stay location is likely home
home = stays[0]
print(f"Likely home location: ({home['latitude']:.6f}, {home['longitude']:.6f})")
print(f"Longest stay: {home['duration_minutes']:.0f} minutes")
```

---

### Workflow 5: Preparing Data for Visualization

```python
from data_loader import LocationDataLoader
import matplotlib.pyplot as plt

loader = LocationDataLoader('output.csv')

# Export visualization-ready data
viz_df = loader.export_for_visualization('viz_data.csv')

# Now ready for plotting
plt.scatter(viz_df['Longitude'], viz_df['Latitude'], alpha=0.5, s=1)
plt.title('Location History Map')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.show()
```

---

## Method Chaining Examples

All filter methods return `self`, enabling method chaining:

```python
from data_loader import LocationDataLoader

loader = LocationDataLoader('output.csv')

# Chain multiple filters
result = (loader
    .filter_by_date_range('2026-03-01', '2026-03-31')
    .filter_by_time_range(8, 18)
    .filter_by_bounds(-34.56, -34.58, -58.44, -58.46)
)

# Now analyze filtered data
stays = result.get_stay_points()
print(f"Found {len(stays)} stay points during work hours in this area")
```

---

## Error Handling

The script provides clear error messages for common issues:

```python
try:
    loader = LocationDataLoader('nonexistent.csv')
except FileNotFoundError as e:
    print(f"Error: {e}")

try:
    loader.filter_by_date_range('invalid', '2026-03-10')
except Exception as e:
    print(f"Date parsing error: {e}")

try:
    speed = loader.get_speed_stats()
except ValueError as e:
    print(f"Analysis error: {e}")  # Missing required columns
```

---

## Performance Tips

For large datasets (>10,000 records):

1. **Filter before analysis:**
   ```python
   # Good: Filter first, then analyze
   loader.filter_by_date_range('2026-03-01', '2026-03-10')
   stays = loader.get_stay_points()
   
   # Avoid: Analyzing full dataset repeatedly
   stays_all = loader.get_stay_points()
   ```

2. **Use appropriate parameters:**
   ```python
   # Cluster analysis is O(n²), use larger distance to reduce computation
   clusters = loader.get_clusters(max_distance_km=1.0)  # Faster
   ```

3. **Cache results:**
   ```python
   summary = loader.get_summary()
   # Reuse summary instead of calling multiple times
   ```

---

## Integration with Visualization Libraries

### Using with Matplotlib

```python
import matplotlib.pyplot as plt
from data_loader import LocationDataLoader

loader = LocationDataLoader('output.csv')
df = loader.export_for_visualization()

plt.figure(figsize=(12, 10))
plt.scatter(df['Longitude'], df['Latitude'], alpha=0.3, s=5, c='blue')

# Add clusters
clusters = loader.get_clusters()
for cluster in clusters:
    plt.plot(cluster['center_lon'], cluster['center_lat'], 'r*', markersize=15)

plt.title('Location History with Clusters')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.tight_layout()
plt.show()
```

### Using with Plotly

```python
import plotly.graph_objects as go
from data_loader import LocationDataLoader

loader = LocationDataLoader('output.csv')
df = loader.export_for_visualization()

fig = go.Figure()

# Add trajectory
fig.add_trace(go.Scattergeo(
    lon=df['Longitude'],
    lat=df['Latitude'],
    mode='markers',
    marker=dict(size=4, opacity=0.5)
))

fig.update_layout(
    title='Location History',
    geo=dict(scope='world')
)

fig.show()
```

### Using with Folium (Interactive Maps)

```python
import folium
from data_loader import LocationDataLoader

loader = LocationDataLoader('output.csv')
summary = loader.get_summary()
bounds = summary['spatial_bounds']

# Create map centered at data center
m = folium.Map(
    location=[bounds['center_lat'], bounds['center_lon']],
    zoom_start=15
)

# Add stay points
stays = loader.get_stay_points()
for stay in stays[:10]:
    folium.CircleMarker(
        location=[stay['latitude'], stay['longitude']],
        radius=5,
        popup=f"Duration: {stay['duration_minutes']:.0f} min"
    ).add_to(m)

m.save('location_map.html')
```

---

## API Reference Summary

| Method | Parameters | Returns | Purpose |
|--------|-----------|---------|---------|
| `get_dataframe()` | - | DataFrame | Access raw data |
| `get_summary()` | - | Dict | Statistics overview |
| `print_report()` | - | None | Console summary |
| `filter_by_date_range()` | start_date, end_date | self | Date filtering |
| `filter_by_time_range()` | start_hour, end_hour | self | Hour filtering |
| `filter_by_bounds()` | north, south, east, west | self | Geographic filtering |
| `reset_filters()` | - | self | Clear filters |
| `get_distance_traveled()` | - | float | Total km traveled |
| `get_speed_stats()` | - | Dict | Speed statistics |
| `get_temporal_density()` | time_unit | Series | Time distribution |
| `get_clusters()` | max_distance_km, min_points | List[Dict] | Location clusters |
| `get_stay_points()` | max_distance_km, min_duration | List[Dict] | Stationary locations |
| `export_for_visualization()` | output_file (opt) | DataFrame | Viz-ready data |

---

## Troubleshooting

**"ModuleNotFoundError: No module named 'pandas'"**
```bash
pip install pandas
```

**"Data does not have a Time column"**
- Ensure CSV has a 'Time' column for temporal analysis
- Acceptable formats: ISO 8601, "YYYY-MM-DD HH:MM:SS", etc.

**Empty results from analysis**
- Data may be filtered too aggressively
- Call `reset_filters()` and try again
- Check data summary with `get_summary()`

**Slow performance on large files**
- Filter data first to reduce dataset size
- Adjust clustering parameters (larger distance = faster)
- Consider processing data in date chunks

---

## Examples

See example usage patterns in the main script section when running:
```bash
python data_loader.py output.csv
```

For more complex workflows, combine methods as shown in the "Common Workflows" section above.
