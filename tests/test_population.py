"""Tests for population calculation using Google Earth Engine."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from analyze_population import calculate_population_gee


class TestPopulationCalculation:
    """Test population calculation with GEE."""
    
    def test_calculate_population_success(self, mock_gee):
        """Test successful population calculation."""
        geometry = {
            "type": "Polygon",
            "coordinates": [[[36.8219, -1.2921], [36.8300, -1.2921], 
                           [36.8300, -1.3000], [36.8219, -1.3000], 
                           [36.8219, -1.2921]]]
        }
        
        # Mock the GEE chain
        mock_collection = mock_gee.ImageCollection.return_value
        mock_image = mock_collection.first.return_value
        mock_geometry = mock_gee.Geometry.return_value
        mock_stats = Mock()
        mock_pop = Mock()
        mock_pop.getInfo.return_value = 50000
        mock_stats.get.return_value = mock_pop
        mock_image.reduceRegion.return_value = mock_stats
        
        result = calculate_population_gee(geometry)
        
        assert result == 50000.0
        assert isinstance(result, float)
        mock_gee.Geometry.assert_called_once_with(geometry)
        mock_image.reduceRegion.assert_called_once()
    
    def test_calculate_population_none_result(self, mock_gee):
        """Test handling of None population result."""
        geometry = {"type": "Polygon", "coordinates": []}
        
        mock_collection = mock_gee.ImageCollection.return_value
        mock_image = mock_collection.first.return_value
        mock_geometry = mock_gee.Geometry.return_value
        mock_stats = Mock()
        mock_stats.get.return_value.getInfo.return_value = None
        mock_image.reduceRegion.return_value = mock_stats
        
        result = calculate_population_gee(geometry)
        
        assert result is None
    
    def test_calculate_population_error_handling(self, mock_gee):
        """Test error handling in population calculation."""
        geometry = {"type": "Polygon", "coordinates": []}
        
        mock_collection = mock_gee.ImageCollection.return_value
        mock_image = mock_collection.first.return_value
        mock_image.reduceRegion.side_effect = Exception("GEE API error")
        
        result = calculate_population_gee(geometry)
        
        assert result is None
    
    def test_calculate_population_custom_parameters(self, mock_gee):
        """Test population calculation with custom parameters."""
        geometry = {"type": "Polygon", "coordinates": []}
        
        mock_collection = mock_gee.ImageCollection.return_value
        mock_image = mock_collection.first.return_value
        mock_geometry = mock_gee.Geometry.return_value
        mock_stats = Mock()
        mock_pop = Mock()
        mock_pop.getInfo.return_value = 100000
        mock_stats.get.return_value = mock_pop
        mock_image.reduceRegion.return_value = mock_stats
        
        result = calculate_population_gee(geometry, dataset_name="custom/dataset", scale=200, max_pixels=500000000)
        
        assert result == 100000.0
        # Verify custom parameters were used
        mock_gee.ImageCollection.assert_called_with("custom/dataset")
        call_kwargs = mock_image.reduceRegion.call_args.kwargs
        assert call_kwargs['scale'] == 200
        assert call_kwargs['maxPixels'] == 500000000

