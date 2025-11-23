# ORS 9.5.1 Configuration Documentation Review

## Key Findings from Documentation Review

### 1. Configuration System Overhaul
**Major Change**: ORS 9.5.1 introduced a configuration restructuring:
- Properties are now divided into `*.build` and `*.service` categories
- `*.build`: Properties affecting graph building (like `source_file`)
- `*.service`: Properties relevant for running the service to handle API requests

**Implication**: The `source_file` property might need to be in a `build` section rather than directly under `engine`.

### 2. Graph Management (Beta)
- New `ors.engine.graph_management` section for scheduled downloads/activations
- Not directly related to our issue, but shows configuration structure changes

### 3. Multiple Profile Support
- ORS now supports multiple individually configured routing profiles
- Profile defaults set using `profile_default` property
- Individual profiles can override defaults

### 4. Docker Compose Overhaul
- Docker setup completely revamped in recent versions
- Improved container logging, documentation, mount permissions
- Smaller image sizes

## Potential Solution Based on Documentation

The configuration structure might need to be:

```yaml
ors:
  engine:
    build:
      source_file: /home/ors/files/kenya-latest.osm.pbf
      graphs_root_path: ./graphs
      graphs_data_access: RAM_STORE
    service:
      # Service-time settings
    profiles:
      driving-car:
        enabled: true
        # profile settings
```

OR possibly:

```yaml
ors:
  engine:
    source_file: /home/ors/files/kenya-latest.osm.pbf  # This might be deprecated
    build:
      source_file: /home/ors/files/kenya-latest.osm.pbf
```

## Current Configuration Issue

Our current config has:
```yaml
ors:
  engine:
    source_file: /home/ors/files/kenya-latest.osm.pbf
    graphs_root_path: ./graphs
    # ... other settings
```

This might be the old format, and ORS 9.5.1 might require:
```yaml
ors:
  engine:
    build:
      source_file: /home/ors/files/kenya-latest.osm.pbf
      graphs_root_path: ./graphs
```

## Next Steps

1. Try restructuring config with `build` section
2. Check if `source_file` needs to be under `engine.build` instead of `engine`
3. Verify if `preparation_mode` is still valid or replaced by build/service distinction

## Documentation References
- Main Configuration Docs: https://giscience.github.io/openrouteservice/run-instance/configuration/
- Graph Management: https://giscience.github.io/openrouteservice/run-instance/configuration/engine/graph-management
- GitHub Releases: https://github.com/GIScience/openrouteservice/releases

## Summary of Documentation Review

### Key Configuration Changes in 9.5.1:
1. **Configuration Restructuring**: Properties divided into `*.build` and `*.service` categories
2. **Graph Management**: New beta feature for scheduled graph updates
3. **Multiple Profile Support**: Enhanced support for multiple profiles with individual configs
4. **Docker Overhaul**: Improved container setup and documentation

### Current Issue Analysis:
- The `source_file` configuration appears correct based on example configs
- Error suggests ORS finds `graphs/driving-car` directory but can't load from it
- ORS then tries to use source_file but reports it "wasn't specified"
- This might be a bug in ORS 9.5.1 where source_file isn't being read from config

### Recommendation:
Given that:
1. Config file structure matches examples
2. File exists and is accessible
3. Config file is being loaded (confirmed in logs)
4. Multiple configuration attempts have failed

This appears to be a **potential bug in ORS 9.5.1** where the `source_file` property is not being properly read from the configuration file, even when correctly specified.

**Next Action**: Create a GitHub issue with full details for the ORS team to investigate.

