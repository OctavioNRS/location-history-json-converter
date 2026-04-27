#!/usr/bin/env python3
"""
Location History Analysis Script
Generates 6 CSV files from Rutas.json semantic location data:
1. Location visits with clustering (arrival-departure cycles)
2. Daily distance between cluster visits
3. Time inside/outside home by weekday (averaged to 0-24h range)
4. Weekly routine heatmap (transition frequency by hour and weekday)
5. 24-hour activity pattern (hourly breakdown of in/out home activity)
6. Hourly activity by weekday (hourly breakdown for each day of week)

Fixed issues:
- 150m clustering radius for location tolerance
- GPS noise filtering (< 20m movements, > 300 km/h speeds)
- Proper hour averaging: normalized to 24 hours per day
- Visit counting: only arrival-departure cycles
- Routine as heatmap: frequency of transitions
"""

import sys
import json
import math
import re
from datetime import datetime, timedelta
from dateutil.parser import isoparse
from dateutil.tz import UTC
from pathlib import Path
from collections import defaultdict
import pandas as pd

# ==================== Configuration ====================
HOME_LATITUDE = -34.56604154950464
HOME_LONGITUDE = -58.460364831614086


# ==================== Helper Functions from converter ====================

def _deg2rad(deg):
    """Convert degrees to radians"""
    return deg * (math.pi / 180)


def _distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates in km using Haversine formula
    Coordinates should be in E7 format (multiplied by 10000000)
    """
    R = 6371  # Radius of the earth in km
    
    # Convert E7 to regular coordinates
    lat1_deg = lat1 / 10000000
    lon1_deg = lon1 / 10000000
    lat2_deg = lat2 / 10000000
    lon2_deg = lon2 / 10000000
    
    dlat = _deg2rad(lat2_deg - lat1_deg)
    dlon = _deg2rad(lon2_deg - lon1_deg)
    
    a = math.sin(dlat/2) * math.sin(dlat/2) + \
        math.cos(_deg2rad(lat1_deg)) * math.cos(_deg2rad(lat2_deg)) * \
        math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c  # Distance in km
    return d


def _distance_decimal(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in km (decimal format)"""
    R = 6371
    dlat = _deg2rad(lat2 - lat1)
    dlon = _deg2rad(lon2 - lon1)
    
    a = math.sin(dlat/2) * math.sin(dlat/2) + \
        math.cos(_deg2rad(lat1)) * math.cos(_deg2rad(lat2)) * \
        math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


# ==================== Location Data Loader ====================

class SemanticLocationLoader:
    """Load and parse semantic location data from Rutas.json"""
    
    def __init__(self, json_file, start_date=None):
        """
        Initialize loader
        start_date: datetime object to filter from (inclusive)
        """
        self.json_file = Path(json_file)
        self.start_date = start_date
        self.locations = self._load_locations()
        print(f"✓ Loaded {len(self.locations)} locations from {self.json_file}")
        if self.start_date:
            print(f"  Starting from: {self.start_date.strftime('%Y-%m-%d')}")
    
    def _load_locations(self) -> list:
        """Extract locations from semantic segments"""
        locations = []
        
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
        except Exception as e:
            print(f"Error loading JSON: {e}")
            return locations
        
        if 'semanticSegments' not in json_data:
            print("No semanticSegments found in JSON")
            return locations
        
        for segment in json_data['semanticSegments']:
            if 'timelinePath' not in segment:
                continue
            
            for path_item in segment['timelinePath']:
                try:
                    # Extract time
                    time_str = path_item.get('time')
                    if not time_str:
                        continue
                    
                    time = isoparse(time_str)
                    
                    # Filter by start date
                    if self.start_date and time < self.start_date:
                        continue
                    
                    # Extract coordinates
                    point_str = path_item.get('point', '')
                    if not point_str:
                        continue
                    
                    # Parse point string (format: "34.5662, -58.4604")
                    point_str = point_str.replace('Â°', '').replace('°', '')
                    parts = point_str.split(',')
                    
                    if len(parts) != 2:
                        continue
                    
                    lat = float(parts[0].strip())
                    lon = float(parts[1].strip())
                    
                    # Store as E7 format for compatibility with converter functions
                    locations.append({
                        'Time': time,
                        'time_decimal': time,
                        'latitudeE7': int(lat * 10000000),
                        'longitudeE7': int(lon * 10000000),
                        'latitude': lat,
                        'longitude': lon,
                        'timestampMs': str(int(time.timestamp() * 1000))
                    })
                
                except (ValueError, IndexError, AttributeError):
                    continue
        
        # Sort by time
        locations.sort(key=lambda x: x['Time'])
        return locations
    
    def get_dataframe(self):
        """Get locations as pandas DataFrame"""
        return pd.DataFrame([{
            'Time': loc['Time'],
            'Latitude': loc['latitude'],
            'Longitude': loc['longitude']
        } for loc in self.locations])


# ==================== Analysis Functions ====================

def cluster_locations(locations, radius_km=0.15):
    """
    Cluster nearby locations using 150m radius.
    Returns dict of clusters with their center points and visit counts.
    """
    clusters = {}
    used_indices = set()
    
    for i in range(len(locations)):
        if i in used_indices:
            continue
        
        cluster_points = [i]
        used_indices.add(i)
        
        # Find all nearby points
        for j in range(i + 1, len(locations)):
            if j in used_indices:
                continue
            
            dist = _distance(
                locations[i]['latitudeE7'],
                locations[i]['longitudeE7'],
                locations[j]['latitudeE7'],
                locations[j]['longitudeE7']
            )
            
            if dist <= radius_km:
                cluster_points.append(j)
                used_indices.add(j)
        
        # Create cluster
        if len(cluster_points) > 0:
            cluster_locs = [locations[idx] for idx in cluster_points]
            center_lat = sum(loc['latitude'] for loc in cluster_locs) / len(cluster_locs)
            center_lon = sum(loc['longitude'] for loc in cluster_locs) / len(cluster_locs)
            
            cluster_key = (round(center_lat, 4), round(center_lon, 4))
            clusters[cluster_key] = {
                'center_lat': center_lat,
                'center_lon': center_lon,
                'latitude_e7': int(center_lat * 10000000),
                'longitude_e7': int(center_lon * 10000000),
                'points': cluster_points,
                'times': [loc['Time'] for loc in cluster_locs],
                'count': len(cluster_points),
                'first_time': cluster_locs[0]['Time']
            }
    
    return clusters


def generate_location_visits_csv(locations, output_file='location_visits.csv'):
    """
    Generate CSV with location visits (arrival-departure cycles).
    Only counts a visit when arriving at a location and later leaving it.
    Columns: Time, Latitude, Longitude, Visit_Count
    """
    print("\n[1/4] Generating location visits CSV...")
    
    # First, cluster locations
    clusters = cluster_locations(locations, radius_km=0.15)
    
    if not clusters:
        print("⚠ No clusters found")
        return None
    
    # Build visit history by cluster
    visits_per_cluster = defaultdict(list)
    
    # Create dataframe for easier processing
    df = pd.DataFrame([{
        'Time': loc['Time'],
        'Latitude': loc['latitude'],
        'Longitude': loc['longitude'],
        'latitudeE7': loc['latitudeE7'],
        'longitudeE7': loc['longitudeE7']
    } for loc in locations]).sort_values('Time')
    
    # For each point, find which cluster it belongs to
    cluster_sequence = []
    for _, row in df.iterrows():
        # Find closest cluster
        best_cluster = None
        best_dist = float('inf')
        
        for (lat, lon), cluster_info in clusters.items():
            dist = _distance(
                int(row['Latitude'] * 10000000),
                int(row['Longitude'] * 10000000),
                cluster_info['latitude_e7'],
                cluster_info['longitude_e7']
            )
            
            if dist < best_dist:
                best_dist = dist
                best_cluster = (lat, lon)
        
        if best_cluster and best_dist <= 0.15:  # Within cluster radius
            cluster_sequence.append(best_cluster)
        else:
            cluster_sequence.append(None)
    
    # Count visits as arrival-departure cycles
    visits_by_cluster = defaultdict(int)
    first_time_by_cluster = {}
    
    i = 0
    while i < len(cluster_sequence):
        current_cluster = cluster_sequence[i]
        
        if current_cluster is None:
            i += 1
            continue
        
        # Record first arrival time for this visit
        if current_cluster not in first_time_by_cluster:
            first_time_by_cluster[current_cluster] = df.iloc[i]['Time']
        
        # Find when we leave this cluster (next different cluster or end of sequence)
        while i < len(cluster_sequence) and cluster_sequence[i] == current_cluster:
            i += 1
        
        # We've left the cluster, count it as a visit
        visits_by_cluster[current_cluster] += 1
    
    rows = []
    for (lat, lon), visit_count in visits_by_cluster.items():
        rows.append({
            'Latitude': lat,
            'Longitude': lon,
            'Visit_Count': visit_count
        })
    
    df_result = pd.DataFrame(rows)
    df_result = df_result.sort_values('Visit_Count', ascending=False)
    df_result.to_csv(output_file, index=False)
    
    print(f"✓ Saved: {output_file} ({len(df_result)} unique locations)")
    if len(df_result) > 0:
        print(f"  Most visited: ({df_result.iloc[0]['Latitude']:.6f}, {df_result.iloc[0]['Longitude']:.6f}) - {int(df_result.iloc[0]['Visit_Count'])} visits")
    
    return df_result


def generate_daily_distance_csv(locations, output_file='daily_distance.csv'):
    """
    Generate CSV with distance traveled each day.
    Calculates distances between cluster visit centers (not all points).
    Filters GPS noise: movements < 20m and speeds > 300 km/h
    Columns: Day, Distance_Meters
    """
    print("\n[2/4] Generating daily distance CSV...")
    
    # First cluster the locations
    clusters = cluster_locations(locations, radius_km=0.15)
    
    if not clusters:
        print("⚠ No clusters found")
        return None
    
    # Create dataframe for easier processing
    df = pd.DataFrame([{
        'Time': loc['Time'],
        'Latitude': loc['latitude'],
        'Longitude': loc['longitude'],
        'latitudeE7': loc['latitudeE7'],
        'longitudeE7': loc['longitudeE7']
    } for loc in locations]).sort_values('Time')
    
    # Build cluster visit sequence with times
    visit_sequence = []  # List of (time, cluster_lat, cluster_lon)
    
    i = 0
    while i < len(df):
        current_row = df.iloc[i]
        current_time = current_row['Time']
        
        # Find which cluster this belongs to
        best_cluster = None
        best_dist = float('inf')
        
        for (lat, lon), cluster_info in clusters.items():
            dist = _distance(
                int(current_row['Latitude'] * 10000000),
                int(current_row['Longitude'] * 10000000),
                cluster_info['latitude_e7'],
                cluster_info['longitude_e7']
            )
            
            if dist < best_dist:
                best_dist = dist
                best_cluster = (lat, lon)
        
        if best_cluster and best_dist <= 0.15:
            # Skip to end of this cluster visit
            j = i
            while j < len(df):
                next_row = df.iloc[j]
                next_dist = _distance(
                    int(next_row['Latitude'] * 10000000),
                    int(next_row['Longitude'] * 10000000),
                    clusters[best_cluster]['latitude_e7'],
                    clusters[best_cluster]['longitude_e7']
                )
                
                if next_dist > 0.15:  # Left cluster
                    break
                j += 1
            
            # Record visit at cluster
            cluster_lat, cluster_lon = best_cluster
            visit_time = df.iloc[i]['Time']
            visit_sequence.append((visit_time, cluster_lat, cluster_lon))
            
            i = j
        else:
            i += 1
    
    # Calculate distances between visits
    daily_distances = defaultdict(float)
    
    for j in range(len(visit_sequence) - 1):
        current_time, current_lat, current_lon = visit_sequence[j]
        next_time, next_lat, next_lon = visit_sequence[j + 1]
        
        # Use decimal distance function
        distance_km = _distance_decimal(current_lat, current_lon, next_lat, next_lon)
        
        time_diff = (next_time - current_time).total_seconds() / 3600  # hours
        
        # Filter 1: Ignore movements < 20m (GPS noise)
        if distance_km * 1000 < 20:
            continue
        
        # Filter 2: Ignore impossible speeds (> 300 km/h)
        if time_diff > 0:
            speed_kmh = distance_km / time_diff
            if speed_kmh > 300:
                continue
        
        # Add to daily total
        date = current_time.date()
        daily_distances[date] += distance_km
    
    rows = []
    for date in sorted(daily_distances.keys()):
        distance_meters = daily_distances[date] * 1000
        rows.append({
            'Day': date,
            'Distance_Meters': round(distance_meters, 2)
        })
    
    df_result = pd.DataFrame(rows)
    df_result.to_csv(output_file, index=False)
    
    print(f"✓ Saved: {output_file} ({len(df_result)} days)")
    if len(df_result) > 0:
        print(f"  Average daily distance: {df_result['Distance_Meters'].mean():.2f} meters")
    
    return df_result


def generate_time_inside_outside_csv(locations, output_file='time_inside_outside_by_weekday.csv'):
    """
    Generate CSV with AVERAGE time inside/outside home by day of week (0-24h range).
    Home location is defined by HOME_LATITUDE and HOME_LONGITUDE constants.
    Normalizes to 24 hours per day by scaling measured time to full day coverage.
    Columns: Day_Of_Week, Hours_In_Home, Hours_Outside
    """
    print("\n[3/4] Generating time inside/outside by weekday CSV...")
    
    HOME_RADIUS_KM = 0.15
    
    print(f"  Home location: ({HOME_LATITUDE:.6f}, {HOME_LONGITUDE:.6f})")
    
    # Create dataframe for easier processing
    df = pd.DataFrame([{
        'Time': loc['Time'],
        'Latitude': loc['latitude'],
        'Longitude': loc['longitude'],
        'Date': loc['Time'].date(),
        'DayOfWeek': loc['Time'].strftime('%A')
    } for loc in locations])
    
    df = df.sort_values('Time')
    
    # Classify as at_home or away
    def is_at_home(lat, lon):
        dist = _distance_decimal(lat, lon, HOME_LATITUDE, HOME_LONGITUDE)
        return dist <= HOME_RADIUS_KM
    
    df['at_home'] = df.apply(lambda row: is_at_home(row['Latitude'], row['Longitude']), axis=1)
    
    # Calculate time inside/outside for each actual day, normalized to 24 hours
    daily_stats = []
    
    for date in df['Date'].unique():
        day_data = df[df['Date'] == date].sort_values('Time')
        
        if len(day_data) < 2:
            continue
        
        day_at_home = 0
        day_away = 0
        
        for i in range(len(day_data) - 1):
            time_diff = (day_data.iloc[i+1]['Time'] - day_data.iloc[i]['Time']).total_seconds() / 3600
            
            if day_data.iloc[i]['at_home']:
                day_at_home += time_diff
            else:
                day_away += time_diff
        
        # Calculate total tracked time and normalize to 24 hours
        total_tracked = day_at_home + day_away
        
        if total_tracked > 0:
            # Scale up to 24 hours: multiply by 24 / total_tracked
            scale_factor = 24.0 / total_tracked
            day_at_home *= scale_factor
            day_away *= scale_factor
        
        weekday = day_data.iloc[0]['DayOfWeek']
        daily_stats.append({
            'Date': date,
            'DayOfWeek': weekday,
            'Hours_In_Home': day_at_home,
            'Hours_Outside': day_away,
            'Total': day_at_home + day_away
        })
    
    # Average by weekday
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    results = []
    
    for weekday in weekday_order:
        weekday_stats = [s for s in daily_stats if s['DayOfWeek'] == weekday]
        
        if len(weekday_stats) == 0:
            continue
        
        avg_at_home = sum(s['Hours_In_Home'] for s in weekday_stats) / len(weekday_stats)
        avg_away = sum(s['Hours_Outside'] for s in weekday_stats) / len(weekday_stats)
        
        results.append({
            'Day_Of_Week': weekday,
            'Hours_In_Home': round(avg_at_home, 2),
            'Hours_Outside': round(avg_away, 2)
        })
    
    df_result = pd.DataFrame(results)
    df_result.to_csv(output_file, index=False)
    
    print(f"✓ Saved: {output_file}")
    if len(df_result) > 0:
        print(f"  Average home time: {df_result['Hours_In_Home'].mean():.2f} hours/day")
        print(f"  Average outside time: {df_result['Hours_Outside'].mean():.2f} hours/day")
        avg_total = (df_result['Hours_In_Home'] + df_result['Hours_Outside']).mean()
        print(f"  Average total (in+out): {avg_total:.2f} hours/day")
    
    return df_result


def generate_routine_csv(locations, output_file='weekly_routine.csv'):
    """
    Generate CSV as a HEATMAP showing frequency of transitions by hour and weekday.
    Instead of listing individual transitions, shows how many times person left/returned
    home at each hour on each day of the week.
    Columns: Day_Of_Week, Hour, Leave_Count, Return_Count
    This creates a timeline heatmap pattern for visualization.
    """
    print("\n[4/4] Generating weekly routine heatmap CSV...")
    
    HOME_RADIUS_KM = 0.15
    
    # Create dataframe
    df = pd.DataFrame([{
        'Time': loc['Time'],
        'Latitude': loc['latitude'],
        'Longitude': loc['longitude'],
        'DayOfWeek': loc['Time'].strftime('%A'),
        'Hour': loc['Time'].hour
    } for loc in locations])
    
    df = df.sort_values('Time')
    
    # Classify as at_home
    def is_at_home(lat, lon):
        dist = _distance_decimal(lat, lon, HOME_LATITUDE, HOME_LONGITUDE)
        return dist <= HOME_RADIUS_KM
    
    df['at_home'] = df.apply(lambda row: is_at_home(row['Latitude'], row['Longitude']), axis=1)
    
    # Detect state transitions
    df['state_change'] = df['at_home'].astype(int).diff().fillna(0)
    
    # Extract leaves (-1) and returns (+1)
    leaves = df[df['state_change'] == -1][['DayOfWeek', 'Hour']].copy()
    returns = df[df['state_change'] == 1][['DayOfWeek', 'Hour']].copy()
    
    # Count transitions by hour and weekday
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    results = []
    
    for weekday in weekday_order:
        for hour in range(24):
            leave_count = len(leaves[(leaves['DayOfWeek'] == weekday) & (leaves['Hour'] == hour)])
            return_count = len(returns[(returns['DayOfWeek'] == weekday) & (returns['Hour'] == hour)])
            
            # Only include hours with activity
            if leave_count > 0 or return_count > 0:
                results.append({
                    'Day_Of_Week': weekday,
                    'Hour': f"{hour:02d}:00",
                    'Leave_Count': leave_count,
                    'Return_Count': return_count
                })
    
    df_result = pd.DataFrame(results)
    if len(df_result) > 0:
        df_result.to_csv(output_file, index=False)
        print(f"✓ Saved: {output_file} ({len(df_result)} time slots with activity)")
        total_transitions = df_result['Leave_Count'].sum() + df_result['Return_Count'].sum()
        print(f"  Total transitions: {total_transitions} (leaves: {int(df_result['Leave_Count'].sum())}, returns: {int(df_result['Return_Count'].sum())})")
    else:
        print("⚠ No transitions detected")
    
    return df_result


def generate_hourly_activity_csv(locations, output_file='hourly_activity_pattern.csv'):
    """
    Generate CSV with 24-hour activity pattern showing average time inside/outside home by hour of day.
    This creates a typical daily profile showing when person is usually home vs away.
    Columns: Hour, Hours_In_Home, Hours_Outside
    """
    print("\n[5/5] Generating 24-hour activity pattern CSV...")
    
    HOME_RADIUS_KM = 0.15
    
    # Create dataframe for easier processing
    df = pd.DataFrame([{
        'Time': loc['Time'],
        'Latitude': loc['latitude'],
        'Longitude': loc['longitude'],
        'Date': loc['Time'].date(),
        'Hour': loc['Time'].hour
    } for loc in locations])
    
    df = df.sort_values('Time')
    
    # Classify as at_home or away
    def is_at_home(lat, lon):
        dist = _distance_decimal(lat, lon, HOME_LATITUDE, HOME_LONGITUDE)
        return dist <= HOME_RADIUS_KM
    
    df['at_home'] = df.apply(lambda row: is_at_home(row['Latitude'], row['Longitude']), axis=1)
    
    # Calculate time inside/outside for each hour of day
    hourly_stats = []
    
    for date in df['Date'].unique():
        day_data = df[df['Date'] == date].sort_values('Time')
        
        if len(day_data) < 2:
            continue
        
        # Calculate daily total for normalization
        day_at_home = 0
        day_away = 0
        
        for i in range(len(day_data) - 1):
            time_diff = (day_data.iloc[i+1]['Time'] - day_data.iloc[i]['Time']).total_seconds() / 3600
            
            if day_data.iloc[i]['at_home']:
                day_at_home += time_diff
            else:
                day_away += time_diff
        
        # Scale to 24 hours for daily total
        total_tracked = day_at_home + day_away
        if total_tracked > 0:
            scale_factor = 24.0 / total_tracked
            
            # Now process by hour
            for hour in range(24):
                hour_data = day_data[day_data['Hour'] == hour].sort_values('Time')
                
                if len(hour_data) < 1:
                    continue
                
                hour_at_home = 0
                hour_away = 0
                
                for i in range(len(hour_data) - 1):
                    time_diff = (hour_data.iloc[i+1]['Time'] - hour_data.iloc[i]['Time']).total_seconds() / 3600
                    
                    if hour_data.iloc[i]['at_home']:
                        hour_at_home += time_diff
                    else:
                        hour_away += time_diff
                
                # Scale THIS HOUR to sum to 1 (not the daily scale factor)
                hour_total = hour_at_home + hour_away
                if hour_total > 0:
                    hour_scale_factor = 1.0 / hour_total
                    hour_at_home *= hour_scale_factor
                    hour_away *= hour_scale_factor
                
                hourly_stats.append({
                    'Date': date,
                    'Hour': hour,
                    'Hours_In_Home': hour_at_home,
                    'Hours_Outside': hour_away
                })
    
    # Average by hour of day
    results = []
    
    for hour in range(24):
        hour_records = [s for s in hourly_stats if s['Hour'] == hour]
        
        if len(hour_records) == 0:
            continue
        
        avg_at_home = sum(s['Hours_In_Home'] for s in hour_records) / len(hour_records)
        avg_away = sum(s['Hours_Outside'] for s in hour_records) / len(hour_records)
        
        results.append({
            'Hour': f"{hour:02d}:00",
              'Hours_In_Home': round(avg_at_home, 2),
              'Hours_Outside': round(1.0 - round(avg_at_home, 2), 2)
        })
    
    df_result = pd.DataFrame(results)
    df_result.to_csv(output_file, index=False)
    
    print(f"✓ Saved: {output_file} (24-hour pattern)")
    if len(df_result) > 0:
        print(f"  Average home time per hour: {df_result['Hours_In_Home'].mean():.2f} hours")
        print(f"  Average outside time per hour: {df_result['Hours_Outside'].mean():.2f} hours")
    
    return df_result


def generate_hourly_activity_by_weekday_csv(locations, output_file='hourly_activity_by_weekday.csv'):
    """
    Generate CSV with hourly activity pattern broken down by weekday.
    Shows hour-by-hour breakdown for each day of the week.
    Columns: Day_Of_Week, Hour, Hours_In_Home, Hours_Outside
    Each hour sums to 1.0 (represents fraction of that hour).
    """
    print("\n[6/6] Generating hourly activity by weekday CSV...")
    
    HOME_RADIUS_KM = 0.15
    
    # Create dataframe for easier processing
    df = pd.DataFrame([{
        'Time': loc['Time'],
        'Latitude': loc['latitude'],
        'Longitude': loc['longitude'],
        'Date': loc['Time'].date(),
        'DayOfWeek': loc['Time'].strftime('%A'),
        'Hour': loc['Time'].hour
    } for loc in locations])
    
    df = df.sort_values('Time')
    
    # Classify as at_home or away
    def is_at_home(lat, lon):
        dist = _distance_decimal(lat, lon, HOME_LATITUDE, HOME_LONGITUDE)
        return dist <= HOME_RADIUS_KM
    
    df['at_home'] = df.apply(lambda row: is_at_home(row['Latitude'], row['Longitude']), axis=1)
    
    # Calculate time inside/outside for each hour of each weekday
    hourly_weekday_stats = []
    
    for date in df['Date'].unique():
        day_data = df[df['Date'] == date].sort_values('Time')
        
        if len(day_data) < 2:
            continue
        
        weekday = day_data.iloc[0]['DayOfWeek']
        
        # Calculate daily scale factor for normalization
        day_at_home = 0
        day_away = 0
        
        for i in range(len(day_data) - 1):
            time_diff = (day_data.iloc[i+1]['Time'] - day_data.iloc[i]['Time']).total_seconds() / 3600
            
            if day_data.iloc[i]['at_home']:
                day_at_home += time_diff
            else:
                day_away += time_diff
        
        total_tracked = day_at_home + day_away
        if total_tracked == 0:
            continue
        
        # Process by hour
        for hour in range(24):
            hour_data = day_data[day_data['Hour'] == hour].sort_values('Time')
            
            if len(hour_data) < 1:
                continue
            
            hour_at_home = 0
            hour_away = 0
            
            for i in range(len(hour_data) - 1):
                time_diff = (hour_data.iloc[i+1]['Time'] - hour_data.iloc[i]['Time']).total_seconds() / 3600
                
                if hour_data.iloc[i]['at_home']:
                    hour_at_home += time_diff
                else:
                    hour_away += time_diff
            
            # Scale THIS HOUR to sum to 1.0
            hour_total = hour_at_home + hour_away
            if hour_total > 0:
                hour_scale_factor = 1.0 / hour_total
                hour_at_home *= hour_scale_factor
                hour_away *= hour_scale_factor
            
            hourly_weekday_stats.append({
                'Date': date,
                'DayOfWeek': weekday,
                'Hour': hour,
                'Hours_In_Home': hour_at_home,
                'Hours_Outside': hour_away
            })
    
    # Average by weekday and hour - include ALL 24 hours for each day
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    results = []
    
    for weekday in weekday_order:
        for hour in range(24):
            records = [s for s in hourly_weekday_stats 
                      if s['DayOfWeek'] == weekday and s['Hour'] == hour]
            
            if len(records) == 0:
                # No data for this hour on this weekday, use neutral default
                avg_at_home = 0.5
                avg_away = 0.5
            else:
                avg_at_home = sum(s['Hours_In_Home'] for s in records) / len(records)
                avg_away = sum(s['Hours_Outside'] for s in records) / len(records)
            
            results.append({
                'Day_Of_Week': weekday,
                'Hour': f"{hour:02d}:00",
                'Hours_In_Home': round(avg_at_home, 2),
                'Hours_Outside': round(1.0 - round(avg_at_home, 2), 2)
            })
    
    df_result = pd.DataFrame(results)
    df_result.to_csv(output_file, index=False)
    
    print(f"✓ Saved: {output_file} (7 weekdays × 24 hours = 168 rows)")
    if len(df_result) > 0:
        print(f"  Total rows: {len(df_result)}")
    
    return df_result


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python analyze_semantic_locations.py <json_file> [start_date YYYY-MM-DD]")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    # Parse start date if provided
    start_date = None
    if len(sys.argv) >= 3:
        try:
            start_date = datetime.strptime(sys.argv[2], '%Y-%m-%d').replace(tzinfo=UTC)
        except ValueError:
            print(f"Invalid date format: {sys.argv[2]}")
            sys.exit(1)
    
    print(f"Loading data from {json_file}...")
    loader = SemanticLocationLoader(json_file, start_date=start_date)
    
    if len(loader.locations) == 0:
        print("✗ No locations loaded")
        sys.exit(1)
    
    # Generate reports
    print("\n" + "="*60)
    print("GENERATING ANALYSIS REPORTS")
    print("="*60)
    print("Fixes applied:")
    print("  ✓ 150m location clustering")
    print("  ✓ GPS noise filtering (< 20m, > 300 km/h)")
    print("  ✓ Hours averaged by weekday")
    print("  ✓ Using Rutas.json semantic segments")
    print("="*60)
    
    generate_location_visits_csv(loader.locations)
    generate_daily_distance_csv(loader.locations)
    generate_time_inside_outside_csv(loader.locations)
    generate_routine_csv(loader.locations)
    generate_hourly_activity_csv(loader.locations)
    generate_hourly_activity_by_weekday_csv(loader.locations)
    
    print("\n" + "="*60)
    print("✓ All 6 reports generated successfully!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
