# Docker Entrypoint Script Analysis

## How ORS Reads source_file Configuration

### Key Finding: Environment Variable Precedence

The docker-entrypoint.sh script (from reference deployment) reveals the critical configuration loading order:

### Configuration Loading Sequence

1. **Environment Variable Check (Line 187)**
   ```bash
   ors_engine_source_file=$(env | grep "^ors\.engine\.source_file=" | awk -F '=' '{print $2}')
   ```
   - First checks for environment variable `ors.engine.source_file`
   - If found, uses this value directly

2. **Config File Fallback (Lines 241-247)**
   ```bash
   if [[ -z "${ors_engine_source_file}" ]]; then
     if [[ "${ors_config_location}" = *.yml ]]; then
       ors_engine_source_file=$(extract_config_info "${ors_config_location}" '.ors.engine.source_file')
     elif [[ "${ors_config_location}" = *.json ]]; then
       ors_engine_source_file=$(extract_config_info "${ors_config_location}" '.ors.services.routing.sources[0]')
     fi
   fi
   ```
   - Only if environment variable is NOT set, extracts from YAML config file
   - Uses `.ors.engine.source_file` path in YAML
   - For JSON configs (deprecated), uses `.ors.services.routing.sources[0]`

3. **Precedence Statement (Line 264)**
   ```bash
   info "Any ENV variables will have precedence over configuration variables from config files."
   ```
   - **Explicit confirmation**: Environment variables override config file values

### Critical Implications

1. **Reference Deployment Strategy**
   - Sets `ors.engine.source_file` as environment variable in docker-compose.yml
   - This ensures the value is always found, regardless of config file issues
   - Takes precedence over any config file value

2. **Current Deployment Issue**
   - Does NOT set `ors.engine.source_file` as environment variable
   - Relies entirely on YAML config file
   - If config file parsing fails or path is wrong, source_file will be empty

3. **Why Current Deployment Fails**
   - ORS entrypoint script checks env var first → not found
   - Falls back to config file → may not be reading correctly in 9.5.1
   - Result: `ors_engine_source_file` is empty
   - ORS reports: "cannot use file for DataReader as it wasn't specified!"

### Additional Configuration Loading

The script also loads:
- `ors.engine.graphs_root_path` (line 183)
- `ors.engine.elevation.cache_path` (line 185)
- Both follow same pattern: env var first, then config file

### Config File Location Resolution (Lines 210-230)

1. Checks `ORS_CONFIG_LOCATION` environment variable
2. If not set, looks for `/home/ors/config/ors-config.yml`
3. If not found, copies example config file

**Current Issue**: 
- Current deployment mounts config to `/home/ors/config` but may not set `ORS_CONFIG_LOCATION`
- Script may not find config file at expected location

### Graph Rebuild Logic (Lines 276-279)

```bash
if [ "${ors_rebuild_graphs}" = "true" ]; then
  # Remove existing graphs
fi
```

- Uses `ors_rebuild_graphs` variable (set from `REBUILD_GRAPHS` env var)
- Current deployment uses deprecated `BUILD_GRAPHS` which may not work correctly

## Root Cause Summary

The current deployment fails because:

1. **Missing Environment Variable**: `ors.engine.source_file` is not set as env var
2. **Config File May Not Be Found**: `ORS_CONFIG_LOCATION` not set, and mount path may be wrong
3. **Deprecated Flag**: Using `BUILD_GRAPHS` instead of `REBUILD_GRAPHS`
4. **Path Mismatch**: Volume mounts use different paths than reference deployment

## Solution

Match the reference deployment pattern:
1. Add `ors.engine.source_file` as environment variable
2. Add `ORS_CONFIG_LOCATION` environment variable
3. Change `BUILD_GRAPHS` to `REBUILD_GRAPHS`
4. Verify config file mount path matches expected location

