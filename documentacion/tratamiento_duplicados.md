# Tratamiento de Duplicados — Medicamentos Vitales No Disponibles

**Universidad Pontificia Bolivariana | Data Office Strategy**
Segunda Entrega Parcial — Mayo 2026
Dataset: INVIMA / datos.gov.co — `sdmr-tfmf`

---

## 1. Contexto y Problema

El dataset de Medicamentos Vitales No Disponibles publicado por el INVIMA presenta **958 registros marcados como duplicados** por el pipeline principal (9.6% del dataset limpio). Estos fueron detectados usando `df.duplicated(keep=False)` de pandas, que marca como duplicado cualquier fila idéntica en **todas** sus columnas.

Sin embargo, en el contexto de medicamentos vitales, un duplicado no siempre es un error. Puede representar:

- Un **error de carga** en el sistema de INVIMA (el mismo registro ingresado múltiples veces).
- **Pacientes distintos** que reciben el mismo medicamento del mismo importador el mismo día con la misma dosis estándar.
- Una **renovación periódica** de una solicitud que vence y se renueva.

Eliminar todos los duplicados automáticamente introduce sesgo en el análisis: se perderían solicitudes legítimas de pacientes reales. Conservarlos todos introduce ruido: se contarían eventos que nunca ocurrieron.

La solución es una **clasificación por criterios** que permita tomar la decisión correcta en cada caso, de forma automática donde los datos lo permiten y con revisión humana solo donde hay ambigüedad real.

---

## 2. Metodología de Clasificación

Cada registro duplicado se clasifica en un grupo usando como llave de agrupación:

```
principio_activo1 + solicitante_importador + fecha_de_autorizacion
```

Dentro de cada grupo se aplican los criterios en orden de prioridad. El resultado es la columna `decision_duplicado` en el dataset.

---

## 3. Criterios Detallados

### C1-B — Más de 2 registros idénticos el mismo día → ELIMINAR

**Condición:**
El mismo principio activo, importador y fecha aparecen **más de 2 veces** con exactamente la misma cantidad.

**Registros afectados:** ~400

**Justificación:**
Cuando un mismo registro aparece 3, 4 o más veces el mismo día con exactamente los mismos valores en todas las columnas, la probabilidad de que sean pacientes distintos es prácticamente nula. Las solicitudes de INVIMA son individuales por trámite — no existe un mecanismo institucional que genere 3 o más autorizaciones idénticas el mismo día de forma legítima. La causa más probable es un error en el sistema de carga o una duplicación técnica en la exportación del dataset.

**Decisión:** Se conserva **1 registro** del grupo y se eliminan los demás.

**Impacto en modelo predictivo:**
Conservar estos duplicados inflaría artificialmente la frecuencia de ciertos medicamentos e importadores, generando señales falsas de alta demanda que el modelo interpretaría como tendencia real.

---

### C1-C — 2 registros idénticos, cantidad > 1,000 unidades → ELIMINAR

**Condición:**
Exactamente 2 registros con mismo principio activo, importador y fecha, con cantidad idéntica **mayor a 1,000 unidades**.

**Registros afectados:** 79

**Justificación:**
Una cantidad superior a 1,000 unidades del mismo medicamento, solicitada dos veces el mismo día por el mismo importador, es incompatible con el concepto de dosis individual para un paciente específico. En el contexto de medicamentos vitales, las dosis individuales para enfermedades crónicas o huérfanas raramente superan las 200-300 unidades por autorización. Cantidades superiores a 1,000 corresponden a compras institucionales o de stock — y duplicar esa cantidad el mismo día apunta a un error de registro.

**Decisión:** Se conserva **1 registro** y se elimina el duplicado.

**Impacto en modelo predictivo:**
Duplicar volúmenes grandes distorsiona las series temporales de cantidad solicitada, afectando cualquier modelo que use esta variable para estimar demanda futura.

---

### C1-D — Urgencia clínica en duplicado → CONSERVAR

**Condición:**
El `tipo_de_solicitud` es **URGENCIA CLÍNICA**, independientemente de la cantidad o el número de repeticiones.

**Registros afectados:** 38

**Justificación:**
Las urgencias clínicas representan pacientes en riesgo inmediato de vida sin alternativa terapéutica disponible. Eliminar un registro de urgencia clínica por considerarlo duplicado implicaría invisibilizar una situación crítica real. El costo de un falso negativo (eliminar una urgencia real) es mucho mayor que el costo de un falso positivo (conservar un posible duplicado). En contextos de salud pública, la decisión conservadora es siempre proteger la integridad del registro clínico.

**Decisión:** **CONSERVAR todos** sin excepción.

**Impacto en modelo predictivo:**
Las urgencias clínicas son precisamente los eventos que el modelo debe aprender a predecir. Eliminarlos reduciría la señal más importante del dataset.

---

### C1-E — 2 registros idénticos, cantidad ≤ 100 unidades → CONSERVAR

**Condición:**
Exactamente 2 registros con mismo principio activo, importador y fecha, con cantidad idéntica **menor o igual a 100 unidades**.

**Registros afectados:** 462

**Justificación:**
Los medicamentos más frecuentes en este rango son tratamientos para enfermedades huérfanas como Fibrosis Quística (ELEXACAFTOR/TEZACAFTOR/IVACAFTOR), Distrofia Muscular (ETEPLIRSEN, CASIMERSEN) y Hipofosfatasia (ASFOTASA ALFA). Estos medicamentos tienen dosis estándar fijas definidas por el peso y la condición del paciente — típicamente entre 6 y 72 unidades por ciclo. Es completamente plausible que el mismo importador tramite dos autorizaciones el mismo día para dos pacientes distintos con la misma dosis estándar.

La mediana de cantidad en el dataset completo para paciente específico es de **9 unidades** — consistente con este rango.

**Decisión:** **CONSERVAR ambos registros**.

**Impacto en modelo predictivo:**
Estos registros representan demanda real de pacientes con enfermedades crónicas que requieren abastecimiento continuo. Eliminarlos subestimaría la frecuencia de solicitudes de medicamentos críticos.

---

### C2 — Cantidades distintas mismo día → CONSERVAR

**Condición:**
Mismo principio activo, importador y fecha, pero con **cantidades diferentes** entre los registros del grupo.

**Registros afectados:** ~2,860

**Justificación:**
Si dos registros comparten principio activo, importador y fecha pero tienen cantidades distintas, son inequívocamente solicitudes diferentes. La cantidad es la única variable que cambia — lo que indica pacientes con dosis distintas (diferente peso corporal, diferente estadio de la enfermedad, diferente esquema terapéutico). El sistema de INVIMA genera un número de autorización por paciente — dos cantidades distintas implican dos pacientes distintos.

**Decisión:** **CONSERVAR todos**.

**Impacto en modelo predictivo:**
Estos registros son los más limpios del dataset. Representan con precisión la diversidad de pacientes y dosis, lo que enriquece cualquier modelo de predicción de demanda.

---

### C3 — Días de diferencia entre registros → CONSERVAR

**Condición:**
Registros del mismo principio activo e importador con **diferencia de días > 0** entre fechas.

**Registros afectados:** ~2

**Justificación:**
Una diferencia de días entre registros del mismo medicamento e importador indica renovación periódica de la solicitud. Las autorizaciones de INVIMA para medicamentos vitales tienen vigencia limitada — cuando vence, el importador debe solicitar una nueva autorización. Este es el comportamiento esperado del proceso institucional y no constituye duplicado en ningún sentido operativo.

**Decisión:** **CONSERVAR todos**.

**Impacto en modelo predictivo:**
Estos registros son fundamentales para construir series temporales por medicamento e importador, que son la base de cualquier modelo de predicción de desabastecimiento.

---

### C4 — Urgencia clínica general → CONSERVAR

**Condición:**
Cualquier registro con `tipo_de_solicitud = URGENCIA CLÍNICA`, independientemente de si forma parte de un grupo duplicado o no.

**Registros afectados:** ~318

**Justificación:**
Criterio de protección general. Antes de cualquier otra clasificación, las urgencias clínicas se marcan como intocables. Este criterio tiene la máxima prioridad en el pipeline porque el impacto institucional y clínico de perder un registro de urgencia supera cualquier ganancia en limpieza del dataset.

**Decisión:** **CONSERVAR todos**.

---

## 4. Los 29 Casos Ambiguos — Análisis y Decisión

### ¿Qué son?

Son exactamente **15 grupos (30 registros)** donde:
- Hay exactamente **2 registros** del mismo medicamento, importador y fecha
- La cantidad es **idéntica** en ambos
- La cantidad está en el rango **101 a 1,000 unidades**
- **No** son urgencias clínicas

Este rango es ambiguo porque:
- Es demasiado alto para ser claramente una dosis individual (> 100)
- Es demasiado bajo para ser claramente un error de volumen (< 1,000)

### Los 15 grupos reales

| Principio activo | Importador | Fecha | Tipo solicitud | Cantidad |
|---|---|---|---|---|
| ASFOTASA ALFA | AUDIFARMA S.A. | 2018-11-15 | PACIENTE ESPECÍFICO | 144 |
| ASFOTASA ALFA | AUDIFARMA S.A. | 2020-05-14 | PACIENTE ESPECÍFICO | 144 |
| ASPARAGINASA | ROCKA INTERNATIONAL | 2022-09-21 | MÁS DE UN PACIENTE | 1,000 |
| BACILO CALMETTE-GUERIN | INNOVEX INTERNATIONAL | 2020-10-19 | MÁS DE UN PACIENTE | 333 |
| CASIMERSEN | VALENTECH PHARMA | 2024-12-04 | PACIENTE ESPECÍFICO | 192 |
| EPINEFRINA | SUMIVITALES S.A.S | 2019-05-13 | MÁS DE UN PACIENTE | 200 |
| EPINEFRINA | SUMIVITALES S.A.S | 2021-03-11 | MÁS DE UN PACIENTE | 200 |
| EXTRACTOS ALÉRGÉNICOS | INMUNOTEK COLOMBIA | 2025-01-27 | MÁS DE UN PACIENTE | 725 |
| EXTRACTOS ALÉRGÉNICOS (Depigoid) | ALERGOLOGOS CLÍNICOS | 2024-04-29 | MÁS DE UN PACIENTE | 250 |
| FLUCITOSINA | EPICUROFARMA S.A.S | 2021-04-12 | MÁS DE UN PACIENTE | 178 |
| MELFALAN | HB HUMAN BIOSCIENCE | 2021-12-02 | MÁS DE UN PACIENTE | 550 |
| MELFALAN | STRENUUS MARKETING | 2022-11-01 | MÁS DE UN PACIENTE | 200 |
| METRELEPTIN | LABORATORIOS BIOPAS | 2021-06-30 | PACIENTE ESPECÍFICO | 180 |
| REMIFENTANILO | BIOMEDICAL PHARMA | 2021-02-09 | MÁS DE UN PACIENTE | 500 |
| TOLVAPTAN | INPHAPRO SAS | 2025-12-17 | PACIENTE ESPECÍFICO | 144 |

### Análisis por tipo de solicitud

**MÁS DE UN PACIENTE (10 grupos):**
El tipo de solicitud ya indica que cubre múltiples pacientes simultáneamente. Si el mismo importador solicita la misma cantidad para más de un paciente dos veces el mismo día, lo más probable es que sean **lotes distintos para grupos de pacientes diferentes** — por ejemplo, dos hospitales distintos tramitados por el mismo importador. Esto es plausible institucionalmente.

**PACIENTE ESPECÍFICO (5 grupos):**
Aquí sí hay mayor ambigüedad. Una cantidad entre 144 y 192 unidades para un paciente específico puede ser:
- Un tratamiento de varios meses consolidado en una sola autorización (plausible para ASFOTASA ALFA y CASIMERSEN que requieren dosificación continua)
- Un error de duplicación (menos probable pero posible)

### Decisión para el modelo predictivo

Para un modelo de predicción, la decisión correcta es **conservar todos los ambiguos** por las siguientes razones:

**Razón 1 — Costo asimétrico del error:**
Si conservamos un duplicado real → el modelo sobreestima demanda en 1 evento puntual.
Si eliminamos una solicitud real → el modelo pierde una señal de demanda legítima que puede repetirse.
El segundo error es más costoso para un sistema de alertas tempranas.

**Razón 2 — Volumen insignificante:**
30 registros sobre 9,957 representa el **0.3% del dataset**. Su impacto en el modelo es estadísticamente despreciable en cualquier dirección.

**Razón 3 — Tipo de solicitud predominante:**
10 de los 15 grupos son "MÁS DE UN PACIENTE" — lo que por definición implica que el importador estaba atendiendo a varios pacientes, haciendo plausible la duplicación legítima.

**Decisión final: CONSERVAR los 29 ambiguos en el dataset_final.csv.**

---

## 5. Resumen de Decisiones y Resultados

| Criterio | Registros | Decisión | Automático |
|---|---|---|---|
| C1-B — Más de 2 idénticos mismo día | ~400 | ELIMINAR | ✅ Sí |
| C1-C — 2 registros, cantidad > 1,000 | 79 | ELIMINAR | ✅ Sí |
| C1-D — Urgencia clínica en duplicado | 38 | CONSERVAR | ✅ Sí |
| C1-E — 2 registros, cantidad ≤ 100 | 462 | CONSERVAR | ✅ Sí |
| C2 — Cantidades distintas mismo día | ~2,860 | CONSERVAR | ✅ Sí |
| C3 — Diferencia de días | ~2 | CONSERVAR | ✅ Sí |
| C4 — Urgencia clínica general | ~318 | CONSERVAR | ✅ Sí |
| AMBIGUO — 2 registros, 101-1,000 u. | 30 | CONSERVAR | ✅ Sí |

### Resultado final

| Métrica | Valor |
|---|---|
| Registros en dataset_clean.csv | 9,957 |
| Registros eliminados | ~479 |
| **Registros en dataset_final.csv** | **~9,478** |
| Reducción | 4.8% |

---

## 6. Impacto en el Modelo Predictivo

### Lo que mejora al tratar los duplicados correctamente

**Series temporales más limpias:**
Al eliminar los errores de carga (C1-B y C1-C), la serie mensual de solicitudes por medicamento refleja demanda real — sin picos artificiales causados por duplicaciones técnicas.

**Frecuencia de medicamentos más precisa:**
Los medicamentos más solicitados (ELEXACAFTOR, BUROSUMAB, ETEPLIRSEN) mantienen su posición correcta en el ranking sin ser inflados por duplicados.

**Señal de urgencia preservada:**
Al conservar todas las urgencias clínicas (C1-D y C4), el modelo tiene acceso a todos los eventos críticos reales para aprender los patrones que preceden a una urgencia.

**Distribución de importadores más real:**
Al limpiar errores de carga de importadores con alto volumen (AUDIFARMA, VALENTECH), su participación porcentual refleja mejor la concentración real del mercado.

### Variables más confiables para el modelo

Después del tratamiento de duplicados, las variables con mayor confiabilidad para modelado predictivo son:

- `principio_activo1` — frecuencia de solicitudes por medicamento
- `nivel_urgencia` — proxy del nivel de criticidad
- `anio_autorizacion` + `mes_autorizacion` — componentes temporales
- `solicitante_importador` — concentración y dependencia de proveedores
- `diagnostico_descripcion` — agrupación por enfermedad

---

## 7. Trazabilidad

Todo el proceso queda registrado en los siguientes archivos generados por `src/duplicados.py`:

| Archivo | Contenido |
|---|---|
| `dataset_final.csv` | Dataset limpio final para dashboard y modelo |
| `revision_ambiguos.csv` | Los 30 casos ambiguos con campos editables |
| `registros_eliminados.csv` | Registros eliminados con criterio aplicado |
| `reporte_duplicados.csv` | Conteo de decisiones por criterio |

El campo `decision_duplicado` en `dataset_final.csv` documenta el criterio aplicado a cada registro, garantizando trazabilidad completa desde el dato original hasta el dato utilizado en el modelo.
