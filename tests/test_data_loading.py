"""Tests for data loading and filtering functions."""
import pytest
import pandas as pd
from pathlib import Path
from analyze_population import (
    load_and_filter_data,
    find_column_by_pattern,
    filter_by_level
)


class TestDataLoading:
    """Test data loading and filtering functionality."""
    
    def test_load_and_filter_data_success(self, sample_excel_file):
        """Test successful loading and filtering of facilities."""
        # Explicitly pass target_levels to avoid config dependency
        df = load_and_filter_data(str(sample_excel_file), target_levels=['4', '5', '6'])
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2  # Should filter to Level 4 and 5 only
        assert 'Hospital A' in df['Facility Name'].values
        assert 'Hospital B' in df['Facility Name'].values
        assert 'Clinic C' not in df['Facility Name'].values  # Level 3 should be filtered out
    
    def test_load_and_filter_data_missing_level_column(self, tmp_path):
        """Test error handling when level column is missing."""
        # Create Excel file without level column
        data = {
            'Facility Name': ['Hospital A'],
            'Latitude': [-1.2921],
            'Longitude': [36.8219]
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / "no_level.xlsx"
        df.to_excel(file_path, index=False)
        
        with pytest.raises(ValueError, match="Could not find.*Level.*column"):
            load_and_filter_data(str(file_path))
    
    def test_load_and_filter_data_empty_file(self, tmp_path):
        """Test handling of empty Excel file."""
        file_path = tmp_path / "empty.xlsx"
        empty_df = pd.DataFrame()
        empty_df.to_excel(file_path, index=False)
        
        with pytest.raises((ValueError, KeyError)):
            load_and_filter_data(str(file_path))
    
    def test_load_and_filter_data_nonexistent_file(self):
        """Test error handling for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            load_and_filter_data("nonexistent_file.xlsx")
    
    def test_filter_target_levels(self, sample_facilities_data):
        """Test that filtering correctly identifies target levels."""
        target_levels = ['4', '5', '6']
        filtered = filter_by_level(sample_facilities_data, 'Keph level', target_levels)
        
        assert len(filtered) == 2
        assert all('Level 4' in str(level) or 'Level 5' in str(level) 
                  for level in filtered['Keph level'].values)
    
    def test_column_name_normalization(self, tmp_path):
        """Test that column names are normalized (stripped of whitespace)."""
        data = {
            ' Facility Name ': ['Hospital A'],
            'Latitude': [-1.2921],
            'Longitude': [36.8219],
            'Keph level': ['Level 4']
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / "whitespace.xlsx"
        df.to_excel(file_path, index=False)
        
        result = load_and_filter_data(str(file_path))
        assert ' Facility Name ' not in result.columns
        assert 'Facility Name' in result.columns or any('Facility' in c for c in result.columns)
    
    def test_find_column_by_pattern(self, sample_facilities_data):
        """Test column finding by pattern."""
        # Test finding latitude column
        lat_col = find_column_by_pattern(sample_facilities_data, ['lat'], None)
        assert lat_col == 'Latitude'
        
        # Test finding level column
        level_col = find_column_by_pattern(sample_facilities_data, ['level'], None)
        assert level_col == 'Keph level'
        
        # Test with default
        missing_col = find_column_by_pattern(sample_facilities_data, ['nonexistent'], 'default')
        assert missing_col == 'default'
        
        # Test with no match and no default
        missing_col = find_column_by_pattern(sample_facilities_data, ['nonexistent'], None)
        assert missing_col is None

