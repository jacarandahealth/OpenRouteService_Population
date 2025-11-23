# Fix Implementation Plan: ORS Deployment Configuration

## Overview

Based on the investigation, the current deployment fails because it's missing critical environment variables that the reference deployment (which worked) used. The ORS entrypoint script prioritizes environment variables over config files.

## Priority Fixes (Must Do)

### 1. Add Environment Variable for source_file (CRITICAL)

**File**: `docker-compose.yml` or `docker-compose-fixed.yml`

**Add to environment section**:
```yaml
environment:
  - ors.engine.source_file=/home/ors/files/kenya-latest.osm.pbf
  - ors.engine.graphs_root_path=/home/ors/graphs
  - ors.engine.elevation.cache_path=/home/ors/elevation_cache
  - ors.engine.profiles.driving-car.enabled=true
```

**Why**: The entrypoint script checks env vars first. This ensures source_file is always found.

### 2. Change BUILD_GRAPHS to REBUILD_GRAPHS

**File**: `docker-compose.yml` or `docker-compose-fixed.yml`

**Change**:
```yaml
# OLD (deprecated):
- BUILD_GRAPHS=True

# NEW (correct):
- REBUILD_GRAPHS=True
```

**Why**: `BUILD_GRAPHS` is deprecated. `REBUILD_GRAPHS` is the correct flag.

### 3. Add ORS_CONFIG_LOCATION Environment Variable

**File**: `docker-compose.yml` or `docker-compose-fixed.yml`

**Add**:
```yaml
environment:
  - ORS_CONFIG_LOCATION=/home/ors/config/ors-config.yml
```

**Why**: Explicitly tells ORS where to find the config file.

### 4. Fix Port Mapping

**File**: `docker-compose.yml` or `docker-compose-fixed.yml`

**Change**:
```yaml
# Option A: Match reference (if ORS runs on 8082 internally)
ports:
  - "8080:8082"

# Option B: Keep current but ensure config file port matches
ports:
  - "8080:8080"
```

**And update config file**:
```yaml
# If using Option A:
server:
  port: 8082

# If using Option B (current):
server:
  port: 8080
```

**Why**: Port mismatch can prevent connections.

### 5. Set preparation_mode to false

**File**: `ors-config-9.5.1-fixed.yml` or active config file

**Change**:
```yaml
preparation_mode: false  # Changed from true
```

**Why**: `preparation_mode: true` only builds graphs and may not serve requests. Set to `false` for normal operation.

## Recommended Fixes (Should Do)

### 6. Align Volume Mount Paths

**Option A: Match Reference Structure**
```yaml
volumes:
  - ./graphs:/home/ors/graphs
  - ./elevation_cache:/home/ors/elevation_cache
  - ./logs:/home/ors/logs
  - ./config:/home/ors/config
  - ./files:/home/ors/files
  - ./kenya-latest.osm.pbf:/home/ors/files/kenya-latest.osm.pbf
```

**Option B: Keep Current Structure (if verified for 9.5.1)**
```yaml
volumes:
  - ./graphs:/home/ors/ors-core/data/graphs
  - ./elevation_cache:/home/ors/ors-core/data/elevation_cache
  - ./logs/ors:/home/ors/ors-core/logs/ors
  - ./conf:/home/ors/config
  - ./kenya-latest.osm.pbf:/home/ors/files/kenya-latest.osm.pbf
```

**Note**: If using Option B, ensure `graphs_root_path` in config matches:
```yaml
graphs_root_path: /home/ors/ors-core/data/graphs
```

### 7. Add Logging Configuration

**File**: `ors-config-9.5.1-fixed.yml`

**Add**:
```yaml
logging:
  file:
    name: ./logs/ors.log
  level:
    root: WARN
    org.heigit: INFO
```

**Why**: Better debugging capability.

### 8. Consider Explicit Version Tag

**File**: `docker-compose.yml`

**Change**:
```yaml
# Instead of:
image: openrouteservice/openrouteservice:latest

# Use explicit version:
image: openrouteservice/openrouteservice:v8.1.0  # Known working
# OR
image: openrouteservice/openrouteservice:9.5.1   # If you need 9.5.1 features
```

**Why**: `latest` can change unexpectedly. Explicit version ensures consistency.

## Implementation Steps

### Step 1: Update docker-compose.yml

Create or update `docker-compose.yml` with these changes:

```yaml
version: '3.8'  # Update from 2.4
services:
  ors-app:
    container_name: ors-app
    image: openrouteservice/openrouteservice:latest  # Or explicit version
    ports:
      - "8080:8082"  # Match reference, or keep 8080:8080 if config uses 8080
    restart: always
    volumes:
      # Option A: Reference structure
      - ./graphs:/home/ors/graphs
      - ./elevation_cache:/home/ors/elevation_cache
      - ./logs:/home/ors/logs
      - ./config:/home/ors/config
      - ./files:/home/ors/files
      - ./kenya-latest.osm.pbf:/home/ors/files/kenya-latest.osm.pbf
    environment:
      # CRITICAL: Add these environment variables
      - REBUILD_GRAPHS=True
      - ORS_CONFIG_LOCATION=/home/ors/config/ors-config.yml
      - ors.engine.source_file=/home/ors/files/kenya-latest.osm.pbf
      - ors.engine.graphs_root_path=/home/ors/graphs
      - ors.engine.elevation.cache_path=/home/ors/elevation_cache
      - ors.engine.profiles.driving-car.enabled=true
      # Java memory settings
      - XMS=2g
      - XMX=8g
      # Optional: Logging
      - CONTAINER_LOG_LEVEL=INFO
      - logging.level.org.heigit=INFO
```

### Step 2: Update Config File

Update `ors-config-9.5.1-fixed.yml`:

```yaml
server:
  port: 8082  # Match docker-compose port mapping, or 8080 if using 8080:8080
  servlet:
    context-path: /ors

ors:
  engine:
    source_file: /home/ors/files/kenya-latest.osm.pbf
    preparation_mode: false  # Changed from true
    graphs_root_path: ./graphs  # Or /home/ors/ors-core/data/graphs if using that structure
    # ... rest of config
```

### Step 3: Verify Directory Structure

Ensure these directories exist:
```bash
mkdir -p graphs elevation_cache logs config files
```

### Step 4: Place Config File

Place your `ors-config-9.5.1-fixed.yml` in the `config/` directory:
```bash
cp ors-config-9.5.1-fixed.yml config/ors-config.yml
```

### Step 5: Test Deployment

```bash
# Stop existing container
docker-compose down

# Start with new configuration
docker-compose up -d

# Check logs
docker-compose logs -f ors-app
```

## Expected Results

After implementing these fixes:

1. ✅ ORS should find `source_file` via environment variable
2. ✅ ORS should locate config file via `ORS_CONFIG_LOCATION`
3. ✅ Graphs should rebuild using `REBUILD_GRAPHS`
4. ✅ ORS should serve requests (preparation_mode: false)
5. ✅ Port mapping should work correctly

## Troubleshooting

If issues persist:

1. **Check logs**: `docker-compose logs ors-app`
2. **Verify env vars**: `docker-compose exec ors-app env | grep ors.engine`
3. **Verify file exists**: `docker-compose exec ors-app ls -la /home/ors/files/`
4. **Verify config location**: `docker-compose exec ors-app ls -la /home/ors/config/`
5. **Check graph directory**: `docker-compose exec ors-app ls -la /home/ors/graphs/`

## Alternative: Minimal Fix (Quick Test)

If you want to test with minimal changes first:

1. Add only these to docker-compose.yml environment:
   ```yaml
   - ors.engine.source_file=/home/ors/files/kenya-latest.osm.pbf
   - REBUILD_GRAPHS=True
   ```

2. Change in config file:
   ```yaml
   preparation_mode: false
   ```

This should resolve the immediate "source_file not specified" error.

## Files to Create/Modify

1. `docker-compose.yml` - Add environment variables, fix port mapping, update volumes
2. `ors-config-9.5.1-fixed.yml` - Change preparation_mode to false, verify port
3. `config/ors-config.yml` - Copy config file to config directory

## Summary

The fix is straightforward: **Add the missing environment variables** that the reference deployment used. The entrypoint script is designed to use environment variables first, and the reference deployment worked because it followed this pattern.

