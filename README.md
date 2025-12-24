# pyvmr

Python client for programmatic access to the [Vascular Model Repository (VMR)](https://www.vascularmodel.com).

## Installation

```bash
pip install pyvmr
```

For CLI support:
```bash
pip install pyvmr[cli]
```

## Quick Start

```python
from pyvmr import VMRClient

# Initialize client
vmr = VMRClient()

# List all models
models = vmr.list_models()
print(f"Found {len(models)} models")

# Search with filters
aorta_models = vmr.search(anatomy="Aorta", species="Human")

# Get a specific model
model = vmr.get_model("0001_H_AO_SVD")
print(f"{model.name}: {model.disease}, Age {model.age}")

# Download a model
vmr.download("0001_H_AO_SVD", output_dir="./data/")

# Download with simulation results
vmr.download("0001_H_AO_SVD", output_dir="./data/", include_simulations=True)

# Batch download
vmr.download_batch(
    ["0001_H_AO_SVD", "0002_H_AO_H"],
    output_dir="./data/"
)
```

## Search Filters

```python
# Filter by anatomy
aorta = vmr.search(anatomy="Aorta")
coronary = vmr.search(anatomy="Coronary")

# Filter by species
human = vmr.search(species="Human")
animal = vmr.search(species="Animal")

# Filter by disease
healthy = vmr.search(disease="Healthy")
coa = vmr.search(disease="Coarctation")

# Filter by demographics
pediatric = vmr.search(age_max=18)
male = vmr.search(sex="Male")

# Combine filters
result = vmr.search(
    anatomy="Aorta",
    species="Human",
    has_simulations=True
)
```

## Working with Simulations

```python
# Get simulations for a model
sims = vmr.get_simulations("0001_H_AO_SVD")
for sim in sims:
    print(f"{sim.short_name}: {sim.method} ({sim.fidelity})")

# Download specific simulation
vmr.download_simulation(
    model_name="0001_H_AO_SVD",
    simulation_name="0001_H_AO_SVD_3D_RIGID_VTP.zip",
    output_dir="./data/"
)
```

## CLI Usage

```bash
# List models
pyvmr list
pyvmr list --anatomy Aorta --species Human

# Search models
pyvmr search --disease COA

# Show model details
pyvmr info 0001_H_AO_SVD

# Download model
pyvmr download 0001_H_AO_SVD --output ./models/

# Download multiple models
pyvmr download 0001_H_AO_SVD 0002_H_AO_H --output ./models/
```

## Caching

The client caches catalog data locally to avoid repeated downloads:

```python
# Custom cache directory
vmr = VMRClient(cache_dir="~/.my_vmr_cache")

# Force refresh catalog
vmr.refresh_catalog()

# Check cache status
print(vmr.cache_info())
```

## License

MIT License
