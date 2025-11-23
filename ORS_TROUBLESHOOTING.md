# ORS 9.5.1 Configuration Troubleshooting

## Current Error
```
Exception at RoutingProfileManager initialization: 
java.lang.IllegalStateException: Couldn't load from existing folder: graphs/driving-car 
but also cannot use file for DataReader as it wasn't specified!
```

## Status
- ✅ **Fixed**: "Expected single profile in config" error - resolved by using `driving-car:` directly as profile key
- ❌ **Current Issue**: ORS cannot read `source_file` from configuration, even though it's correctly specified

## Configuration Attempts
1. ✅ Single profile structure: `profiles: driving-car:` - Works (no "Expected single profile" error)
2. ✅ Config file loading: Confirmed via logs - `/home/ors/config/ors-config.yml` is loaded
3. ✅ File exists: `/home/ors/files/kenya-latest.osm.pbf` (327MB) - verified accessible
4. ❌ Source file not being read: ORS reports "cannot use file for DataReader as it wasn't specified"

## Current Configuration (`ors-config-9.5.1-fixed.yml`)
```yaml
ors:
  engine:
    source_file: /home/ors/files/kenya-latest.osm.pbf
    graphs_root_path: ./graphs
    preparation_mode: true
    profiles:
      driving-car:
        enabled: true
```

## GitHub Issues Search Results
- **No specific issues found** for this exact error message in public searches
- Error appears to be uncommon or version-specific to 9.5.1
- Related searches for "source_file" and "DataReader" didn't return relevant results
- **Recommendation**: Create a new GitHub issue with full error details and configuration

## Attempted Solutions
1. ✅ Environment variable `ORS_ENGINE_SOURCE_FILE` - **Did not resolve**
2. ✅ Config file `source_file` specification - **Not being read by ORS**
3. ✅ Multiple path formats (relative/absolute) - **No change**
4. ✅ BUILD_GRAPHS true/false - **No change**
5. ✅ preparation_mode true/false - **No change**

## Possible Causes
1. **Configuration format issue**: ORS 9.5.1 might require `source_file` to be specified differently
2. **Environment variable override**: Docker environment might be overriding config file settings
3. **Profile-specific source_file**: May need to specify `source_file` at profile level instead of engine level
4. **Path resolution**: Relative vs absolute path issues with `graphs_root_path`

## Next Steps to Try

### 1. Try Environment Variable for Source File
Set `ORS_ENGINE_SOURCE_FILE` environment variable in docker-compose.yml:
```yaml
environment:
  - ORS_ENGINE_SOURCE_FILE=/home/ors/files/kenya-latest.osm.pbf
  - BUILD_GRAPHS=True
```

### 2. Check if Source File Needs to be at Profile Level
Try specifying source_file within the profile configuration:
```yaml
profiles:
  driving-car:
    source_file: /home/ors/files/kenya-latest.osm.pbf
    enabled: true
```

### 3. Verify Docker Volume Mount
Ensure the file mount in docker-compose.yml is correct:
```yaml
volumes:
  - ./kenya-latest.osm.pbf:/home/ors/files/kenya-latest.osm.pbf
```

### 4. Try Absolute Path for graphs_root_path
```yaml
graphs_root_path: /home/ors/ors-core/data/graphs
```

### 5. Check ORS 9.5.1 Release Notes
Review changelog for configuration changes in version 9.5.1:
- https://github.com/GIScience/openrouteservice/releases

### 6. Post Issue on GitHub
If none of the above work, create a GitHub issue with:
- ORS version: 9.5.1
- Error message: Full stack trace
- Configuration file: Redacted version
- Docker setup: docker-compose.yml structure
- Logs: Relevant log excerpts

## Resources
- ORS Documentation: https://giscience.github.io/openrouteservice/
- GitHub Repository: https://github.com/GIScience/openrouteservice
- Community Forum: https://ask.openrouteservice.org/
- Docker Hub: https://hub.docker.com/r/openrouteservice/openrouteservice

## Current Working Config Structure
The following structure successfully avoids "Expected single profile" error:
- `profile_default.enabled: false`
- Single profile: `profiles.driving-car.enabled: true`
- Profile key matches profile name: `driving-car` (not `car` with `profile: driving-car`)

