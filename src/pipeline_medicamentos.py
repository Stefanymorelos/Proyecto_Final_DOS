"""
Pipeline de limpieza, validación y gobierno de datos
Dataset: Medicamentos Vitales No Disponibles — INVIMA / datos.gov.co
Universidad Pontificia Bolivariana — Data Office Strategy
"""

import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import pandera.pandas as pa

# =============================================================================
# 1. FUNCIONES DE LIMPIEZA
# =============================================================================

def limpiar_nombre_columna(col: str) -> str:
    """Normaliza nombres de columna: sin tildes, minúsculas, sin espacios."""
    col = unicodedata.normalize("NFKD", col)
    col = "".join(c for c in col if not unicodedata.combining(c))
    col = col.lower().strip()
    col = re.sub(r"[^a-z0-9]+", "_", col)
    return col.strip("_")


def quitar_tildes(texto: str) -> str:
    """Elimina tildes/diacríticos de un string ya en mayúsculas."""
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


def limpiar_texto(x):
    """
    Limpieza general de texto:
    - Elimina nulos y cadenas vacías/placeholder
    - Convierte a mayúsculas
    - Quita tildes para homologar variantes (FARMACÉUTICO = FARMACEUTICO)
    - Colapsa espacios múltiples y saltos de línea
    """
    if pd.isna(x):
        return pd.NA

    x = str(x).strip()
    x = re.sub(r"[\r\n\t]+", " ", x)   # saltos de línea en PRESENTACIÓN_COMERCIAL
    x = re.sub(r"\s+", " ", x)
    x = x.upper()
    x = quitar_tildes(x)

    if x in {"", "-", "N/A", "NAN", "NO REPORTADO", "NO REPORTA", "SIN DATO"}:
        return pd.NA

    return x


def limpiar_unidad(x):
    """Normaliza unidades de medida homologando separadores y símbolos."""
    x = limpiar_texto(x)
    if pd.isna(x):
        return pd.NA

    reemplazos = {
        "Μ": "M", "µ": "M",
        "MG / ML": "MG/ML",
        "UI / ML": "UI/ML",
        "MCG / ML": "MCG/ML",
        "GBQ / VIAL": "GBQ/VIAL",
        "MBQ / VIAL": "MBQ/VIAL",
        "MG / VIAL": "MG/VIAL",
        "UG/ML": "MCG/ML",          # variante común
        "UG": "MCG",
    }
    for original, normalizado in reemplazos.items():
        x = x.replace(original, normalizado)

    return x


def normalizar_campos_secundarios(df: pd.DataFrame) -> pd.DataFrame:
    """
    Si no hay segundo principio activo, marca los campos secundarios
    como 'NO APLICA' en lugar de dejarlos nulos.
    """
    cols = ["principio_activo2", "concentracion_del_medicamento2", "unidad_medida2"]
    existentes = [c for c in cols if c in df.columns]

    if len(existentes) == 3:
        sin_segundo = df["principio_activo2"].isna()
        for col in existentes:
            df.loc[sin_segundo, col] = "NO APLICA"

    return df


def parsear_cantidad(x) -> float:
    """
    Convierte cantidad a float.
    Maneja comas como separador de miles (10,000 → 10000.0).
    """
    if pd.isna(x):
        return np.nan
    x = str(x).replace(",", "").strip()
    try:
        val = float(x)
        return val if val > 0 else np.nan
    except ValueError:
        return np.nan


def parsear_fecha(serie: pd.Series) -> pd.Series:
    """
    Intenta parsear fechas con el formato del dataset de INVIMA.
    Si falla, intenta parseo genérico como fallback.
    """
    resultado = pd.to_datetime(serie, format="%Y %b %d %I:%M:%S %p", errors="coerce")
    # Fallback para filas que no matchearon el formato principal
    mask_nat = resultado.isna()
    if mask_nat.any():
        resultado[mask_nat] = pd.to_datetime(serie[mask_nat], errors="coerce")
    return resultado


def clasificar_urgencia(tipo) -> str:
    """
    Derivar nivel de urgencia a partir del tipo de solicitud.
    Aproximación a 'causa/severidad' del desabastecimiento.
    """
    if pd.isna(tipo):
        return "DESCONOCIDO"
    tipo = str(tipo).upper()
    if "URGENCIA" in tipo:
        return "ALTA"
    elif "MAS DE UN PACIENTE" in tipo or "MÁS DE UN PACIENTE" in tipo:
        return "MEDIA"
    elif "PACIENTE ESPECIFICO" in tipo or "PACIENTE ESPECÍFICO" in tipo:
        return "BAJA"
    return "DESCONOCIDO"


# =============================================================================
# 2. ESTANDARIZACIÓN COMPLETA
# =============================================================================

def estandarizar_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica todas las transformaciones de limpieza y normalización al dataset.
    No elimina filas — marca problemas con flags para decisión posterior.
    """
    df = df.copy()

    # --- Nombres de columnas ---
    df.columns = [limpiar_nombre_columna(c) for c in df.columns]

    # Renombrar columna de diagnóstico que viene mal formateada en el CSV
    rename_map = {}
    for col in df.columns:
        if "diagnostico_cie" in col and "codigo" not in col:
            rename_map[col] = "diagnostico_descripcion"
        elif "codigo_diagnostico" in col:
            rename_map[col] = "codigo_diagnostico_cie10"
    if rename_map:
        df = df.rename(columns=rename_map)

    # --- Limpiar texto en columnas object ---
    cols_texto = df.select_dtypes(include="object").columns.tolist()
    for col in cols_texto:
        df[col] = df[col].map(limpiar_texto)

    # --- Unidades ---
    for col in ["unidad_medida1", "unidad_medida2"]:
        if col in df.columns:
            df[col] = df[col].map(limpiar_unidad)

    # --- Fechas ---
    if "fecha_de_autorizacion" in df.columns:
        df["fecha_de_autorizacion"] = parsear_fecha(df["fecha_de_autorizacion"])
        df["anio_autorizacion"] = df["fecha_de_autorizacion"].dt.year.astype("Int64")
        df["mes_autorizacion"] = df["fecha_de_autorizacion"].dt.month.astype("Int64")

    # --- Cantidad solicitada ---
    if "cantidad_solicitada" in df.columns:
        df["cantidad_solicitada"] = df["cantidad_solicitada"].map(parsear_cantidad)

    # --- Campos secundarios ---
    df = normalizar_campos_secundarios(df)

    # --- Variable derivada: nivel de urgencia (proxy de causa) ---
    if "tipo_de_solicitud" in df.columns:
        df["nivel_urgencia"] = df["tipo_de_solicitud"].map(clasificar_urgencia)

    # --- Flag de duplicados exactos (no se eliminan) ---
    df["duplicado_flag"] = df.duplicated(keep=False)

    return df


# =============================================================================
# 3. ESQUEMA DE VALIDACIÓN PANDERA
# =============================================================================

TIPOS_SOLICITUD_VALIDOS = [
    "PACIENTE ESPECIFICO",
    "MAS DE UN PACIENTE",
    "URGENCIA CLINICA",
]

NIVELES_URGENCIA_VALIDOS = ["ALTA", "MEDIA", "BAJA", "DESCONOCIDO"]

schema = pa.DataFrameSchema(
    {
        "fecha_de_autorizacion": pa.Column(
            pa.DateTime,
            nullable=False,
            checks=[
                pa.Check.ge(pd.Timestamp("2018-01-01"), error="fecha_menor_a_2018"),
                pa.Check.le(pd.Timestamp.today().normalize(), error="fecha_futura"),
            ],
        ),
        "tipo_de_solicitud": pa.Column(
            pa.String,
            nullable=False,
            checks=pa.Check.isin(TIPOS_SOLICITUD_VALIDOS, error="tipo_solicitud_invalido"),
        ),
        "principio_activo1": pa.Column(
            pa.String,
            nullable=False,
            checks=pa.Check.str_length(min_value=2, error="principio_activo1_muy_corto"),
        ),
        "cantidad_solicitada": pa.Column(
            float,
            nullable=False,
            checks=pa.Check.gt(0, error="cantidad_no_positiva"),
        ),
        "codigo_diagnostico_cie10": pa.Column(
            pa.String,
            nullable=True,
            checks=pa.Check.str_length(min_value=2, error="codigo_cie10_muy_corto"),
        ),
        "nivel_urgencia": pa.Column(
            pa.String,
            nullable=False,
            checks=pa.Check.isin(NIVELES_URGENCIA_VALIDOS, error="nivel_urgencia_invalido"),
        ),
        "anio_autorizacion": pa.Column(
            pa.Int64,
            nullable=True,
            checks=pa.Check.in_range(2018, 2030, error="anio_fuera_de_rango"),
        ),
        "mes_autorizacion": pa.Column(
            pa.Int64,
            nullable=True,
            checks=pa.Check.in_range(1, 12, error="mes_fuera_de_rango"),
        ),
        "duplicado_flag": pa.Column(bool, nullable=False),
    },
    coerce=True,
    strict=False,
)


# =============================================================================
# 4. SEPARAR VÁLIDOS Y RECHAZADOS
# =============================================================================

def validar_y_separar(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Valida el dataframe con el schema Pandera.
    Retorna (válidos, rechazados) donde rechazados incluye la razón del error.
    """
    try:
        validos = schema.validate(df, lazy=True)
        rechazados = pd.DataFrame(columns=list(df.columns) + ["error_reason"])
        return validos, rechazados

    except pa.errors.SchemaErrors as err:
        errores = err.failure_cases.copy()
        indices_invalidos = errores["index"].dropna().unique().tolist()

        rechazados = df.loc[df.index.isin(indices_invalidos)].copy()

        errores["detalle"] = (
            errores["column"].astype(str) + "_" + errores["check"].astype(str)
        )
        razones = (
            errores.groupby("index")["detalle"]
            .apply(lambda x: " | ".join(map(str, x)))
        )
        rechazados["error_reason"] = rechazados.index.map(razones).fillna(
            "error_desconocido"
        )

        validos = df.loc[~df.index.isin(indices_invalidos)].copy()
        validos = schema.validate(validos, lazy=True)

        return validos, rechazados


# =============================================================================
# 5. REPORTES DE CALIDAD
# =============================================================================

def resumen_calidad(

    df_raw: pd.DataFrame,
    df_std: pd.DataFrame,
    df_valid: pd.DataFrame,
    df_rejected: pd.DataFrame,
) -> pd.DataFrame:
    """Genera métricas de calidad antes y después del proceso de validación para evaluar el impacto del pipeline."""
    pct_rechazo = (
        round(len(df_rejected) / len(df_std) * 100, 2) if len(df_std) > 0 else 0
    )

    resumen = pd.DataFrame(
        {
            "metrica": [
                "filas_originales",
                "filas_estandarizadas",
                "filas_validas",
                "filas_rechazadas",
                "porcentaje_rechazo",
                "duplicados_sospechosos",
                "nulos_fecha_antes",
                "nulos_fecha_despues",
                "nulos_cantidad_antes",
                "nulos_cantidad_despues",
                "registros_urgencia_alta",
                "registros_urgencia_media",
                "registros_urgencia_baja",
            ],
            "valor": [
                len(df_raw),
                len(df_std),
                len(df_valid),
                len(df_rejected),
                pct_rechazo,
                int(df_std["duplicado_flag"].sum()),
                int(df_std["fecha_de_autorizacion"].isna().sum()),
                int(df_valid["fecha_de_autorizacion"].isna().sum()),
                int(df_std["cantidad_solicitada"].isna().sum()),
                int(df_valid["cantidad_solicitada"].isna().sum()),
                int((df_valid["nivel_urgencia"] == "ALTA").sum()),
                int((df_valid["nivel_urgencia"] == "MEDIA").sum()),
                int((df_valid["nivel_urgencia"] == "BAJA").sum()),
            ],
        }
    )
    return resumen


def top_razones_rechazo(df_rejected: pd.DataFrame) -> pd.DataFrame:
    if df_rejected.empty:
        return pd.DataFrame(columns=["error_reason", "count"])
    return (
        df_rejected["error_reason"]
        .value_counts()
        .rename_axis("error_reason")
        .reset_index(name="count")
    )


def resumen_duplicados(df_std: pd.DataFrame) -> pd.DataFrame:
    if "duplicado_flag" not in df_std.columns:
        return pd.DataFrame(columns=df_std.columns)
    return df_std[df_std["duplicado_flag"]].copy()


# =============================================================================
# PIPELINE DE CALIDAD DE DATOS
# =============================================================================
# Flujo:
# 1. Carga dataset raw
# 2. Limpieza y estandarización
# 3. Validación con Pandera
# 4. Separación de registros inválidos
# 5. Generación de reportes de calidad
# =============================================================================

def run_pipeline(
    input_file: str, output_dir: str
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Ejecuta el pipeline completo:
      1. Carga el CSV raw
      2. Estandariza y limpia
      3. Valida con Pandera
      4. Genera reportes de calidad
      5. Guarda todos los outputs en output_dir

    Retorna: (df_valid, df_rejected, summary)
    """
    input_file = Path(input_file)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"{'='*60}")
    print("PIPELINE — Medicamentos Vitales No Disponibles")
    print(f"{'='*60}")

    # Carga
    print(f"\n[1/4] Cargando: {input_file.name}")
    df_raw = pd.read_csv(input_file)
    print(f"      Filas cargadas: {len(df_raw):,}")

    # Estandarización
    print("[2/4] Estandarizando y limpiando...")
    df_std = estandarizar_dataset(df_raw)
    print(f"      Columnas resultantes: {list(df_std.columns)}")

    # Validación
    print("[3/4] Validando con Pandera...")
    df_valid, df_rejected = validar_y_separar(df_std)
    print(f"      Válidos:    {len(df_valid):,}")
    print(f"      Rechazados: {len(df_rejected):,}")

    # Reportes
    print("[4/4] Generando reportes de calidad...")
    summary = resumen_calidad(df_raw, df_std, df_valid, df_rejected)
    top_errors = top_razones_rechazo(df_rejected)
    df_duplicados = resumen_duplicados(df_std)

    # Guardar outputs
    df_valid.to_csv(output_dir / "dataset_clean.csv", index=False)
    df_rejected.to_csv(output_dir / "dataset_rejected.csv", index=False)
    summary.to_csv(output_dir / "quality_summary.csv", index=False)
    top_errors.to_csv(output_dir / "top_error_reasons.csv", index=False)
    df_duplicados.to_csv(output_dir / "suspected_duplicates.csv", index=False)

    print(f"\n{'='*60}")
    print("RESUMEN DE CALIDAD")
    print(f"{'='*60}")
    print(summary.to_string(index=False))

    if not df_rejected.empty:
        print(f"\nPrincipales razones de rechazo:")
        print(top_errors.to_string(index=False))

    print(f"\n✓ Archivos guardados en: {output_dir.resolve()}")
    print(f"{'='*60}\n")

    return df_valid, df_rejected, summary


if __name__ == "__main__":
    print("Ejecuta el proyecto desde main.py")
