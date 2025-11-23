# Files to Clean Up

## Summary
This document lists files that can be safely removed to clean up the repository.

## 1. Redundant ORS Config Files (Keep only: `config/ors-config.yml` and `ors-config-v8.1.0.yml`)
Since we're using ORS v8.1.0, we can remove all the v9.x config files and experimental configs:

- `ors-config-9.5.1-build-structure.yml` ❌ (v9.x, not needed)
- `ors-config-9.5.1-fixed.yml` ❌ (v9.x, not needed)
- `ors-config-car-only.yml` ❌ (experimental)
- `ors-config-final.yml` ❌ (experimental)
- `ors-config-kenya-minimal.yml` ❌ (experimental)
- `ors-config-kenya-single.yml` ❌ (experimental)
- `ors-config-kenya.yml` ❌ (experimental)
- `ors-config-single-car.yml` ❌ (experimental)
- `ors-config-source-example.yml` ❌ (example file)
- `ors-config-working.yml` ❌ (temporary/working file)
- `ors-config.yml` (root level) ❌ (duplicate - actual config is in `config/ors-config.yml`)

**Keep:**
- `config/ors-config.yml` ✅ (active config)
- `ors-config-v8.1.0.yml` ✅ (reference for v8.1.0)

## 2. Redundant Docker Compose Files (Keep only: `docker-compose.yml`)
- `docker-compose-fixed.yml` ❌ (temporary fix file)
- `docker-compose-v8.yml` ❌ (temporary file created during migration)

**Keep:**
- `docker-compose.yml` ✅ (active file)

## 3. Historical/Investigation Documentation (Can archive or remove)
These are historical investigation documents that may not be needed anymore:

- `CONFIG_FILE_COMPARISON.md` ❌ (historical investigation)
- `DEPLOYMENT_STATUS.md` ❌ (historical status)
- `DEPLOYMENT_SUCCESS.md` ❌ (historical success doc)
- `DOCKER_COMPOSE_COMPARISON.md` ❌ (historical comparison)
- `ENTRYPOINT_SCRIPT_ANALYSIS.md` ❌ (historical analysis)
- `FIX_IMPLEMENTATION_PLAN.md` ❌ (historical plan)
- `IMPLEMENTATION_COMPLETE.md` ❌ (historical completion doc)
- `INVESTIGATION_FINDINGS.md` ❌ (historical investigation)
- `INVESTIGATION_SUMMARY.md` ❌ (historical summary)
- `ORS_9.5.1_CONFIG_FINDINGS.md` ❌ (v9.x findings, not relevant)
- `PROJECT_RENAME.md` ❌ (historical rename doc)

**Keep:**
- `README.md` ✅ (main documentation)
- `DEPLOYMENT_INSTRUCTIONS.md` ✅ (useful deployment guide)
- `ORS_TROUBLESHOOTING.md` ✅ (useful troubleshooting guide)
- `KENYA_DATA_SOURCE.md` ✅ (useful data source info)

## 4. Example/Test Files
- `files/example-heidelberg.osm.gz` ❌ (example file)
- `files/example-heidelberg.test.pbf` ❌ (test file)
- `config/example-ors-config.env` ❌ (example file)
- `config/example-ors-config.yml` ❌ (example file)

**Keep:**
- `files/kenya-latest.osm.pbf` ✅ (actual data file, but should be in .gitignore)

## 5. Generated/Cache Files (Should be in .gitignore - already are)
These are already in .gitignore but still exist in the repo:

- `__pycache__/` ❌ (Python cache)
- `elevation_cache/` ❌ (generated cache)
- `graphs/` ❌ (generated graphs)
- `logs/` ❌ (log files)
- `kakamega_isochrone.json` ❌ (generated output)
- `kakamega_isochrone_map.html` ❌ (generated output)
- `kenya-latest.osm.pbf\` (directory) ❌ (duplicate/empty?)

## 6. Reference Deployment Directory
- `reference_deployment/` ❌ (entire directory - appears to be a reference copy)

## 7. Temporary/Fix Scripts (May not be needed)
- `fix_ors_container.ps1` ❌ (temporary fix script)
- `fix_ors_container.sh` ❌ (temporary fix script)
- `update_ors_config.sh` ❌ (may not be needed if config is stable)

**Keep:**
- `deploy_ors.ps1` ✅ (useful deployment script)
- `startup-script.sh` ✅ (used in GCP deployment)

## 8. Duplicate Files
- `kenya-latest.osm.pbf\` (appears to be an empty directory) ❌

## Files to Keep (Essential)
- All Python scripts (`*.py`)
- `config.yaml` (main config)
- `config/ors-config.yml` (active ORS config)
- `ors-config-v8.1.0.yml` (reference)
- `docker-compose.yml` (active)
- `requirements.txt`
- `README.md`
- `DEPLOYMENT_INSTRUCTIONS.md`
- `ORS_TROUBLESHOOTING.md`
- `KENYA_DATA_SOURCE.md`
- `deploy_ors.ps1`
- `startup-script.sh`
- `tests/` directory
- `.gitignore`

## Cleanup Commands

```bash
# Remove redundant config files
rm ors-config-9.5.1-*.yml
rm ors-config-car-only.yml
rm ors-config-final.yml
rm ors-config-kenya*.yml
rm ors-config-single-car.yml
rm ors-config-source-example.yml
rm ors-config-working.yml
rm ors-config.yml  # root level duplicate

# Remove redundant docker-compose files
rm docker-compose-fixed.yml
rm docker-compose-v8.yml

# Remove historical documentation
rm CONFIG_FILE_COMPARISON.md
rm DEPLOYMENT_STATUS.md
rm DEPLOYMENT_SUCCESS.md
rm DOCKER_COMPOSE_COMPARISON.md
rm ENTRYPOINT_SCRIPT_ANALYSIS.md
rm FIX_IMPLEMENTATION_PLAN.md
rm IMPLEMENTATION_COMPLETE.md
rm INVESTIGATION_FINDINGS.md
rm INVESTIGATION_SUMMARY.md
rm ORS_9.5.1_CONFIG_FINDINGS.md
rm PROJECT_RENAME.md

# Remove example files
rm files/example-heidelberg.*
rm config/example-ors-config.*

# Remove temporary scripts
rm fix_ors_container.ps1
rm fix_ors_container.sh
rm update_ors_config.sh

# Remove reference deployment
rm -rf reference_deployment/

# Remove generated/cache files (already in .gitignore)
rm -rf __pycache__/
rm -rf elevation_cache/
rm -rf graphs/
rm -rf logs/
rm kakamega_isochrone.*
rm -rf kenya-latest.osm.pbf\  # if it's an empty directory
```

