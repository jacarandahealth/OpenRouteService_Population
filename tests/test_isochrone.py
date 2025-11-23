"""Tests for isochrone generation."""
import pytest
from unittest.mock import Mock, patch
from analyze_population import (
    get_isochrone_with_retry,
    validate_coordinates,
    InvalidCoordinateError
)


class TestCoordinateValidation:
    """Test coordinate validation."""
    
    def test_validate_coordinates_valid(self):
        """Test validation of valid coordinates."""
        lat, lon = validate_coordinates(-1.2921, 36.8219)
        assert lat == -1.2921
        assert lon == 36.8219
    
    def test_validate_coordinates_invalid_lat_too_high(self):
        """Test validation fails for latitude > 90."""
        with pytest.raises(InvalidCoordinateError, match="Latitude out of range"):
            validate_coordinates(91, 36.8219)
    
    def test_validate_coordinates_invalid_lat_too_low(self):
        """Test validation fails for latitude < -90."""
        with pytest.raises(InvalidCoordinateError, match="Latitude out of range"):
            validate_coordinates(-91, 36.8219)
    
    def test_validate_coordinates_invalid_lon_too_high(self):
        """Test validation fails for longitude > 180."""
        with pytest.raises(InvalidCoordinateError, match="Longitude out of range"):
            validate_coordinates(-1.2921, 181)
    
    def test_validate_coordinates_invalid_lon_too_low(self):
        """Test validation fails for longitude < -180."""
        with pytest.raises(InvalidCoordinateError, match="Longitude out of range"):
            validate_coordinates(-1.2921, -181)
    
    def test_validate_coordinates_none(self):
        """Test validation fails for None coordinates."""
        with pytest.raises(InvalidCoordinateError, match="cannot be None"):
            validate_coordinates(None, 36.8219)
        
        with pytest.raises(InvalidCoordinateError, match="cannot be None"):
            validate_coordinates(-1.2921, None)
    
    def test_validate_coordinates_string_conversion(self):
        """Test that string coordinates are converted to float."""
        lat, lon = validate_coordinates("-1.2921", "36.8219")
        assert isinstance(lat, float)
        assert isinstance(lon, float)
        assert lat == -1.2921
        assert lon == 36.8219


class TestIsochroneGeneration:
    """Test isochrone generation with retry logic."""
    
    def test_get_isochrone_success(self, mock_ors_client, sample_isochrone_response):
        """Test successful isochrone generation."""
        result = get_isochrone_with_retry(mock_ors_client, -1.2921, 36.8219)
        
        assert result is not None
        assert result == sample_isochrone_response
        mock_ors_client.isochrones.assert_called_once()
    
    def test_get_isochrone_retry_on_failure(self, mocker):
        """Test retry logic on failure."""
        mock_client = Mock()
        # First two calls fail, third succeeds
        mock_client.isochrones.side_effect = [
            Exception("Network error"),
            Exception("Timeout"),
            {"type": "FeatureCollection", "features": []}
        ]
        
        with patch('analyze_population.time.sleep'):  # Don't actually sleep in tests
            result = get_isochrone_with_retry(mock_client, -1.2921, 36.8219, max_retries=3)
        
        assert result is not None
        assert mock_client.isochrones.call_count == 3
    
    def test_get_isochrone_max_retries_exceeded(self, mocker):
        """Test that None is returned when max retries exceeded."""
        mock_client = Mock()
        mock_client.isochrones.side_effect = Exception("Persistent error")
        
        with patch('analyze_population.time.sleep'):
            result = get_isochrone_with_retry(mock_client, -1.2921, 36.8219, max_retries=2)
        
        assert result is None
        assert mock_client.isochrones.call_count == 2
    
    def test_get_isochrone_correct_parameters_single_range(self, mock_ors_client):
        """Test that isochrone is called with correct parameters for single range."""
        get_isochrone_with_retry(mock_ors_client, -1.2921, 36.8219, ranges_sec=[7200])
        
        call_args = mock_ors_client.isochrones.call_args
        assert call_args is not None
        
        kwargs = call_args.kwargs
        assert kwargs['locations'] == [[36.8219, -1.2921]]  # Note: lon, lat order
        assert kwargs['profile'] == 'driving-car'
        assert kwargs['range'] == [7200]
    
    def test_get_isochrone_multiple_ranges(self, mock_ors_client):
        """Test that isochrone is called with correct parameters for multiple ranges."""
        ranges = [900, 1800, 2700]  # 15, 30, 45 minutes
        get_isochrone_with_retry(mock_ors_client, -1.2921, 36.8219, ranges_sec=ranges)
        
        call_args = mock_ors_client.isochrones.call_args
        assert call_args is not None
        
        kwargs = call_args.kwargs
        assert kwargs['locations'] == [[36.8219, -1.2921]]
        assert kwargs['profile'] == 'driving-car'
        assert kwargs['range'] == ranges
    
    def test_get_isochrone_backward_compatibility_int(self, mock_ors_client):
        """Test backward compatibility with single int range."""
        get_isochrone_with_retry(mock_ors_client, -1.2921, 36.8219, ranges_sec=3600)
        
        call_args = mock_ors_client.isochrones.call_args
        assert call_args is not None
        
        kwargs = call_args.kwargs
        assert kwargs['range'] == [3600]  # Should be converted to list

