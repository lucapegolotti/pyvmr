"""pyvmr - Python client for the Vascular Model Repository.

Example:
    >>> from pyvmr import VMRClient
    >>> vmr = VMRClient()
    >>> models = vmr.search(anatomy="Aorta", species="Human")
    >>> vmr.download(models[0].name, output_dir="./data/")
"""

from .client import VMRClient
from .models import AdditionalDataset, Model, SimulationResult
from .download import DownloadError, format_size

__version__ = "0.1.0"
__all__ = [
    "VMRClient",
    "Model",
    "SimulationResult",
    "AdditionalDataset",
    "DownloadError",
    "format_size",
]
