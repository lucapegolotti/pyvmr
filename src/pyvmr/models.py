"""Data models for VMR entities."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Model:
    """Represents a vascular model from the VMR.

    Attributes:
        name: Unique model identifier (e.g., "0001_H_AO_SVD")
        legacy_name: Previous naming convention identifier
        image_number: Image reference number
        sex: Patient sex (Male/Female)
        age: Patient age in years
        species: Species (Human/Animal)
        ethnicity: Patient ethnicity if available
        animal: Animal type if species is Animal
        anatomy: Anatomical region (e.g., Aorta, Coronary)
        disease: Disease condition
        procedure: Medical procedure if any
        has_images: Whether model includes imaging data
        has_paths: Whether model includes centerline paths
        has_segmentations: Whether model includes segmentations
        has_models: Whether model includes 3D models
        has_meshes: Whether model includes computational meshes
        has_simulations: Whether simulation results are available
        notes: Additional notes
        doi: Digital Object Identifier for citation
        citation: Citation information
        image_manufacturer: Imaging equipment manufacturer
        image_type: Type of medical image
        image_source: Source of imaging data
        image_modality: Imaging modality (CT, MRI, etc.)
        has_results: Whether results are available
        date_added: Date model was added to VMR
        order_uploaded: Upload order number
        model_creator: Creator of the model
    """
    name: str
    legacy_name: str = ""
    image_number: str = ""
    sex: str = ""
    age: Optional[float] = None
    species: str = ""
    ethnicity: str = ""
    animal: str = ""
    anatomy: str = ""
    disease: str = ""
    procedure: str = ""
    has_images: bool = False
    has_paths: bool = False
    has_segmentations: bool = False
    has_models: bool = False
    has_meshes: bool = False
    has_simulations: bool = False
    notes: str = ""
    doi: str = ""
    citation: str = ""
    image_manufacturer: str = ""
    image_type: str = ""
    image_source: str = ""
    image_modality: str = ""
    has_results: bool = False
    date_added: Optional[datetime] = None
    order_uploaded: Optional[int] = None
    model_creator: str = ""

    # Computed/cached properties
    _file_size: Optional[int] = field(default=None, repr=False)

    @property
    def download_url(self) -> str:
        """Get the download URL for this model."""
        from .constants import PROJECTS_DOWNLOAD_URL
        return PROJECTS_DOWNLOAD_URL.format(name=self.name)

    @property
    def pdf_url(self) -> str:
        """Get the PDF documentation URL for this model."""
        from .constants import PDF_DOWNLOAD_URL
        return PDF_DOWNLOAD_URL.format(name=self.name)

    @property
    def image_url(self) -> str:
        """Get the preview image URL for this model."""
        from .constants import IMAGE_URL
        return IMAGE_URL.format(name=self.name)

    @property
    def file_size(self) -> Optional[int]:
        """Get the file size in bytes if known."""
        return self._file_size

    @file_size.setter
    def file_size(self, value: int):
        """Set the file size."""
        self._file_size = value

    @property
    def file_size_mb(self) -> Optional[float]:
        """Get the file size in megabytes if known."""
        if self._file_size is None:
            return None
        return self._file_size / (1024 * 1024)

    def __str__(self) -> str:
        parts = [self.name]
        if self.anatomy:
            parts.append(self.anatomy)
        if self.disease:
            parts.append(self.disease)
        if self.species:
            parts.append(self.species)
        return " | ".join(parts)


@dataclass
class SimulationResult:
    """Represents a simulation result file from the VMR.

    Attributes:
        model_name: Name of the parent model
        full_filename: Full simulation file name
        image_number: Model image reference number
        short_name: Short/display name for the simulation
        legacy_name: Previous naming convention
        fidelity: Simulation fidelity level (e.g., 3D)
        method: Simulation method (e.g., RIGID, FSI)
        condition: Simulation conditions
        results_type: Type of results
        file_type: File format type (e.g., VTP, VTU)
        creator: Simulation creator
        notes: Additional notes
    """
    model_name: str
    full_filename: str
    image_number: str = ""
    short_name: str = ""
    legacy_name: str = ""
    fidelity: str = ""
    method: str = ""
    condition: str = ""
    results_type: str = ""
    file_type: str = ""
    creator: str = ""
    notes: str = ""

    _file_size: Optional[int] = field(default=None, repr=False)

    @property
    def download_url(self) -> str:
        """Get the download URL for this simulation result."""
        from .constants import RESULTS_DOWNLOAD_URL
        return RESULTS_DOWNLOAD_URL.format(
            model_name=self.model_name,
            filename=self.full_filename
        )

    @property
    def file_size(self) -> Optional[int]:
        """Get the file size in bytes if known."""
        return self._file_size

    @file_size.setter
    def file_size(self, value: int):
        """Set the file size."""
        self._file_size = value

    def __str__(self) -> str:
        return f"{self.model_name}/{self.short_name or self.full_filename}"


@dataclass
class AdditionalDataset:
    """Represents an additional dataset from the VMR.

    Attributes:
        name: Dataset name/identifier
        notes: Description or notes
        citation: Citation information
    """
    name: str
    notes: str = ""
    citation: str = ""

    _file_size: Optional[int] = field(default=None, repr=False)

    @property
    def download_url(self) -> str:
        """Get the download URL for this dataset."""
        from .constants import ADDITIONAL_DOWNLOAD_URL
        return ADDITIONAL_DOWNLOAD_URL.format(name=self.name)

    @property
    def file_size(self) -> Optional[int]:
        """Get the file size in bytes if known."""
        return self._file_size

    @file_size.setter
    def file_size(self, value: int):
        """Set the file size."""
        self._file_size = value


@dataclass
class Abbreviation:
    """Represents a code abbreviation mapping.

    Attributes:
        category: Category type (Species, Anatomy, Disease, etc.)
        short_name: Abbreviated code
        long_name: Full name/description
    """
    category: str
    short_name: str
    long_name: str
