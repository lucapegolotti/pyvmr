"""Tests for catalog management."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from pyvmr.catalog import CatalogManager


# Sample CSV data for testing
SAMPLE_PROJECTS_CSV = """Name,Legacy Name,Image Number,Sex,Age,Species,Ethnicity,Animal,Anatomy,Disease,Procedure,Images,Paths,Segmentations,Models,Meshes,Simulations,Notes,DOI,Citation,Image Manufacturer,Image Type,Image Source,Image Modality,Results,Date Added,Order Uploaded,Model Creator
0001_H_AO_SVD,0063_1001,0001,Male,3.00,Human,-,-,Aorta,Single Ventricle Defect,None,1,1,1,1,1,1,Test note,10.1111/test,Test Citation,GE,CT,Hospital,CT,1,27 Dec 2021,1,Test Creator
0002_H_AO_H,0064_1002,0002,Female,25.00,Human,Caucasian,-,Aorta,Healthy,None,1,1,1,1,1,0,,,,,,,,0,28 Dec 2021,2,Another Creator"""

SAMPLE_RESULTS_CSV = """Model Name,Full Simulation File Name,Model Image Number,Short Simulation File Name,Legacy Simulation File Name,Simulation Fidelity,Simulation Method,Simulation Condition,Results Type,Results File Type,Simulation Creator,Notes
0001_H_AO_SVD,0001_H_AO_SVD_3D_RIGID_VTP.zip,0001,3D RIGID VTP,legacy_name,3D,RIGID,Normal,Flow,VTP,Creator,Note"""

SAMPLE_FILE_SIZES_CSV = """Name,Size
svprojects/0001_H_AO_SVD.zip,169774061
svprojects/0002_H_AO_H.zip,50000000
svresults/0001_H_AO_SVD/0001_H_AO_SVD_3D_RIGID_VTP.zip,5000000"""

SAMPLE_ABBREVIATIONS_CSV = """Category,Short Name,Long Name
Species,H,Human
Species,A,Animal
Anatomy,AO,Aorta"""

SAMPLE_ADDITIONAL_CSV = """Name,Notes,Citation
SVCardiacDemoModel,Demo model,Citation here"""


class TestCatalogManager:
    """Tests for CatalogManager class."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """Create a temporary cache directory."""
        return tmp_path / "cache"

    @pytest.fixture
    def mock_responses(self):
        """Set up mock HTTP responses."""
        def create_mock_response(text):
            mock = MagicMock()
            mock.text = text
            mock.raise_for_status = MagicMock()
            return mock
        return create_mock_response

    def test_init_creates_cache_dir(self, temp_cache_dir):
        """Test that initialization creates cache directory."""
        manager = CatalogManager(cache_dir=str(temp_cache_dir))
        assert temp_cache_dir.exists()

    @patch("pyvmr.catalog.requests.get")
    def test_get_models(self, mock_get, temp_cache_dir, mock_responses):
        """Test fetching and parsing models."""
        # Set up mock responses
        def side_effect(url, **kwargs):
            if "svprojects" in url:
                return mock_responses(SAMPLE_PROJECTS_CSV)
            elif "file_sizes" in url:
                return mock_responses(SAMPLE_FILE_SIZES_CSV)
            return mock_responses("")

        mock_get.side_effect = side_effect

        manager = CatalogManager(cache_dir=str(temp_cache_dir))
        models = manager.get_models()

        assert len(models) == 2
        assert models[0].name == "0001_H_AO_SVD"
        assert models[0].species == "Human"
        assert models[0].anatomy == "Aorta"
        assert models[0].age == 3.0
        assert models[0].has_simulations is True
        assert models[0].file_size == 169774061

    @patch("pyvmr.catalog.requests.get")
    def test_get_simulations(self, mock_get, temp_cache_dir, mock_responses):
        """Test fetching and parsing simulations."""
        def side_effect(url, **kwargs):
            if "svresults" in url:
                return mock_responses(SAMPLE_RESULTS_CSV)
            elif "file_sizes" in url:
                return mock_responses(SAMPLE_FILE_SIZES_CSV)
            return mock_responses("")

        mock_get.side_effect = side_effect

        manager = CatalogManager(cache_dir=str(temp_cache_dir))
        sims = manager.get_simulations()

        assert len(sims) == 1
        assert sims[0].model_name == "0001_H_AO_SVD"
        assert sims[0].method == "RIGID"
        assert sims[0].file_size == 5000000

    @patch("pyvmr.catalog.requests.get")
    def test_get_abbreviations(self, mock_get, temp_cache_dir, mock_responses):
        """Test fetching and parsing abbreviations."""
        mock_get.return_value = mock_responses(SAMPLE_ABBREVIATIONS_CSV)

        manager = CatalogManager(cache_dir=str(temp_cache_dir))
        abbrs = manager.get_abbreviations()

        assert len(abbrs) == 3
        assert abbrs[0].category == "Species"
        assert abbrs[0].short_name == "H"
        assert abbrs[0].long_name == "Human"

    @patch("pyvmr.catalog.requests.get")
    def test_get_file_sizes(self, mock_get, temp_cache_dir, mock_responses):
        """Test fetching and parsing file sizes."""
        mock_get.return_value = mock_responses(SAMPLE_FILE_SIZES_CSV)

        manager = CatalogManager(cache_dir=str(temp_cache_dir))
        sizes = manager.get_file_sizes()

        assert sizes["svprojects/0001_H_AO_SVD.zip"] == 169774061
        assert sizes["svprojects/0002_H_AO_H.zip"] == 50000000

    @patch("pyvmr.catalog.requests.get")
    def test_caching(self, mock_get, temp_cache_dir, mock_responses):
        """Test that data is cached."""
        mock_get.return_value = mock_responses(SAMPLE_FILE_SIZES_CSV)

        manager = CatalogManager(cache_dir=str(temp_cache_dir))

        # First call should fetch
        sizes1 = manager.get_file_sizes()
        assert mock_get.call_count == 1

        # Second call should use cache
        sizes2 = manager.get_file_sizes()
        assert mock_get.call_count == 1  # No additional call

        assert sizes1 == sizes2

    @patch("pyvmr.catalog.requests.get")
    def test_force_refresh(self, mock_get, temp_cache_dir, mock_responses):
        """Test force refresh bypasses cache."""
        mock_get.return_value = mock_responses(SAMPLE_FILE_SIZES_CSV)

        manager = CatalogManager(cache_dir=str(temp_cache_dir))

        # First call
        manager.get_file_sizes()
        assert mock_get.call_count == 1

        # Force refresh
        manager.get_file_sizes(force_refresh=True)
        assert mock_get.call_count == 2

    @patch("pyvmr.catalog.requests.get")
    def test_cache_info(self, mock_get, temp_cache_dir, mock_responses):
        """Test cache info reporting."""
        mock_get.return_value = mock_responses(SAMPLE_FILE_SIZES_CSV)

        manager = CatalogManager(cache_dir=str(temp_cache_dir))
        manager.get_file_sizes()

        info = manager.cache_info()

        assert str(temp_cache_dir) in info["cache_dir"]
        assert info["cache_ttl_hours"] == 24
        assert "file_sizes" in info["resources"]
        assert info["resources"]["file_sizes"]["valid"] is True


class TestCatalogParsing:
    """Tests for CSV parsing edge cases."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create a CatalogManager with temp cache."""
        return CatalogManager(cache_dir=str(tmp_path / "cache"))

    def test_parse_bool_field(self, manager):
        """Test boolean field parsing."""
        assert manager._parse_bool_field(1) is True
        assert manager._parse_bool_field(0) is False
        assert manager._parse_bool_field("1") is True
        assert manager._parse_bool_field("yes") is True
        assert manager._parse_bool_field(None) is False

    def test_parse_float_field(self, manager):
        """Test float field parsing."""
        assert manager._parse_float_field(3.5) == 3.5
        assert manager._parse_float_field("3.5") == 3.5
        assert manager._parse_float_field(None) is None
        assert manager._parse_float_field("invalid") is None

    def test_parse_int_field(self, manager):
        """Test integer field parsing."""
        assert manager._parse_int_field(42) == 42
        assert manager._parse_int_field("42") == 42
        assert manager._parse_int_field(42.9) == 42
        assert manager._parse_int_field(None) is None

    def test_parse_date_field(self, manager):
        """Test date field parsing."""
        result = manager._parse_date_field("27 Dec 2021")
        assert result is not None
        assert result.year == 2021
        assert result.month == 12
        assert result.day == 27

        assert manager._parse_date_field(None) is None
        assert manager._parse_date_field("invalid") is None

    def test_parse_str_field(self, manager):
        """Test string field parsing."""
        assert manager._parse_str_field("test") == "test"
        assert manager._parse_str_field("  test  ") == "test"
        assert manager._parse_str_field(None) == ""
