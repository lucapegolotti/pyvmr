"""Main VMR client interface."""

from pathlib import Path
from typing import Callable, List, Optional, Union

from .catalog import CatalogManager
from .constants import (
    ADDITIONAL_DOWNLOAD_URL,
    CACHE_TTL_HOURS,
    DEFAULT_CACHE_DIR,
    PDF_DOWNLOAD_URL,
    PROJECTS_DOWNLOAD_URL,
    RESULTS_DOWNLOAD_URL,
)
from .download import DownloadManager, format_size
from .filters import filter_models, filter_simulations, summarize_models
from .models import AdditionalDataset, Model, SimulationResult


class VMRClient:
    """Client for interacting with the Vascular Model Repository.

    Example:
        >>> from pyvmr import VMRClient
        >>> vmr = VMRClient()
        >>> models = vmr.search(anatomy="Aorta", species="Human")
        >>> vmr.download(models[0].name, output_dir="./data/")
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        cache_ttl_hours: int = CACHE_TTL_HOURS,
        show_progress: bool = True,
    ):
        """Initialize the VMR client.

        Args:
            cache_dir: Directory for caching catalog data. Defaults to ~/.pyvmr
            cache_ttl_hours: Cache time-to-live in hours. Defaults to 24.
            show_progress: Whether to show progress bars during downloads
        """
        self._catalog = CatalogManager(
            cache_dir=cache_dir,
            cache_ttl_hours=cache_ttl_hours,
        )
        self._downloader = DownloadManager(show_progress=show_progress)
        self._show_progress = show_progress

    def list_models(self) -> List[Model]:
        """List all models in the repository.

        Returns:
            List of all Model objects
        """
        return self._catalog.get_models()

    def get_model(self, name: str) -> Optional[Model]:
        """Get a specific model by name.

        Args:
            name: Model name (e.g., "0001_H_AO_SVD")

        Returns:
            Model object if found, None otherwise
        """
        models = self._catalog.get_models()
        for model in models:
            if model.name == name:
                return model
        return None

    def search(
        self,
        *,
        name: Optional[str] = None,
        species: Optional[str] = None,
        anatomy: Optional[str] = None,
        disease: Optional[str] = None,
        sex: Optional[str] = None,
        age_min: Optional[float] = None,
        age_max: Optional[float] = None,
        ethnicity: Optional[str] = None,
        has_simulations: Optional[bool] = None,
        has_meshes: Optional[bool] = None,
        has_segmentations: Optional[bool] = None,
        has_images: Optional[bool] = None,
        has_paths: Optional[bool] = None,
        has_results: Optional[bool] = None,
        model_creator: Optional[str] = None,
        custom_filter: Optional[Callable[[Model], bool]] = None,
    ) -> List[Model]:
        """Search for models matching criteria.

        All string comparisons are case-insensitive and support partial matching.

        Args:
            name: Filter by model name (partial match)
            species: Filter by species (Human, Animal, or codes H, A)
            anatomy: Filter by anatomy (Aorta, Coronary, etc.)
            disease: Filter by disease condition
            sex: Filter by sex (Male, Female)
            age_min: Minimum age in years
            age_max: Maximum age in years
            ethnicity: Filter by ethnicity
            has_simulations: Filter by simulation availability
            has_meshes: Filter by mesh availability
            has_segmentations: Filter by segmentation availability
            has_images: Filter by image availability
            has_paths: Filter by path availability
            has_results: Filter by results availability
            model_creator: Filter by model creator
            custom_filter: Custom filter function

        Returns:
            List of models matching all criteria
        """
        models = self._catalog.get_models()
        return filter_models(
            models,
            name=name,
            species=species,
            anatomy=anatomy,
            disease=disease,
            sex=sex,
            age_min=age_min,
            age_max=age_max,
            ethnicity=ethnicity,
            has_simulations=has_simulations,
            has_meshes=has_meshes,
            has_segmentations=has_segmentations,
            has_images=has_images,
            has_paths=has_paths,
            has_results=has_results,
            model_creator=model_creator,
            custom_filter=custom_filter,
        )

    def get_simulations(self, model_name: str) -> List[SimulationResult]:
        """Get simulation results for a specific model.

        Args:
            model_name: Name of the model

        Returns:
            List of SimulationResult objects for the model
        """
        all_sims = self._catalog.get_simulations()
        return filter_simulations(all_sims, model_name=model_name)

    def list_simulations(self) -> List[SimulationResult]:
        """List all simulation results in the repository.

        Returns:
            List of all SimulationResult objects
        """
        return self._catalog.get_simulations()

    def get_additional_datasets(self) -> List[AdditionalDataset]:
        """Get all additional datasets.

        Returns:
            List of AdditionalDataset objects
        """
        return self._catalog.get_additional_datasets()

    def get_download_size(self, name: str) -> Optional[int]:
        """Get the download size for a model in bytes.

        Args:
            name: Model name

        Returns:
            Size in bytes if known, None otherwise
        """
        model = self.get_model(name)
        if model:
            return model.file_size
        return None

    def download(
        self,
        name: str,
        output_dir: Union[str, Path] = ".",
        extract: bool = False,
        include_simulations: bool = False,
        include_pdf: bool = False,
    ) -> Path:
        """Download a model by name.

        Args:
            name: Model name (e.g., "0001_H_AO_SVD")
            output_dir: Directory to save files. Defaults to current directory.
            extract: If True, extract ZIP files after download
            include_simulations: If True, also download simulation results
            include_pdf: If True, also download PDF documentation

        Returns:
            Path to downloaded file (or extracted directory if extract=True)
        """
        model = self.get_model(name)
        if not model:
            raise ValueError(f"Model not found: {name}")

        output_dir = Path(output_dir)

        # Download main model
        url = PROJECTS_DOWNLOAD_URL.format(name=name)
        output_path = output_dir / f"{name}.zip"

        result = self._downloader.download(
            url=url,
            output_path=output_path,
            expected_size=model.file_size,
            description=name,
            extract=extract,
        )

        # Download simulations if requested
        if include_simulations:
            sims = self.get_simulations(name)
            if sims:
                sim_dir = output_dir / f"{name}_simulations"
                self.download_simulations(name, output_dir=sim_dir, extract=extract)

        # Download PDF if requested
        if include_pdf:
            self.download_pdf(name, output_dir=output_dir)

        return result

    def download_simulation(
        self,
        model_name: str,
        simulation_name: str,
        output_dir: Union[str, Path] = ".",
        extract: bool = False,
    ) -> Path:
        """Download a specific simulation result.

        Args:
            model_name: Name of the parent model
            simulation_name: Full simulation file name
            output_dir: Directory to save file
            extract: If True, extract ZIP files after download

        Returns:
            Path to downloaded file
        """
        # Find the simulation to get its size
        sims = self.get_simulations(model_name)
        sim = None
        for s in sims:
            if s.full_filename == simulation_name:
                sim = s
                break

        url = RESULTS_DOWNLOAD_URL.format(
            model_name=model_name,
            filename=simulation_name,
        )

        output_dir = Path(output_dir)
        output_path = output_dir / simulation_name

        return self._downloader.download(
            url=url,
            output_path=output_path,
            expected_size=sim.file_size if sim else None,
            description=simulation_name,
            extract=extract,
        )

    def download_simulations(
        self,
        model_name: str,
        output_dir: Union[str, Path] = ".",
        extract: bool = False,
    ) -> List[Path]:
        """Download all simulation results for a model.

        Args:
            model_name: Name of the model
            output_dir: Directory to save files
            extract: If True, extract ZIP files after download

        Returns:
            List of paths to downloaded files
        """
        sims = self.get_simulations(model_name)
        if not sims:
            return []

        downloads = [
            {
                "url": RESULTS_DOWNLOAD_URL.format(
                    model_name=model_name,
                    filename=sim.full_filename,
                ),
                "filename": sim.full_filename,
                "size": sim.file_size,
            }
            for sim in sims
        ]

        return self._downloader.download_batch(
            downloads=downloads,
            output_dir=output_dir,
            extract=extract,
        )

    def download_pdf(
        self,
        name: str,
        output_dir: Union[str, Path] = ".",
    ) -> Path:
        """Download PDF documentation for a model.

        Args:
            name: Model name
            output_dir: Directory to save file

        Returns:
            Path to downloaded file
        """
        url = PDF_DOWNLOAD_URL.format(name=name)
        output_dir = Path(output_dir)
        output_path = output_dir / f"{name}.pdf"

        return self._downloader.download(
            url=url,
            output_path=output_path,
            description=f"{name}.pdf",
        )

    def download_batch(
        self,
        names: List[str],
        output_dir: Union[str, Path] = ".",
        extract: bool = False,
        include_simulations: bool = False,
    ) -> List[Path]:
        """Download multiple models.

        Args:
            names: List of model names
            output_dir: Directory to save files
            extract: If True, extract ZIP files after download
            include_simulations: If True, also download simulation results

        Returns:
            List of paths to downloaded files
        """
        # Gather download info
        downloads = []
        for name in names:
            model = self.get_model(name)
            if model:
                downloads.append({
                    "url": PROJECTS_DOWNLOAD_URL.format(name=name),
                    "filename": f"{name}.zip",
                    "size": model.file_size,
                })

        output_dir = Path(output_dir)
        results = self._downloader.download_batch(
            downloads=downloads,
            output_dir=output_dir,
            extract=extract,
        )

        # Download simulations if requested
        if include_simulations:
            for name in names:
                sims = self.get_simulations(name)
                if sims:
                    sim_dir = output_dir / f"{name}_simulations"
                    self.download_simulations(name, output_dir=sim_dir, extract=extract)

        return results

    def download_additional_dataset(
        self,
        name: str,
        output_dir: Union[str, Path] = ".",
        extract: bool = False,
    ) -> Path:
        """Download an additional dataset.

        Args:
            name: Dataset name
            output_dir: Directory to save file
            extract: If True, extract ZIP files after download

        Returns:
            Path to downloaded file
        """
        # Find the dataset to get its size
        datasets = self.get_additional_datasets()
        dataset = None
        for d in datasets:
            if d.name == name:
                dataset = d
                break

        url = ADDITIONAL_DOWNLOAD_URL.format(name=name)
        output_dir = Path(output_dir)
        output_path = output_dir / f"{name}.zip"

        return self._downloader.download(
            url=url,
            output_path=output_path,
            expected_size=dataset.file_size if dataset else None,
            description=name,
            extract=extract,
        )

    def refresh_catalog(self):
        """Force refresh of all cached catalog data."""
        self._catalog.refresh()

    def cache_info(self) -> dict:
        """Get information about the cache state.

        Returns:
            Dictionary with cache status information
        """
        return self._catalog.cache_info()

    def summary(self) -> dict:
        """Get summary statistics for all models.

        Returns:
            Dictionary with summary statistics
        """
        models = self._catalog.get_models()
        return summarize_models(models)

    def __repr__(self) -> str:
        models = self._catalog.get_models()
        return f"<VMRClient: {len(models)} models>"
