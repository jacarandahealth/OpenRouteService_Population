# ORS Deployment Investigation Summary

## Investigation Complete

All todos have been completed. The investigation has identified why the reference deployment worked and why the current deployment fails.

## Key Finding

**The reference deployment (v8.1.0) worked because it used environment variables for critical configuration, particularly `ors.engine.source_file`. The current deployment (9.5.1/latest) fails because it relies solely on YAML config files, and the ORS entrypoint script prioritizes environment variables over config files.**

## Root Cause

The ORS docker-entrypoint.sh script:
1. First checks for environment variable `ors.engine.source_file`
2. Only if not found, extracts from YAML config file
3. Explicitly states: "Any ENV variables will have precedence over configuration variables from config files"

**Current deployment does NOT set this environment variable**, causing ORS to fail reading the source_file.

## Critical Differences

1. **Missing Environment Variable**: `ors.engine.source_file` not set in docker-compose.yml
2. **Missing Config Location**: `ORS_CONFIG_LOCATION` not set
3. **Deprecated Flag**: Using `BUILD_GRAPHS` instead of `REBUILD_GRAPHS`
4. **Port Mismatch**: Docker-compose and config file ports don't align
5. **Preparation Mode**: Set to `true` (builds only) instead of `false` (serves requests)
6. **Path Structure**: Different volume mount paths than reference

## Documentation Created

1. **DOCKER_COMPOSE_COMPARISON.md** - Detailed comparison of docker-compose files
2. **ENTRYPOINT_SCRIPT_ANALYSIS.md** - Analysis of how ORS reads configuration
3. **CONFIG_FILE_COMPARISON.md** - Comparison of YAML config files
4. **INVESTIGATION_FINDINGS.md** - Complete findings document
5. **FIX_IMPLEMENTATION_PLAN.md** - Actionable fix plan with code examples

## Quick Fix

The minimal fix to resolve the immediate error:

1. Add to docker-compose.yml environment section:
   ```yaml
   - ors.engine.source_file=/home/ors/files/kenya-latest.osm.pbf
   - REBUILD_GRAPHS=True
   - ORS_CONFIG_LOCATION=/home/ors/config/ors-config.yml
   ```

2. Change in config file:
   ```yaml
   preparation_mode: false
   ```

3. Fix port mapping to match config file port.

## Next Steps

See **FIX_IMPLEMENTATION_PLAN.md** for complete implementation steps with code examples.

