"""
Create isochrone map for Kakamega County Referral Hospital and calculate population
"""
import requests
import folium
import json
import time
import ee
from config import get_config
from logger import get_logger
from auth_gee import initialize_gee

logger = get_logger(__name__)

# Load configuration
config = get_config()

# Facilities to process
facilities = [
    {
        "name": "Kakamega County Referral Hospital",
        "lat": 0.2745556,
        "lon": 34.7582332,
        "range_seconds": 2700  # 45 minutes
    },
    {
        "name": "Wajir County Referral Hospital",
        "lat": 1.74742,
        "lon": 40.06259,
        "range_seconds": 2700  # 45 minutes
    }
]

# ORS endpoint from config
ors_base_url = config.ors_base_url
ors_url = f"{ors_base_url}/v2/isochrones/driving-car"

# Initialize GEE once for all facilities
print("Initializing Google Earth Engine...")
initialize_gee()
config = get_config()

# Prepare GEE dataset (do this once for efficiency)
dataset_collection = ee.ImageCollection(config.gee_dataset)
dataset_2020 = dataset_collection.filterDate('2020-01-01', '2021-01-01')
collection_size = dataset_2020.size().getInfo()
if collection_size > 0:
    gee_dataset = dataset_2020.mosaic()
else:
    gee_dataset = dataset_collection.sort('system:time_start', False).first()
scale_to_use = max(config.gee_scale, 250)

# Process each facility
results = []
for facility in facilities:
    facility_name = facility["name"]
    lat = facility["lat"]
    lon = facility["lon"]
    range_seconds = facility["range_seconds"]
    
    print(f"\n{'='*60}")
    print(f"Processing: {facility_name}")
    print(f"Location: ({lat}, {lon})")
    print(f"Generating {range_seconds/60:.0f}-minute isochrone...")
    
    # Request isochrone
    payload = {
        "locations": [[lon, lat]],  # ORS expects [lon, lat]
        "range": [range_seconds],
        "range_type": "time",
        "attributes": ["area", "reachfactor", "total_pop"]
    }
    
    print(f"Requesting isochrone from {ors_url}...")
    start_time = time.time()
    
    try:
        response = requests.post(
            ors_url, 
            json=payload, 
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        elapsed_time = time.time() - start_time
    except requests.exceptions.ConnectionError as e:
        print(f"\n✗ Connection Error: Cannot reach ORS server at {ors_url}")
        print(f"  Error details: {e}")
        continue
    except requests.exceptions.Timeout as e:
        print(f"\n✗ Timeout Error: Request to {ors_url} timed out")
        continue
    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")
        continue
    
    if response.status_code != 200:
        print(f"\n✗ Error: Status {response.status_code}")
        print(f"Response: {response.text}")
        continue
    
    iso_json = response.json()
    
    if not iso_json or 'features' not in iso_json or len(iso_json['features']) == 0:
        print("Error: No isochrone features returned")
        continue
    
    print(f"Isochrone generated successfully in {elapsed_time:.2f} seconds!")
    
    # Extract geometry for population calculation
    feature = iso_json['features'][0]
    geom = feature.get('geometry')
    
    if not geom:
        print("Error: No geometry in isochrone response")
        continue
    
    # Calculate population using Google Earth Engine
    print("Calculating population within isochrone...")
    try:
        gee_geom = ee.Geometry(geom)
        
        stats = gee_dataset.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=gee_geom,
            scale=scale_to_use,
            maxPixels=config.gee_max_pixels
        )
        
        all_stats = stats.getInfo()
        population = all_stats.get('population') if all_stats else None
        
        if population is None:
            logger.warning(f"GEE returned None for {facility_name}")
            population = 0
        else:
            population = float(population)
        
        print(f"Population: {population:,.0f} people")
        
    except Exception as e:
        logger.error(f"GEE population calculation error for {facility_name}: {e}", exc_info=True)
        print(f"Error calculating population: {e}")
        population = None
    
    # Store results
    results.append({
        "name": facility_name,
        "lat": lat,
        "lon": lon,
        "range_seconds": range_seconds,
        "isochrone": iso_json,
        "population": population
    })
    
    # Small delay between requests
    time.sleep(1)

# Print summary
print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")
total_population = 0
for result in results:
    pop = result.get('population', 0) if result.get('population') is not None else 0
    total_population += pop
    print(f"{result['name']}: {pop:,.0f} people")
print(f"{'='*60}")
print(f"Total Population (both facilities): {total_population:,.0f} people")
print(f"{'='*60}")

# Create map with all facilities
print("\nCreating map with all facilities...")

# Calculate center point for map view
if results:
    avg_lat = sum(r['lat'] for r in results) / len(results)
    avg_lon = sum(r['lon'] for r in results) / len(results)
    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=7  # Zoomed out to show both facilities
    )
    
    # Color scheme for different facilities
    colors = ['#3388ff', '#ff5733', '#33ff57', '#ff33f5', '#f5ff33']
    
    for i, result in enumerate(results):
        color = colors[i % len(colors)]
        facility_name = result['name']
        lat = result['lat']
        lon = result['lon']
        range_seconds = result['range_seconds']
        population = result.get('population')
        iso_json = result['isochrone']
        
        # Add isochrone
        folium.GeoJson(
            iso_json,
            style_function=lambda x, c=color: {
                'fillColor': c,
                'color': c,
                'weight': 2,
                'fillOpacity': 0.4
            },
            tooltip=f"{facility_name} - {range_seconds/60:.0f} min<br>Population: {population:,.0f}" if population else f"{facility_name} - {range_seconds/60:.0f} min"
        ).add_to(m)
        
        # Add hospital marker
        folium.Marker(
            [lat, lon],
            popup=f"<b>{facility_name}</b><br>Coordinates: {lat}, {lon}<br>Population: {population:,.0f}" if population else f"<b>{facility_name}</b><br>Coordinates: {lat}, {lon}",
            tooltip=facility_name,
            icon=folium.Icon(color='red', icon='hospital-o', prefix='fa')
        ).add_to(m)
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 200px; 
                background-color: white; z-index:9999; 
                border:2px solid grey; padding: 10px;
                font-size:12px">
    <h4 style="margin-top:0">Facilities</h4>
    '''
    for i, result in enumerate(results):
        color = colors[i % len(colors)]
        pop = result.get('population', 0) if result.get('population') is not None else 0
        legend_html += f'<p style="margin:5px 0;"><span style="color:{color};font-weight:bold;">■</span> {result["name"]}<br><small>Pop: {pop:,.0f}</small></p>'
    legend_html += '</div>'
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Save map
    output_file = "kenya_facilities_isochrone_map.html"
    m.save(output_file)
    print(f"Map saved to: {output_file}")
    print(f"\nOpen {output_file} in your browser to view the map!")
    
    # Save results JSON
    results_json = {
        "facilities": [
            {
                "name": r["name"],
                "lat": r["lat"],
                "lon": r["lon"],
                "range_minutes": r["range_seconds"] / 60,
                "population": r.get("population")
            }
            for r in results
        ],
        "total_population": total_population
    }
    with open("facilities_isochrone_results.json", "w") as f:
        json.dump(results_json, f, indent=2)
    print("Results saved to: facilities_isochrone_results.json")
else:
    print("No facilities processed successfully")

