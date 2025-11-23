"""
Generate an isochrone map for a single location.
Quick utility script to create isochrone maps for specific facilities.
"""
import openrouteservice
import folium
from config import get_config
from logger import get_logger
from analyze_population import get_isochrone_with_retry, validate_coordinates

logger = get_logger(__name__)


def generate_isochrone_map(
    lat: float,
    lon: float,
    facility_name: str,
    range_seconds: int = 3600,
    output_file: str = None
):
    """
    Generate an isochrone map for a single location.
    
    Args:
        lat: Latitude
        lon: Longitude
        facility_name: Name of the facility
        range_seconds: Time range in seconds (default 3600 = 1 hour)
        output_file: Output HTML file path (default: isochrone_{facility_name}.html)
    """
    config = get_config()
    
    # Validate coordinates
    try:
        lat, lon = validate_coordinates(lat, lon)
    except Exception as e:
        logger.error(f"Invalid coordinates: {e}")
        raise
    
    logger.info(f"Generating {range_seconds/60:.0f}-minute isochrone for {facility_name}")
    logger.info(f"Location: ({lat}, {lon})")
    
    # Initialize ORS client
    logger.info(f"Connecting to ORS at {config.ors_base_url}...")
    ors_client = openrouteservice.Client(
        key=config.ors_api_key,
        base_url=config.ors_base_url
    )
    
    # Generate isochrone
    logger.info("Requesting isochrone from ORS...")
    iso_json = get_isochrone_with_retry(
        ors_client,
        lat,
        lon,
        range_sec=range_seconds,
        max_retries=config.ors_retry_attempts
    )
    
    if not iso_json or 'features' not in iso_json or len(iso_json['features']) == 0:
        logger.error("Failed to generate isochrone")
        raise ValueError("Could not generate isochrone. Check ORS server connection.")
    
    logger.info("Isochrone generated successfully")
    
    # Create map
    logger.info("Creating map...")
    m = folium.Map(
        location=[lat, lon],
        zoom_start=11  # Closer zoom for single facility
    )
    
    # Add isochrone
    folium.GeoJson(
        iso_json,
        style_function=lambda x: {
            'fillColor': config.map_isochrone_color,
            'color': config.map_isochrone_color,
            'weight': 2,
            'fillOpacity': config.map_isochrone_opacity
        },
        tooltip=f"{facility_name} - {range_seconds/60:.0f} minute driving area"
    ).add_to(m)
    
    # Add facility marker
    folium.Marker(
        [lat, lon],
        popup=f"<b>{facility_name}</b><br>Coordinates: {lat}, {lon}",
        tooltip=facility_name,
        icon=folium.Icon(color='red', icon='hospital-o', prefix='fa')
    ).add_to(m)
    
    # Add title
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 400px; height: 90px; 
                background-color: white; z-index:9999; 
                border:2px solid grey; padding: 10px;
                font-size:14px">
    <h4 style="margin-top:0">{facility_name}</h4>
    <p style="margin-bottom:0"><b>{range_seconds/60:.0f}-minute</b> driving isochrone</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Save map
    if output_file is None:
        # Clean facility name for filename
        safe_name = facility_name.replace(' ', '_').replace('/', '_')
        output_file = f"isochrone_{safe_name}.html"
    
    m.save(output_file)
    logger.info(f"Map saved to: {output_file}")
    
    return output_file


def main():
    """Main function for command-line usage."""
    import sys
    import os
    
    # Meru Teaching and Referral Hospital coordinates
    lat = 0.050608
    lon = 37.6508131
    facility_name = "Meru Teaching and Referral Hospital"
    range_seconds = 3600  # 1 hour
    
    # Check if user wants to use public ORS API
    use_public_api = os.getenv('USE_PUBLIC_ORS', '').lower() in ('true', '1', 'yes')
    public_api_key = os.getenv('ORS_PUBLIC_API_KEY', '')
    
    if use_public_api and public_api_key:
        logger.info("Using public OpenRouteService API")
        config = get_config()
        import openrouteservice
        
        # Create client with public API
        client = openrouteservice.Client(key=public_api_key)
        # Temporarily override config
        original_base_url = config.ors_base_url
        config._config['ors']['base_url'] = 'https://api.openrouteservice.org'
        
        try:
            # Use the public API client directly
            logger.info("Connecting to public OpenRouteService API...")
            logger.info("Requesting isochrone from ORS...")
            
            iso_json = client.isochrones(
                locations=[[lon, lat]],
                profile='driving-car',
                range=[range_seconds],
                attributes=['total_pop']
            )
            
            if not iso_json or 'features' not in iso_json or len(iso_json['features']) == 0:
                raise ValueError("Could not generate isochrone")
            
            logger.info("Isochrone generated successfully")
            
            # Create map
            logger.info("Creating map...")
            m = folium.Map(location=[lat, lon], zoom_start=11)
            
            folium.GeoJson(
                iso_json,
                style_function=lambda x: {
                    'fillColor': config.map_isochrone_color,
                    'color': config.map_isochrone_color,
                    'weight': 2,
                    'fillOpacity': config.map_isochrone_opacity
                },
                tooltip=f"{facility_name} - {range_seconds/60:.0f} minute driving area"
            ).add_to(m)
            
            folium.Marker(
                [lat, lon],
                popup=f"<b>{facility_name}</b><br>Coordinates: {lat}, {lon}",
                tooltip=facility_name,
                icon=folium.Icon(color='red', icon='hospital-o', prefix='fa')
            ).add_to(m)
            
            title_html = f'''
            <div style="position: fixed; 
                        top: 10px; left: 50px; width: 400px; height: 90px; 
                        background-color: white; z-index:9999; 
                        border:2px solid grey; padding: 10px;
                        font-size:14px">
            <h4 style="margin-top:0">{facility_name}</h4>
            <p style="margin-bottom:0"><b>{range_seconds/60:.0f}-minute</b> driving isochrone</p>
            </div>
            '''
            m.get_root().html.add_child(folium.Element(title_html))
            
            safe_name = facility_name.replace(' ', '_').replace('/', '_')
            output_file = f"isochrone_{safe_name}.html"
            m.save(output_file)
            
            print(f"\n✓ Success! Isochrone map generated: {output_file}")
            print(f"Open {output_file} in your browser to view the map.")
            return
            
        except Exception as e:
            logger.error(f"Failed with public API: {e}")
            print(f"\n✗ Error with public API: {e}")
            print("\nTo use public ORS API:")
            print("  1. Get a free API key from https://openrouteservice.org/dev/#/signup")
            print("  2. Set environment variable: set ORS_PUBLIC_API_KEY=your_key_here")
            print("  3. Set environment variable: set USE_PUBLIC_ORS=true")
            sys.exit(1)
        finally:
            config._config['ors']['base_url'] = original_base_url
    
    try:
        output_file = generate_isochrone_map(
            lat=lat,
            lon=lon,
            facility_name=facility_name,
            range_seconds=range_seconds
        )
        print(f"\n✓ Success! Isochrone map generated: {output_file}")
        print(f"Open {output_file} in your browser to view the map.")
    except Exception as e:
        logger.error(f"Failed to generate isochrone map: {e}", exc_info=True)
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check ORS server is running: python check_ors.py")
        print("  2. Update config.yaml with correct ORS server URL")
        print("  3. Or use public ORS API:")
        print("     - Get API key: https://openrouteservice.org/dev/#/signup")
        print("     - Set: set ORS_PUBLIC_API_KEY=your_key")
        print("     - Set: set USE_PUBLIC_ORS=true")
        print("     - Run this script again")
        sys.exit(1)


if __name__ == "__main__":
    main()

