"""
Create isochrone map for Kakamega County Referral Hospital
"""
import requests
import folium
import json
import time

# Hospital coordinates
lat = 0.2745556
lon = 34.7582332
facility_name = "Kakamega County Referral Hospital"
range_seconds = 2700  # 45 minutes

# ORS endpoint
ors_url = "http://localhost:8080/ors/v2/isochrones/driving-car"

print(f"Generating {range_seconds/60:.0f}-minute isochrone for {facility_name}")
print(f"Location: ({lat}, {lon})")

# Request isochrone (POST request with JSON body)
payload = {
    "locations": [[lon, lat]],  # ORS expects [lon, lat]
    "range": [range_seconds],
    "range_type": "time",
    "attributes": ["area", "reachfactor", "total_pop"]
}

print(f"Requesting isochrone from {ors_url}...")
start_time = time.time()
response = requests.post(ors_url, json=payload, headers={"Content-Type": "application/json"})
elapsed_time = time.time() - start_time

if response.status_code != 200:
    print(f"Error: Status {response.status_code}")
    print(f"Response: {response.text}")
    exit(1)

iso_json = response.json()

if not iso_json or 'features' not in iso_json or len(iso_json['features']) == 0:
    print("Error: No isochrone features returned")
    print(f"Response: {json.dumps(iso_json, indent=2)}")
    exit(1)

print(f"Isochrone generated successfully in {elapsed_time:.2f} seconds!")

# Save raw JSON
with open("kakamega_isochrone.json", "w") as f:
    json.dump(iso_json, f, indent=2)
print("Saved isochrone data to kakamega_isochrone.json")

# Create map
print("Creating map...")
m = folium.Map(
    location=[lat, lon],
    zoom_start=11
)

# Add isochrone
folium.GeoJson(
    iso_json,
    style_function=lambda x: {
        'fillColor': '#3388ff',
        'color': '#3388ff',
        'weight': 2,
        'fillOpacity': 0.4
    },
    tooltip=f"{facility_name} - {range_seconds/60:.0f} minute driving area"
).add_to(m)

# Add hospital marker
folium.Marker(
    [lat, lon],
    popup=f"<b>{facility_name}</b><br>Coordinates: {lat}, {lon}",
    tooltip=facility_name,
    icon=folium.Icon(color='red', icon='hospital-o', prefix='fa')
).add_to(m)

# Add title
title_html = f'''
<div style="position: fixed; 
            top: 10px; left: 50px; width: 450px; height: 90px; 
            background-color: white; z-index:9999; 
            border:2px solid grey; padding: 10px;
            font-size:14px">
<h4 style="margin-top:0">{facility_name}</h4>
<p style="margin-bottom:0"><b>{range_seconds/60:.0f}-minute</b> driving isochrone</p>
</div>
'''
m.get_root().html.add_child(folium.Element(title_html))

# Save map
output_file = "kakamega_isochrone_map.html"
m.save(output_file)
print(f"Map saved to: {output_file}")
print(f"\nOpen {output_file} in your browser to view the map!")

