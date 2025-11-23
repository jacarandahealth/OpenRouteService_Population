# Docker Compose Configuration Comparison

## Reference Deployment (Working - v8.1.0) vs Current Deployment (Not Working - latest/9.5.1)

### Critical Differences

#### 1. Version Tag
- **Reference**: `image: openrouteservice/openrouteservice:v8.1.0` (explicit version)
- **Current**: `image: openrouteservice/openrouteservice:latest` (implicit, likely 9.5.1)
- **Impact**: Major configuration structure changes between v8.1.0 and 9.5.1

#### 2. Docker Compose Version
- **Reference**: `version: '3.8'`
- **Current**: `version: '2.4'`
- **Impact**: Different feature support and syntax

#### 3. Port Mapping
- **Reference**: `"8080:8082"` (host:container) - ORS runs on 8082 internally
- **Current**: `"8080:8080"` (host:container) - Assumes ORS runs on 8080
- **Impact**: Port mismatch could cause connection issues

#### 4. Graph Rebuild Flag
- **Reference**: `REBUILD_GRAPHS: True` (correct, non-deprecated)
- **Current**: `BUILD_GRAPHS=True` (deprecated flag)
- **Impact**: Deprecated flag may not work correctly in newer versions

#### 5. Source File Configuration (CRITICAL)
- **Reference**: Environment variable `ors.engine.source_file: /home/ors/files/kenya-latest.osm.pbf`
- **Current**: No environment variable set - relies only on YAML config file
- **Impact**: Docker entrypoint script checks env vars first, then falls back to config file. Missing env var may cause issues.

#### 6. Volume Mount Structure
- **Reference**: 
  - Single comprehensive mount: `./ors-docker:/home/ors`
  - Individual mounts for organization:
    - `./graphs:/home/ors/graphs`
    - `./elevation_cache:/home/ors/elevation_cache`
    - `./config:/home/ors/config`
    - `./logs:/home/ors/logs`
    - `./files:/home/ors/files`
  
- **Current**:
  - Individual mounts to different paths:
    - `./graphs:/home/ors/ors-core/data/graphs`
    - `./elevation_cache:/home/ors/ors-core/data/elevation_cache`
    - `./logs/ors:/home/ors/ors-core/logs/ors`
    - `./logs/tomcat:/home/ors/ors-core/logs/tomcat`
    - `./conf:/home/ors/ors-conf`
    - `./kenya-latest.osm.pbf:/home/ors/ors-core/data/osm_file.pbf`
  
- **Impact**: Path structure differs significantly. Reference uses `/home/ors/*` while current uses `/home/ors/ors-core/data/*`. This path mismatch could prevent ORS from finding files.

#### 7. Config File Location
- **Reference**: 
  - Mount: `./config:/home/ors/config`
  - Environment variable: `ORS_CONFIG_LOCATION: /home/ors/config/ors-config.yml`
  - Explicitly tells ORS where to find config
  
- **Current**:
  - Mount: `./conf:/home/ors/ors-conf` (different path!)
  - No `ORS_CONFIG_LOCATION` environment variable
  - ORS may not find config file at expected location

#### 8. Environment Variables - Source File
- **Reference**: 
  ```yaml
  ors.engine.source_file: /home/ors/files/kenya-latest.osm.pbf
  ors.engine.graphs_root_path: /home/ors/graphs
  ors.engine.elevation.cache_path: /home/ors/elevation_cache
  ors.engine.profiles.car.enabled: true
  ```
- **Current**: None of these environment variables are set
- **Impact**: ORS entrypoint script prioritizes env vars over config files. Missing env vars means ORS must read from config file, which may be failing.

#### 9. Java Memory Configuration
- **Reference**: 
  - `XMS: 1g`
  - `XMX: 2g`
  - Uses separate env vars
  
- **Current**: 
  - `JAVA_OPTS` with `-Xms2g -Xmx8g` embedded in single string
  - Different approach to memory configuration

#### 10. Additional Configuration
- **Reference**: 
  - `CONTAINER_LOG_LEVEL: INFO`
  - `logging.level.org.heigit: INFO`
  - `env_file: ./ors-config.env` (optional env file)
  - Healthcheck configured
  
- **Current**: 
  - No log level configuration
  - No healthcheck
  - No env_file reference

#### 11. User Configuration
- **Reference**: User commented out (defaults to root)
- **Current**: `user: "${UID:-0}:${GID:-0}"` (uses environment variables or defaults to root)

## Summary of Critical Issues

1. **Missing Environment Variable for source_file**: This is the most critical difference. The reference deployment uses `ors.engine.source_file` as an environment variable, which takes precedence over config file values.

2. **Path Structure Mismatch**: Current deployment uses `/home/ors/ors-core/data/*` paths while reference uses `/home/ors/*`. This could cause ORS to look in wrong locations.

3. **Deprecated BUILD_GRAPHS Flag**: Should use `REBUILD_GRAPHS` instead.

4. **Missing ORS_CONFIG_LOCATION**: Reference explicitly sets where config file is located.

5. **Port Mapping**: Reference maps to container port 8082, current assumes 8080.

## Recommended Fixes

1. Add environment variable: `ors.engine.source_file: /home/ors/files/kenya-latest.osm.pbf`
2. Change `BUILD_GRAPHS` to `REBUILD_GRAPHS`
3. Align volume mount paths with reference structure OR verify current paths work with ORS version
4. Add `ORS_CONFIG_LOCATION` environment variable
5. Fix port mapping to match container's internal port (8082)
6. Consider using explicit version tag instead of `latest`

