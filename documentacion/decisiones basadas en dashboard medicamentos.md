# Decisiones Estratégicas — Dashboard de Medicamentos Vitales No Disponibles
**Universidad Pontificia Bolivariana | Data Office Strategy**  
**Fuente:** INVIMA / datos.gov.co  
**Documento generado a partir del análisis del sistema de monitoreo de solicitudes**

---

## 1. Contexto del Dashboard

El dashboard centraliza el seguimiento de solicitudes de medicamentos vitales no disponibles en Colombia, clasificadas por **nivel de urgencia** (ALTA, MEDIA, BAJA), agrupadas por principio activo, diagnóstico CIE-10 e importador. Permite identificar patrones temporales, cuellos de botella en la cadena de suministro y riesgos sistémicos.

---

## 2. Hallazgos Críticos y Decisiones Recomendadas

### 🚨 2.1 Concentración de Riesgo en Importadores

**Hallazgo:**  
Los **3 principales importadores concentran un porcentaje significativo del total de solicitudes**, lo que genera una dependencia crítica en la cadena de abastecimiento. El dashboard emite una alerta explícita de *riesgo sistémico alto* cuando esta concentración es elevada.

**Decisiones recomendadas:**

- **Diversificación de proveedores:** Establecer contratos marco con al menos 2 importadores alternativos para los principios activos de mayor demanda, reduciendo la dependencia de los actores dominantes.
- **Plan de contingencia por importador:** Definir umbrales de stockout por importador clave y activar protocolos de sustitución automática cuando un proveedor no cumpla con tiempos de entrega.
- **Auditoría de capacidad logística:** Evaluar la capacidad real de respuesta de los top 3 importadores ante picos de demanda estacionales o crisis sanitarias.

---

### 💊 2.2 Principios Activos con Mayor Volumen de Solicitudes y Urgencia Clínica

**Hallazgo:**  
El dashboard identifica los **Top 15 principios activos más solicitados** y los **Top 10 en urgencia clínica ALTA**. Existe un subconjunto de medicamentos que concentra tanto alto volumen como alta urgencia, representando el mayor riesgo para los pacientes.

**Decisiones recomendadas:**

- **Lista de vigilancia prioritaria (watchlist):** Construir un inventario diferenciado para los principios activos que simultáneamente aparecen en el top de volumen y en el top de urgencia ALTA. Estos requieren stock de seguridad ampliado (mínimo 60–90 días).
- **Alertas de reorden automáticas:** Implementar disparadores de reorden en el sistema de gestión hospitalaria vinculados directamente a los datos del dashboard.
- **Negociación de acceso preferencial:** Iniciar negociaciones con fabricantes internacionales para garantizar cupos de suministro prioritario en escenarios de escasez global.

---

### 🏥 2.3 Diagnósticos CIE-10 con Mayor Demanda de Medicamentos No Disponibles

**Hallazgo:**  
Los **Top 15 diagnósticos** concentran la mayoría de las solicitudes. Existe, además, un porcentaje de registros **sin diagnóstico reportado**, lo que reduce la trazabilidad clínica y dificulta la planificación.

**Decisiones recomendadas:**

- **Protocolos de tratamiento alternativos:** Para los diagnósticos más frecuentes con medicamentos no disponibles, desarrollar guías clínicas de sustitución terapéutica validadas por el comité farmacológico institucional.
- **Mejora de la calidad del dato:** Establecer obligatoriedad del código CIE-10 en el formulario de solicitud. El porcentaje de registros sin diagnóstico debe reducirse por debajo del 5% como meta operativa.
- **Modelo predictivo de demanda por patología:** Cruzar los datos de diagnósticos estacionales (temporadas de influenza, enfermedades respiratorias, etc.) con el historial de solicitudes para anticipar desabastecimientos.

---

### 📈 2.4 Patrones Temporales y Estacionalidad

**Hallazgo:**  
El análisis de evolución temporal (solicitudes por año y serie mensual) permite identificar **tendencias crecientes o decrecientes** en el tiempo. La estacionalidad mensual histórica revela meses de mayor presión sobre el sistema.

**Decisiones recomendadas:**

- **Compras anticipadas en meses críticos:** Programar órdenes de compra con 2–3 meses de anticipación a los picos históricos de demanda identificados en el gráfico de estacionalidad mensual.
- **Revisión presupuestal dinámica:** Ajustar el presupuesto de adquisición de medicamentos vitales según la curva de demanda histórica, asignando mayores recursos en los trimestres de mayor actividad.
- **Monitoreo de tendencia interanual:** Si la tendencia anual es creciente, escalar la capacidad de respuesta del sistema de forma proporcional. Si es decreciente, investigar si responde a mejoras reales en disponibilidad o a subregistro.

---

### 🚦 2.5 Distribución y Evolución del Nivel de Urgencia

**Hallazgo:**  
El dashboard segmenta las solicitudes en **ALTA, MEDIA y BAJA** urgencia y muestra su evolución en el tiempo. Un aumento en la proporción de solicitudes ALTA es indicador de deterioro del sistema de abastecimiento.

**Decisiones recomendadas:**

- **Índice de urgencia como KPI institucional:** Formalizar el ratio `Urgencia ALTA / Total solicitudes` como indicador clave de gestión, con metas de reducción trimestral definidas (ej: no superar el 30%).
- **Triage farmacológico:** Priorizar la gestión de solicitudes ALTA con un equipo dedicado y tiempos de respuesta máximos definidos (ej: resolución en menos de 24 horas).
- **Análisis de causas raíz en urgencias ALTA:** Para los medicamentos que concentran más urgencias clínicas, realizar análisis de causa raíz periódicos (mínimo trimestral) para determinar si el problema es de oferta, distribución o previsión de demanda.

---

## 3. Mejoras Operativas al Sistema de Datos

| Problema identificado | Acción recomendada | Responsable sugerido |
|---|---|---|
| Registros sin diagnóstico CIE-10 | Campo obligatorio en formulario de solicitud | Área de sistemas / clínica |
| Clasificación de urgencia derivada (no reportada) | Capturar nivel de urgencia directamente en el origen | INVIMA / hospitales |
| Sin información de tiempo de resolución | Agregar campo `fecha_de_resolución` al dataset | Data Office |
| Dependencia de un solo CSV estático | Conectar dashboard a fuente de datos actualizada en tiempo real | Equipo de ingeniería de datos |

---

## 4. Roadmap de Decisiones por Horizonte Temporal

### Corto plazo (0–3 meses)
- [ ] Identificar y contactar proveedores alternativos para los top 10 principios activos en urgencia ALTA.
- [ ] Establecer la obligatoriedad del campo CIE-10 en los formularios de solicitud.
- [ ] Definir umbrales de alerta y notificación automática basados en los KPIs del dashboard.

### Mediano plazo (3–12 meses)
- [ ] Implementar modelo de predicción de demanda por principio activo y mes.
- [ ] Negociar contratos de suministro garantizado con los principales fabricantes internacionales.
- [ ] Desarrollar guías de sustitución terapéutica para los diagnósticos más críticos.

### Largo plazo (1–3 años)
- [ ] Integrar el dashboard con el sistema nacional de gestión de medicamentos en tiempo real.
- [ ] Establecer un comité interinstitucional de vigilancia farmacológica basado en los datos del sistema.
- [ ] Publicar reportes periódicos de transparencia sobre disponibilidad de medicamentos vitales en Colombia.

---

## 5. Conclusión

El dashboard de Medicamentos Vitales No Disponibles es una herramienta de alto valor estratégico que permite pasar de la **reactividad** (gestionar desabastecimientos cuando ocurren) a la **proactividad** (anticipar y prevenir fallas de suministro). La condición para maximizar su impacto es la **calidad del dato en origen** y la **institucionalización de sus KPIs** como métricas de gestión formal dentro de la Universidad Pontificia Bolivariana y las entidades del sistema de salud.

---

*Documento generado por Data Office Strategy — UPB*  
*Para uso interno de toma de decisiones clínicas y administrativas*
