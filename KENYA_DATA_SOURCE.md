# Kenya OSM Data Source

## Primary Source: Geofabrik

The Kenya OpenStreetMap (OSM) data is available from **Geofabrik**, which provides free, regularly updated OSM extracts.

### Download URL
```
https://download.geofabrik.de/africa/kenya-latest.osm.pbf
```

### File Information
- **Format**: PBF (Protocol Buffer Format) - compressed binary format
- **Size**: Approximately 50-100 MB (varies with updates)
- **Update Frequency**: Daily updates available
- **License**: Open Database License (ODbL)

### Alternative Sources

1. **Geofabrik (Recommended)**
   - URL: https://download.geofabrik.de/africa/kenya.html
   - Direct download: https://download.geofabrik.de/africa/kenya-latest.osm.pbf
   - Provides daily updates
   - Fast and reliable CDN

2. **OpenStreetMap Full Planet**
   - URL: https://planet.openstreetmap.org/
   - Requires extracting Kenya region (more complex)
   - Only if you need the absolute latest data

3. **BBBike**
   - URL: https://download.bbbike.org/osm/bbbike/
   - Alternative extract provider
   - Less frequently updated than Geofabrik

### Using the Data

The startup script (`startup-script.sh`) automatically downloads the Kenya OSM data:
```bash
wget https://download.geofabrik.de/africa/kenya-latest.osm.pbf -O kenya-latest.osm.pbf
```

The fix script (`fix_ors_container.ps1`) will also download it if missing.

### Manual Download

If you need to download manually:

**On Linux/Mac:**
```bash
wget https://download.geofabrik.de/africa/kenya-latest.osm.pbf
```

**On Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri "https://download.geofabrik.de/africa/kenya-latest.osm.pbf" -OutFile "kenya-latest.osm.pbf"
```

**On Windows (using wget if installed):**
```cmd
wget https://download.geofabrik.de/africa/kenya-latest.osm.pbf
```

### Verification

After downloading, verify the file:
```bash
# Check file size (should be ~50-100 MB)
ls -lh kenya-latest.osm.pbf

# Check file type
file kenya-latest.osm.pbf
# Should show: "OSM XML Protocolbuffer Binary Format"
```

### Notes

- The file is named `kenya-latest.osm.pbf` - the "latest" indicates it's the most recent extract
- Geofabrik updates extracts daily, so you can re-download to get the latest OSM data
- The PBF format is more efficient than XML for large datasets
- ORS will process this file and build routing graphs (takes 15-20 minutes for Kenya)

