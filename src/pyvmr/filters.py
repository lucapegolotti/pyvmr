"""Query and filter utilities for VMR models."""

from typing import Callable, List, Optional, Union

from .models import Model, SimulationResult


def filter_models(
    models: List[Model],
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
    """Filter models based on various criteria.

    All string comparisons are case-insensitive and support partial matching.

    Args:
        models: List of models to filter
        name: Filter by model name (partial match)
        species: Filter by species (Human, Animal, or codes H, A)
        anatomy: Filter by anatomy (Aorta, Coronary, etc. or codes AO, CORO)
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
        Filtered list of models
    """
    result = models

    if name is not None:
        result = [m for m in result if _match_string(m.name, name)]

    if species is not None:
        result = [m for m in result if _match_species(m.species, species)]

    if anatomy is not None:
        result = [m for m in result if _match_string(m.anatomy, anatomy)]

    if disease is not None:
        result = [m for m in result if _match_string(m.disease, disease)]

    if sex is not None:
        result = [m for m in result if _match_exact(m.sex, sex)]

    if age_min is not None:
        result = [m for m in result if m.age is not None and m.age >= age_min]

    if age_max is not None:
        result = [m for m in result if m.age is not None and m.age <= age_max]

    if ethnicity is not None:
        result = [m for m in result if _match_string(m.ethnicity, ethnicity)]

    if has_simulations is not None:
        result = [m for m in result if m.has_simulations == has_simulations]

    if has_meshes is not None:
        result = [m for m in result if m.has_meshes == has_meshes]

    if has_segmentations is not None:
        result = [m for m in result if m.has_segmentations == has_segmentations]

    if has_images is not None:
        result = [m for m in result if m.has_images == has_images]

    if has_paths is not None:
        result = [m for m in result if m.has_paths == has_paths]

    if has_results is not None:
        result = [m for m in result if m.has_results == has_results]

    if model_creator is not None:
        result = [m for m in result if _match_string(m.model_creator, model_creator)]

    if custom_filter is not None:
        result = [m for m in result if custom_filter(m)]

    return result


def filter_simulations(
    simulations: List[SimulationResult],
    *,
    model_name: Optional[str] = None,
    fidelity: Optional[str] = None,
    method: Optional[str] = None,
    condition: Optional[str] = None,
    results_type: Optional[str] = None,
    file_type: Optional[str] = None,
    creator: Optional[str] = None,
    custom_filter: Optional[Callable[[SimulationResult], bool]] = None,
) -> List[SimulationResult]:
    """Filter simulation results based on various criteria.

    All string comparisons are case-insensitive and support partial matching.

    Args:
        simulations: List of simulations to filter
        model_name: Filter by parent model name
        fidelity: Filter by simulation fidelity (e.g., 3D)
        method: Filter by simulation method (e.g., RIGID, FSI)
        condition: Filter by simulation condition
        results_type: Filter by results type
        file_type: Filter by file type (e.g., VTP, VTU)
        creator: Filter by simulation creator
        custom_filter: Custom filter function

    Returns:
        Filtered list of simulation results
    """
    result = simulations

    if model_name is not None:
        result = [s for s in result if _match_string(s.model_name, model_name)]

    if fidelity is not None:
        result = [s for s in result if _match_string(s.fidelity, fidelity)]

    if method is not None:
        result = [s for s in result if _match_string(s.method, method)]

    if condition is not None:
        result = [s for s in result if _match_string(s.condition, condition)]

    if results_type is not None:
        result = [s for s in result if _match_string(s.results_type, results_type)]

    if file_type is not None:
        result = [s for s in result if _match_string(s.file_type, file_type)]

    if creator is not None:
        result = [s for s in result if _match_string(s.creator, creator)]

    if custom_filter is not None:
        result = [s for s in result if custom_filter(s)]

    return result


def _match_string(value: str, pattern: str) -> bool:
    """Case-insensitive partial string matching."""
    if not value or not pattern:
        return False
    return pattern.lower() in value.lower()


def _match_exact(value: str, pattern: str) -> bool:
    """Case-insensitive exact string matching."""
    if not value or not pattern:
        return False
    return pattern.lower() == value.lower()


def _match_species(value: str, pattern: str) -> bool:
    """Match species with support for codes (H=Human, A=Animal)."""
    if not value or not pattern:
        return False

    value_lower = value.lower()
    pattern_lower = pattern.lower()

    # Direct match
    if pattern_lower in value_lower:
        return True

    # Code matching
    species_map = {
        "h": "human",
        "a": "animal",
        "human": "human",
        "animal": "animal",
    }

    pattern_normalized = species_map.get(pattern_lower, pattern_lower)
    value_normalized = species_map.get(value_lower, value_lower)

    return pattern_normalized == value_normalized


def get_unique_values(models: List[Model], field: str) -> List[str]:
    """Get unique values for a model field.

    Args:
        models: List of models
        field: Field name to extract values from

    Returns:
        Sorted list of unique non-empty values
    """
    values = set()
    for model in models:
        value = getattr(model, field, None)
        if value:
            values.add(value)
    return sorted(values)


def summarize_models(models: List[Model]) -> dict:
    """Generate a summary of model statistics.

    Args:
        models: List of models to summarize

    Returns:
        Dictionary with summary statistics
    """
    total = len(models)

    if total == 0:
        return {"total": 0}

    # Count by species
    species_counts = {}
    for m in models:
        species = m.species or "Unknown"
        species_counts[species] = species_counts.get(species, 0) + 1

    # Count by anatomy
    anatomy_counts = {}
    for m in models:
        anatomy = m.anatomy or "Unknown"
        anatomy_counts[anatomy] = anatomy_counts.get(anatomy, 0) + 1

    # Count by disease
    disease_counts = {}
    for m in models:
        disease = m.disease or "Unknown"
        disease_counts[disease] = disease_counts.get(disease, 0) + 1

    # Count features
    with_simulations = sum(1 for m in models if m.has_simulations)
    with_meshes = sum(1 for m in models if m.has_meshes)
    with_segmentations = sum(1 for m in models if m.has_segmentations)

    # Age statistics
    ages = [m.age for m in models if m.age is not None]
    age_stats = {}
    if ages:
        age_stats = {
            "min": min(ages),
            "max": max(ages),
            "mean": sum(ages) / len(ages),
            "count": len(ages),
        }

    # Total size
    total_size = sum(m.file_size or 0 for m in models)

    return {
        "total": total,
        "by_species": species_counts,
        "by_anatomy": anatomy_counts,
        "by_disease": disease_counts,
        "with_simulations": with_simulations,
        "with_meshes": with_meshes,
        "with_segmentations": with_segmentations,
        "age_statistics": age_stats,
        "total_size_bytes": total_size,
        "total_size_gb": total_size / (1024**3) if total_size else 0,
    }
