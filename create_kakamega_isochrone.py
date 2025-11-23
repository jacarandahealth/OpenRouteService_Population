"""
Create multi-colored isochrone maps for Kakamega and Wajir County Referral Hospitals.
Generates 15, 30, and 45 minute isochrones with population calculations for each.
"""
import openrouteservice
import folium
import json
import time
from config import get_config
from logger import get_logger
from auth_gee import initialize_gee
from analyze_population import (
    get_isochrone_with_retry,
    calculate_population_gee,
    validate_coordinates
)

logger = get_logger(__name__)

# Load configuration
config = get_config()

# Facilities to process
facilities = [
    {
        "name": "Kakamega County Referral Hospital",
        "lat": 0.2745556,
        "lon": 34.7582332
    },
    {
        "name": "Wajir County Referral Hospital",
        "lat": 1.74742,
        "lon": 40.06259
    }
]

# Get time ranges from config (15, 30, 45 minutes)
ranges_sec = config.range_seconds
if isinstance(ranges_sec, int):
    ranges_sec = [ranges_sec]

# Initialize GEE
print("Initializing Google Earth Engine...")
initialize_gee()

# Initialize ORS client
print(f"Connecting to ORS at {config.ors_base_url}...")
ors_client = openrouteservice.Client(
    key=config.ors_api_key,
    base_url=config.ors_base_url
)

# Process each facility
results = []
for facility in facilities:
    facility_name = facility["name"]
    lat = facility["lat"]
    lon = facility["lon"]
    
    print(f"\n{'='*60}")
    print(f"Processing: {facility_name}")
    print(f"Location: ({lat}, {lon})")
    
    # Validate coordinates
    try:
        lat, lon = validate_coordinates(lat, lon)
    except Exception as e:
        logger.error(f"Invalid coordinates for {facility_name}: {e}")
        print(f"✗ Invalid coordinates: {e}")
        continue
    
    # Generate multiple isochrones (15, 30, 45 minutes)
    # Note: ORS v8.1.0 only supports 1 isochrone per request, so we make separate calls
    print(f"Generating isochrones for {', '.join([f'{r//60} min' for r in ranges_sec])}...")
    start_time = time.time()
    
    isochrones_by_range = {}
    populations_by_range = {}
    all_features = []
    
    # Generate each isochrone separately
    for range_sec in ranges_sec:
        range_min = range_sec // 60
        print(f"  Requesting {range_min}-minute isochrone...")
        
        # Request single isochrone
        iso_json = get_isochrone_with_retry(ors_client, lat, lon, [range_sec])
        
        if not iso_json or 'features' not in iso_json or len(iso_json['features']) == 0:
            logger.warning(f"Failed to generate isochrone for {facility_name} at {range_min} minutes")
            continue
        
        feature = iso_json['features'][0]
        geom = feature.get('geometry')
        
        if not geom:
            logger.warning(f"No geometry in isochrone response for {facility_name} at {range_min} minutes")
            continue
        
        # Calculate population for this isochrone
        print(f"    Calculating population...")
        pop = calculate_population_gee(geom)
        
        if pop is None:
            logger.warning(f"Failed to calculate population for {facility_name} at {range_min} minutes")
            pop = -1
        else:
            print(f"    Population: {pop:,.0f} people")
        
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
        print("✗ Error: Failed to generate any isochrones")
        continue
    
    elapsed_time = time.time() - start_time
    print(f"✓ Generated {len(isochrones_by_range)} isochrones in {elapsed_time:.2f} seconds!")
    
    # Create combined GeoJSON for storage
    combined_geojson = {
        "type": "FeatureCollection",
        "features": all_features
    }
    
    # Store results
    results.append({
        "name": facility_name,
        "lat": lat,
        "lon": lon,
        "isochrones": isochrones_by_range,
        "populations": populations_by_range,
        "isochrone_geojson": combined_geojson
    })

# Print summary with totals
print(f"\n{'='*60}")
print("POPULATION SUMMARY")
print(f"{'='*60}")

# Calculate totals
total_15min = 0
total_30min = 0
total_45min = 0
facility_totals = {}

for result in results:
    facility_name = result['name']
    populations = result.get('populations', {})
    
    # Calculate facility total (using 45-min as it's the largest catchment)
    facility_total = populations.get(45, 0) if 45 in populations and populations[45] >= 0 else 0
    facility_totals[facility_name] = facility_total
    
    print(f"\n{facility_name}:")
    for range_min in sorted(populations.keys()):
        pop = populations[range_min]
        if pop >= 0:
            print(f"  {range_min}-min isochrone: {pop:,.0f} people")
            # Add to combined totals
            if range_min == 15:
                total_15min += pop
            elif range_min == 30:
                total_30min += pop
            elif range_min == 45:
                total_45min += pop
        else:
            print(f"  {range_min}-min isochrone: Calculation failed")
    
    print(f"  → Facility Total (45-min catchment): {facility_total:,.0f} people")

print(f"\n{'='*60}")
print("COMBINED TOTALS (All Facilities)")
print(f"{'='*60}")
print(f"  15-min isochrones combined: {total_15min:,.0f} people")
print(f"  30-min isochrones combined: {total_30min:,.0f} people")
print(f"  45-min isochrones combined: {total_45min:,.0f} people")
print(f"  → Grand Total (45-min catchments): {sum(facility_totals.values()):,.0f} people")
print(f"{'='*60}")

# Create map with all facilities
print("\nCreating map with multi-colored isochrones...")

# Calculate center point for map view
if results:
    avg_lat = sum(r['lat'] for r in results) / len(results)
    avg_lon = sum(r['lon'] for r in results) / len(results)
    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=7  # Zoomed out to show both facilities
    )
    
    # Get color mapping from config
    color_map = config.map_isochrone_colors
    
    for result in results:
        facility_name = result['name']
        lat = result['lat']
        lon = result['lon']
        populations = result.get('populations', {})
        
        # Add isochrones in reverse order (45, 30, 15) so smaller ones appear on top
        for range_min in sorted(result['isochrones'].keys(), reverse=True):
            iso_data = result['isochrones'][range_min]
            pop = populations.get(range_min, 0)
            color = color_map.get(range_min, config.map_isochrone_color)
            
            # Create a GeoJSON feature collection for this single isochrone
            single_feature_geojson = {
                "type": "FeatureCollection",
                "features": [iso_data['feature']]
            }
            
            folium.GeoJson(
                single_feature_geojson,
                style_function=lambda x, c=color: {
                    'fillColor': c,
                    'color': c,
                    'weight': 2,
                    'fillOpacity': config.map_isochrone_opacity
                },
                tooltip=f"{facility_name} - {range_min} min: {pop:,.0f} people" if pop >= 0 else f"{facility_name} - {range_min} min"
            ).add_to(m)
        
        # Add facility marker with detailed population info
        pop_lines = []
        facility_total = 0
        for k, v in sorted(populations.items()):
            if v >= 0:
                pop_lines.append(f"{k} min: {v:,.0f}")
                if k == 45:  # Use 45-min as facility total
                    facility_total = v
            else:
                pop_lines.append(f"{k} min: N/A")
        
        pop_text = "<br>".join(pop_lines)
        if facility_total > 0:
            pop_text += f"<br><b>Total (45-min): {facility_total:,.0f}</b>"
        
        folium.Marker(
            [lat, lon],
            popup=f"<b>{facility_name}</b><br>Coordinates: {lat}, {lon}<br><br>Population:<br>{pop_text}",
            tooltip=f"{facility_name}<br>Total: {facility_total:,.0f}" if facility_total > 0 else facility_name,
            icon=folium.Icon(color='red', icon='hospital-o', prefix='fa')
        ).add_to(m)
    
    # Add legend for time ranges with combined totals
    if color_map:
        color_items = sorted(color_map.items())
        
        # Map totals to time ranges
        totals_map = {
            15: total_15min,
            30: total_30min,
            45: total_45min
        }
        
        legend_items = "\n".join([
            f'<p style="margin:5px 0;"><span style="color:{color}">●</span> {range_min} minutes<br><small style="margin-left:20px;">Total: {totals_map.get(range_min, 0):,.0f} people</small></p>'
            for range_min, color in color_items
        ])
        
        # Add grand total at the bottom
        grand_total = sum(facility_totals.values())
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
    
    # Save map
    output_file = "kakamega_wajir_isochrone_map.html"
    m.save(output_file)
    print(f"✓ Map saved to: {output_file}")
    print(f"\nOpen {output_file} in your browser to view the map!")
    
    # Save results JSON with totals
    facilities_data = []
    for r in results:
        populations = r.get("populations", {})
        facility_total = populations.get(45, 0) if 45 in populations and populations[45] >= 0 else 0
        
        facilities_data.append({
            "name": r["name"],
            "lat": r["lat"],
            "lon": r["lon"],
            "populations": {
                f"{k}_min": v for k, v in populations.items()
            },
            "facility_total_45min": facility_total
        })
    
    # Calculate combined totals
    combined_totals = {
        "15_min": total_15min,
        "30_min": total_30min,
        "45_min": total_45min,
        "grand_total_45min": sum(facility_totals.values())
    }
    
    results_json = {
        "facilities": facilities_data,
        "combined_totals": combined_totals,
        "summary": {
            "total_facilities": len(results),
            "facility_totals": {name: total for name, total in facility_totals.items()}
        }
    }
    
    with open("kakamega_wajir_isochrone_results.json", "w") as f:
        json.dump(results_json, f, indent=2)
    print("✓ Results saved to: kakamega_wajir_isochrone_results.json")
else:
    print("✗ No facilities processed successfully")

