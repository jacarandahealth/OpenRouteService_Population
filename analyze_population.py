"""
Main script for isochrone population analysis.
Generates 1-hour driving time isochrones for health facilities and calculates population.
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
    
    Args:
        df: DataFrame to search
        patterns: List of patterns to search for
        default: Default column name if not found
    
    Returns:
        Column name if found, or default if provided, or None
    """
    for pattern in patterns:
        matching_cols = [c for c in df.columns if pattern.lower() in c.lower()]
        if matching_cols:
            return matching_cols[0]
    
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
    
    # Find level column
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
    range_sec: int = 3600,
    max_retries: int = None,
    retry_delay: float = None
) -> Optional[Dict[str, Any]]:
    """
    Generate isochrone with retry logic.
    
    Args:
        client: OpenRouteService client
        lat: Latitude
        lon: Longitude
        range_sec: Time range in seconds
        max_retries: Maximum retry attempts (default from config)
        retry_delay: Initial retry delay in seconds (default from config)
    
    Returns:
        Isochrone GeoJSON response or None if failed
    """
    config = get_config()
    if max_retries is None:
        max_retries = config.ors_retry_attempts
    if retry_delay is None:
        retry_delay = config.ors_retry_delay
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"Requesting isochrone for ({lat}, {lon}), attempt {attempt + 1}/{max_retries}")
            iso = client.isochrones(
                locations=[[lon, lat]],
                profile='driving-car',
                range=[range_sec],
                attributes=['total_pop']
            )
            logger.debug(f"Successfully generated isochrone for ({lat}, {lon})")
            return iso
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(
                    f"Error generating isochrone for ({lat}, {lon}), attempt {attempt + 1}/{max_retries}: {e}. "
                    f"Retrying in {wait_time:.1f}s..."
                )
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to generate isochrone for ({lat}, {lon}) after {max_retries} attempts: {e}")
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
    config
) -> Optional[Dict[str, Any]]:
    """
    Process a single facility: generate isochrone and calculate population.
    
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
    lon_col = find_column_by_pattern(df, ['lon'], 'Longitude')
    name_col = find_column_by_pattern(df, ['name'], 'Facility Name')
    
    try:
        lat = row[lat_col]
        lon = row[lon_col]
        name = row[name_col] if name_col else f"Facility at ({lat}, {lon})"
    except KeyError as e:
        logger.error(f"Missing required column: {e}")
        return None
    
    logger.info(f"Processing {name} ({lat}, {lon})...")
    
    # Validate coordinates
    try:
        lat, lon = validate_coordinates(lat, lon)
    except InvalidCoordinateError as e:
        logger.error(f"Invalid coordinates for {name}: {e}")
        return None
    
    # Generate isochrone
    iso_json = get_isochrone_with_retry(ors_client, lat, lon, config.range_seconds)
    
    if not iso_json or 'features' not in iso_json or len(iso_json['features']) == 0:
        logger.warning(f"Failed to generate isochrone for {name}")
        return None
    
    # Extract geometry
    feature = iso_json['features'][0]
    geom = feature.get('geometry')
    
    if not geom:
        logger.warning(f"No geometry in isochrone response for {name}")
        return None
    
    # Calculate population
    pop = calculate_population_gee(geom)
    
    if pop is None:
        logger.warning(f"Failed to calculate population for {name}, setting to -1")
        pop = -1
    
    logger.info(f"  Population: {pop:,.0f}")
    
    # Prepare result
    result = row.to_dict()
    result['population_1hr'] = pop
    result['isochrone'] = iso_json
    result['lat'] = lat
    result['lon'] = lon
    result['name'] = name
    
    return result


def create_map(results: list, config) -> folium.Map:
    """
    Create Folium map with facilities and isochrones.
    
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
    
    for result in results:
        if 'isochrone' not in result:
            continue
        
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
        
        # Add marker
        if lat is not None and lon is not None:
            folium.Marker([lat, lon], popup=f"{name}<br>Population: {pop:,.0f}").add_to(m)
    
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
        
        for index, row in df.iterrows():
            result = process_facility(row, df, ors_client, config)
            
            if result:
                results.append(result)
            
            # Sleep between requests to be nice to the server
            time.sleep(config.sleep_between_requests)
        
        logger.info(f"Successfully processed {len(results)} out of {total} facilities")
        
        # 5. Save results
        if results:
            # Prepare DataFrame for CSV (exclude isochrone data)
            csv_data = []
            for result in results:
                csv_row = {k: v for k, v in result.items() if k != 'isochrone'}
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
