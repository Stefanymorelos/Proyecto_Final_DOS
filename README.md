# Proyecto DataOffice - Medicamentos Vitales No Disponibles

## Descripción del proyecto
Este proyecto desarrolla una solución de analítica de datos para el conjunto de datos **Medicamentos Vitales No Disponibles** de Datos Abiertos Colombia. El objetivo es transformar un dataset público en una base limpia, validada y útil para la toma de decisiones estratégicas relacionadas con abastecimiento, monitoreo y seguimiento de medicamentos críticos.

## Objetivo general
Diseñar un pipeline reproducible de limpieza, normalización y validación de datos, complementado con análisis exploratorio, para identificar patrones relevantes en las solicitudes de medicamentos vitales no disponibles en Colombia.

## Problema de negocio
Las autorizaciones de medicamentos vitales no disponibles reflejan necesidades críticas del sistema de salud. Sin embargo, los datos abiertos suelen venir con problemas de calidad, heterogeneidad semántica y posibles duplicados, lo cual dificulta su uso estratégico. Este proyecto busca convertir esos datos en información confiable para análisis institucional.

## Dataset utilizado
- **Nombre:** Medicamentos Vitales No Disponibles
- **Fuente:** Datos Abiertos Colombia / INVIMA
- **Formato:** CSV
- **Ubicación en el repositorio:** `data/raw/`

## Estructura del proyecto
```text
Proyecto-DataOffice/
│
├── data/
│   ├── raw/
│   │   └── MEDICAMENTOS_VITALES_NO_DISPONIBLES_20260420.csv
│   └── processed/
│       ├── dataset_clean.csv
│       ├── dataset_rejected.csv
│       ├── quality_summary.csv
│       ├── top_error_reasons.csv
│       └── suspected_duplicates.csv
│
├── documentacion/
│   ├── estrategia.md
│   ├── procesos_bpm.md
│   ├── arquitectura_datos.md
│   └── gobierno_datos.md
│
├── img/
│   └── diagrama_bpm.png
│
├── notebooks/
│   └── eda_medicamentos.ipynb
│
├── src/
│   └── proyecto_final_medicamentos.py
│
├── main.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Tecnologías utilizadas
- Python
- Pandas
- NumPy
- Pandera
- Jupyter Notebook

## Pipeline implementado
El pipeline realiza las siguientes tareas:

1. **Carga del dataset original**
2. **Estandarización de nombres de columnas**
3. **Limpieza y normalización de texto**
4. **Homologación de unidades de medida**
5. **Conversión de fechas y cantidades**
6. **Marcado de duplicados sospechosos**
7. **Validación con Pandera**
8. **Separación de registros válidos y rechazados**
9. **Generación de reportes de calidad**

## Salidas generadas
El pipeline produce los siguientes archivos en `data/processed/`:

- `dataset_clean.csv`: dataset validado y listo para análisis
- `dataset_rejected.csv`: registros rechazados con razón específica
- `quality_summary.csv`: resumen de calidad antes y después del procesamiento
- `top_error_reasons.csv`: principales causas de rechazo
- `suspected_duplicates.csv`: registros marcados como duplicados sospechosos

## Resultados actuales del procesamiento
- Filas originales: **10017**
- Filas válidas: **9957**
- Filas rechazadas: **60**
- Porcentaje de rechazo: **0.6%**
- Duplicados sospechosos: **958**

Los rechazos encontrados fueron:
- `cantidad_solicitada_not_nullable`: 59
- `fecha_de_autorizacion_fecha_futura`: 1

## Instalación
Desde la raíz del proyecto:

```bash
pip install -r requirements.txt
```

## Ejecución
Para correr el pipeline completo:

```bash
python main.py
```

## Análisis exploratorio
El notebook `notebooks/eda_medicamentos.ipynb` contiene un análisis exploratorio inicial del dataset limpio, incluyendo:
- evolución temporal de solicitudes
- principios activos más frecuentes
- tipos de solicitud
- principales importadores
- análisis de duplicados sospechosos