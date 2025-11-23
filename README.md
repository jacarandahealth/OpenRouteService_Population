# OpenRouteService Population Analysis

A comprehensive Python toolkit for generating driving-time isochrones around health facilities in Kenya and calculating population estimates within those catchment areas. This project combines **OpenRouteService (ORS)** for routing/isochrone generation and **Google Earth Engine (GEE)** for population data analysis.

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [OpenRouteService Setup](#-openrouteservice-ors-setup)
- [Deployment](#-deployment)
- [API Reference](#-api-reference)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

## 🚀 Project Overview

This project automates the process of analyzing health facility accessibility by:

1. **Generating Isochrones**: Calculate the geographic area reachable within specified driving times (e.g., 15, 30, 45 minutes) using OpenRouteService
2. **Population Analysis**: Use Google Earth Engine's WorldPop dataset to estimate the total population within each catchment area
3. **Visualization**: Create interactive HTML maps showing facilities, isochrones, and population data
4. **Batch Processing**: Analyze multiple facilities from Excel files or process individual facilities programmatically

### Use Cases

- **Health Facility Planning**: Assess population coverage for existing or proposed health facilities
- **Accessibility Analysis**: Identify underserved areas based on driving time
- **Resource Allocation**: Prioritize facility improvements based on population served
- **Catchment Area Mapping**: Visualize and document service areas for health facilities

## ✨ Features

- ✅ **Multi-facility Support**: Process single facilities or batch process from Excel files
- ✅ **Flexible Time Ranges**: Configure multiple isochrone time ranges (15, 30, 45 minutes, etc.)
- ✅ **Population Estimation**: Accurate population counts using WorldPop 2020 data
- ✅ **Interactive Maps**: Folium-based HTML maps with facility markers and isochrone overlays
- ✅ **Self-hosted ORS**: Deploy your own OpenRouteService instance to avoid API limits
- ✅ **GCP Deployment**: Automated scripts for deploying ORS on Google Cloud Platform
- ✅ **Comprehensive Logging**: Detailed logs for debugging and audit trails
- ✅ **Configuration Management**: YAML-based config with environment variable overrides
- ✅ **Error Handling**: Robust error handling with retry logic and informative messages
- ✅ **Test Suite**: Comprehensive pytest-based test coverage

## 📂 Project Structure

```
OpenRouteService_Population/
├── analyze_population.py          # Main script for batch processing facilities from Excel
├── create_kakamega_isochrone.py   # Example script for processing specific facilities
├── generate_single_isochrone.py  # Utility for generating single isochrones
├── config.yaml                    # Main configuration file
├── config.py                      # Configuration management module
├── logger.py                       # Logging configuration
├── auth_gee.py                    # Google Earth Engine authentication
├── check_ors.py                   # ORS server health check utility
├── get_gcp_ors_ip.py              # GCP instance IP management
├── deploy_ors.ps1                 # PowerShell script for GCP deployment
├── startup-script.sh              # VM startup script for ORS installation
├── docker-compose.yml             # Docker Compose configuration for ORS
├── config/
│   └── ors-config.yml            # OpenRouteService configuration
├── tests/                         # Test suite
│   ├── test_config.py
│   ├── test_data_loading.py
│   ├── test_isochrone.py
│   ├── test_population.py
│   └── test_logger.py
├── files/                         # Data files
│   └── kenya-latest.osm.pbf      # OpenStreetMap data for Kenya
├── logs/                          # Log files
│   └── analysis.log
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── DEPLOYMENT_INSTRUCTIONS.md     # Detailed deployment guide
├── ORS_TROUBLESHOOTING.md        # ORS-specific troubleshooting
└── KENYA_DATA_SOURCE.md          # Data source documentation
```

## 🛠️ Prerequisites

### Required

- **Python 3.8+** (Python 3.9+ recommended)
- **Google Earth Engine Account**: [Sign up here](https://earthengine.google.com/)
- **Google Cloud SDK (gcloud)**: Required for GCP deployment (optional if using existing ORS instance)
- **Docker & Docker Compose**: Required for local ORS deployment (optional)

### Recommended

- **Git**: For version control
- **Virtual Environment**: For Python dependency isolation
- **Text Editor/IDE**: VS Code, PyCharm, or similar

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/jacarandahealth/OpenRouteService_Population.git
cd OpenRouteService_Population
```

### 2. Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Authenticate Google Earth Engine

The project requires GEE authentication to access the WorldPop dataset:

```bash
# Option 1: Using the provided script
python auth_gee.py

# Option 2: Using earthengine CLI directly
earthengine authenticate
```

Follow the browser prompts to authorize your account. This only needs to be done once per machine.

### 5. Configure the Project

Edit `config.yaml` to set your ORS server URL and other parameters (see [Configuration](#-configuration) section below).

## 🧩 Configuration

Configuration is managed through `config.yaml` with support for environment variable overrides.

### Configuration File (`config.yaml`)

Key configuration sections:

#### OpenRouteService Settings
```yaml
ors:
  base_url: "http://34.134.47.254:8080/ors"  # Your ORS server URL
  health_url: "http://34.134.47.254:8080/ors/v2/health"
  timeout: 30                                 # Request timeout in seconds
  retry_attempts: 3                           # Number of retry attempts
  retry_delay: 1                              # Initial retry delay (seconds)
```

#### File Paths
```yaml
files:
  input_file: "KMHFR_MNCH_Facilities_Only.xlsx"  # Input Excel file
  output_csv: "population_analysis_results.csv"  # Output CSV file
  output_map: "isochrone_map.html"              # Output HTML map
```

#### Analysis Parameters
```yaml
analysis:
  range_seconds: [900, 1800, 2700]  # Isochrone time ranges (15, 30, 45 min)
  target_levels: ["4", "5", "6"]    # Facility levels to filter
  sleep_between_requests: 0.5       # Delay between API calls (seconds)
```

#### Google Earth Engine Settings
```yaml
gee:
  dataset: "WorldPop/GP/100m/pop"  # WorldPop Global Population dataset
  scale: 100                        # Resolution in meters
  max_pixels: 1000000000            # Maximum pixels for computation
```

#### Map Visualization
```yaml
map:
  center_lat: 0.0236                # Map center latitude (Kenya)
  center_lon: 37.9062               # Map center longitude
  zoom_start: 6                     # Initial zoom level
  isochrone_colors:                 # Color mapping by time range
    15: "#ff0000"                   # Red for 15 minutes
    30: "#ff8800"                   # Orange for 30 minutes
    45: "#ffaa00"                   # Yellow for 45 minutes
  isochrone_opacity: 0.3            # Isochrone fill opacity
```

### Environment Variables

You can override any configuration value using environment variables. Convert nested keys to uppercase with underscores:

- `ors.base_url` → `ORS_BASE_URL`
- `files.input_file` → `FILES_INPUT_FILE`
- `analysis.range_seconds` → `ANALYSIS_RANGE_SECONDS`
- `gee.dataset` → `GEE_DATASET`

**Example:**
```bash
export ORS_BASE_URL="http://your-server:8080/ors"
export FILES_INPUT_FILE="/path/to/facilities.xlsx"
python analyze_population.py
```

## 🏃‍♂️ Usage

### Batch Processing from Excel File

Process multiple facilities from an Excel file:

```bash
python analyze_population.py
```

**Input Requirements:**
- Excel file must contain columns with:
  - **Level**: Facility level (e.g., "4", "5", "6")
  - **Latitude/Lat**: Facility latitude
  - **Longitude/Lon/Lng**: Facility longitude
  - **Name**: Facility name (optional but recommended)

**Output:**
- `population_analysis_results.csv`: CSV file with facility data and population estimates
- `isochrone_map.html`: Interactive map showing all facilities and isochrones
- `logs/analysis.log`: Detailed execution logs

### Processing Specific Facilities

Use `create_kakamega_isochrone.py` as a template for processing specific facilities:

```python
# Edit the facilities list in create_kakamega_isochrone.py
facilities = [
    {
        "name": "Kakamega County Referral Hospital",
        "lat": 0.2745556,
        "lon": 34.7582332,
        "range_seconds": 2700  # 45 minutes
    },
    {
        "name": "Wajir County Referral Hospital",
        "lat": 1.74742,
        "lon": 40.06259,
        "range_seconds": 2700
    }
]
```

Then run:
```bash
python create_kakamega_isochrone.py
```

**Output:**
- `kenya_facilities_isochrone_map.html`: Interactive map with all specified facilities
- `facilities_isochrone_results.json`: JSON results with coordinates and population data

### Single Isochrone Generation

Generate a single isochrone for testing:

```bash
python generate_single_isochrone.py
```

## 🗺️ OpenRouteService (ORS) Setup

This project uses a **self-hosted** OpenRouteService instance to avoid public API rate limits and costs.

### Option A: Use Existing Instance

The default configuration points to a GCP-hosted instance:
```
http://34.134.47.254:8080/ors
```

**Verify connectivity:**
```bash
python check_ors.py
```

This will test:
- Server reachability
- Health endpoint response
- Isochrone API functionality

### Option B: Deploy Your Own Instance

#### Local Deployment (Docker)

1. **Ensure Docker is running:**
   ```bash
   docker ps
   ```

2. **Start ORS container:**
   ```bash
   docker-compose up -d
   ```

3. **Monitor logs:**
   ```bash
   docker-compose logs -f ors-app
   ```

4. **Update config.yaml:**
   ```yaml
   ors:
     base_url: "http://localhost:8080/ors"
   ```

#### GCP Deployment

1. **Prerequisites:**
   - Google Cloud SDK installed and authenticated
   - Billing enabled on GCP project
   - Appropriate permissions for Compute Engine

2. **Deploy using PowerShell script:**
   ```powershell
   ./deploy_ors.ps1
   ```

   The script will:
   - Create a GCP Compute Engine instance
   - Install Docker and dependencies
   - Download Kenya OSM data
   - Start OpenRouteService container
   - Configure firewall rules

3. **Get instance IP address:**
   ```bash
   # Option 1: Using helper script
   python get_gcp_ors_ip.py --update-config
   
   # Option 2: Using gcloud CLI
   gcloud compute instances describe ors-kenya-server \
     --zone=us-central1-a \
     --format="get(networkInterfaces[0].accessConfigs[0].natIP)"
   ```

4. **Wait for graph building:**
   - Initial graph building takes 15-20 minutes
   - Monitor progress: `docker-compose logs -f ors-app`
   - Look for "Graph build complete" message

### Finding Your GCP Instance IP Address

**Option 1: Helper Script (Recommended)**
```bash
# Get IP address only
python get_gcp_ors_ip.py

# Get IP and update config.yaml automatically
python get_gcp_ors_ip.py --update-config

# List all GCP instances
python get_gcp_ors_ip.py --list
```

**Option 2: GCP Console**
1. Go to [GCP Console](https://console.cloud.google.com/compute/instances)
2. Find instance `ors-kenya-server`
3. Check "External IP" column

**Option 3: gcloud CLI**
```bash
gcloud compute instances describe ors-kenya-server \
  --zone=us-central1-a \
  --format="get(networkInterfaces[0].accessConfigs[0].natIP)"
```

## 🚀 Deployment

### ORS Version

This project is configured for **OpenRouteService v8.1.0**. The configuration files (`docker-compose.yml`, `config/ors-config.yml`) are optimized for this version.

### Docker Compose Configuration

The `docker-compose.yml` file defines:
- ORS container with Kenya OSM data
- Port mapping (8080:8080)
- Volume mounts for data and graphs
- Environment variables for configuration

### ORS Configuration

The `config/ors-config.yml` file contains:
- Server port settings
- Engine profiles (driving-car enabled)
- Source file path for OSM data
- Graph storage location

See `DEPLOYMENT_INSTRUCTIONS.md` for detailed deployment steps.

## 📚 API Reference

### Main Scripts

#### `analyze_population.py`

Main script for batch processing facilities from Excel files.

**Functionality:**
- Loads facilities from Excel file
- Filters by facility level
- Generates isochrones for each facility
- Calculates population within catchment areas
- Creates interactive map visualization
- Exports results to CSV

**Usage:**
```bash
python analyze_population.py
```

#### `create_kakamega_isochrone.py`

Script for processing specific facilities with custom coordinates.

**Functionality:**
- Processes multiple facilities from a Python list
- Generates isochrones for each facility
- Calculates population estimates
- Creates combined map visualization
- Exports results to JSON

**Usage:**
```bash
python create_kakamega_isochrone.py
```

### Utility Scripts

#### `check_ors.py`

Health check utility for ORS server.

**Usage:**
```bash
python check_ors.py
```

**Checks:**
- Server connectivity
- Health endpoint response
- Isochrone API functionality

#### `get_gcp_ors_ip.py`

GCP instance IP management utility.

**Usage:**
```bash
# Get IP address
python get_gcp_ors_ip.py

# Get IP and update config.yaml
python get_gcp_ors_ip.py --update-config

# List all instances
python get_gcp_ors_ip.py --list
```

### Core Modules

#### `config.py`

Configuration management module.

**Functions:**
- `get_config()`: Load configuration from YAML and environment variables
- Properties: `ors_base_url`, `gee_dataset`, `input_file`, etc.

#### `logger.py`

Logging configuration module.

**Functions:**
- `get_logger(name)`: Get configured logger instance
- Supports file and console logging with different levels

#### `auth_gee.py`

Google Earth Engine authentication.

**Functions:**
- `initialize_gee()`: Initialize and authenticate GEE
- Handles authentication state checking

## 🧪 Testing

The project includes a comprehensive test suite using pytest.

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test Files

```bash
pytest tests/test_config.py
pytest tests/test_data_loading.py
pytest tests/test_isochrone.py
pytest tests/test_population.py
pytest tests/test_logger.py
```

### Run with Coverage

```bash
pytest --cov=. --cov-report=html tests/
```

### Test Structure

Tests use mocks for external dependencies (ORS, GEE) so they can run without network access:
- **test_config.py**: Configuration loading and environment variable overrides
- **test_data_loading.py**: Excel file parsing and data validation
- **test_isochrone.py**: Isochrone generation and API interaction
- **test_population.py**: Population calculation logic
- **test_logger.py**: Logging configuration and output

## ⚠️ Troubleshooting

### Google Earth Engine Issues

**Problem: Authentication Error**
```
ee.ee_exception.EEException: Not logged in
```

**Solution:**
```bash
python auth_gee.py
# or
earthengine authenticate
```

**Problem: Dataset Not Found**
```
EEException: ImageCollection asset 'WorldPop/...' not found
```

**Solution:**
- Check dataset name in `config.yaml`
- Verify GEE account has access to WorldPop datasets
- Use recommended dataset: `WorldPop/GP/100m/pop`

**Problem: Population Returns Zero**
- Ensure isochrone geometry is valid
- Check that GEE dataset covers the area of interest
- Verify scale parameter (try increasing to 250m)
- Check GEE logs for computation errors

### OpenRouteService Issues

**Problem: Connection Refused**
```
ConnectionError: Cannot reach ORS server
```

**Solutions:**
1. **Check server status:**
   ```bash
   python check_ors.py
   ```

2. **Verify IP address:**
   ```bash
   python get_gcp_ors_ip.py --update-config
   ```

3. **Check GCP instance status:**
   ```bash
   gcloud compute instances describe ors-kenya-server --zone=us-central1-a
   ```

4. **Start stopped instance:**
   ```bash
   gcloud compute instances start ors-kenya-server --zone=us-central1-a
   ```

5. **Check firewall rules:**
   ```bash
   gcloud compute firewall-rules list --filter='name:allow-ors-8080'
   ```

6. **View instance logs:**
   ```bash
   gcloud compute instances get-serial-port-output ors-kenya-server --zone=us-central1-a
   ```

**Problem: Graph Building Not Complete**
- Initial graph building takes 15-20 minutes
- Check Docker logs: `docker-compose logs -f ors-app`
- Look for "Graph build complete" message
- Service may be accessible but not fully ready

**Problem: Timeout Errors**
- Increase timeout in `config.yaml`: `ors.timeout: 60`
- Check server load and network connectivity
- Verify OSM data file is complete

### Data Loading Issues

**Problem: Missing Columns**
```
KeyError: 'level' not found
```

**Solution:**
- Ensure Excel file has required columns:
  - `level` or `Level` (facility level)
  - `lat` or `latitude` or `Latitude`
  - `lon` or `longitude` or `Longitude` or `lng`
  - `name` or `Name` (optional but recommended)
- Column names are case-insensitive

**Problem: Invalid Coordinates**
```
ValueError: Invalid latitude/longitude
```

**Solution:**
- Verify coordinates are within valid ranges:
  - Latitude: -90 to 90
  - Longitude: -180 to 180
- Check for missing or null coordinate values
- Ensure coordinates are numeric, not text

### Configuration Issues

**Problem: Config File Not Found**
```
FileNotFoundError: config.yaml
```

**Solution:**
- Ensure `config.yaml` exists in project root
- Check file path if using custom location
- Verify YAML syntax is valid

**Problem: Environment Variables Not Working**
- Use uppercase with underscores: `ORS_BASE_URL` not `ors.base_url`
- Restart terminal/IDE after setting environment variables
- Check for typos in variable names

### Performance Issues

**Problem: Slow Population Calculation**
- GEE computations can take time for large areas
- Consider increasing `gee.scale` to reduce computation time
- Check `gee.max_pixels` setting
- Monitor GEE quota usage

**Problem: Memory Issues**
- Process facilities in smaller batches
- Increase system memory if processing many facilities
- Use `analysis.sleep_between_requests` to throttle API calls

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes:**
   - Follow existing code style
   - Add tests for new features
   - Update documentation as needed
4. **Test your changes:**
   ```bash
   pytest tests/
   ```
5. **Commit with clear messages:**
   ```bash
   git commit -m "Add feature: description"
   ```
6. **Push and create pull request**

### Code Style

- Follow PEP 8 Python style guide
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and small

### Testing Requirements

- All new features must include tests
- Maintain or improve test coverage
- Tests should be fast and independent

## 📄 License

[Add license information here]

## 🙏 Acknowledgments

- **OpenRouteService**: For routing and isochrone generation
- **Google Earth Engine**: For population data access
- **WorldPop**: For global population datasets
- **OpenStreetMap**: For road network data

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation in `DEPLOYMENT_INSTRUCTIONS.md` and `ORS_TROUBLESHOOTING.md`
- Review logs in `logs/analysis.log` for detailed error information

---

**Last Updated:** November 2024
**Version:** 1.0.0
