# Deployment Status

## Current Situation

The deployment has been configured with all the fixes from the investigation:
- ✅ Environment variables set (`ors.engine.source_file`, `ORS_ENGINE_SOURCE_FILE`)
- ✅ Config file updated with correct paths
- ✅ Source file copied to container (287.58 MB)
- ✅ File is accessible in container at `/home/ors/files/kenya-latest.osm.pbf`
- ✅ All volume mounts configured correctly

## Persistent Error

ORS 9.5.1 is still reporting:
```
Exception at RoutingProfileManager initialization: 
java.lang.IllegalStateException: Couldn't load from existing folder: graphs/driving-car 
but also cannot use file for DataReader as it wasn't specified!
```

## Analysis

1. **Environment variables are set**: Confirmed via `docker-compose exec ors-app env`
2. **File exists**: Confirmed via `ls -lh /home/ors/files/kenya-latest.osm.pbf` (287.6M)
3. **Config file loaded**: Logs show `/home/ors/config/ors-config.yml` is loaded
4. **Config file has source_file**: Confirmed `source_file: /home/ors/files/kenya-latest.osm.pbf`

## Possible Causes

1. **ORS 9.5.1 Bug**: The application may not be reading environment variables correctly
2. **Path Resolution Issue**: ORS might be looking for relative path `graphs/driving-car` instead of absolute
3. **Version Incompatibility**: v8.1.0 worked, but 9.5.1 may have breaking changes
4. **Spring Boot Property Binding**: ORS 9.5.1 might require different property format

## Next Steps to Try

1. **Use v8.1.0** (known working version from reference):
   ```yaml
   image: openrouteservice/openrouteservice:v8.1.0
   ```

2. **Check ORS 9.5.1 release notes** for breaking changes

3. **Try different environment variable format**:
   - Spring Boot uses `ORS_ENGINE_SOURCE_FILE` (already tried)
   - Or system properties via JAVA_OPTS (already tried)

4. **Verify graphs directory structure** - ensure it's writable and correct

5. **Check if preparation_mode affects source_file reading**

## Recommendation

Since the reference deployment (v8.1.0) worked and we've replicated its configuration pattern, but ORS 9.5.1 is still failing, the issue appears to be a version-specific problem with ORS 9.5.1.

**Suggested action**: Try using v8.1.0 (the working version) to confirm the configuration is correct, then investigate ORS 9.5.1-specific issues.

