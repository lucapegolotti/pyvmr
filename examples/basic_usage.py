"""Basic usage examples for pyvmr."""

from pyvmr import VMRClient

# Initialize the client
vmr = VMRClient()

# List all models
print("=== All Models ===")
models = vmr.list_models()
print(f"Total models: {len(models)}")
print()

# Search for specific models
print("=== Human Aorta Models ===")
aorta_models = vmr.search(anatomy="Aorta", species="Human")
print(f"Found {len(aorta_models)} human aorta models")
for model in aorta_models[:5]:
    print(f"  - {model.name}: {model.disease}")
print()

# Search pediatric models
print("=== Pediatric Models (age < 18) ===")
pediatric = vmr.search(age_max=18)
print(f"Found {len(pediatric)} pediatric models")
print()

# Get a specific model
print("=== Model Details ===")
model = vmr.get_model("0001_H_AO_SVD")
if model:
    print(f"Name: {model.name}")
    print(f"Species: {model.species}")
    print(f"Anatomy: {model.anatomy}")
    print(f"Disease: {model.disease}")
    print(f"Age: {model.age}")
    print(f"Sex: {model.sex}")
    print(f"Has Simulations: {model.has_simulations}")
    if model.file_size:
        print(f"Download Size: {model.file_size_mb:.1f} MB")
print()

# Get simulations for a model
print("=== Simulations ===")
sims = vmr.get_simulations("0001_H_AO_SVD")
print(f"Found {len(sims)} simulations for 0001_H_AO_SVD")
for sim in sims:
    print(f"  - {sim.short_name}: {sim.method} ({sim.fidelity})")
print()

# Get summary statistics
print("=== Repository Summary ===")
summary = vmr.summary()
print(f"Total models: {summary['total']}")
print(f"With simulations: {summary['with_simulations']}")
print(f"Species: {summary['by_species']}")
print()

# Example: Download a model (commented out to avoid actual download)
# vmr.download("0001_H_AO_SVD", output_dir="./data/")

# Example: Download with simulations
# vmr.download("0001_H_AO_SVD", output_dir="./data/", include_simulations=True)

# Example: Batch download
# vmr.download_batch(["0001_H_AO_SVD", "0002_H_AO_H"], output_dir="./data/")

print("Done!")
