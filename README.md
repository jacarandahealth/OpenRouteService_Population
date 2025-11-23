# OpenRouteService Population Analysis

This project automates the process of generating 1-hour driving time isochrones for health facilities in Kenya and calculating the total population within those areas. It leverages a self-hosted **OpenRouteService (ORS)** instance for isochrone generation and **Google Earth Engine (GEE)** for population data analysis.

## 🚀 Project Overview

The main goal is to assess accessibility to health facilities (Level 4, 5, and 6) by:
1.  **Filtering Facilities**: Reading a list of facilities from an Excel file and filtering for specific levels.
2.  **Generating Isochrones**: Calculating the area reachable within a 1-hour drive using OpenRouteService.
3.  **Calculating Population**: Using Google Earth Engine's `WorldPop/GP/100m/population/2020` dataset to sum the population within the generated isochrone polygons.
4.  **Visualizing**: Creating an interactive HTML map (`isochrone_map.html`) showing the facilities and their catchment areas.

## 📂 Project Structure

*   `analyze_population.py`: The main Python script that orchestrates the data loading, isochrone generation, population calculation, and mapping.
*   `config.yaml`: Configuration file with all settings (ORS URL, file paths, analysis parameters).
*   `config.py`: Configuration management module that loads settings from YAML and environment variables.
*   `logger.py`: Logging configuration module for structured logging.
*   `auth_gee.py`: Google Earth Engine authentication utility.
*   `check_ors.py`: Utility script to check the health status of the ORS server.
*   `get_gcp_ors_ip.py`: Helper script to get the external IP address of GCP-deployed ORS instance.
*   `deploy_ors.ps1`: PowerShell script to deploy a Google Cloud Compute Engine instance running OpenRouteService with Kenya OSM data.
*   `startup-script.sh`: Bash script used by the VM deployment to install Docker, download OSM data, and start the ORS container.
*   `requirements.txt`: Python dependencies.
*   `tests/`: Unit test suite (pytest).
*   `KMHFR_MNCH_Facilities_Only.xlsx`: (Input) Excel file containing health facility data.

## 🛠️ Prerequisites

*   **Python 3.8+**
*   **Google Earth Engine Account**: You need access to GEE. [Sign up here](https://earthengine.google.com/).
*   **Google Cloud SDK (gcloud)**: Required if you plan to deploy the ORS server using the provided scripts.

## ⚙️ Setup & Installation

1.  **Clone the repository** (or navigate to the project directory).

2.  **Install Python Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure the Project**:
    - Edit `config.yaml` to set your ORS server URL, file paths, and other parameters.
    - Alternatively, set environment variables (see Configuration section below).
    - The default configuration uses relative paths from the project root.

4.  **Authenticate Google Earth Engine**:
    The script requires GEE authentication to access the WorldPop dataset.
    ```bash
    python auth_gee.py
    ```
    Or use the command line:
    ```bash
    earthengine authenticate
    ```
    Follow the instructions in the browser to authorize your account.

## 🗺️ OpenRouteService (ORS) Setup

This project is configured to use a **self-hosted** ORS instance to avoid public API rate limits and costs.

### Option A: Use Existing Instance
The default configuration in `config.yaml` points to:
`http://34.134.47.254:8080/ors`

Ensure this server is running and accessible. You can check it with:
```bash
python check_ors.py
```

### Option B: Deploy Your Own Instance
If you need to deploy a new instance on Google Cloud:
1.  Ensure you have `gcloud` installed and authenticated.
2.  Run the deployment script:
    ```powershell
    ./deploy_ors.ps1
    ```
3.  Wait for the instance to initialize (approx. 15-20 mins for graph building).
4.  The deployment script will display the instance IP address. Update `config.yaml` with this IP, or run:
    ```bash
    python get_gcp_ors_ip.py --update-config
    ```

### Finding Your GCP Instance IP Address

If you need to find the IP address of an existing GCP instance:

**Option 1: Using the helper script (Recommended)**
```bash
# Get the IP address
python get_gcp_ors_ip.py

# Get IP and automatically update config.yaml
python get_gcp_ors_ip.py --update-config

# List all GCP instances to find yours
python get_gcp_ors_ip.py --list
```

**Option 2: Using gcloud CLI directly**
```bash
gcloud compute instances describe ors-kenya-server --zone=us-central1-a --format="get(networkInterfaces[0].accessConfigs[0].natIP)"
```

**Option 3: Via GCP Console**
1. Go to [GCP Console](https://console.cloud.google.com/compute/instances)
2. Find your instance (`ors-kenya-server`)
3. Check the "External IP" column

## 🏃‍♂️ Usage

1.  **Prepare Data**: Ensure your Excel file with facility data is in the project directory (or update the path in `config.yaml`).
2.  **Run the Analysis**:
    ```bash
    python analyze_population.py
    ```
3.  **View Results**:
    *   **Console**: Progress and population counts are logged to console (INFO level).
    *   **Log File**: Detailed logs are saved to `logs/analysis.log` (DEBUG level).
    *   **CSV**: Results are saved to `population_analysis_results.csv` (configurable in `config.yaml`).
    *   **Map**: Open `isochrone_map.html` in your browser to view the interactive map.

## 🧩 Configuration

Configuration is managed through `config.yaml` with support for environment variable overrides.

### Configuration File (`config.yaml`)

Edit `config.yaml` to customize:
*   **ORS Settings**: `ors.base_url`, `ors.timeout`, `ors.retry_attempts`
*   **File Paths**: `files.input_file`, `files.output_csv`, `files.output_map` (relative to project root or absolute)
*   **Analysis Parameters**: `analysis.range_seconds`, `analysis.target_levels`, `analysis.sleep_between_requests`
*   **GEE Settings**: `gee.dataset`, `gee.scale`, `gee.max_pixels`
*   **Logging**: `logging.level`, `logging.file`, etc.
*   **Map Settings**: `map.center_lat`, `map.center_lon`, `map.zoom_start`, etc.

### Environment Variables

You can override any configuration value using environment variables. Convert nested keys to uppercase with underscores:
- `ors.base_url` → `ORS_BASE_URL`
- `files.input_file` → `FILES_INPUT_FILE`
- `analysis.range_seconds` → `ANALYSIS_RANGE_SECONDS`

Example:
```bash
export ORS_BASE_URL="http://your-server:8080/ors"
export FILES_INPUT_FILE="/path/to/facilities.xlsx"
python analyze_population.py
```

See `.env.example` (if available) for a complete list of environment variables.

## 🧪 Testing

The project includes a comprehensive test suite using pytest. Run tests with:

```bash
pytest tests/
```

Or run specific test files:
```bash
pytest tests/test_data_loading.py
pytest tests/test_isochrone.py
pytest tests/test_population.py
pytest tests/test_config.py
```

Tests use mocks for external dependencies (ORS, GEE) so they can run without network access.

## ⚠️ Troubleshooting

*   **GEE Authentication Error**: If you see `ee.ee_exception.EEException: Not logged in`, run `python auth_gee.py` or `earthengine authenticate` again.
*   **ORS Connection Error**: 
    - **GCP Instance IP Changed**: GCP instances may get new IP addresses if stopped/started. Get the current IP:
      ```bash
      python get_gcp_ors_ip.py --update-config
      ```
    - **Instance Not Running**: Check if your GCP instance is running:
      ```bash
      gcloud compute instances describe ors-kenya-server --zone=us-central1-a
      ```
      If stopped, start it:
      ```bash
      gcloud compute instances start ors-kenya-server --zone=us-central1-a
      ```
    - **Check Server Status**: Test connectivity:
      ```bash
      python check_ors.py
      ```
    - **Firewall Rules**: Verify port 8080 is open:
      ```bash
      gcloud compute firewall-rules list --filter='name:allow-ors-8080'
      ```
    - **Instance Logs**: Check if ORS container is running:
      ```bash
      gcloud compute instances get-serial-port-output ors-kenya-server --zone=us-central1-a
      ```
    - **Graph Building**: The initial graph building process can take 15-20 minutes. The instance may be accessible but ORS may not be ready yet.
*   **Missing Columns**: If the script fails to find columns in the Excel file, ensure your Excel file has columns containing "level", "lat"/"latitude", "lon"/"longitude", and "name" (case-insensitive).
*   **Configuration Issues**: 
    - Check that `config.yaml` exists and is valid YAML.
    - Verify file paths are correct (relative to project root or absolute).
    - Check logs in `logs/analysis.log` for detailed error messages.
*   **Invalid Coordinates**: The script validates coordinates. Ensure lat/lon values are within valid ranges (-90 to 90 for latitude, -180 to 180 for longitude).
