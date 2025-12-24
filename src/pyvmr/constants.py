"""Constants for the VMR client."""

# Base URL for the Vascular Model Repository
BASE_URL = "https://www.vascularmodel.com"

# CSV catalog endpoints
PROJECTS_CSV_URL = f"{BASE_URL}/dataset/dataset-svprojects.csv"
RESULTS_CSV_URL = f"{BASE_URL}/dataset/dataset-svresults.csv"
FILE_SIZES_CSV_URL = f"{BASE_URL}/dataset/file_sizes.csv"
ABBREVIATIONS_CSV_URL = f"{BASE_URL}/dataset/dataset-abbreviations.csv"
ADDITIONAL_DATA_CSV_URL = f"{BASE_URL}/dataset/additionaldata.csv"

# Download URL patterns
PROJECTS_DOWNLOAD_URL = f"{BASE_URL}/svprojects/{{name}}.zip"
RESULTS_DOWNLOAD_URL = f"{BASE_URL}/svresults/{{model_name}}/{{filename}}"
ADDITIONAL_DOWNLOAD_URL = f"{BASE_URL}/additionaldata/{{name}}.zip"
PDF_DOWNLOAD_URL = f"{BASE_URL}/vmr-pdfs/{{name}}.pdf"
IMAGE_URL = f"{BASE_URL}/img/vmr-images/{{name}}.png"

# CSV column mappings for projects
PROJECT_COLUMNS = {
    "name": "Name",
    "legacy_name": "Legacy Name",
    "image_number": "Image Number",
    "sex": "Sex",
    "age": "Age",
    "species": "Species",
    "ethnicity": "Ethnicity",
    "animal": "Animal",
    "anatomy": "Anatomy",
    "disease": "Disease",
    "procedure": "Procedure",
    "images": "Images",
    "paths": "Paths",
    "segmentations": "Segmentations",
    "models": "Models",
    "meshes": "Meshes",
    "simulations": "Simulations",
    "notes": "Notes",
    "doi": "DOI",
    "citation": "Citation",
    "image_manufacturer": "Image Manufacturer",
    "image_type": "Image Type",
    "image_source": "Image Source",
    "image_modality": "Image Modality",
    "results": "Results",
    "date_added": "Date Added",
    "order_uploaded": "Order Uploaded",
    "model_creator": "Model Creator",
}

# CSV column mappings for simulation results
RESULTS_COLUMNS = {
    "model_name": "Model Name",
    "full_filename": "Full Simulation File Name",
    "image_number": "Model Image Number",
    "short_name": "Short Simulation File Name",
    "legacy_name": "Legacy Simulation File Name",
    "fidelity": "Simulation Fidelity",
    "method": "Simulation Method",
    "condition": "Simulation Condition",
    "results_type": "Results Type",
    "file_type": "Results File Type",
    "creator": "Simulation Creator",
    "notes": "Notes",
}

# Species abbreviation mappings
SPECIES_CODES = {
    "H": "Human",
    "A": "Animal",
}

# Common anatomy abbreviation mappings
ANATOMY_CODES = {
    "AO": "Aorta",
    "CORO": "Coronary",
    "PULM": "Pulmonary",
    "PA": "Pulmonary Artery",
    "CA": "Cerebral Artery",
    "AORTO": "Aorto-iliac",
    "CEREB": "Cerebrovascular",
}

# Common disease abbreviation mappings
DISEASE_CODES = {
    "H": "Healthy",
    "CAD": "Coronary Artery Disease",
    "COA": "Coarctation of Aorta",
    "AAA": "Abdominal Aortic Aneurysm",
    "TAA": "Thoracic Aortic Aneurysm",
    "PAH": "Pulmonary Arterial Hypertension",
    "SVD": "Single Ventricle Defect",
    "MFS": "Marfan Syndrome",
    "KD": "Kawasaki Disease",
}

# Default cache settings
DEFAULT_CACHE_DIR = "~/.pyvmr"
CACHE_TTL_HOURS = 24

# Download settings
DEFAULT_CHUNK_SIZE = 8192
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1.0
