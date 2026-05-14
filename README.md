# Proyecto DataOffice — Medicamentos Vitales No Disponibles

## Descripción

Solución de analítica de datos sobre el dataset **Medicamentos Vitales No Disponibles** de INVIMA / datos.gov.co. Transforma datos abiertos en información confiable para la toma de decisiones estratégicas sobre abastecimiento de medicamentos críticos en Colombia.

## Dataset

- **Fuente:** Datos Abiertos Colombia — datos.gov.co / INVIMA
- **Identificador:** `sdmr-tfmf`
- **Ubicación:** `data/raw/`

## Estructura del proyecto

```text
Proyecto-DataOffice/ 
├── data/
│   ├── raw/                          ← CSV original INVIMA
│   └── processed/                    ← Outputs del pipeline
│       ├── dataset_clean.csv         ← Dataset validado
│       ├── dataset_final.csv         ← Dataset sin duplicados (dashboard)
│       ├── dataset_rejected.csv      ← Registros rechazados
│       ├── quality_summary.csv       ← Resumen de calidad
│       ├── registros_eliminados.csv  ← Duplicados eliminados
│       ├── revision_ambiguos.csv     ← Casos ambiguos conservados
│       └── reporte_duplicados.csv    ← Trazabilidad de decisiones
├── documentacion/
│   ├── Entrega_1.pdf                 ← Problema, estrategia y BPM
│   ├── Entrega_2.md                  ← Gobierno de datos
│   ├── tratamiento_duplicados.md     ← Criterios de duplicados
│   └── Presentacion.pptx             ← Presentación final del proyecto
├── img/
│   └── diagrama_bpm.png
├── notebooks/
│   └── eda_medicamentos.ipynb
├── src/
│   ├── pipeline_medicamentos.py      ← Pipeline principal
│   └── duplicados.py                 ← Tratamiento de duplicados
├── dashboard/
│   └── app.py                        ← Dashboard Plotly Dash
├── main.py
├── requirements.txt
└── README.md
```

## Tecnologías

Python 3.12 — Pandas — NumPy — Pandera — Matplotlib — Plotly Dash

## Pipeline

`main.py` ejecuta dos etapas en secuencia:

**Etapa 1 — Limpieza y validación** (`src/pipeline_medicamentos.py`):
1. Normalización de columnas, texto, tildes y unidades
2. Conversión de fechas y cantidades
3. Derivación de `nivel_urgencia` como proxy de causa
4. Validación con schema Pandera
5. Separación de válidos y rechazados

**Etapa 2 — Tratamiento de duplicados** (`src/duplicados.py`):

| Criterio | Condición | Decisión |
|---|---|---|
| C1-B | >2 registros idénticos mismo día | ELIMINAR |
| C1-C | 2 registros, cantidad > 1,000 | ELIMINAR |
| C1-D | Urgencia clínica | CONSERVAR |
| C1-E | 2 registros, cantidad ≤ 100 | CONSERVAR |
| C2 | Cantidades distintas mismo día | CONSERVAR |
| AMBIGUO | 2 registros, cantidad 101-1,000 | CONSERVAR |

## Resultados del procesamiento

| Métrica | Valor |
|---|---|
| Filas originales | 10,017 |
| Filas válidas (dataset_clean) | 9,955 |
| Filas rechazadas | 62 (0.6%) |
| Duplicados eliminados | 513 |
| **Registros finales (dataset_final)** | **9,442** |

**Razones de rechazo:**

| Error | Registros |
|---|---|
| `cantidad_solicitada_not_nullable` | 59 |
| `codigo_diagnostico_cie10_muy_corto` | 2 |
| `fecha_de_autorizacion_fecha_futura` | 1 |

## Nivel de urgencia — proxy de causa

| Tipo de solicitud | Nivel | Registros |
|---|---|---|
| URGENCIA CLÍNICA | ALTA | 954 (9.6%) |
| MÁS DE UN PACIENTE | MEDIA | 3,425 (34.4%) |
| PACIENTE ESPECIFICO | BAJA | 5,576 (56%) |

## Señales de riesgo identificadas

- **Concentración de importadores** — 3 actores concentran el 29.2% de solicitudes
- **Enfermedades huérfanas** — Distrofia Muscular (1,129), Fibrosis Quística (922) sin producción nacional
- **Tendencia creciente** — de 710 solicitudes en 2020 a 1,688 en 2025

## Instalación y ejecución

```bash
pip install -r requirements.txt
python main.py
```

Dashboard:
```bash
pip install dash plotly
python dashboard/app.py
```
Abre `http://127.0.0.1:8050`

## Gobierno de datos

Documentado en `documentacion/Entrega_2.md` y `documentacion/tratamiento_duplicados.md`. Incluye roles, catálogo de 14 campos, 10 reglas de calidad y trazabilidad completa del linaje de datos.
