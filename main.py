from pathlib import Path
from src.pipeline_medicamentos import run_pipeline
from src.duplicados import run_duplicados

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

csv_files = list(RAW_DIR.glob("*.csv"))
if len(csv_files) == 0:
    raise FileNotFoundError("No se encontró ningún archivo CSV en data/raw")

INPUT_FILE = max(csv_files, key=lambda f: f.stat().st_mtime)

if __name__ == "__main__":
    print(f"Archivo seleccionado: {INPUT_FILE.name}")
    
    # Paso 1 — pipeline principal
    run_pipeline(str(INPUT_FILE), str(OUTPUT_DIR))
    
    # Paso 2 — tratamiento de duplicados
    run_duplicados(
        clean_path=str(OUTPUT_DIR / "dataset_clean.csv"),
        output_dir=str(OUTPUT_DIR),
    )