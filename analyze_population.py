"""
Main script for isochrone population analysis.
Generates multiple driving time isochrones (15, 30, 45 minutes) for health facilities 
and calculates population within each isochrone area.
"""
import ee
import openrouteservice
import pandas as pd
import folium
import time
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

from config import get_config
from logger import get_logger
from auth_gee import initialize_gee

logger = get_logger(__name__)


class IsochroneAnalysisError(Exception):
    """Custom exception for isochrone analysis errors."""
    pass


class InvalidCoordinateError(Exception):
    """Exception for invalid coordinate values."""
    pass


def validate_coordinates(lat: float, lon: float) -> Tuple[float, float]:
    """
    Validate and normalize coordinates.
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        Tuple of (lat, lon) if valid
    
    Raises:
        InvalidCoordinateError: If coordinates are invalid
    """
    if lat is None or lon is None:
        raise InvalidCoordinateError("Coordinates cannot be None")
    
    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        raise InvalidCoordinateError(f"Invalid coordinate types: lat={type(lat)}, lon={type(lon)}")
    
    if not (-90 <= lat <= 90):
        raise InvalidCoordinateError(f"Latitude out of range: {lat} (must be -90 to 90)")
    
    if not (-180 <= lon <= 180):
        raise InvalidCoordinateError(f"Longitude out of range: {lon} (must be -180 to 180)")
    
    return lat, lon


def find_column_by_pattern(df: pd.DataFrame, patterns: list, default: str = None) -> Optional[str]:
    """
    Find column in DataFrame matching any of the given patterns (case-insensitive).
    Prioritizes exact matches, then columns that start/end with the pattern.
    
    Args:
        df: DataFrame to search
        patterns: List of patterns to search for
        default: Default column name if not found
    
    Returns:
        Column name if found, or default if provided, or None
    """
    for pattern in patterns:
        pattern_lower = pattern.lower()
        # First try exact match (case-insensitive)
        exact_match = [c for c in df.columns if c.lower() == pattern_lower]
        if exact_match:
            return exact_match[0]
        
        # Then try columns that start or end with the pattern (word boundary)
        word_boundary_match = [
            c for c in df.columns 
            if c.lower().startswith(pattern_lower) or c.lower().endswith(pattern_lower)
        ]
        if word_boundary_match:
            return word_boundary_match[0]
        
        # Finally try any column containing the pattern (fallback)
        containing_match = [c for c in df.columns if pattern_lower in c.lower()]
        if containing_match:
            return containing_match[0]
    
    return default


def filter_by_level(df: pd.DataFrame, level_col: str, target_levels: list) -> pd.DataFrame:
    """
    Filter DataFrame by facility level.
    
    Args:
        df: DataFrame to filter
        level_col: Column name containing level information
        target_levels: List of target level strings to match
    
    Returns:
        Filtered DataFrame
    """
    def is_target_level(val):
        val_str = str(val)
        return any(level in val_str for level in target_levels)
    
    return df[df[level_col].apply(is_target_level)].copy()


def load_and_filter_data(filepath: str, target_levels: list = None) -> pd.DataFrame:
    """
    Load facilities data from Excel file and filter by level.
    
    Args:
        filepath: Path to Excel file
        target_levels: List of target levels to filter (default from config)
    
    Returns:
        Filtered DataFrame
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If required columns are missing
    """
    config = get_config()
    if target_levels is None:
        target_levels = config.target_levels
    
    logger.info(f"Loading data from {filepath}...")
    
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")
    
    try:
        df = pd.read_excel(filepath)
    except Exception as e:
        logger.error(f"Failed to read Excel file: {e}", exc_info=True)
        raise
    
    logger.debug(f"Columns found: {df.columns.tolist()}")
    
    # Normalize column names (strip whitespace)
    df.columns = [c.strip() for c in df.columns]
    
    # Find level column - prefer 'keph_level_name' over 'keph_level' (UUID)
    level_col = None
    if 'keph_level_name' in df.columns:
        level_col = 'keph_level_name'
    else:
        level_col = find_column_by_pattern(df, ['level'], None)
    
    if not level_col:
        raise ValueError("Could not find a 'Level' column. Please check the Excel file.")
    
    logger.info(f"Using column '{level_col}' for filtering.")
    
    # Filter by level
    filtered_df = filter_by_level(df, level_col, target_levels)
    logger.info(f"Filtered down to {len(filtered_df)} facilities from {len(df)}.")
    
    if len(filtered_df) == 0:
        logger.warning("No facilities match the target levels after filtering.")
    
    return filtered_df


def get_isochrone_with_retry(
    client: openrouteservice.Client,
    lat: float,
    lon: float,
    ranges_sec: list = None,
    max_retries: int = None,
    retry_delay: float = None
) -> Optional[Dict[str, Any]]:
    """
    Generate multiple isochrones with retry logic.
    
    Args:
        client: OpenRouteService client
        lat: Latitude
        lon: Longitude
        ranges_sec: List of time ranges in seconds (e.g., [900, 1800, 2700] for 15, 30, 45 min)
                    If None, uses config default. If single int, converts to list for backward compatibility.
        max_retries: Maximum retry attempts (default from config)
        retry_delay: Initial retry delay in seconds (default from config)
    
    Returns:
        Isochrone GeoJSON response with multiple features, or None if failed
    """
    config = get_config()
    if ranges_sec is None:
        ranges_sec = config.range_seconds
    # Handle backward compatibility - if single value, convert to list
    if isinstance(ranges_sec, int):
        ranges_sec = [ranges_sec]
    
    if max_retries is None:
        max_retries = config.ors_retry_attempts
    if retry_delay is None:
        retry_delay = config.ors_retry_delay
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"Requesting isochrones for ({lat}, {lon}), ranges: {ranges_sec}, attempt {attempt + 1}/{max_retries}")
            iso = client.isochrones(
                locations=[[lon, lat]],
                profile='driving-car',
                range=ranges_sec,  # Pass list directly - ORS supports multiple ranges
                attributes=['total_pop']
            )
            logger.debug(f"Successfully generated {len(iso.get('features', []))} isochrones for ({lat}, {lon})")
            return iso
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(
                    f"Error generating isochrones for ({lat}, {lon}), attempt {attempt + 1}/{max_retries}: {e}. "
                    f"Retrying in {wait_time:.1f}s..."
                )
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to generate isochrones for ({lat}, {lon}) after {max_retries} attempts: {e}")
                return None
    
    return None


def calculate_population_gee(geometry: Dict[str, Any], dataset_name: str = None, scale: int = None, max_pixels: int = None) -> Optional[float]:
    """
    Calculate population within geometry using Google Earth Engine.
    
    Args:
        geometry: GeoJSON geometry dictionary
        dataset_name: GEE dataset name (default from config)
        scale: Scale in meters (default from config)
        max_pixels: Maximum pixels (default from config)
    
    Returns:
        Population count or None if calculation fails
    """
    config = get_config()
    if dataset_name is None:
        dataset_name = config.gee_dataset
    if scale is None:
        scale = config.gee_scale
    if max_pixels is None:
        max_pixels = config.gee_max_pixels
    
    try:
        logger.debug(f"Calculating population for geometry using dataset {dataset_name}")
        # WorldPop/GP/100m/pop is an ImageCollection with multiple years/tiles
        # Filter for 2020 data and mosaic tiles together
        dataset_collection = ee.ImageCollection(dataset_name)
        dataset_2020 = dataset_collection.filterDate('2020-01-01', '2021-01-01')
        
        # Mosaic 2020 images if available, otherwise use most recent
        collection_size = dataset_2020.size().getInfo()
        if collection_size > 0:
            dataset = dataset_2020.mosaic()
        else:
            dataset = dataset_collection.sort('system:time_start', False).first()
        
        gee_geom = ee.Geometry(geometry)
        
        # Use a slightly coarser scale (250m) to ensure reliable data retrieval
        scale_to_use = max(scale, 250)
        
        stats = dataset.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=gee_geom,
            scale=scale_to_use,
            maxPixels=max_pixels
        )
        
        population = stats.get('population').getInfo()
        
        if population is None:
            logger.warning("GEE returned None for population calculation")
            return None
        
        logger.debug(f"Population calculated: {population:,.0f}")
        return float(population)
    except Exception as e:
        logger.error(f"GEE population calculation error: {e}", exc_info=True)
        return None


def process_facility(
    row: pd.Series,
    df: pd.DataFrame,
    ors_client: openrouteservice.Client,
    config,
    facility_num: int = None,
    total: int = None
) -> Optional[Dict[str, Any]]:
    """
    Process a single facility: generate multiple isochrones and calculate population for each.
    
    Args:
        row: Facility row from DataFrame
        df: Full DataFrame (for column detection)
        ors_client: OpenRouteService client
        config: Configuration object
    
    Returns:
        Dictionary with facility data and results, or None if processing failed
    """
    # Find coordinate and name columns
    lat_col = find_column_by_pattern(df, ['lat'], 'Latitude')
    lon_col = find_column_by_pattern(df, ['lon', 'long'], 'Longitude')  # Handle both 'lon' and 'long'
    name_col = find_column_by_pattern(df, ['name'], 'Facility Name')
    
    try:
        lat_raw = row[lat_col]
        lon_raw = row[lon_col]
        name = row[name_col] if name_col else f"Facility at ({lat_raw}, {lon_raw})"
    except KeyError as e:
        logger.error(f"Missing required column: {e}")
        return None
    
    # Convert to numeric, handling string values and NaN
    try:
        lat_raw = pd.to_numeric(lat_raw, errors='coerce')
        lon_raw = pd.to_numeric(lon_raw, errors='coerce')
    except (ValueError, TypeError):
        pass  # Will be caught by validate_coordinates
    
    # Check if coordinates are swapped (Kenya lat: -4.5 to 5.5, lon: 33.9 to 41.9)
    # If lat is > 10 or lon is < -5, they're likely swapped
    if (lat_raw is not None and lon_raw is not None and 
        not pd.isna(lat_raw) and not pd.isna(lon_raw)):
        if (lat_raw > 10 or lon_raw < -5):
            # Coordinates are swapped, swap them back
            lat, lon = lon_raw, lat_raw
            logger.debug(f"Swapped coordinates for {name}: ({lat_raw}, {lon_raw}) -> ({lat}, {lon})")
        else:
            lat, lon = lat_raw, lon_raw
    else:
        lat, lon = lat_raw, lon_raw
    
    # Show progress info if provided
    progress_info = ""
    if facility_num is not None and total is not None:
        progress_pct = (facility_num / total) * 100
        progress_info = f" [{facility_num}/{total} - {progress_pct:.1f}%]"
    
    logger.info(f"Processing {name} ({lat}, {lon})...")
    print(f"  Facility: {name}{progress_info}")
    print(f"  Location: ({lat:.6f}, {lon:.6f})")
    
    # Validate coordinates
    try:
        lat, lon = validate_coordinates(lat, lon)
    except InvalidCoordinateError as e:
        logger.error(f"Invalid coordinates for {name}: {e}")
        return None
    
    # Get ranges from config (ensure it's a list)
    ranges_sec = config.range_seconds
    if isinstance(ranges_sec, int):
        ranges_sec = [ranges_sec]
    
    # Generate each isochrone separately (ORS v8.1.0 only supports 1 isochrone per request)
    isochrones_by_range = {}
    populations_by_range = {}
    all_features = []
    
    for range_sec in ranges_sec:
        range_min = range_sec // 60
        logger.debug(f"Requesting {range_min}-minute isochrone for {name}...")
        print(f"    Generating {range_min}-minute isochrone...", end=" ", flush=True)
        
        # Request single isochrone
        iso_json = get_isochrone_with_retry(ors_client, lat, lon, [range_sec])
        
        if not iso_json or 'features' not in iso_json or len(iso_json['features']) == 0:
            logger.warning(f"Failed to generate isochrone for {name} at {range_min} minutes")
            print("[FAILED]")
            continue
        
        feature = iso_json['features'][0]
        geom = feature.get('geometry')
        
        if not geom:
            logger.warning(f"No geometry in isochrone response for {name} at {range_min} minutes")
            print("[NO GEOMETRY]")
            continue
        
        print("[OK]", end=" ", flush=True)
        
        # Calculate population for this isochrone
        print("Calculating population...", end=" ", flush=True)
        pop = calculate_population_gee(geom)
        if pop is None:
            logger.warning(f"Failed to calculate population for {name} at {range_min} minutes, setting to -1")
            pop = -1
            print("[FAILED]")
        else:
            print(f"[OK] Population: {pop:,.0f}")
        
        logger.info(f"  {range_min}-min isochrone: Population: {pop:,.0f}")
        
        # Store isochrone and population by time range
        isochrones_by_range[range_min] = {
            'geometry': geom,
            'feature': feature,
            'range_seconds': range_sec
        }
        populations_by_range[range_min] = pop
        all_features.append(feature)
        
        # Small delay between requests
        time.sleep(config.sleep_between_requests)
    
    if not isochrones_by_range:
        logger.warning(f"Failed to generate any isochrones for {name}")
        return None
    
    # Create combined GeoJSON for storage
    combined_geojson = {
        "type": "FeatureCollection",
        "features": all_features
    }
    
    # Prepare result
    result = row.to_dict()
    result['lat'] = lat
    result['lon'] = lon
    result['name'] = name
    result['isochrones'] = isochrones_by_range  # Changed from single 'isochrone'
    result['populations'] = populations_by_range
    
    # For backward compatibility and map rendering, also store the full GeoJSON
    result['isochrone_geojson'] = combined_geojson
    
    # Also keep backward-compatible single isochrone field (use largest range)
    if all_features:
        result['isochrone'] = {
            "type": "FeatureCollection",
            "features": [all_features[-1]]  # Largest range
        }
        result['population_1hr'] = populations_by_range.get(max(populations_by_range.keys()) if populations_by_range else 0, -1)
    
    return result


def create_map(results: list, config) -> folium.Map:
    """
    Create Folium map with facilities and multiple colored isochrones.
    
    Args:
        results: List of result dictionaries
        config: Configuration object
    
    Returns:
        Folium Map object
    """
    m = folium.Map(
        location=[config.map_center_lat, config.map_center_lon],
        zoom_start=config.map_zoom_start
    )
    
    # Get color mapping from config
    color_map = config.map_isochrone_colors
    
    # Define darker border colors for each time range
    border_color_map = {
        15: "#1565C0",  # Dark blue
        30: "#6A1B9A",  # Dark purple
        45: "#C62828"   # Dark red
    }
    
    for result in results:
        # Check for new format (multiple isochrones) or old format (single isochrone)
        if 'isochrones' in result:
            # New format: multiple isochrones
            name = result.get('name', 'Unknown')
            lat = result.get('lat')
            lon = result.get('lon')
            populations = result.get('populations', {})
            
            # Add isochrones in reverse order (largest to smallest) so smaller ones appear on top
            for range_min in sorted(result['isochrones'].keys(), reverse=True):
                iso_data = result['isochrones'][range_min]
                pop = populations.get(range_min, 0)
                color = color_map.get(range_min, config.map_isochrone_color)  # Default color if not specified
                border_color = border_color_map.get(range_min, color)  # Use darker border color
                
                # Create a GeoJSON feature collection for this single isochrone
                single_feature_geojson = {
                    "type": "FeatureCollection",
                    "features": [iso_data['feature']]
                }
                
                folium.GeoJson(
                    single_feature_geojson,
                    style_function=lambda x, fill_c=color, border_c=border_color: {
                        'fillColor': fill_c,
                        'color': border_c,
                        'weight': 2,
                        'fillOpacity': config.map_isochrone_opacity
                    },
                    tooltip=f"{name} - {range_min} min: {pop:,.0f} people"
                ).add_to(m)
            
            # Add facility marker (smaller circle marker)
            if lat is not None and lon is not None:
                pop_text = ", ".join([f"{k}min: {v:,.0f}" for k, v in sorted(populations.items())])
                folium.CircleMarker(
                    [lat, lon],
                    radius=5,  # Smaller marker size
                    popup=f"<b>{name}</b><br>Population:<br>{pop_text}",
                    color='red',
                    fill=True,
                    fillColor='red',
                    fillOpacity=0.8,
                    weight=2
                ).add_to(m)
        
        elif 'isochrone' in result:
            # Old format: single isochrone (backward compatibility)
            name = result.get('name', 'Unknown')
            pop = result.get('population_1hr', 0)
            lat = result.get('lat')
            lon = result.get('lon')
            
            # Add isochrone
            folium.GeoJson(
                result['isochrone'],
                style_function=lambda x: {
                    'fillColor': config.map_isochrone_color,
                    'color': config.map_isochrone_color,
                    'weight': 1,
                    'fillOpacity': config.map_isochrone_opacity
                },
                tooltip=f"{name}: {pop:,.0f}"
            ).add_to(m)
            
            # Add marker (smaller circle marker)
            if lat is not None and lon is not None:
                folium.CircleMarker(
                    [lat, lon],
                    radius=5,  # Smaller marker size
                    popup=f"{name}<br>Population: {pop:,.0f}",
                    color='red',
                    fill=True,
                    fillColor='red',
                    fillOpacity=0.8,
                    weight=2
                ).add_to(m)
    
    # Add legend with totals if using multiple isochrones
    if color_map:
        # Calculate combined totals across all facilities
        total_15min = 0
        total_30min = 0
        total_45min = 0
        
        for result in results:
            if 'populations' in result:
                populations = result.get('populations', {})
                if 15 in populations and populations[15] >= 0:
                    total_15min += populations[15]
                if 30 in populations and populations[30] >= 0:
                    total_30min += populations[30]
                if 45 in populations and populations[45] >= 0:
                    total_45min += populations[45]
        
        totals_map = {
            15: total_15min,
            30: total_30min,
            45: total_45min
        }
        
        color_items = sorted(color_map.items())
        legend_items = "\n".join([
            f'<p style="margin:5px 0"><span style="color:{color}">●</span> {range_min} minutes<br><small style="margin-left:20px;">Total: {totals_map.get(range_min, 0):,.0f} people</small></p>'
            for range_min, color in color_items
        ])
        
        # Add grand total
        grand_total = total_45min
        legend_items += f'<hr style="margin:10px 0;"><p style="margin:5px 0;"><b>Grand Total (45-min):</b><br><small style="margin-left:20px;">{grand_total:,.0f} people</small></p>'
        
        legend_html = f'''
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 250px; height: auto; 
                    background-color: white; z-index:9999; 
                    border:2px solid grey; padding: 10px;
                    font-size:14px">
        <h4 style="margin-top:0">Isochrone Times & Totals</h4>
        {legend_items}
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
    
    return m


def main():
    """Main execution function."""
    config = get_config()
    logger.info("Starting isochrone population analysis")
    
    try:
        # 1. Initialize GEE
        logger.info("Initializing Google Earth Engine...")
        initialize_gee()
        
        # 2. Load and filter data
        logger.info("Loading facility data...")
        try:
            df = load_and_filter_data(config.input_file, config.target_levels)
        except (FileNotFoundError, ValueError) as e:
            logger.error(f"Data loading error: {e}", exc_info=True)
            return
        
        if len(df) == 0:
            logger.error("No facilities to process after filtering")
            return
        
        # Randomly sample 30% of facilities for faster test run
        original_count = len(df)
        df = df.sample(frac=0.3, random_state=42)
        logger.info(f"Randomly sampled 30% of facilities: {len(df)} out of {original_count} facilities")
        
        # 3. Initialize ORS client
        logger.info(f"Connecting to ORS at {config.ors_base_url}...")
        
        # Pre-flight connection check
        try:
            import requests
            health_response = requests.get(config.ors_health_url, timeout=5)
            if health_response.status_code != 200:
                logger.warning(f"ORS health check returned status {health_response.status_code}")
                logger.warning("Continuing anyway, but connection may fail...")
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to ORS server!")
            logger.error("")
            logger.error("Troubleshooting:")
            logger.error("  1. Get current GCP instance IP: python get_gcp_ors_ip.py")
            logger.error("  2. Update config: python get_gcp_ors_ip.py --update-config")
            logger.error("  3. Check instance status: python check_ors.py")
            logger.error("")
            raise ConnectionError(
                f"Cannot connect to ORS server at {config.ors_base_url}. "
                f"Please verify the server is running and the IP address is correct. "
                f"Run 'python get_gcp_ors_ip.py' to get the current GCP instance IP."
            )
        except Exception as e:
            logger.warning(f"Pre-flight check failed: {e}, continuing anyway...")
        
        ors_client = openrouteservice.Client(
            key=config.ors_api_key,
            base_url=config.ors_base_url
        )
        
        # 4. Process facilities
        results = []
        total = len(df)
        logger.info(f"Processing {total} facilities...")
        print(f"\n{'='*70}")
        print(f"Processing {total} facilities...")
        print(f"{'='*70}\n")
        
        for idx, (index, row) in enumerate(df.iterrows(), 1):
            # Calculate progress
            progress_pct = (idx / total) * 100
            print(f"[{idx}/{total}] ({progress_pct:.1f}%) Processing facility {idx}...")
            
            result = process_facility(row, df, ors_client, config, facility_num=idx, total=total)
            
            if result:
                results.append(result)
                print(f"  [SUCCESS] Successfully processed: {result.get('name', 'Unknown')}\n")
            else:
                print(f"  [FAILED] Failed to process facility {idx}\n")
            
            # Sleep between requests to be nice to the server
            time.sleep(config.sleep_between_requests)
        
        print(f"\n{'='*70}")
        print(f"Processing complete: {len(results)} out of {total} facilities successfully processed")
        print(f"{'='*70}\n")
        logger.info(f"Successfully processed {len(results)} out of {total} facilities")
        
        # 5. Save results
        if results:
            # Prepare DataFrame for CSV (exclude isochrone data)
            csv_data = []
            for result in results:
                csv_row = {k: v for k, v in result.items() 
                          if k not in ['isochrones', 'isochrone', 'isochrone_geojson']}
                
                # Add population columns for each time range
                populations = result.get('populations', {})
                for range_min in sorted(populations.keys()):
                    csv_row[f'population_{range_min}min'] = populations[range_min]
                
                csv_data.append(csv_row)
            
            result_df = pd.DataFrame(csv_data)
            result_df.to_csv(config.output_csv, index=False)
            logger.info(f"Saved results to {config.output_csv}")
            
            # Create and save map
            m = create_map(results, config)
            m.save(config.output_map)
            logger.info(f"Saved map to {config.output_map}")
        else:
            logger.warning("No results to save")
    
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
