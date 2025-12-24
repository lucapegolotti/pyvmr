"""Catalog management for fetching, parsing, and caching VMR data."""

import json
import os
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests

from .constants import (
    ADDITIONAL_DATA_CSV_URL,
    ABBREVIATIONS_CSV_URL,
    CACHE_TTL_HOURS,
    DEFAULT_CACHE_DIR,
    DEFAULT_TIMEOUT,
    FILE_SIZES_CSV_URL,
    PROJECT_COLUMNS,
    PROJECTS_CSV_URL,
    RESULTS_COLUMNS,
    RESULTS_CSV_URL,
)
from .models import AdditionalDataset, Abbreviation, Model, SimulationResult


class CatalogManager:
    """Manages fetching, parsing, and caching of VMR catalog data."""

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        cache_ttl_hours: int = CACHE_TTL_HOURS,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """Initialize the catalog manager.

        Args:
            cache_dir: Directory for caching catalog data. Defaults to ~/.pyvmr
            cache_ttl_hours: Cache time-to-live in hours. Defaults to 24.
            timeout: HTTP request timeout in seconds. Defaults to 30.
        """
        self.cache_dir = Path(os.path.expanduser(cache_dir or DEFAULT_CACHE_DIR))
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.timeout = timeout

        # In-memory cache
        self._models: Optional[List[Model]] = None
        self._simulations: Optional[List[SimulationResult]] = None
        self._additional_datasets: Optional[List[AdditionalDataset]] = None
        self._abbreviations: Optional[List[Abbreviation]] = None
        self._file_sizes: Optional[Dict[str, int]] = None

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, name: str) -> Path:
        """Get the cache file path for a given resource."""
        return self.cache_dir / f"{name}.csv"

    def _get_cache_meta_path(self) -> Path:
        """Get the cache metadata file path."""
        return self.cache_dir / "cache_meta.json"

    def _is_cache_valid(self, name: str) -> bool:
        """Check if the cache for a resource is still valid."""
        cache_path = self._get_cache_path(name)
        meta_path = self._get_cache_meta_path()

        if not cache_path.exists() or not meta_path.exists():
            return False

        try:
            with open(meta_path) as f:
                meta = json.load(f)

            if name not in meta:
                return False

            cached_time = datetime.fromisoformat(meta[name]["timestamp"])
            return datetime.now() - cached_time < self.cache_ttl
        except (json.JSONDecodeError, KeyError, ValueError):
            return False

    def _update_cache_meta(self, name: str):
        """Update the cache metadata for a resource."""
        meta_path = self._get_cache_meta_path()

        meta = {}
        if meta_path.exists():
            try:
                with open(meta_path) as f:
                    meta = json.load(f)
            except json.JSONDecodeError:
                pass

        meta[name] = {"timestamp": datetime.now().isoformat()}

        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

    def _fetch_csv(self, url: str, name: str, force_refresh: bool = False) -> pd.DataFrame:
        """Fetch a CSV file from URL or cache.

        Args:
            url: URL to fetch from
            name: Cache key name
            force_refresh: If True, bypass cache

        Returns:
            DataFrame with CSV data
        """
        cache_path = self._get_cache_path(name)

        # Try to use cache
        if not force_refresh and self._is_cache_valid(name):
            return pd.read_csv(cache_path)

        # Fetch from remote
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()

        # Parse CSV
        df = pd.read_csv(StringIO(response.text))

        # Save to cache
        df.to_csv(cache_path, index=False)
        self._update_cache_meta(name)

        return df

    def _parse_bool_field(self, value) -> bool:
        """Parse a boolean field from CSV (1/0 or yes/no)."""
        if pd.isna(value):
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value == 1
        return str(value).lower() in ("1", "yes", "true")

    def _parse_float_field(self, value) -> Optional[float]:
        """Parse a float field from CSV."""
        if pd.isna(value):
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _parse_int_field(self, value) -> Optional[int]:
        """Parse an integer field from CSV."""
        if pd.isna(value):
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    def _parse_date_field(self, value) -> Optional[datetime]:
        """Parse a date field from CSV."""
        if pd.isna(value):
            return None
        try:
            # Try common date formats
            for fmt in ["%d %b %Y", "%Y-%m-%d", "%m/%d/%Y"]:
                try:
                    return datetime.strptime(str(value), fmt)
                except ValueError:
                    continue
            return None
        except (ValueError, TypeError):
            return None

    def _parse_str_field(self, value) -> str:
        """Parse a string field from CSV."""
        if pd.isna(value):
            return ""
        return str(value).strip()

    def get_models(self, force_refresh: bool = False) -> List[Model]:
        """Get all models from the catalog.

        Args:
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            List of Model objects
        """
        if self._models is not None and not force_refresh:
            return self._models

        df = self._fetch_csv(PROJECTS_CSV_URL, "projects", force_refresh)
        file_sizes = self.get_file_sizes(force_refresh)

        models = []
        for _, row in df.iterrows():
            name = self._parse_str_field(row.get(PROJECT_COLUMNS["name"]))
            if not name:
                continue

            model = Model(
                name=name,
                legacy_name=self._parse_str_field(row.get(PROJECT_COLUMNS["legacy_name"])),
                image_number=self._parse_str_field(row.get(PROJECT_COLUMNS["image_number"])),
                sex=self._parse_str_field(row.get(PROJECT_COLUMNS["sex"])),
                age=self._parse_float_field(row.get(PROJECT_COLUMNS["age"])),
                species=self._parse_str_field(row.get(PROJECT_COLUMNS["species"])),
                ethnicity=self._parse_str_field(row.get(PROJECT_COLUMNS["ethnicity"])),
                animal=self._parse_str_field(row.get(PROJECT_COLUMNS["animal"])),
                anatomy=self._parse_str_field(row.get(PROJECT_COLUMNS["anatomy"])),
                disease=self._parse_str_field(row.get(PROJECT_COLUMNS["disease"])),
                procedure=self._parse_str_field(row.get(PROJECT_COLUMNS["procedure"])),
                has_images=self._parse_bool_field(row.get(PROJECT_COLUMNS["images"])),
                has_paths=self._parse_bool_field(row.get(PROJECT_COLUMNS["paths"])),
                has_segmentations=self._parse_bool_field(row.get(PROJECT_COLUMNS["segmentations"])),
                has_models=self._parse_bool_field(row.get(PROJECT_COLUMNS["models"])),
                has_meshes=self._parse_bool_field(row.get(PROJECT_COLUMNS["meshes"])),
                has_simulations=self._parse_bool_field(row.get(PROJECT_COLUMNS["simulations"])),
                notes=self._parse_str_field(row.get(PROJECT_COLUMNS["notes"])),
                doi=self._parse_str_field(row.get(PROJECT_COLUMNS["doi"])),
                citation=self._parse_str_field(row.get(PROJECT_COLUMNS["citation"])),
                image_manufacturer=self._parse_str_field(row.get(PROJECT_COLUMNS["image_manufacturer"])),
                image_type=self._parse_str_field(row.get(PROJECT_COLUMNS["image_type"])),
                image_source=self._parse_str_field(row.get(PROJECT_COLUMNS["image_source"])),
                image_modality=self._parse_str_field(row.get(PROJECT_COLUMNS["image_modality"])),
                has_results=self._parse_bool_field(row.get(PROJECT_COLUMNS["results"])),
                date_added=self._parse_date_field(row.get(PROJECT_COLUMNS["date_added"])),
                order_uploaded=self._parse_int_field(row.get(PROJECT_COLUMNS["order_uploaded"])),
                model_creator=self._parse_str_field(row.get(PROJECT_COLUMNS["model_creator"])),
            )

            # Set file size if available
            size_key = f"svprojects/{name}.zip"
            if size_key in file_sizes:
                model.file_size = file_sizes[size_key]

            models.append(model)

        self._models = models
        return models

    def get_simulations(self, force_refresh: bool = False) -> List[SimulationResult]:
        """Get all simulation results from the catalog.

        Args:
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            List of SimulationResult objects
        """
        if self._simulations is not None and not force_refresh:
            return self._simulations

        df = self._fetch_csv(RESULTS_CSV_URL, "results", force_refresh)
        file_sizes = self.get_file_sizes(force_refresh)

        simulations = []
        for _, row in df.iterrows():
            model_name = self._parse_str_field(row.get(RESULTS_COLUMNS["model_name"]))
            full_filename = self._parse_str_field(row.get(RESULTS_COLUMNS["full_filename"]))

            if not model_name or not full_filename:
                continue

            sim = SimulationResult(
                model_name=model_name,
                full_filename=full_filename,
                image_number=self._parse_str_field(row.get(RESULTS_COLUMNS["image_number"])),
                short_name=self._parse_str_field(row.get(RESULTS_COLUMNS["short_name"])),
                legacy_name=self._parse_str_field(row.get(RESULTS_COLUMNS["legacy_name"])),
                fidelity=self._parse_str_field(row.get(RESULTS_COLUMNS["fidelity"])),
                method=self._parse_str_field(row.get(RESULTS_COLUMNS["method"])),
                condition=self._parse_str_field(row.get(RESULTS_COLUMNS["condition"])),
                results_type=self._parse_str_field(row.get(RESULTS_COLUMNS["results_type"])),
                file_type=self._parse_str_field(row.get(RESULTS_COLUMNS["file_type"])),
                creator=self._parse_str_field(row.get(RESULTS_COLUMNS["creator"])),
                notes=self._parse_str_field(row.get(RESULTS_COLUMNS["notes"])),
            )

            # Set file size if available
            size_key = f"svresults/{model_name}/{full_filename}"
            if size_key in file_sizes:
                sim.file_size = file_sizes[size_key]

            simulations.append(sim)

        self._simulations = simulations
        return simulations

    def get_additional_datasets(self, force_refresh: bool = False) -> List[AdditionalDataset]:
        """Get all additional datasets from the catalog.

        Args:
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            List of AdditionalDataset objects
        """
        if self._additional_datasets is not None and not force_refresh:
            return self._additional_datasets

        df = self._fetch_csv(ADDITIONAL_DATA_CSV_URL, "additional", force_refresh)
        file_sizes = self.get_file_sizes(force_refresh)

        datasets = []
        for _, row in df.iterrows():
            name = self._parse_str_field(row.get("Name"))
            if not name:
                continue

            dataset = AdditionalDataset(
                name=name,
                notes=self._parse_str_field(row.get("Notes")),
                citation=self._parse_str_field(row.get("Citation")),
            )

            # Set file size if available
            size_key = f"additionaldata/{name}.zip"
            if size_key in file_sizes:
                dataset.file_size = file_sizes[size_key]

            datasets.append(dataset)

        self._additional_datasets = datasets
        return datasets

    def get_abbreviations(self, force_refresh: bool = False) -> List[Abbreviation]:
        """Get all abbreviation mappings from the catalog.

        Args:
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            List of Abbreviation objects
        """
        if self._abbreviations is not None and not force_refresh:
            return self._abbreviations

        df = self._fetch_csv(ABBREVIATIONS_CSV_URL, "abbreviations", force_refresh)

        abbreviations = []
        for _, row in df.iterrows():
            abbr = Abbreviation(
                category=self._parse_str_field(row.get("Category")),
                short_name=self._parse_str_field(row.get("Short Name")),
                long_name=self._parse_str_field(row.get("Long Name")),
            )
            abbreviations.append(abbr)

        self._abbreviations = abbreviations
        return abbreviations

    def get_file_sizes(self, force_refresh: bool = False) -> Dict[str, int]:
        """Get file size mappings from the catalog.

        Args:
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            Dictionary mapping file paths to sizes in bytes
        """
        if self._file_sizes is not None and not force_refresh:
            return self._file_sizes

        df = self._fetch_csv(FILE_SIZES_CSV_URL, "file_sizes", force_refresh)

        file_sizes = {}
        for _, row in df.iterrows():
            name = self._parse_str_field(row.get("Name"))
            size = self._parse_int_field(row.get("Size"))
            if name and size is not None:
                file_sizes[name] = size

        self._file_sizes = file_sizes
        return file_sizes

    def refresh(self):
        """Force refresh all cached data."""
        self._models = None
        self._simulations = None
        self._additional_datasets = None
        self._abbreviations = None
        self._file_sizes = None

        # Refresh all catalogs
        self.get_file_sizes(force_refresh=True)
        self.get_models(force_refresh=True)
        self.get_simulations(force_refresh=True)
        self.get_additional_datasets(force_refresh=True)
        self.get_abbreviations(force_refresh=True)

    def cache_info(self) -> Dict:
        """Get information about the cache state.

        Returns:
            Dictionary with cache status information
        """
        meta_path = self._get_cache_meta_path()

        info = {
            "cache_dir": str(self.cache_dir),
            "cache_ttl_hours": self.cache_ttl.total_seconds() / 3600,
            "resources": {},
        }

        if meta_path.exists():
            try:
                with open(meta_path) as f:
                    meta = json.load(f)

                for name, data in meta.items():
                    cache_path = self._get_cache_path(name)
                    info["resources"][name] = {
                        "cached": cache_path.exists(),
                        "timestamp": data.get("timestamp"),
                        "valid": self._is_cache_valid(name),
                        "size_bytes": cache_path.stat().st_size if cache_path.exists() else 0,
                    }
            except json.JSONDecodeError:
                pass

        return info
