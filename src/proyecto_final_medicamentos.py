import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import pandera.pandas as pa

# 1. FUNCIONES BÁSICAS

def limpiar_nombre_columna(col):
    col = unicodedata.normalize("NFKD", col)
    col = "".join(c for c in col if not unicodedata.combining(c))
    col = col.lower().strip()
    col = re.sub(r"[^a-z0-9]+", "_", col)
    return col.strip("_")


def limpiar_texto(x):
    if pd.isna(x):
        return pd.NA

    x = str(x).strip().upper()
    x = re.sub(r"\s+", " ", x)

    if x in ["", "-", "N/A", "NAN", "NO REPORTADO"]:
        return pd.NA

    return x


def limpiar_unidad(x):
    x = limpiar_texto(x)
    if pd.isna(x):
        return pd.NA

    # normalización de caracteres y separadores
    x = x.replace("Μ", "M").replace("µ", "M")
    x = x.replace("MG / ML", "MG/ML")
    x = x.replace("UI / ML", "UI/ML")
    x = x.replace("MCG / ML", "MCG/ML")
    x = x.replace("GBQ / VIAL", "GBQ/VIAL")
    x = x.replace("MBQ / VIAL", "MBQ/VIAL")
    x = x.replace("MG / VIAL", "MG/VIAL")

    return x


def normalizar_no_aplica_secundarios(df):
    columnas_secundarias = [
        "principio_activo2",
        "concentracion_del_medicamento2",
        "unidad_medida2",
    ]

    existentes = [c for c in columnas_secundarias if c in df.columns]

    if len(existentes) == 3:
        mask_sin_segundo_principio = df["principio_activo2"].isna()

        df.loc[mask_sin_segundo_principio, "principio_activo2"] = "NO APLICA"
        df.loc[mask_sin_segundo_principio, "concentracion_del_medicamento2"] = "NO APLICA"
        df.loc[mask_sin_segundo_principio, "unidad_medida2"] = "NO APLICA"

    return df


def parsear_cantidad(x):
    if pd.isna(x):
        return np.nan

    x = str(x).replace(",", "").strip()

    try:
        return float(x)
    except ValueError:
        return np.nan

# 2. LIMPIEZA INICIAL

def estandarizar_dataset(df):
    df = df.copy()

    # Normalizar nombres de columnas
    df.columns = [limpiar_nombre_columna(c) for c in df.columns]

    # Limpiar texto
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].map(limpiar_texto)

    # Limpiar unidades
    for col in ["unidad_medida1", "unidad_medida2"]:
        if col in df.columns:
            df[col] = df[col].map(limpiar_unidad)

    # Fechas
    if "fecha_de_autorizacion" in df.columns:
        df["fecha_de_autorizacion"] = pd.to_datetime(
            df["fecha_de_autorizacion"],
            format="%Y %b %d %I:%M:%S %p",
            errors="coerce"
        )
        df["anio_autorizacion"] = df["fecha_de_autorizacion"].dt.year.astype("Int64")
        df["mes_autorizacion"] = df["fecha_de_autorizacion"].dt.month.astype("Int64")

    # Cantidades
    if "cantidad_solicitada" in df.columns:
        df["cantidad_solicitada"] = df["cantidad_solicitada"].map(parsear_cantidad)

    # No aplica en campos opcionales/estructurales
    df = normalizar_no_aplica_secundarios(df)

    # Marcar duplicados exactos, no eliminarlos
    df["duplicado_flag"] = df.duplicated(keep=False)

    return df

# 3. ESQUEMA PANDERA

VALID_TIPO_SOLICITUD = [
    "PACIENTE ESPECIFICO",
    "MÁS DE UN PACIENTE",
    "URGENCIA CLÍNICA"
]

schema = pa.DataFrameSchema(
    {
        "fecha_de_autorizacion": pa.Column(
            pa.DateTime,
            nullable=False,
            checks=[
                pa.Check.ge(pd.Timestamp("2018-01-01"), error="fecha_menor_a_2018"),
                pa.Check.le(pd.Timestamp.today().normalize(), error="fecha_futura")
            ]
        ),
        "tipo_de_solicitud": pa.Column(
            pa.String,
            nullable=False,
            checks=pa.Check.isin(VALID_TIPO_SOLICITUD, error="tipo_solicitud_invalido")
        ),
        "principio_activo1": pa.Column(
            pa.String,
            nullable=False,
            checks=pa.Check.str_length(min_value=2, error="principio_activo1_invalido")
        ),
        "cantidad_solicitada": pa.Column(
            float,
            nullable=False,
            checks=pa.Check.gt(0, error="cantidad_no_positiva")
        ),
        "codigo_diagnostico_cie_10": pa.Column(
            pa.String,
            nullable=True
        ),
        "anio_autorizacion": pa.Column(
            pa.Int64,
            nullable=True,
            checks=pa.Check.in_range(2018, 2030, error="anio_fuera_de_rango")
        ),
        "mes_autorizacion": pa.Column(
            pa.Int64,
            nullable=True,
            checks=pa.Check.in_range(1, 12, error="mes_fuera_de_rango")
        ),
        "duplicado_flag": pa.Column(
            bool,
            nullable=False
        ),
    },
    coerce=True,
    strict=False
)

# 4. SEPARAR VÁLIDOS Y RECHAZADOS

def validar_y_separar(df):
    try:
        validos = schema.validate(df, lazy=True)
        rechazados = pd.DataFrame(columns=list(df.columns) + ["error_reason"])
        return validos, rechazados

    except pa.errors.SchemaErrors as err:
        errores = err.failure_cases.copy()
        indices_invalidos = errores["index"].dropna().unique().tolist()

        rechazados = df.loc[df.index.isin(indices_invalidos)].copy()

        errores["detalle"] = errores["column"].astype(str) + "_" + errores["check"].astype(str)

        razones = (
            errores.groupby("index")["detalle"]
            .apply(lambda x: " | ".join(map(str, x)))
        )

        rechazados["error_reason"] = rechazados.index.map(razones)
        rechazados["error_reason"] = rechazados["error_reason"].fillna("error_desconocido")

        validos = df.loc[~df.index.isin(indices_invalidos)].copy()
        validos = schema.validate(validos, lazy=True)

        return validos, rechazados

# 5. RESUMEN

def resumen_calidad(df_raw, df_std, df_valid, df_rejected):
    resumen = pd.DataFrame({
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
        ],
        "valor": [
            len(df_raw),
            len(df_std),
            len(df_valid),
            len(df_rejected),
            round(len(df_rejected) / len(df_std) * 100, 2) if len(df_std) > 0 else 0,
            int(df_std["duplicado_flag"].sum()),
            int(df_std["fecha_de_autorizacion"].isna().sum()),
            int(df_valid["fecha_de_autorizacion"].isna().sum()),
            int(df_std["cantidad_solicitada"].isna().sum()),
            int(df_valid["cantidad_solicitada"].isna().sum()),
        ]
    })
    return resumen


def top_razones_rechazo(df_rejected):
    if df_rejected.empty:
        return pd.DataFrame(columns=["error_reason", "count"])

    conteo = (
        df_rejected["error_reason"]
        .value_counts()
        .rename_axis("error_reason")
        .reset_index(name="count")
    )
    return conteo


def resumen_duplicados(df_std):
    if "duplicado_flag" not in df_std.columns:
        return pd.DataFrame(columns=df_std.columns)

    return df_std[df_std["duplicado_flag"]].copy()

# 6. PIPELINE

def run_pipeline(input_file, output_dir):
    input_file = Path(input_file)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df_raw = pd.read_csv(input_file)
    df_std = estandarizar_dataset(df_raw)
    df_valid, df_rejected = validar_y_separar(df_std)

    summary = resumen_calidad(df_raw, df_std, df_valid, df_rejected)
    top_errors = top_razones_rechazo(df_rejected)
    df_duplicados = resumen_duplicados(df_std)

    df_valid.to_csv(output_dir / "dataset_clean.csv", index=False)
    df_rejected.to_csv(output_dir / "dataset_rejected.csv", index=False)
    summary.to_csv(output_dir / "quality_summary.csv", index=False)
    top_errors.to_csv(output_dir / "top_error_reasons.csv", index=False)
    df_duplicados.to_csv(output_dir / "suspected_duplicates.csv", index=False)

    print(summary)
    print("\nPrincipales razones de rechazo:")
    if not df_rejected.empty:
        print(df_rejected["error_reason"].value_counts().head(10))
    else:
        print("No hubo registros rechazados.")

    print(f"\nArchivos guardados en: {output_dir.resolve()}")

    return df_valid, df_rejected, summary


if __name__ == "__main__":
    print("Ejecuta el proyecto desde main.py")