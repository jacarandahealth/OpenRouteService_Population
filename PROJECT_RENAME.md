# Project Rename: OpenRouteService_Population

## Changes Made

The project has been renamed from "Isochrone_GoogleMaps" to "OpenRouteService_Population".

### Files Updated

1. **README.md** - Updated project title and description
2. **config.yaml** - Updated configuration file header comment

### Directory Rename

To complete the rename, you'll need to rename the project directory:

**Windows:**
```powershell
# Navigate to parent directory
cd C:\Users\JayPatel\EngineeringProjects
# Rename directory
Rename-Item -Path "Isochrone_GoogleMaps" -NewName "OpenRouteService_Population"
# Navigate back into the renamed directory
cd OpenRouteService_Population
```

**Or manually:**
1. Close any open files/IDEs
2. Navigate to `C:\Users\JayPatel\EngineeringProjects\`
3. Right-click on `Isochrone_GoogleMaps` folder
4. Select "Rename"
5. Enter: `OpenRouteService_Population`

### Git Considerations

If you've already committed, the git history will remain intact after renaming the directory. You may want to update the remote URL if it references the old name:

```bash
# After renaming the directory, check if remote needs updating
git remote -v
# If remote URL contains old name, update it:
# git remote set-url origin <new-url>
```

### Note

The workspace path in your IDE/editor will need to be updated after renaming the directory. You may need to:
- Close the current workspace
- Open the newly renamed directory as the workspace

