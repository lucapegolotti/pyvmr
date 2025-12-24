"""Tests for filter utilities."""

import pytest
from pyvmr.models import Model, SimulationResult
from pyvmr.filters import (
    filter_models,
    filter_simulations,
    get_unique_values,
    summarize_models,
)


@pytest.fixture
def sample_models():
    """Create sample models for testing."""
    return [
        Model(
            name="0001_H_AO_SVD",
            species="Human",
            anatomy="Aorta",
            disease="Single Ventricle Defect",
            sex="Male",
            age=3.0,
            has_simulations=True,
            has_meshes=True,
        ),
        Model(
            name="0002_H_AO_H",
            species="Human",
            anatomy="Aorta",
            disease="Healthy",
            sex="Female",
            age=25.0,
            has_simulations=False,
            has_meshes=True,
        ),
        Model(
            name="0003_H_CORO_CAD",
            species="Human",
            anatomy="Coronary",
            disease="Coronary Artery Disease",
            sex="Male",
            age=55.0,
            has_simulations=True,
            has_meshes=False,
        ),
        Model(
            name="0004_A_AO_H",
            species="Animal",
            anatomy="Aorta",
            disease="Healthy",
            sex="Male",
            age=2.0,
            has_simulations=False,
            has_meshes=True,
        ),
    ]


@pytest.fixture
def sample_simulations():
    """Create sample simulation results for testing."""
    return [
        SimulationResult(
            model_name="0001_H_AO_SVD",
            full_filename="0001_H_AO_SVD_3D_RIGID_VTP.zip",
            fidelity="3D",
            method="RIGID",
            file_type="VTP",
        ),
        SimulationResult(
            model_name="0001_H_AO_SVD",
            full_filename="0001_H_AO_SVD_3D_FSI_VTU.zip",
            fidelity="3D",
            method="FSI",
            file_type="VTU",
        ),
        SimulationResult(
            model_name="0003_H_CORO_CAD",
            full_filename="0003_H_CORO_CAD_3D_RIGID_VTP.zip",
            fidelity="3D",
            method="RIGID",
            file_type="VTP",
        ),
    ]


class TestFilterModels:
    """Tests for filter_models function."""

    def test_no_filters(self, sample_models):
        """Test with no filters returns all models."""
        result = filter_models(sample_models)
        assert len(result) == 4

    def test_filter_by_species_human(self, sample_models):
        """Test filtering by species=Human."""
        result = filter_models(sample_models, species="Human")
        assert len(result) == 3
        assert all(m.species == "Human" for m in result)

    def test_filter_by_species_code(self, sample_models):
        """Test filtering by species code (H)."""
        result = filter_models(sample_models, species="H")
        assert len(result) == 3

    def test_filter_by_anatomy(self, sample_models):
        """Test filtering by anatomy."""
        result = filter_models(sample_models, anatomy="Aorta")
        assert len(result) == 3

    def test_filter_by_anatomy_partial(self, sample_models):
        """Test filtering by partial anatomy match."""
        result = filter_models(sample_models, anatomy="Coro")
        assert len(result) == 1
        assert result[0].name == "0003_H_CORO_CAD"

    def test_filter_by_disease(self, sample_models):
        """Test filtering by disease."""
        result = filter_models(sample_models, disease="Healthy")
        assert len(result) == 2

    def test_filter_by_sex(self, sample_models):
        """Test filtering by sex."""
        result = filter_models(sample_models, sex="Male")
        assert len(result) == 3

    def test_filter_by_age_range(self, sample_models):
        """Test filtering by age range."""
        result = filter_models(sample_models, age_min=10, age_max=30)
        assert len(result) == 1
        assert result[0].name == "0002_H_AO_H"

    def test_filter_by_age_min(self, sample_models):
        """Test filtering by minimum age."""
        result = filter_models(sample_models, age_min=20)
        assert len(result) == 2

    def test_filter_by_age_max(self, sample_models):
        """Test filtering by maximum age."""
        result = filter_models(sample_models, age_max=5)
        assert len(result) == 2

    def test_filter_by_has_simulations(self, sample_models):
        """Test filtering by simulation availability."""
        result = filter_models(sample_models, has_simulations=True)
        assert len(result) == 2

    def test_filter_by_has_meshes(self, sample_models):
        """Test filtering by mesh availability."""
        result = filter_models(sample_models, has_meshes=True)
        assert len(result) == 3

    def test_filter_multiple_criteria(self, sample_models):
        """Test filtering by multiple criteria."""
        result = filter_models(
            sample_models,
            species="Human",
            anatomy="Aorta",
            has_simulations=True,
        )
        assert len(result) == 1
        assert result[0].name == "0001_H_AO_SVD"

    def test_filter_custom(self, sample_models):
        """Test custom filter function."""
        result = filter_models(
            sample_models,
            custom_filter=lambda m: m.age is not None and m.age < 10,
        )
        assert len(result) == 2

    def test_filter_by_name(self, sample_models):
        """Test filtering by name."""
        result = filter_models(sample_models, name="0001")
        assert len(result) == 1
        assert result[0].name == "0001_H_AO_SVD"


class TestFilterSimulations:
    """Tests for filter_simulations function."""

    def test_no_filters(self, sample_simulations):
        """Test with no filters returns all simulations."""
        result = filter_simulations(sample_simulations)
        assert len(result) == 3

    def test_filter_by_model_name(self, sample_simulations):
        """Test filtering by model name."""
        result = filter_simulations(sample_simulations, model_name="0001_H_AO_SVD")
        assert len(result) == 2

    def test_filter_by_method(self, sample_simulations):
        """Test filtering by simulation method."""
        result = filter_simulations(sample_simulations, method="RIGID")
        assert len(result) == 2

    def test_filter_by_file_type(self, sample_simulations):
        """Test filtering by file type."""
        result = filter_simulations(sample_simulations, file_type="VTP")
        assert len(result) == 2


class TestGetUniqueValues:
    """Tests for get_unique_values function."""

    def test_unique_species(self, sample_models):
        """Test getting unique species values."""
        result = get_unique_values(sample_models, "species")
        assert set(result) == {"Animal", "Human"}

    def test_unique_anatomy(self, sample_models):
        """Test getting unique anatomy values."""
        result = get_unique_values(sample_models, "anatomy")
        assert set(result) == {"Aorta", "Coronary"}


class TestSummarizeModels:
    """Tests for summarize_models function."""

    def test_summary(self, sample_models):
        """Test generating summary statistics."""
        summary = summarize_models(sample_models)

        assert summary["total"] == 4
        assert summary["by_species"]["Human"] == 3
        assert summary["by_species"]["Animal"] == 1
        assert summary["by_anatomy"]["Aorta"] == 3
        assert summary["with_simulations"] == 2

    def test_summary_empty(self):
        """Test summary with empty list."""
        summary = summarize_models([])
        assert summary["total"] == 0

    def test_summary_age_stats(self, sample_models):
        """Test age statistics in summary."""
        summary = summarize_models(sample_models)
        age_stats = summary["age_statistics"]

        assert age_stats["count"] == 4
        assert age_stats["min"] == 2.0
        assert age_stats["max"] == 55.0
