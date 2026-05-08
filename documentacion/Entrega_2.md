# Gobierno de Datos — Medicamentos Vitales No Disponibles

**Universidad Pontificia Bolivariana | Data Office Strategy**
Segunda Entrega Parcial — Mayo 2026
Fuente: INVIMA / datos.gov.co — dataset `sdmr-tfmf`

---

## 1. Introducción

El gobierno de datos es el conjunto de políticas, procesos, roles y estándares que garantizan que los datos de una organización sean confiables, consistentes, seguros y utilizables para la toma de decisiones.

En este proyecto, el gobierno de datos define cómo se gestiona el dataset de Medicamentos Vitales No Disponibles publicado por INVIMA, desde su ingesta hasta su uso en el sistema de alerta temprana. Este documento está alineado con los roles del diagrama BPM de la primera entrega y con los resultados del pipeline de limpieza implementado.

---

## 2. Roles y Responsabilidades

El modelo adopta los cuatro roles definidos en el diagrama BPMN del proyecto, cada uno responsable de una capa específica del pipeline.

| Rol | Responsable | Responsabilidades principales | Herramientas |
|---|---|---|---|
| Data Analyst | Equipo analítica | Identificar fuentes, registrar solicitudes de ingesta, definir requisitos de negocio | datos.gov.co, GitHub |
| Data Engineer | Equipo ingeniería | Extraer, cargar y validar datos en capa Bronze/Raw, corregir errores técnicos | Python, Pandas, Pandera, GitHub |
| Data Steward | Equipo gobierno | Aplicar reglas de calidad, estandarizar datos, gestionar catálogo y políticas | Great Expectations, Python |
| Plataforma BI | Equipo visualización | Publicar dataset en capa Gold, actualizar dashboards y generar alertas tempranas | Plotly Dash |

> En el contexto académico del proyecto, cada miembro del equipo asume uno o más roles de forma rotativa, garantizando que todos comprenden el flujo completo de datos.

---

## 3. Catálogo de Datos

Documenta todos los campos del dataset limpio (`dataset_clean.csv`). Es la referencia oficial para cualquier análisis o visualización que consuma los datos del proyecto.

| Campo | Tipo | Obligatorio | Valores válidos | Descripción |
|---|---|---|---|---|
| `fecha_de_autorizacion` | DateTime | Sí | 2018-01-01 → hoy | Fecha en que INVIMA autorizó la importación del medicamento |
| `tipo_de_solicitud` | String | Sí | PACIENTE ESPECIFICO / MAS DE UN PACIENTE / URGENCIA CLINICA | Clasificación del tipo de necesidad que origina la solicitud |
| `solicitante_importador` | String | No | Texto libre normalizado | Empresa o entidad que realiza la solicitud de importación |
| `principio_activo1` | String | Sí | Mín. 2 caracteres | Sustancia farmacológica activa principal del medicamento |
| `concentracion_del_medicamento1` | String | No | Texto normalizado | Concentración del principio activo primario |
| `unidad_medida1` | String | No | MG, ML, UI, MCG, etc. | Unidad de medida homologada por el pipeline |
| `principio_activo2` | String | No | NO APLICA si no existe | Segundo principio activo en medicamentos combinados |
| `cantidad_solicitada` | Float | Sí | > 0 | Número de unidades solicitadas para importación |
| `diagnostico_descripcion` | String | No | Descripción CIE-10 | Diagnóstico clínico asociado a la solicitud |
| `codigo_diagnostico_cie10` | String | No | Mín. 2 caracteres | Código alfanumérico del diagnóstico CIE-10 |
| `nivel_urgencia` | String | Sí | ALTA / MEDIA / BAJA / DESCONOCIDO | Variable derivada del tipo de solicitud — proxy del nivel de criticidad |
| `duplicado_flag` | Boolean | Sí | True / False | Marca registros posiblemente duplicados. Se conservan para revisión manual |
| `anio_autorizacion` | Int64 | No | 2018–2030 | Año extraído de la fecha de autorización |
| `mes_autorizacion` | Int64 | No | 1–12 | Mes extraído de la fecha de autorización |

> `nivel_urgencia` es una variable **derivada** — no existe en el dataset original de INVIMA. Fue construida por el pipeline desde `tipo_de_solicitud` como proxy del nivel de criticidad, dado que el dataset no incluye una columna explícita de causa del desabastecimiento.

---

## 4. Reglas de Calidad de Datos

Definen los criterios que debe cumplir cada registro para ser válido. Están implementadas en el pipeline mediante el esquema Pandera (`proyecto_final_medicamentos.py`).

| Regla | Descripción | Acción si falla | Responsable |
|---|---|---|---|
| R01 — Fecha válida | `fecha_de_autorizacion` debe estar entre 2018-01-01 y la fecha actual | Registro rechazado: `fecha_futura` | Data Engineer |
| R02 — Tipo solicitud | `tipo_de_solicitud` debe pertenecer a los 3 valores definidos | Registro rechazado: `tipo_solicitud_invalido` | Data Engineer |
| R03 — Principio activo | `principio_activo1` no puede ser nulo ni menor a 2 caracteres | Registro rechazado: `principio_activo1_muy_corto` | Data Engineer |
| R04 — Cantidad positiva | `cantidad_solicitada` debe ser un número mayor a 0 | Registro rechazado: `cantidad_no_positiva` | Data Engineer |
| R05 — Nivel urgencia | `nivel_urgencia` debe ser ALTA, MEDIA, BAJA o DESCONOCIDO | Registro rechazado: `nivel_urgencia_invalido` | Data Steward |
| R06 — Duplicados | Registros idénticos en todas sus columnas se marcan con `duplicado_flag=True` | Se conservan para revisión manual, no se eliminan | Data Steward |
| R07 — Unidades | Variantes (`MG / ML`, `UG`, `µ`) se normalizan a forma estándar | Transformación automática en pipeline | Data Engineer |
| R08 — Texto | Todos los campos de texto se normalizan: mayúsculas, sin tildes, sin espacios múltiples | Transformación automática en pipeline | Data Engineer |
| R09 — Campos secundarios | Si no hay segundo principio activo, campos secundarios = `NO APLICA` | Transformación automática en pipeline | Data Engineer |
| R10 — Diagnóstico | `codigo_diagnostico_cie10` debe tener mínimo 2 caracteres si está presente | Advertencia en reporte de calidad | Data Steward |

### 4.1 Resultados de validación — Mayo 2026

Ejecución del pipeline sobre `MEDICAMENTOS_VITALES_NO_DISPONIBLES_20260420.csv`:

| Métrica | Valor |
|---|---|
| Filas originales | 10,017 |
| Filas válidas | 9,957 (99.4%) |
| Filas rechazadas | 60 (0.6%) |
| Duplicados sospechosos | 958 (9.6%) |
| Error principal | `cantidad_solicitada_not_nullable` — 59 registros |
| Error secundario | `fecha_de_autorizacion_fecha_futura` — 1 registro |

El bajo porcentaje de rechazo indica calidad estructural aceptable. Sin embargo, el 9.6% de duplicados requiere revisión manual antes de usar los datos en modelos predictivos.

---

## 5. Estándares de Datos

### 5.1 Normalización de texto
- Todos los campos de texto se almacenan en **mayúsculas sin tildes**.
- Los espacios múltiples y saltos de línea se colapsan a un solo espacio.
- Los valores `""`, `-`, `N/A`, `NO REPORTA`, `SIN DATO` se unifican como nulo (`pd.NA`).

### 5.2 Fechas
- Formato estándar: **ISO 8601** (`YYYY-MM-DD HH:MM:SS`).
- Solo se aceptan fechas desde el **1 de enero de 2018**.
- No se aceptan fechas futuras a la fecha de ejecución del pipeline.

### 5.3 Cantidades
- Se almacenan como `float64`.
- Las comas como separadores de miles se eliminan automáticamente (`10,000 → 10000.0`).
- Solo se aceptan valores **estrictamente mayores a cero**.

### 5.4 Unidades de medida
- Variantes con espacios se normalizan: `MG / ML → MG/ML`, `UI / ML → UI/ML`.
- El símbolo `µ` (micro) se reemplaza por `M`.
- `UG` se normaliza a `MCG` (nomenclatura farmacéutica internacional).

### 5.5 Código del repositorio
- Todo el código se desarrolla en **Python 3.12** siguiendo **PEP 8**.
- Las funciones deben incluir **docstring** descriptivo.
- Los commits en GitHub deben ser descriptivos e incluir el componente modificado.
- La rama `main` está protegida — los cambios se integran mediante **pull requests**.

---

## 6. Seguridad y Privacidad de los Datos

| Capa | Política aplicada | Justificación |
|---|---|---|
| Raw / Bronze | Acceso restringido al equipo de ingeniería. Datos sin transformar no disponibles para consumo directo | Evitar uso de datos sin validar en análisis o decisiones |
| Processed / Silver | Acceso para Data Steward y equipo de analítica. Solo datos que pasaron validación Pandera | Garantizar análisis sobre datos confiables |
| Gold / Publicación | Acceso abierto al equipo de BI y tomadores de decisión. Dataset listo para dashboard | Facilitar decisiones sin exponer datos intermedios |
| Datos personales | El dataset no contiene datos de pacientes identificables. Solo diagnósticos CIE-10 agregados | Cumplimiento Ley 1581 de 2012 — Habeas Data Colombia |
| Repositorio GitHub | Repositorio privado durante el desarrollo. Ramas protegidas en `main` | Control de versiones y trazabilidad de cambios |

---

## 7. Trazabilidad y Linaje de Datos

El linaje describe el recorrido completo de los datos desde la fuente hasta el dashboard, permitiendo auditar cualquier transformación y reproducir los resultados.

### 7.1 Flujo de linaje

```
datos.gov.co (INVIMA)
    │
    ▼
data/raw/  ← Descarga CSV / API REST
    │
    ▼
estandarizar_dataset()  ← Limpieza, normalización, variables derivadas
    │
    ▼
validar_y_separar()  ← Schema Pandera
    │
    ├── data/processed/dataset_clean.csv      ← Válidos
    └── data/processed/dataset_rejected.csv   ← Rechazados con razón
    │
    ├── notebooks/eda_medicamentos.ipynb       ← Análisis exploratorio
    └── dashboard/app.py                       ← Visualización interactiva
```

### 7.2 Reproducibilidad

El pipeline es completamente reproducible. Cualquier miembro del equipo o evaluador puede ejecutar `python main.py` sobre el CSV raw y obtener exactamente los mismos archivos en `data/processed/`. Las versiones de todas las librerías están fijadas en `requirements.txt`.

---

## 8. Sistema de Alerta Temprana — Lógica de Gobierno

### 8.1 Variable de nivel de urgencia (proxy de causa)

El dataset de INVIMA no incluye una columna explícita de causa del desabastecimiento. Se derivó `nivel_urgencia` desde `tipo_de_solicitud`:

| Tipo de solicitud | Nivel de urgencia | Interpretación |
|---|---|---|
| URGENCIA CLÍNICA | ALTA | Paciente en riesgo inmediato, sin alternativa terapéutica |
| MÁS DE UN PACIENTE | MEDIA | Escasez que afecta a múltiples pacientes simultáneamente |
| PACIENTE ESPECIFICO | BAJA | Necesidad individual, medicamento de difícil acceso local |

### 8.2 Criterios de activación de alerta

Un medicamento entra en estado de alerta cuando cumple alguna de estas condiciones:

- Su `nivel_urgencia` es **ALTA** (urgencia clínica activa).
- Aparece más de una vez en el mismo mes con nivel MEDIA o ALTA.
- Su principio activo está en el **top 15 más solicitados históricamente**.
- El diagnóstico asociado corresponde a una enfermedad huérfana o rara.

### 8.3 Respuesta por nivel

**ALTA — Urgencia clínica:**
- Activación inmediata del proceso de importación de emergencia ante INVIMA.
- Notificación directa al Ministerio de Salud.
- Priorización en el dashboard para visibilidad institucional.

**MEDIA — Más de un paciente:**
- Monitoreo semanal del comportamiento del principio activo.
- Revisión del historial de solicitudes del importador principal.
- Evaluación de alternativas terapéuticas disponibles en el mercado nacional.

**BAJA — Paciente específico:**
- Registro y seguimiento en el sistema.
- Acumulación de datos para detección de tendencias emergentes.
- Si el mismo medicamento acumula 3 o más solicitudes en un trimestre, escala a nivel MEDIA.

### 8.4 Señales de riesgo identificadas en el EDA

- **Alta concentración de importadores**: los 3 principales (AUDIFARMA, GLOBAL SERVICE PHARMACEUTICAL, VALENTECH) concentran el 29.2% de solicitudes. Una falla en cualquiera genera impacto sistémico inmediato.
- **Dependencia de enfermedades huérfanas**: Distrofia Muscular (1,129 casos), Fibrosis Quística (922 casos) y Acondroplasia dominan los diagnósticos — enfermedades que dependen 100% de importación.
- **Estacionalidad en marzo**: el mes de marzo concentra históricamente el mayor volumen de solicitudes, lo que permite anticipar picos y reforzar inventarios preventivamente.

---

## 9. Próximos Pasos — Entrega Final

- Implementar modelo predictivo de alertas tempranas basado en series temporales por principio activo.
- Construir dashboard interactivo en Plotly Dash con filtros por nivel de urgencia, año y diagnóstico.
- Completar el catálogo de datos con ejemplos de valores reales por cada campo.
- Realizar la presentación final del pitch (10-12 minutos) con demostración del dashboard en vivo.
