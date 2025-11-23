"""Pytest fixtures for test suite."""
import pytest
import pandas as pd
import json
from pathlib import Path
import tempfile


@pytest.fixture
def sample_facilities_data():
    """Sample facilities DataFrame for testing."""
    data = {
        'Facility Name': ['Hospital A', 'Hospital B', 'Clinic C'],
        'Latitude': [-1.2921, -1.3000, -1.2800],
        'Longitude': [36.8219, 36.8300, 36.8100],
        'Keph level': ['Level 4', 'Level 5', 'Level 3'],
        'County': ['Nairobi', 'Nairobi', 'Nairobi']
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_excel_file(sample_facilities_data, tmp_path):
    """Create a temporary Excel file with sample data."""
    file_path = tmp_path / "test_facilities.xlsx"
    sample_facilities_data.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def sample_isochrone_response():
    """Sample ORS isochrone response."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [36.8219, -1.2921],
                        [36.8300, -1.2921],
                        [36.8300, -1.3000],
                        [36.8219, -1.3000],
                        [36.8219, -1.2921]
                    ]]
                },
                "properties": {
                    "group_index": 0,
                    "value": 3600,
                    "center": [36.8219, -1.2921]
                }
            }
        ]
    }


@pytest.fixture
def mock_ors_client(mocker, sample_isochrone_response):
    """Mock OpenRouteService client."""
    mock_client = mocker.Mock()
    mock_client.isochrones.return_value = sample_isochrone_response
    return mock_client


@pytest.fixture
def mock_gee(mocker):
    """Mock Google Earth Engine."""
    mock_ee = mocker.patch('analyze_population.ee')
    mock_image = mocker.Mock()
    mock_collection = mocker.Mock()
    mock_collection.first.return_value = mock_image
    
    # Mock reduceRegion
    mock_stats = mocker.Mock()
    mock_stats.get.return_value.getInfo.return_value = 50000
    mock_image.reduceRegion.return_value = mock_stats
    
    mock_ee.ImageCollection.return_value = mock_collection
    return mock_ee

