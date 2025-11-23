# Complete Investigation Findings: Reference vs Current Deployment

## Executive Summary

The reference deployment (v8.1.0) worked because it uses **environment variables** to configure critical settings, particularly `ors.engine.source_file`. The current deployment (9.5.1/latest) fails because it relies solely on YAML config files, and the ORS entrypoint script prioritizes environment variables over config files.

## Root Cause

**Primary Issue**: Missing environment variable `ors.engine.source_file` in docker-compose.yml

The ORS docker-entrypoint.sh script:
1. First checks for environment variable `ors.engine.source_file`
2. Only if not found, extracts from YAML config file
3. Explicitly states: "Any ENV variables will have precedence over configuration variables from config files"

Current deployment does NOT set this environment variable, causing ORS to fail reading the source_file.

## Critical Differences Identified

### 1. Docker Compose Configuration

#### Version
- **Reference**: `openrouteservice/openrouteservice:v8.1.0` (explicit)
- **Current**: `openrouteservice/openrouteservice:latest` (implicit, likely 9.5.1)

#### Environment Variables (CRITICAL)
- **Reference**: Sets `ors.engine.source_file: /home/ors/files/kenya-latest.osm.pbf` as env var
- **Current**: No environment variable set - relies only on YAML config

#### Graph Rebuild Flag
- **Reference**: `REBUILD_GRAPHS: True` (correct)
- **Current**: `BUILD_GRAPHS=True` (deprecated)

#### Config Location
- **Reference**: `ORS_CONFIG_LOCATION: /home/ors/config/ors-config.yml`
- **Current**: Not set

#### Port Mapping
- **Reference**: `"8080:8082"` (ORS runs on 8082 internally)
- **Current**: `"8080:8080"` (assumes 8080)

#### Volume Mounts
- **Reference**: Uses `/home/ors/*` paths
  - `./ors-docker:/home/ors`
  - `./graphs:/home/ors/graphs`
  - `./files:/home/ors/files`
  - `./config:/home/ors/config`
  
- **Current**: Uses `/home/ors/ors-core/data/*` paths
  - `./graphs:/home/ors/ors-core/data/graphs`
  - `./kenya-latest.osm.pbf:/home/ors/ors-core/data/osm_file.pbf`
  - `./conf:/home/ors/config`

### 2. Configuration File Structure

#### Profile Structure
- **Reference (v8.1.0)**: `profiles.car.profile: driving-car`
- **Current (9.5.1)**: `profiles.driving-car:` (correct for version, but different pattern)

#### Preparation Mode
- **Reference**: `preparation_mode: false` (serves requests)
- **Current**: `preparation_mode: true` (builds graphs only, may not serve requests)

#### Server Port
- **Reference**: `port: 8082`
- **Current**: `port: 8080` (mismatch with docker-compose)

#### Source File Path
- **Both**: `/home/ors/files/kenya-latest.osm.pbf` (same, correct)

### 3. Entrypoint Script Behavior

The docker-entrypoint.sh script (from reference deployment) shows:

1. **Line 187**: Checks environment variable first
   ```bash
   ors_engine_source_file=$(env | grep "^ors\.engine\.source_file=" | awk -F '=' '{print $2}')
   ```

2. **Lines 241-247**: Falls back to config file only if env var not found
   ```bash
   if [[ -z "${ors_engine_source_file}" ]]; then
     ors_engine_source_file=$(extract_config_info "${ors_config_location}" '.ors.engine.source_file')
   fi
   ```

3. **Line 264**: Explicit precedence statement
   ```
   "Any ENV variables will have precedence over configuration variables from config files."
   ```

## Why Reference Deployment Worked

1. ✅ Set `ors.engine.source_file` as environment variable
2. ✅ Set `ORS_CONFIG_LOCATION` to explicitly point to config file
3. ✅ Used `REBUILD_GRAPHS` (non-deprecated flag)
4. ✅ Matched port mapping (8080:8082)
5. ✅ Used consistent path structure (`/home/ors/*`)
6. ✅ Set `preparation_mode: false` to serve requests

## Why Current Deployment Fails

1. ❌ Missing `ors.engine.source_file` environment variable
2. ❌ Missing `ORS_CONFIG_LOCATION` environment variable
3. ❌ Uses deprecated `BUILD_GRAPHS` flag
4. ❌ Port mismatch (8080:8080 vs 8082)
5. ❌ Different path structure (`/home/ors/ors-core/data/*`)
6. ❌ `preparation_mode: true` may prevent serving requests

## Error Analysis

The error message:
```
Exception at RoutingProfileManager initialization: 
java.lang.IllegalStateException: Couldn't load from existing folder: graphs/driving-car 
but also cannot use file for DataReader as it wasn't specified!
```

This indicates:
1. ORS tried to load existing graphs from `graphs/driving-car` (failed - graphs may be incomplete/corrupt)
2. ORS then tried to use source_file to rebuild graphs (failed - source_file not found/read)
3. Result: Cannot proceed without either existing graphs or source file

## Version Compatibility Notes

- v8.1.0: Uses `profiles.car.profile: driving-car` structure
- v9.5.1: Uses `profiles.driving-car:` structure directly
- Both are valid for their respective versions
- The profile structure difference is NOT the issue

## Path Structure Analysis

Reference deployment uses:
- `/home/ors/files/` for OSM files
- `/home/ors/graphs/` for graph data
- `/home/ors/config/` for configuration

Current deployment uses:
- `/home/ors/files/kenya-latest.osm.pbf` (correct for source file)
- `/home/ors/ors-core/data/graphs` (different path)
- `/home/ors/config` (correct, but may not be found without ORS_CONFIG_LOCATION)

The path differences may cause issues if ORS 9.5.1 expects different paths, but the primary issue is the missing environment variable.

## Conclusion

The reference deployment worked because it used environment variables for critical configuration. The current deployment fails because:

1. **Primary**: Missing `ors.engine.source_file` environment variable
2. **Secondary**: Missing `ORS_CONFIG_LOCATION` environment variable
3. **Tertiary**: Using deprecated `BUILD_GRAPHS` flag
4. **Additional**: Port and path mismatches

The fix should prioritize adding the environment variables, as this is the most critical difference and aligns with how the entrypoint script is designed to work.

