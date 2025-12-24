"""Tests for data models."""

import pytest
from pyvmr.models import Model, SimulationResult, AdditionalDataset


class TestModel:
    """Tests for the Model class."""

    def test_create_model(self):
        """Test creating a model with required fields."""
        model = Model(name="0001_H_AO_SVD")
        assert model.name == "0001_H_AO_SVD"
        assert model.species == ""
        assert model.age is None

    def test_create_model_with_all_fields(self):
        """Test creating a model with all fields."""
        model = Model(
            name="0001_H_AO_SVD",
            species="Human",
            anatomy="Aorta",
            disease="Single Ventricle Defect",
            sex="Male",
            age=3.0,
            has_simulations=True,
        )
        assert model.name == "0001_H_AO_SVD"
        assert model.species == "Human"
        assert model.anatomy == "Aorta"
        assert model.disease == "Single Ventricle Defect"
        assert model.age == 3.0
        assert model.has_simulations is True

    def test_model_download_url(self):
        """Test download URL generation."""
        model = Model(name="0001_H_AO_SVD")
        assert model.download_url == "https://www.vascularmodel.com/svprojects/0001_H_AO_SVD.zip"

    def test_model_pdf_url(self):
        """Test PDF URL generation."""
        model = Model(name="0001_H_AO_SVD")
        assert model.pdf_url == "https://www.vascularmodel.com/vmr-pdfs/0001_H_AO_SVD.pdf"

    def test_model_image_url(self):
        """Test image URL generation."""
        model = Model(name="0001_H_AO_SVD")
        assert model.image_url == "https://www.vascularmodel.com/img/vmr-images/0001_H_AO_SVD.png"

    def test_model_file_size(self):
        """Test file size property."""
        model = Model(name="test")
        assert model.file_size is None
        assert model.file_size_mb is None

        model.file_size = 1024 * 1024 * 100  # 100 MB
        assert model.file_size == 104857600
        assert model.file_size_mb == 100.0

    def test_model_str(self):
        """Test string representation."""
        model = Model(
            name="0001_H_AO_SVD",
            anatomy="Aorta",
            disease="SVD",
            species="Human",
        )
        assert "0001_H_AO_SVD" in str(model)
        assert "Aorta" in str(model)


class TestSimulationResult:
    """Tests for the SimulationResult class."""

    def test_create_simulation(self):
        """Test creating a simulation result."""
        sim = SimulationResult(
            model_name="0001_H_AO_SVD",
            full_filename="0001_H_AO_SVD_3D_RIGID_VTP.zip",
        )
        assert sim.model_name == "0001_H_AO_SVD"
        assert sim.full_filename == "0001_H_AO_SVD_3D_RIGID_VTP.zip"

    def test_simulation_download_url(self):
        """Test download URL generation."""
        sim = SimulationResult(
            model_name="0001_H_AO_SVD",
            full_filename="0001_H_AO_SVD_3D_RIGID_VTP.zip",
        )
        expected = "https://www.vascularmodel.com/svresults/0001_H_AO_SVD/0001_H_AO_SVD_3D_RIGID_VTP.zip"
        assert sim.download_url == expected

    def test_simulation_str(self):
        """Test string representation."""
        sim = SimulationResult(
            model_name="0001_H_AO_SVD",
            full_filename="0001_H_AO_SVD_3D_RIGID_VTP.zip",
            short_name="3D RIGID",
        )
        assert "0001_H_AO_SVD" in str(sim)


class TestAdditionalDataset:
    """Tests for the AdditionalDataset class."""

    def test_create_dataset(self):
        """Test creating an additional dataset."""
        dataset = AdditionalDataset(
            name="SVCardiacDemoModel",
            notes="Demo model for cardiac simulations",
        )
        assert dataset.name == "SVCardiacDemoModel"
        assert "Demo" in dataset.notes

    def test_dataset_download_url(self):
        """Test download URL generation."""
        dataset = AdditionalDataset(name="SVCardiacDemoModel")
        assert dataset.download_url == "https://www.vascularmodel.com/additionaldata/SVCardiacDemoModel.zip"
