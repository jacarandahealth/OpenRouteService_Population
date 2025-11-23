# ORS Config File Comparison

## Reference Config (Working - v8.1.0) vs Current Config (Not Working - 9.5.1)

### Key Structural Differences

#### 1. Profile Structure (CRITICAL)

**Reference (v8.1.0)**:
```yaml
profiles:
  car:
    profile: driving-car
    enabled: true
    # ... other settings
```

- Profile key is `car` (custom name)
- Profile type specified via `profile: driving-car`
- This is the v8.1.0 pattern

**Current (9.5.1)**:
```yaml
profiles:
  driving-car:
    enabled: true
    # ... other settings
```

- Profile key directly matches profile type: `driving-car`
- No separate `profile:` field
- This is the 9.5.1 pattern (confirmed working per troubleshooting notes)

**Status**: Current structure is correct for 9.5.1, but differs from reference.

#### 2. Source File Path

**Reference**:
```yaml
source_file: /home/ors/files/kenya-latest.osm.pbf
```

**Current**:
```yaml
source_file: /home/ors/files/kenya-latest.osm.pbf
```

**Status**: ✅ Same path - correct

#### 3. Graphs Root Path

**Reference**:
```yaml
graphs_root_path: ./graphs
```

**Current**:
```yaml
graphs_root_path: ./graphs
```

**Status**: ✅ Same path - correct

#### 4. Preparation Mode

**Reference**:
```yaml
preparation_mode: false
```

**Current**:
```yaml
preparation_mode: true
```

**Impact**: 
- `false`: Normal operation mode, serves requests
- `true`: Preparation mode, builds graphs only
- Current setting may prevent serving requests

#### 5. Profile Default Settings

**Reference**:
```yaml
profile_default:
  enabled: false
  elevation: true
  elevation_smoothing: false
  encoder_flags_size: 8
  instructions: true
  optimize: false
  traffic: false
  maximum_distance: 100000
  # ... many more default settings
```

**Current**:
```yaml
profile_default:
  enabled: false
```

**Impact**: Current config has minimal profile_default settings. Reference has comprehensive defaults that profiles inherit.

#### 6. Profile Configuration Detail

**Reference** - Full car profile config:
```yaml
car:
  profile: driving-car
  encoder_options:
    turn_costs: true
    block_fords: false
    use_acceleration: true
  preparation:
    min_network_size: 200
    methods:
      ch:
        enabled: true
        threads: 1
        weightings: fastest
      lm:
        enabled: false
        threads: 1
        weightings: fastest,shortest
        landmarks: 16
      core:
        enabled: true
        threads: 1
        weightings: fastest,shortest
        landmarks: 64
        lmsets: highways;allow_all
  execution:
    methods:
      lm:
        active_landmarks: 6
      core:
        active_landmarks: 6
  ext_storages:
    WayCategory:
    HeavyVehicle:
    WaySurfaceType:
    RoadAccessRestrictions:
      use_for_warnings: true
  enabled: true
```

**Current** - Minimal car profile config:
```yaml
driving-car:
  enabled: true
  encoder_options:
    turn_costs: true
    block_fords: false
    use_acceleration: true
  preparation:
    min_network_size: 200
    methods:
      ch:
        enabled: true
        threads: 1
        weightings: fastest
      core:
        enabled: true
        threads: 1
        weightings: fastest,shortest
        landmarks: 64
        lmsets: highways;allow_all
  execution:
    methods:
      core:
        active_landmarks: 6
  ext_storages:
    WayCategory:
    HeavyVehicle:
    WaySurfaceType:
    Tollways:
    RoadAccessRestrictions:
      use_for_warnings: true
```

**Differences**:
- Current has `Tollways` in ext_storages (not in reference)
- Reference has `lm` (landmark) method enabled/disabled, current doesn't specify
- Current is missing some preparation method details

#### 7. Server Configuration

**Reference**:
```yaml
server:
  port: 8082
  error:
    whitelabel:
      enabled: false
  servlet:
    context-path: /ors
  tomcat:
    keep-alive-timeout: 30000
```

**Current**:
```yaml
server:
  port: 8080
  servlet:
    context-path: /ors
```

**Impact**: Port mismatch! Reference uses 8082, current uses 8080. This matches the docker-compose port mapping issue.

#### 8. Endpoints Configuration

**Reference**: Full endpoint configuration with all settings
**Current**: Minimal endpoint configuration

**Status**: Current may be missing some endpoint settings, but core endpoints are enabled.

#### 9. Elevation Configuration

**Reference**:
```yaml
elevation:
  preprocessed: false
  data_access: MMAP
  cache_clear: false
  provider: multi
  cache_path: ./elevation_cache
```

**Current**:
```yaml
elevation:
  preprocessed: false
  data_access: MMAP
  cache_clear: false
  provider: multi
  cache_path: ./elevation_cache
```

**Status**: ✅ Identical - correct

#### 10. Logging Configuration

**Reference**: Full logging configuration
**Current**: No logging configuration in minimal config

**Impact**: May affect debugging ability

## Summary of Critical Differences

1. **Preparation Mode**: Current uses `true`, reference uses `false`
   - This may prevent ORS from serving requests

2. **Server Port**: Current uses `8080`, reference uses `8082`
   - Must match docker-compose port mapping

3. **Profile Structure**: Different but both correct for their respective versions
   - Reference: `car.profile: driving-car` (v8.1.0)
   - Current: `driving-car:` directly (v9.5.1)

4. **Profile Default Settings**: Current has minimal defaults
   - May be missing important inherited settings

5. **Profile Detail**: Current has less detailed preparation/execution methods
   - May affect routing performance/features

## Configuration Validity

The current config structure appears valid for ORS 9.5.1, but:
- `preparation_mode: true` may be preventing normal operation
- Port mismatch with docker-compose could cause issues
- Missing environment variable for `source_file` is the primary issue (from docker-compose analysis)

## Recommendation

The config file itself is likely fine, but:
1. Set `preparation_mode: false` to allow serving requests
2. Ensure server port matches docker-compose mapping (8082 if using reference pattern)
3. Most importantly: Add `ors.engine.source_file` environment variable in docker-compose.yml

