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
│   ├── Entrega_1 (Problema, estrategia, modelado inicial de procesos y boceto de arquitectura)
│   ├── Entrega_2 (Primer borrador del gobierno de datos: definición de roles, reglas y estándares)
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

El pipeline realiza las siguientes tareas en orden:

1. **Carga del dataset original** desde `data/raw/`
2. **Normalización de nombres de columnas** — sin tildes, minúsculas, sin espacios
3. **Limpieza y normalización de texto** — quita tildes, colapsa espacios, elimina placeholders (`NO REPORTA`, `-`, `N/A`)
4. **Homologación de unidades de medida** — estandariza variantes como `MG / ML → MG/ML`, `UG → MCG`
5. **Conversión de fechas** — formato INVIMA con fallback genérico para variaciones del CSV
6. **Conversión de cantidades** — maneja comas como separador de miles (`10,000 → 10000.0`)
7. **Normalización de campos secundarios** — marca `NO APLICA` cuando no hay segundo principio activo
8. **Derivación de nivel de urgencia** — variable construida desde `tipo_de_solicitud` como proxy de causa del desabastecimiento
9. **Marcado de duplicados sospechosos** — se conservan para revisión, no se eliminan
10. **Validación con Pandera** — esquema estricto sobre columnas críticas
11. **Separación de válidos y rechazados** — con razón específica por registro
12. **Generación de reportes de calidad** — métricas antes y después del procesamiento

## Salidas generadas

El pipeline produce los siguientes archivos en `data/processed/`:

| Archivo | Descripción |
|---|---|
| `dataset_clean.csv` | Dataset validado y listo para análisis |
| `dataset_rejected.csv` | Registros rechazados con razón específica |
| `quality_summary.csv` | Resumen de calidad antes y después del procesamiento |
| `top_error_reasons.csv` | Principales causas de rechazo |
| `suspected_duplicates.csv` | Registros marcados como duplicados sospechosos |

## Resultados del procesamiento

| Métrica | Valor |
|---|---|
| Filas originales | 10,017 |
| Filas válidas | 9,957 |
| Filas rechazadas | 60 |
| Porcentaje de rechazo | 0.6% |
| Duplicados sospechosos | 958 (9.6%) |
| Registros urgencia ALTA | 956 |
| Registros urgencia MEDIA | 3,467 |
| Registros urgencia BAJA | 5,594 |

**Razones de rechazo encontradas:**

| Error | Registros |
|---|---|
| `cantidad_solicitada_not_nullable` | 59 |
| `fecha_de_autorizacion_fecha_futura` | 1 |

El porcentaje de rechazo bajo (0.6%) indica buena calidad estructural del dataset publicado por INVIMA. Los 958 duplicados sospechosos (9.6%) se conservan en el dataset limpio con un flag `duplicado_flag` para revisión manual, dado que en el contexto de medicamentos vitales un duplicado puede representar una solicitud legítima repetida y no necesariamente un error.

## Análisis exploratorio (EDA)

El notebook `notebooks/eda_medicamentos.ipynb` contiene el análisis exploratorio completo del dataset limpio, incluyendo:

- **Evolución temporal anual** — el año con más solicitudes fue 2025 con 1,684 registros
- **Serie mensual de solicitudes** — detección de estacionalidad mes a mes
- **Patrón estacional** — marzo es históricamente el mes con más solicitudes
- **Tipo de solicitud y nivel de urgencia** — el 9.6% corresponde a urgencia clínica (ALTA)
- **Top 15 principios activos** — ELEXACAFTOR / TEZACAFTOR / IVACAFTOR lidera con 921 registros
- **Top 15 diagnósticos CIE-10** — Distrofia Muscular es el diagnóstico más frecuente (1,129 casos)
- **Cruce urgencia ALTA vs principio activo** — identifica medicamentos de mayor criticidad clínica
- **Concentración de importadores** — los 3 principales (AUDIFARMA, GLOBAL SERVICE PHARMACEUTICAL, VALENTECH) concentran el 29.2% de solicitudes
- **Distribución de cantidad solicitada** — mediana de 20 unidades, con outliers hasta 304,475
- **Análisis de duplicados sospechosos** — 958 registros marcados para revisión manual

## Sistema de alerta temprana — lógica implementada

El sistema de alerta temprana se construye sobre tres elementos derivados directamente del pipeline y el EDA:

### 1. Variable de nivel de urgencia (proxy de causa)

Dado que el dataset de INVIMA no incluye una columna explícita de causa del desabastecimiento, se derivó la variable `nivel_urgencia` a partir del tipo de solicitud:

| Tipo de solicitud | Nivel de urgencia | Interpretación |
|---|---|---|
| URGENCIA CLÍNICA | ALTA | Paciente en riesgo inmediato, sin alternativa terapéutica |
| MÁS DE UN PACIENTE | MEDIA | Escasez que afecta a múltiples pacientes simultáneamente |
| PACIENTE ESPECIFICO | BAJA | Necesidad individual, medicamento de difícil acceso |

### 2. Criterios de alerta

Un medicamento entra en estado de alerta cuando cumple alguna de estas condiciones:

- Su `nivel_urgencia` es **ALTA** (urgencia clínica activa)
- Aparece más de una vez en el mismo mes con nivel MEDIA o ALTA
- Su principio activo está en el **top 15 más solicitados históricamente**
- El diagnóstico asociado corresponde a una enfermedad huérfana o rara (alta dependencia de importación)

### 3. Respuesta al desabastecimiento según nivel

**Nivel ALTA — Urgencia clínica:**
- Activación inmediata del proceso de importación de emergencia ante INVIMA
- Notificación directa al Ministerio de Salud
- Priorización en el dashboard para visibilidad institucional

**Nivel MEDIA — Más de un paciente:**
- Monitoreo semanal del comportamiento del principio activo
- Revisión del historial de solicitudes del importador principal
- Evaluación de alternativas terapéuticas disponibles en el mercado nacional

**Nivel BAJA — Paciente específico:**
- Registro y seguimiento en el sistema
- Acumulación de datos para detección de tendencias emergentes
- Si el mismo medicamento acumula 3 o más solicitudes en un trimestre, escala a nivel MEDIA

### 4. Señales de riesgo identificadas en el EDA

- **Alta concentración de importadores**: los 3 principales importadores concentran el 29.2% de las solicitudes. Una falla en cualquiera de ellos genera un impacto sistémico inmediato.
- **Dependencia de medicamentos huérfanos**: Distrofia Muscular, Fibrosis Quística y Acondroplasia dominan los diagnósticos — enfermedades que dependen 100% de importación por ausencia de producción nacional.
- **Estacionalidad en marzo**: el mes de marzo concentra históricamente el mayor volumen de solicitudes, lo que permite anticipar picos de demanda y reforzar el inventario preventivamente.

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
