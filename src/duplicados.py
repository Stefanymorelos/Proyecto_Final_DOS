"""
Módulo de tratamiento de duplicados — Medicamentos Vitales No Disponibles
Universidad Pontificia Bolivariana — Data Office Strategy

Ubicación en el proyecto:
  src/duplicados.py

Se llama DESPUÉS de run_pipeline() en main.py, usando dataset_clean.csv como entrada.
El output es dataset_final.csv — este es el CSV que alimenta el dashboard.

Criterios implementados:
  C1-B  Más de 2 registros idénticos mismo día          → ELIMINAR automático
  C1-C  2 registros idénticos, cantidad > 1,000         → ELIMINAR automático
  C1-D  Urgencia clínica en duplicado                   → CONSERVAR automático
  C1-E  2 registros idénticos, cantidad <= 100          → CONSERVAR automático
  C2    Mismas columnas, cantidades distintas            → CONSERVAR automático
  C3    Días de diferencia (renovación periódica)       → CONSERVAR automático
  C4    Urgencia clínica general                        → CONSERVAR automático
  AMBIGUO 2 registros, cantidad entre 101 y 1,000      → revisión humana (29 casos)
"""

from pathlib import Path
import pandas as pd


# =============================================================================
# CLASIFICACIÓN
# =============================================================================

def _clasificar_grupo(grupo: pd.DataFrame) -> list[str]:
    """
    Clasifica cada fila de un grupo con mismo principio activo,
    importador y fecha según los criterios definidos.
    """
    if len(grupo) == 1:
        return ["UNICO"] * len(grupo)

    decisiones = []
    n = len(grupo)
    cantidades_str = grupo["cantidad_solicitada"].astype(str)
    cantidades_num = pd.to_numeric(
        grupo["cantidad_solicitada"].astype(str).str.replace(",", ""),
        errors="coerce",
    )
    todas_iguales = cantidades_str.nunique() == 1
    cantidad_val  = cantidades_num.iloc[0] if todas_iguales else None

    for _, fila in grupo.iterrows():
        tipo = str(fila.get("tipo_de_solicitud", "")).upper()

        # C4 — Urgencia clínica: conservar siempre sin importar nada más
        if "URGENCIA" in tipo:
            decisiones.append("CONSERVAR_C4")

        # Cantidades distintas → pacientes diferentes (C2)
        elif not todas_iguales:
            decisiones.append("CONSERVAR_C2")

        # A partir de aquí: todos los registros del grupo tienen cantidad idéntica

        # C1-B — Más de 2 registros idénticos → error de carga masivo
        elif n > 2:
            decisiones.append("ELIMINAR_C1B")

        # C1-C — 2 registros, cantidad alta → volumen incompatible con paciente único
        elif cantidad_val is not None and cantidad_val > 1000:
            decisiones.append("ELIMINAR_C1C")

        # C1-E — 2 registros, cantidad baja → dosis individual, pacientes distintos
        elif cantidad_val is not None and cantidad_val <= 100:
            decisiones.append("CONSERVAR_C1E")

        # AMBIGUO — 2 registros, cantidad entre 101 y 1,000 → revisión humana
        else:
            decisiones.append("AMBIGUO")

    return decisiones


# =============================================================================
# PIPELINE PRINCIPAL
# =============================================================================

def run_duplicados(
    clean_path: str,
    output_dir: str,
    revision_path: str = None,
) -> pd.DataFrame:
    """
    Trata los duplicados del dataset limpio y genera dataset_final.csv.

    Parámetros:
      clean_path    : ruta a dataset_clean.csv
      output_dir    : carpeta de salida (data/processed/)
      revision_path : ruta al CSV con decisiones del Data Steward sobre
                      los AMBIGUOS (opcional). Si no existe, los AMBIGUOS
                      se conservan por defecto.

    Outputs generados:
      dataset_final.csv        → dataset limpio sin duplicados, listo para dashboard
      revision_ambiguos.csv    → los 29 casos ambiguos para revisión humana
      reporte_duplicados.csv   → trazabilidad completa de decisiones
      registros_eliminados.csv → registros eliminados con razón
    """
    clean_path = Path(clean_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("TRATAMIENTO DE DUPLICADOS")
    print("=" * 60)

    # ── Cargar dataset limpio ────────────────────────────────────────────────
    print(f"\n[1/4] Cargando: {clean_path.name}")
    df = pd.read_csv(clean_path)
    print(f"      Registros: {len(df):,}")

    # ── Clasificar ───────────────────────────────────────────────────────────
    print("\n[2/4] Clasificando duplicados...")

    cols_grupo = ["principio_activo1", "solicitante_importador", "fecha_de_autorizacion"]

    df["decision_duplicado"] = (
        df.groupby(cols_grupo, group_keys=False)
        .apply(lambda g: pd.Series(_clasificar_grupo(g), index=g.index))
    )

    dist = df["decision_duplicado"].value_counts()
    print("\n      Distribución de decisiones:")
    for decision, count in dist.items():
        simbolo = "✓" if "CONSERVAR" in decision or decision == "UNICO" else "✗" if "ELIMINAR" in decision else "?"
        print(f"      {simbolo}  {decision:<20} {count:>6} registros")

    # ── Aplicar decisiones del Data Steward sobre AMBIGUOS ──────────────────
    print("\n[3/4] Procesando casos ambiguos...")

    ambiguos = df[df["decision_duplicado"] == "AMBIGUO"].copy()
    print(f"      Casos ambiguos encontrados: {len(ambiguos)}")

    if len(ambiguos) > 0:
        # Generar archivo para revisión humana
        ambiguos_rev = ambiguos.copy()
        ambiguos_rev["decision_data_steward"] = "CONSERVAR"  # default: conservar
        ambiguos_rev["justificacion"] = ""
        ruta_ambiguos = output_dir / "revision_ambiguos.csv"
        ambiguos_rev.to_csv(ruta_ambiguos, index=True)
        print(f"      Archivo generado: revision_ambiguos.csv")

        # Leer decisiones si el Data Steward ya revisó
        if revision_path and Path(revision_path).exists():
            rev = pd.read_csv(revision_path, index_col=0)
            indices_rev = rev.index[rev.index.isin(df.index)]
            for idx in indices_rev:
                dec = str(rev.loc[idx, "decision_data_steward"]).strip().upper()
                if dec == "ELIMINAR":
                    df.loc[idx, "decision_duplicado"] = "ELIMINAR_AMBIGUO"
                else:
                    df.loc[idx, "decision_duplicado"] = "CONSERVAR_AMBIGUO"
            print(f"      Decisiones del Data Steward aplicadas: {len(indices_rev)}")
        else:
            # Sin revisión: conservar por defecto (decisión conservadora)
            df.loc[df["decision_duplicado"] == "AMBIGUO", "decision_duplicado"] = "CONSERVAR_AMBIGUO"
            print("      Sin revisión del Data Steward → AMBIGUOS conservados por defecto")

    # ── Separar y guardar ────────────────────────────────────────────────────
    print("\n[4/4] Generando outputs...")

    mask_eliminar = df["decision_duplicado"].str.startswith("ELIMINAR")
    df_final      = df[~mask_eliminar].copy()
    df_eliminados = df[mask_eliminar].copy()

    # Reporte de trazabilidad
    reporte = (
        df["decision_duplicado"]
        .value_counts()
        .rename_axis("decision")
        .reset_index(name="registros")
    )
    reporte["accion"] = reporte["decision"].apply(
        lambda x: "ELIMINADO" if "ELIMINAR" in x else "CONSERVADO"
    )

    # Guardar
    df_final.to_csv(output_dir / "dataset_final.csv", index=False)
    df_eliminados.to_csv(output_dir / "registros_eliminados.csv", index=False)
    reporte.to_csv(output_dir / "reporte_duplicados.csv", index=False)

    print(f"\n{'='*60}")
    print("RESUMEN FINAL")
    print(f"{'='*60}")
    print(f"  Registros entrada:   {len(df):>6,}")
    print(f"  Registros eliminados:{len(df_eliminados):>6,}")
    print(f"  Registros finales:   {len(df_final):>6,}")
    print(f"\n  ✓ dataset_final.csv listo para el dashboard")
    print(f"{'='*60}\n")

    return df_final
