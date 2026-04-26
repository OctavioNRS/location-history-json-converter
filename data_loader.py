#!/usr/bin/env python3
"""
Data Loader for Location History CSV Files
Provides utilities to load, parse, and manipulate location data for visualization.
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from shapely.geometry import Point, box
import math


class LocationDataLoader:
    """Load and manipulate location history data from CSV files."""
    
    def __init__(self, csv_file: str):
        """
        Initialize the data loader and read CSV file.
        
        Args:
            csv_file: Path to CSV file with headers in first row
        """
        self.csv_file = Path(csv_file)
        self.data = None
        self.original_data = None
        self._load_data()
    
    def _load_data(self):
        """Load CSV file and prepare data structures."""
        if not self.csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_file}")
        
        # Read CSV with first row as headers
        self.data = pd.read_csv(self.csv_file)
        self.original_data = self.data.copy()
        
        # Parse datetime if 'Time' column exists
        if 'Time' in self.data.columns:
            self.data['Time'] = pd.to_datetime(self.data['Time'])
            self.original_data['Time'] = pd.to_datetime(self.original_data['Time'])
        
        print(f"Loaded {len(self.data)} records from {self.csv_file}")
        print(f"Columns: {list(self.data.columns)}")
    
    def get_dataframe(self) -> pd.DataFrame:
        """Return current data as DataFrame."""
        return self.data.copy()
    
    def get_summary(self) -> Dict:
        """
        Get summary statistics of the data.
        
        Returns:
            Dictionary with count, date range, and spatial bounds
        """
        summary = {
            'total_records': len(self.data),
            'columns': list(self.data.columns)
        }
        
        if 'Time' in self.data.columns:
            summary['time_range'] = {
                'start': self.data['Time'].min(),
                'end': self.data['Time'].max(),
                'duration_days': (self.data['Time'].max() - self.data['Time'].min()).days
            }
        
        # Spatial bounds if latitude/longitude present
        if 'Latitude' in self.data.columns and 'Longitude' in self.data.columns:
            summary['spatial_bounds'] = {
                'north': self.data['Latitude'].max(),
                'south': self.data['Latitude'].min(),
                'east': self.data['Longitude'].max(),
                'west': self.data['Longitude'].min(),
                'center_lat': self.data['Latitude'].mean(),
                'center_lon': self.data['Longitude'].mean()
            }
        
        return summary
    
    def filter_by_date_range(self, start_date: str, end_date: str) -> 'LocationDataLoader':
        """
        Filter data by date range.
        
        Args:
            start_date: Start date as string (YYYY-MM-DD)
            end_date: End date as string (YYYY-MM-DD)
        
        Returns:
            self for method chaining
        """
        if 'Time' not in self.data.columns:
            raise ValueError("Data does not have a Time column")
        
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date) + timedelta(days=1)
        
        self.data = self.data[(self.data['Time'] >= start) & (self.data['Time'] < end)]
        print(f"Filtered to {len(self.data)} records between {start_date} and {end_date}")
        return self
    
    def filter_by_time_range(self, start_hour: int, end_hour: int) -> 'LocationDataLoader':
        """
        Filter data by hour of day.
        
        Args:
            start_hour: Hour to start (0-23)
            end_hour: Hour to end (0-23)
        
        Returns:
            self for method chaining
        """
        if 'Time' not in self.data.columns:
            raise ValueError("Data does not have a Time column")
        
        self.data['_hour'] = self.data['Time'].dt.hour
        self.data = self.data[(self.data['_hour'] >= start_hour) & (self.data['_hour'] <= end_hour)]
        self.data.drop('_hour', axis=1, inplace=True)
        print(f"Filtered to {len(self.data)} records in hours {start_hour}-{end_hour}")
        return self
    
    def filter_by_bounds(self, north: float, south: float, east: float, west: float) -> 'LocationDataLoader':
        """
        Filter data by geographic bounding box.
        
        Args:
            north: Northern latitude bound
            south: Southern latitude bound
            east: Eastern longitude bound
            west: Western longitude bound
        
        Returns:
            self for method chaining
        """
        if 'Latitude' not in self.data.columns or 'Longitude' not in self.data.columns:
            raise ValueError("Data does not have Latitude/Longitude columns")
        
        self.data = self.data[
            (self.data['Latitude'] <= north) & (self.data['Latitude'] >= south) &
            (self.data['Longitude'] <= east) & (self.data['Longitude'] >= west)
        ]
        print(f"Filtered to {len(self.data)} records within bounds")
        return self
    
    def reset_filters(self) -> 'LocationDataLoader':
        """Reset data to original state."""
        self.data = self.original_data.copy()
        print("Filters reset")
        return self
    
    def get_temporal_density(self, time_unit: str = 'hour') -> pd.Series:
        """
        Get data point density over time.
        
        Args:
            time_unit: 'hour', 'day', 'day_of_week', or 'hour_of_day'
        
        Returns:
            Series with temporal density
        """
        if 'Time' not in self.data.columns:
            raise ValueError("Data does not have a Time column")
        
        if time_unit == 'hour':
            return self.data['Time'].dt.floor('h').value_counts().sort_index()
        elif time_unit == 'day':
            return self.data['Time'].dt.date.value_counts().sort_index()
        elif time_unit == 'day_of_week':
            return self.data['Time'].dt.day_name().value_counts()
        elif time_unit == 'hour_of_day':
            return self.data['Time'].dt.hour.value_counts().sort_index()
        else:
            raise ValueError(f"Unknown time_unit: {time_unit}")
    
    def get_distance_traveled(self) -> float:
        """
        Calculate total distance traveled using haversine formula.
        
        Returns:
            Total distance in kilometers
        """
        if 'Latitude' not in self.data.columns or 'Longitude' not in self.data.columns:
            raise ValueError("Data does not have Latitude/Longitude columns")
        
        if len(self.data) < 2:
            return 0.0
        
        # Sort by time if available
        if 'Time' in self.data.columns:
            data = self.data.sort_values('Time')
        else:
            data = self.data
        
        lats = data['Latitude'].values
        lons = data['Longitude'].values
        
        total_distance = 0.0
        for i in range(len(lats) - 1):
            dist = self._haversine_distance(
                lats[i], lons[i], lats[i+1], lons[i+1]
            )
            total_distance += dist
        
        return total_distance
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates using haversine formula.
        
        Args:
            lat1, lon1: First coordinate
            lat2, lon2: Second coordinate
        
        Returns:
            Distance in kilometers
        """
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def get_clusters(self, max_distance_km: float = 0.5, min_points: int = 3) -> List[Dict]:
        """
        Identify location clusters using distance-based clustering.
        
        Args:
            max_distance_km: Maximum distance to consider points in same cluster
            min_points: Minimum points to form a cluster
        
        Returns:
            List of cluster dictionaries with center, point count, and visit times
        """
        if 'Latitude' not in self.data.columns or 'Longitude' not in self.data.columns:
            raise ValueError("Data does not have Latitude/Longitude columns")
        
        clusters = []
        used_indices = set()
        data = self.data.reset_index(drop=True)
        
        for i in range(len(data)):
            if i in used_indices:
                continue
            
            cluster_indices = {i}
            used_indices.add(i)
            
            # Find nearby points
            for j in range(i + 1, len(data)):
                if j in used_indices:
                    continue
                
                dist = self._haversine_distance(
                    data.loc[i, 'Latitude'], data.loc[i, 'Longitude'],
                    data.loc[j, 'Latitude'], data.loc[j, 'Longitude']
                )
                
                if dist <= max_distance_km:
                    cluster_indices.add(j)
                    used_indices.add(j)
            
            # Only keep clusters with minimum points
            if len(cluster_indices) >= min_points:
                cluster_data = data.loc[list(cluster_indices)]
                cluster = {
                    'center_lat': cluster_data['Latitude'].mean(),
                    'center_lon': cluster_data['Longitude'].mean(),
                    'point_count': len(cluster_indices),
                    'visit_times': cluster_data['Time'].tolist() if 'Time' in cluster_data.columns else [],
                    'first_visit': cluster_data['Time'].min() if 'Time' in cluster_data.columns else None,
                    'last_visit': cluster_data['Time'].max() if 'Time' in cluster_data.columns else None
                }
                clusters.append(cluster)
        
        return clusters
    
    def get_speed_stats(self) -> Dict:
        """
        Calculate speed statistics (requires Time column).
        
        Returns:
            Dictionary with speed statistics in km/h
        """
        if 'Time' not in self.data.columns:
            raise ValueError("Data does not have a Time column")
        
        if 'Latitude' not in self.data.columns or 'Longitude' not in self.data.columns:
            raise ValueError("Data does not have Latitude/Longitude columns")
        
        if len(self.data) < 2:
            return {'error': 'Insufficient data'}
        
        data = self.data.sort_values('Time')
        lats = data['Latitude'].values
        lons = data['Longitude'].values
        times = data['Time'].values
        
        speeds = []
        for i in range(len(data) - 1):
            dist = self._haversine_distance(lats[i], lons[i], lats[i+1], lons[i+1])
            time_diff = (times[i+1] - times[i]) / np.timedelta64(1, 'h')  # hours
            
            if time_diff > 0:
                speed = dist / time_diff
                speeds.append(speed)
        
        speeds = np.array(speeds)
        
        return {
            'mean_speed_kmh': float(np.mean(speeds)),
            'max_speed_kmh': float(np.max(speeds)),
            'min_speed_kmh': float(np.min(speeds)),
            'std_speed_kmh': float(np.std(speeds)),
            'median_speed_kmh': float(np.median(speeds))
        }
    
    def get_stay_points(self, max_distance_km: float = 0.1, min_duration_minutes: float = 10) -> List[Dict]:
        """
        Identify stay points (stationary locations).
        
        Args:
            max_distance_km: Maximum distance to consider as staying in place
            min_duration_minutes: Minimum duration to count as stay
        
        Returns:
            List of stay points with location, duration, and timestamps
        """
        if 'Time' not in self.data.columns:
            raise ValueError("Data does not have a Time column")
        
        if 'Latitude' not in self.data.columns or 'Longitude' not in self.data.columns:
            raise ValueError("Data does not have Latitude/Longitude columns")
        
        data = self.data.sort_values('Time').reset_index(drop=True)
        stay_points = []
        i = 0
        
        while i < len(data):
            stay_start = i
            center_lat = data.loc[i, 'Latitude']
            center_lon = data.loc[i, 'Longitude']
            
            # Find consecutive points within max_distance
            j = i + 1
            while j < len(data):
                dist = self._haversine_distance(
                    center_lat, center_lon,
                    data.loc[j, 'Latitude'], data.loc[j, 'Longitude']
                )
                if dist > max_distance_km:
                    break
                j += 1
            
            # Calculate duration
            stay_end = j - 1
            duration = (data.loc[stay_end, 'Time'] - data.loc[stay_start, 'Time']).total_seconds() / 60
            
            if duration >= min_duration_minutes:
                stay_point = {
                    'latitude': data.loc[stay_start:stay_end, 'Latitude'].mean(),
                    'longitude': data.loc[stay_start:stay_end, 'Longitude'].mean(),
                    'start_time': data.loc[stay_start, 'Time'],
                    'end_time': data.loc[stay_end, 'Time'],
                    'duration_minutes': duration,
                    'point_count': stay_end - stay_start + 1
                }
                stay_points.append(stay_point)
            
            i = j if j > i + 1 else i + 1
        
        return stay_points
    
    def export_for_visualization(self, output_file: str = None) -> pd.DataFrame:
        """
        Export data in a format suitable for visualization.
        
        Args:
            output_file: Optional file to save cleaned data
        
        Returns:
            Cleaned DataFrame ready for plotting
        """
        export_data = self.data.copy()
        
        # Ensure key columns are present
        if 'Latitude' not in export_data.columns or 'Longitude' not in export_data.columns:
            raise ValueError("Data must have Latitude and Longitude columns")
        
        # Remove any null values in spatial data
        export_data = export_data.dropna(subset=['Latitude', 'Longitude'])
        
        # Add useful columns for visualization
        if 'Time' in export_data.columns:
            export_data['date'] = export_data['Time'].dt.date
            export_data['hour'] = export_data['Time'].dt.hour
            export_data['day_of_week'] = export_data['Time'].dt.day_name()
        
        if output_file:
            export_data.to_csv(output_file, index=False)
            print(f"Data exported to {output_file}")
        
        return export_data
    
    def print_report(self):
        """Print a formatted summary report of the data."""
        summary = self.get_summary()
        
        print("\n" + "="*60)
        print("LOCATION DATA REPORT")
        print("="*60)
        print(f"\nFile: {self.csv_file}")
        print(f"Total Records: {summary['total_records']}")
        print(f"Columns: {', '.join(summary['columns'])}")
        
        if 'time_range' in summary:
            tr = summary['time_range']
            print(f"\nTime Range:")
            print(f"  Start: {tr['start']}")
            print(f"  End: {tr['end']}")
            print(f"  Duration: {tr['duration_days']} days")
        
        if 'spatial_bounds' in summary:
            sb = summary['spatial_bounds']
            print(f"\nSpatial Bounds:")
            print(f"  North: {sb['north']:.6f}")
            print(f"  South: {sb['south']:.6f}")
            print(f"  East: {sb['east']:.6f}")
            print(f"  West: {sb['west']:.6f}")
            print(f"  Center: ({sb['center_lat']:.6f}, {sb['center_lon']:.6f})")
        
        try:
            distance = self.get_distance_traveled()
            print(f"\nTotal Distance Traveled: {distance:.2f} km")
        except:
            pass
        
        try:
            speed_stats = self.get_speed_stats()
            print(f"\nSpeed Statistics:")
            print(f"  Mean: {speed_stats['mean_speed_kmh']:.2f} km/h")
            print(f"  Max: {speed_stats['max_speed_kmh']:.2f} km/h")
            print(f"  Min: {speed_stats['min_speed_kmh']:.2f} km/h")
            print(f"  Median: {speed_stats['median_speed_kmh']:.2f} km/h")
        except:
            pass
        
        print("\n" + "="*60 + "\n")


def main():
    """Main function to demonstrate usage."""
    if len(sys.argv) < 2:
        print("Usage: python data_loader.py <csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    # Load data
    loader = LocationDataLoader(csv_file)
    
    # Print summary
    loader.print_report()
    
    # Example: Get temporal density
    print("\nHourly Data Density:")
    hourly = loader.get_temporal_density('hour')
    print(hourly.head(10))
    
    # Example: Get stay points
    print("\nIdentified Stay Points:")
    stays = loader.get_stay_points()
    for i, stay in enumerate(stays[:5]):
        print(f"\nStay {i+1}:")
        print(f"  Location: ({stay['latitude']:.6f}, {stay['longitude']:.6f})")
        print(f"  Duration: {stay['duration_minutes']:.1f} minutes")
        print(f"  Time: {stay['start_time']} to {stay['end_time']}")


if __name__ == "__main__":
    main()
