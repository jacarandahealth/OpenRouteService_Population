# Deployment Instructions

## Prerequisites

1. **Docker Desktop must be running**
   - Start Docker Desktop application
   - Wait for it to fully start (whale icon in system tray should be steady)

2. **Verify Docker is running:**
   ```bash
   docker ps
   ```
   Should return container list (or empty list if no containers running)

## Deployment Steps

### Step 1: Start Docker Desktop
- Open Docker Desktop application
- Wait until it shows "Docker Desktop is running"

### Step 2: Stop any existing containers
```bash
docker-compose down
```

### Step 3: Start ORS with new configuration
```bash
docker-compose up -d
```

The `-d` flag runs containers in detached mode (background).

### Step 4: Monitor logs
```bash
docker-compose logs -f ors-app
```

Watch for:
- ✅ "OSM source file set to /home/ors/files/kenya-latest.osm.pbf"
- ✅ "Using graphs folder /home/ors/graphs"
- ✅ "All checks passed"
- ✅ Graph building progress (if REBUILD_GRAPHS=True)
- ❌ Any error messages

### Step 5: Verify environment variables
```bash
docker-compose exec ors-app env | grep -E "(ors\.engine|REBUILD_GRAPHS|ORS_CONFIG)"
```

Should show:
- `ors.engine.source_file=/home/ors/files/kenya-latest.osm.pbf`
- `REBUILD_GRAPHS=True`
- `ORS_CONFIG_LOCATION=/home/ors/config/ors-config.yml`

### Step 6: Test ORS health endpoint
```bash
curl http://localhost:8080/ors/v2/health
```

Expected response:
```json
{"status":"ready"}
```

Or use PowerShell:
```powershell
Invoke-WebRequest -Uri http://localhost:8080/ors/v2/health
```

### Step 7: Verify files in container
```bash
# Check source file exists
docker-compose exec ors-app ls -la /home/ors/files/kenya-latest.osm.pbf

# Check config file exists
docker-compose exec ors-app ls -la /home/ors/config/ors-config.yml

# Check graphs directory
docker-compose exec ors-app ls -la /home/ors/graphs/
```

## Expected Behavior

### First Run (Graph Building)
- Container starts
- ORS reads environment variables
- Finds source file at `/home/ors/files/kenya-latest.osm.pbf`
- Starts building graphs (this can take 30+ minutes for Kenya data)
- Logs show graph building progress
- Health endpoint may return "not ready" during building

### After Graph Building
- Health endpoint returns `{"status":"ready"}`
- Can make routing/isochrone requests
- Graphs are cached in `./graphs` directory

## Troubleshooting

### Docker Desktop Not Running
**Error**: `The system cannot find the file specified`
**Solution**: Start Docker Desktop application

### Container Fails to Start
**Check logs**:
```bash
docker-compose logs ors-app
```

**Common issues**:
1. **Source file not found**: Verify `kenya-latest.osm.pbf` exists in project root
2. **Config file not found**: Verify `config/ors-config.yml` exists
3. **Permission issues**: Check file permissions on mounted volumes

### Source File Not Found
**Error**: `cannot use file for DataReader as it wasn't specified!`
**Solution**: 
1. Verify environment variable is set:
   ```bash
   docker-compose exec ors-app env | grep ors.engine.source_file
   ```
2. Verify file exists in container:
   ```bash
   docker-compose exec ors-app ls -la /home/ors/files/
   ```
3. Check volume mount in docker-compose.yml

### Port Already in Use
**Error**: `Bind for 0.0.0.0:8080 failed: port is already allocated`
**Solution**:
1. Find process using port 8080:
   ```bash
   netstat -ano | findstr :8080
   ```
2. Stop the process or change port in docker-compose.yml

### Graph Building Takes Too Long
- Normal for large OSM files (Kenya is ~327MB)
- Can take 30-60 minutes depending on hardware
- Monitor progress in logs
- Once built, graphs are cached and startup is fast

## Quick Commands Reference

```bash
# Start containers
docker-compose up -d

# Stop containers
docker-compose down

# View logs
docker-compose logs -f ors-app

# Restart container
docker-compose restart ors-app

# Execute command in container
docker-compose exec ors-app <command>

# Check container status
docker-compose ps

# Remove containers and volumes (clean slate)
docker-compose down -v
```

## Next Steps After Successful Deployment

1. **Test isochrone generation**:
   ```bash
   curl "http://localhost:8080/ors/v2/isochrones/driving-car?profile=driving-car&range_type=time&range=600&locations=-1.2921,36.8219"
   ```

2. **Access Swagger UI**:
   - Open browser: `http://localhost:8080/ors/swagger-ui`
   - Explore API endpoints

3. **Monitor resource usage**:
   ```bash
   docker stats ors-app
   ```

## Notes

- Graph building is a one-time process (unless REBUILD_GRAPHS=True)
- Graphs are persisted in `./graphs` directory
- First startup will be slow (graph building)
- Subsequent startups will be fast (graphs already built)
- Set `REBUILD_GRAPHS=False` after initial build to speed up restarts

