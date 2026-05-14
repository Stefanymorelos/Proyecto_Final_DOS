"""
Dashboard — Medicamentos Vitales No Disponibles
Universidad Pontificia Bolivariana | Data Office Strategy

Cómo correr:
    pip install dash plotly pandas
    python dashboard/app.py

Luego abre en el navegador: http://127.0.0.1:8050
"""

from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, callback

# =============================================================================
# CARGA Y PREPARACIÓN DE DATOS
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "processed" / "dataset_final.csv"

df = pd.read_csv(DATA_PATH)

# Fechas
df["fecha_de_autorizacion"] = pd.to_datetime(df["fecha_de_autorizacion"], errors="coerce")
df["anio"] = df["fecha_de_autorizacion"].dt.year.astype("Int64")
df["mes"]  = df["fecha_de_autorizacion"].dt.month.astype("Int64")

# Cantidad
df["cantidad_solicitada"] = pd.to_numeric(
    df["cantidad_solicitada"].astype(str).str.replace(",", ""), errors="coerce"
)

# Columna diagnóstico — detectar nombre real
col_diag = next((c for c in df.columns if "diagnostico" in c and "codigo" not in c), None)
col_cod  = next((c for c in df.columns if "codigo" in c and "diagnostico" in c), None)

# Nivel urgencia — derivar si no existe
if "nivel_urgencia" not in df.columns:
    def clasificar(tipo):
        t = str(tipo).upper()
        if "URGENCIA" in t:    return "ALTA"
        elif "MAS DE UN" in t: return "MEDIA"
        elif "ESPECIFICO" in t: return "BAJA"
        return "DESCONOCIDO"
    df["nivel_urgencia"] = df["tipo_de_solicitud"].map(clasificar)

# Opciones para filtros
anios = sorted(df["anio"].dropna().unique().astype(int).tolist())
urgencias = ["ALTA", "MEDIA", "BAJA"]

# =============================================================================
# PALETA DE COLORES
# =============================================================================

COLORES = {
    "ALTA":   "#C0392B",
    "MEDIA":  "#E67E22",
    "BAJA":   "#27AE60",
    "azul":   "#1C7293",
    "azulOsc":"#065A82",
    "teal":   "#028090",
    "fondo":  "#F0F7FB",
    "card":   "#FFFFFF",
}

TEMPLATE = "plotly_white"

# =============================================================================
# APP
# =============================================================================

app = Dash(__name__, suppress_callback_exceptions=True)
app.title = "Medicamentos Vitales — Dashboard"

# =============================================================================
# LAYOUT
# =============================================================================

app.layout = html.Div(
    style={"fontFamily": "Segoe UI, Arial, sans-serif", "backgroundColor": COLORES["fondo"]},
    children=[

        # ── Header ───────────────────────────────────────────────────────────
        html.Div(
            style={
                "backgroundColor": COLORES["azulOsc"],
                "padding": "20px 32px",
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
            },
            children=[
                html.Div([
                    html.H1(
                        "Medicamentos Vitales No Disponibles",
                        style={"color": "white", "margin": 0, "fontSize": "22px", "fontWeight": "700"},
                    ),
                    html.P(
                        "Sistema de Alerta Temprana | Universidad Pontificia Bolivariana",
                        style={"color": "#A0C8E0", "margin": "4px 0 0 0", "fontSize": "13px"},
                    ),
                ]),
                html.Div(
                    f"Dataset: {len(df):,} registros | INVIMA / datos.gov.co",
                    style={"color": "#A0C8E0", "fontSize": "12px"},
                ),
            ],
        ),

        # ── Filtros globales ─────────────────────────────────────────────────
        html.Div(
            style={
                "backgroundColor": "white",
                "padding": "16px 32px",
                "display": "flex",
                "gap": "24px",
                "alignItems": "center",
                "borderBottom": f"3px solid {COLORES['teal']}",
                "flexWrap": "wrap",
            },
            children=[
                html.Div([
                    html.Label("Año", style={"fontSize": "12px", "color": COLORES["azulOsc"], "fontWeight": "600"}),
                    dcc.RangeSlider(
                        id="filtro-anio",
                        min=anios[0], max=anios[-1],
                        value=[anios[0], anios[-1]],
                        marks={str(a): str(a) for a in anios},
                        step=1,
                    ),
                ], style={"flex": "2", "minWidth": "300px"}),

                html.Div([
                    html.Label("Nivel de urgencia", style={"fontSize": "12px", "color": COLORES["azulOsc"], "fontWeight": "600"}),
                    dcc.Checklist(
                        id="filtro-urgencia",
                        options=[{"label": f"  {u}", "value": u} for u in urgencias],
                        value=urgencias,
                        inline=True,
                        style={"fontSize": "13px"},
                        inputStyle={"marginRight": "4px"},
                    ),
                ], style={"flex": "1", "minWidth": "250px"}),

                html.Div([
                    html.Label("Principio activo", style={"fontSize": "12px", "color": COLORES["azulOsc"], "fontWeight": "600"}),
                    dcc.Dropdown(
                        id="filtro-principio",
                        options=[{"label": p, "value": p} for p in sorted(df["principio_activo1"].dropna().unique())],
                        placeholder="Todos",
                        clearable=True,
                        style={"fontSize": "13px"},
                    ),
                ], style={"flex": "1", "minWidth": "220px"}),
            ],
        ),

        # ── KPI Cards ────────────────────────────────────────────────────────
        html.Div(id="kpi-cards", style={"padding": "20px 32px 0 32px"}),

        # ── Pestañas ─────────────────────────────────────────────────────────
        html.Div(
            style={"padding": "16px 32px 32px 32px"},
            children=[
                dcc.Tabs(
                    id="tabs",
                    value="tab-temporal",
                    colors={"primary": COLORES["azulOsc"], "background": COLORES["fondo"], "border": "#D1E8F0"},
                    children=[
                        dcc.Tab(label="📈  Evolución Temporal",    value="tab-temporal"),
                        dcc.Tab(label="💊  Medicamentos Críticos",  value="tab-medicamentos"),
                        dcc.Tab(label="🏥  Diagnósticos CIE-10",   value="tab-diagnosticos"),
                        dcc.Tab(label="🚨  Sistema de Alertas",    value="tab-alertas"),
                        dcc.Tab(label="🏢  Importadores",          value="tab-importadores"),
                    ],
                ),
                html.Div(id="tab-content", style={"marginTop": "16px"}),
            ],
        ),
    ],
)

# =============================================================================
# HELPERS
# =============================================================================

def filtrar(anio_range, urgencias_sel, principio):
    mask = (
        df["anio"].between(anio_range[0], anio_range[1]) &
        df["nivel_urgencia"].isin(urgencias_sel)
    )
    if principio:
        mask &= df["principio_activo1"] == principio
    return df[mask]


def card(titulo, valor, color, subtitulo=""):
    return html.Div(
        style={
            "backgroundColor": "white",
            "borderRadius": "8px",
            "padding": "16px 20px",
            "flex": "1",
            "minWidth": "140px",
            "borderTop": f"4px solid {color}",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
        },
        children=[
            html.P(titulo, style={"margin": "0 0 6px 0", "fontSize": "12px", "color": "#666", "fontWeight": "600"}),
            html.H2(valor, style={"margin": "0", "fontSize": "26px", "color": color, "fontWeight": "700"}),
            html.P(subtitulo, style={"margin": "4px 0 0 0", "fontSize": "11px", "color": "#999"}),
        ],
    )


def grafica_container(figura, altura=420):
    return html.Div(
        dcc.Graph(figure=figura, style={"height": f"{altura}px"}),
        style={
            "backgroundColor": "white",
            "borderRadius": "8px",
            "padding": "8px",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.06)",
        },
    )


def fila(*elementos, gap="16px"):
    return html.Div(
        style={"display": "flex", "gap": gap, "flexWrap": "wrap"},
        children=list(elementos),
    )

# =============================================================================
# CALLBACKS
# =============================================================================

@callback(
    Output("kpi-cards", "children"),
    Input("filtro-anio", "value"),
    Input("filtro-urgencia", "value"),
    Input("filtro-principio", "value"),
)
def actualizar_kpis(anio_range, urgencias_sel, principio):
    dff = filtrar(anio_range, urgencias_sel, principio)
    total      = len(dff)
    n_alta     = (dff["nivel_urgencia"] == "ALTA").sum()
    n_media    = (dff["nivel_urgencia"] == "MEDIA").sum()
    n_meds     = dff["principio_activo1"].nunique()
    n_imp      = dff["solicitante_importador"].nunique()

    return html.Div(
        style={"display": "flex", "gap": "12px", "flexWrap": "wrap", "marginBottom": "8px"},
        children=[
            card("Total solicitudes",     f"{total:,}",   COLORES["azulOsc"]),
            card("Urgencia ALTA",         f"{n_alta:,}",  COLORES["ALTA"],   f"{n_alta/total*100:.1f}% del total"),
            card("Urgencia MEDIA",        f"{n_media:,}", COLORES["MEDIA"],  f"{n_media/total*100:.1f}% del total"),
            card("Principios activos",    f"{n_meds:,}",  COLORES["teal"]),
            card("Importadores únicos",   f"{n_imp:,}",   COLORES["azul"]),
        ],
    )


@callback(
    Output("tab-content", "children"),
    Input("tabs", "value"),
    Input("filtro-anio", "value"),
    Input("filtro-urgencia", "value"),
    Input("filtro-principio", "value"),
)
def actualizar_tabs(tab, anio_range, urgencias_sel, principio):
    dff = filtrar(anio_range, urgencias_sel, principio)

    # ── TAB 1: Temporal ───────────────────────────────────────────────────────
    if tab == "tab-temporal":
        por_anio = dff.groupby("anio").size().reset_index(name="solicitudes")
        fig_anio = px.bar(
            por_anio, x="anio", y="solicitudes",
            title="Solicitudes por año",
            color_discrete_sequence=[COLORES["azul"]],
            text="solicitudes", template=TEMPLATE,
        )
        fig_anio.update_traces(textposition="outside")
        fig_anio.update_layout(xaxis_title="Año", yaxis_title="Solicitudes", showlegend=False)

        por_mes = dff.groupby(["anio", "mes"]).size().reset_index(name="solicitudes")
        por_mes["periodo"] = por_mes["anio"].astype(str) + "-" + por_mes["mes"].astype(str).str.zfill(2)
        por_mes = por_mes.sort_values("periodo")
        fig_serie = px.line(
            por_mes, x="periodo", y="solicitudes",
            title="Serie mensual de solicitudes",
            color_discrete_sequence=[COLORES["teal"]],
            template=TEMPLATE,
        )
        fig_serie.update_traces(mode="lines+markers", marker_size=4)
        fig_serie.update_layout(xaxis_title="Año-Mes", yaxis_title="Solicitudes")
        n = max(1, len(por_mes) // 12)
        fig_serie.update_xaxes(tickangle=45, tickvals=por_mes["periodo"].tolist()[::n])

        est = dff.groupby("mes").size().reset_index(name="solicitudes")
        meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        est["mes_nombre"] = est["mes"].apply(lambda m: meses[int(m)-1])
        fig_est = px.bar(
            est, x="mes_nombre", y="solicitudes",
            title="Estacionalidad mensual histórica",
            color_discrete_sequence=[COLORES["azulOsc"]],
            template=TEMPLATE,
        )
        fig_est.update_layout(xaxis_title="Mes", yaxis_title="Total solicitudes")

        return html.Div([
            fila(
                html.Div(grafica_container(fig_anio), style={"flex": "1", "minWidth": "300px"}),
                html.Div(grafica_container(fig_est),  style={"flex": "1", "minWidth": "300px"}),
            ),
            html.Div(style={"height": "16px"}),
            grafica_container(fig_serie, altura=320),
        ])

    # ── TAB 2: Medicamentos ───────────────────────────────────────────────────
    elif tab == "tab-medicamentos":
        top_med = dff["principio_activo1"].value_counts().head(15).reset_index()
        top_med.columns = ["principio_activo", "solicitudes"]
        fig_med = px.bar(
            top_med.sort_values("solicitudes"),
            x="solicitudes", y="principio_activo",
            orientation="h",
            title="Top 15 principios activos más solicitados",
            color="solicitudes",
            color_continuous_scale=["#A8D5E8", COLORES["azulOsc"]],
            template=TEMPLATE,
            text="solicitudes",
        )
        fig_med.update_traces(textposition="outside")
        fig_med.update_layout(yaxis_title="", xaxis_title="Solicitudes", coloraxis_showscale=False)

        urgencia_med = dff[dff["nivel_urgencia"] == "ALTA"]["principio_activo1"].value_counts().head(10).reset_index()
        urgencia_med.columns = ["principio_activo", "solicitudes"]
        fig_urg_med = px.bar(
            urgencia_med.sort_values("solicitudes"),
            x="solicitudes", y="principio_activo",
            orientation="h",
            title="Top 10 principios activos en URGENCIA CLÍNICA",
            color_discrete_sequence=[COLORES["ALTA"]],
            template=TEMPLATE,
            text="solicitudes",
        )
        fig_urg_med.update_traces(textposition="outside")
        fig_urg_med.update_layout(yaxis_title="", xaxis_title="Solicitudes")

        return fila(
            html.Div(grafica_container(fig_med,     altura=500), style={"flex": "1", "minWidth": "300px"}),
            html.Div(grafica_container(fig_urg_med, altura=500), style={"flex": "1", "minWidth": "300px"}),
        )

    # ── TAB 3: Diagnósticos ───────────────────────────────────────────────────
    elif tab == "tab-diagnosticos":
        if col_diag and col_diag in dff.columns:
            top_diag = dff[col_diag].value_counts().head(15).reset_index()
            top_diag.columns = ["diagnostico", "solicitudes"]
            fig_diag = px.bar(
                top_diag.sort_values("solicitudes"),
                x="solicitudes", y="diagnostico",
                orientation="h",
                title="Top 15 diagnósticos CIE-10 con más solicitudes",
                color="solicitudes",
                color_continuous_scale=["#A8D5E8", COLORES["azulOsc"]],
                template=TEMPLATE,
                text="solicitudes",
            )
            fig_diag.update_traces(textposition="outside")
            fig_diag.update_layout(
                yaxis_title="", xaxis_title="Solicitudes",
                coloraxis_showscale=False,
                yaxis={"tickfont": {"size": 10}},
            )

            diag_urgencia = dff[dff["nivel_urgencia"] == "ALTA"][col_diag].value_counts().head(10).reset_index()
            diag_urgencia.columns = ["diagnostico", "solicitudes"]
            fig_diag_urg = px.bar(
                diag_urgencia.sort_values("solicitudes"),
                x="solicitudes", y="diagnostico",
                orientation="h",
                title="Diagnósticos en solicitudes de URGENCIA CLÍNICA",
                color_discrete_sequence=[COLORES["ALTA"]],
                template=TEMPLATE,
                text="solicitudes",
            )
            fig_diag_urg.update_traces(textposition="outside")
            fig_diag_urg.update_layout(
                yaxis_title="", xaxis_title="Solicitudes",
                yaxis={"tickfont": {"size": 10}},
            )

            pct_sin = dff[col_diag].isna().sum() / len(dff) * 100

            return html.Div([
                html.Div(
                    f"⚠️  {pct_sin:.1f}% de registros sin diagnóstico reportado",
                    style={
                        "backgroundColor": "#FFF3CD", "border": "1px solid #F0C040",
                        "borderRadius": "6px", "padding": "10px 16px",
                        "fontSize": "13px", "marginBottom": "16px",
                        "color": "#856404",
                    },
                ),
                fila(
                    html.Div(grafica_container(fig_diag,     altura=500), style={"flex": "1", "minWidth": "300px"}),
                    html.Div(grafica_container(fig_diag_urg, altura=500), style={"flex": "1", "minWidth": "300px"}),
                ),
            ])
        else:
            return html.P("Columna de diagnóstico no encontrada.", style={"color": "red"})

    # ── TAB 4: Alertas ────────────────────────────────────────────────────────
    elif tab == "tab-alertas":
        dist_urg = dff["nivel_urgencia"].value_counts().reset_index()
        dist_urg.columns = ["nivel", "solicitudes"]
        colores_urg = [COLORES.get(n, "#999") for n in dist_urg["nivel"]]
        fig_pie = px.pie(
            dist_urg, names="nivel", values="solicitudes",
            title="Distribución por nivel de urgencia",
            color="nivel",
            color_discrete_map=COLORES,
            template=TEMPLATE,
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")

        tend_urg = dff.groupby(["anio", "nivel_urgencia"]).size().reset_index(name="solicitudes")
        fig_tend = px.line(
            tend_urg, x="anio", y="solicitudes", color="nivel_urgencia",
            title="Evolución de urgencias por año",
            color_discrete_map=COLORES,
            markers=True, template=TEMPLATE,
        )
        fig_tend.update_layout(xaxis_title="Año", yaxis_title="Solicitudes", legend_title="Nivel")

        alta_med = dff[dff["nivel_urgencia"] == "ALTA"].groupby("principio_activo1").size().reset_index(name="urgencias")
        alta_med = alta_med.sort_values("urgencias", ascending=False).head(10)
        fig_alerta = px.bar(
            alta_med.sort_values("urgencias"),
            x="urgencias", y="principio_activo1",
            orientation="h",
            title="Medicamentos con más urgencias clínicas",
            color_discrete_sequence=[COLORES["ALTA"]],
            template=TEMPLATE,
            text="urgencias",
        )
        fig_alerta.update_traces(textposition="outside")
        fig_alerta.update_layout(yaxis_title="", xaxis_title="Urgencias ALTA")

        return html.Div([
            fila(
                html.Div(grafica_container(fig_pie,  altura=380), style={"flex": "1", "minWidth": "280px"}),
                html.Div(grafica_container(fig_tend, altura=380), style={"flex": "2", "minWidth": "300px"}),
            ),
            html.Div(style={"height": "16px"}),
            grafica_container(fig_alerta, altura=380),
        ])

    # ── TAB 5: Importadores ───────────────────────────────────────────────────
    elif tab == "tab-importadores":
        top_imp = dff["solicitante_importador"].value_counts().head(15).reset_index()
        top_imp.columns = ["importador", "solicitudes"]
        top_imp["pct"] = (top_imp["solicitudes"] / len(dff) * 100).round(1)

        fig_imp = px.bar(
            top_imp.sort_values("solicitudes"),
            x="solicitudes", y="importador",
            orientation="h",
            title="Top 15 importadores por volumen de solicitudes",
            color="solicitudes",
            color_continuous_scale=["#A8D5E8", COLORES["azulOsc"]],
            template=TEMPLATE,
            text="pct",
        )
        fig_imp.update_traces(texttemplate="%{text}%", textposition="outside")
        fig_imp.update_layout(yaxis_title="", xaxis_title="Solicitudes", coloraxis_showscale=False)

        imp_urg = dff[dff["nivel_urgencia"] == "ALTA"].groupby("solicitante_importador").size().reset_index(name="urgencias")
        imp_urg = imp_urg.sort_values("urgencias", ascending=False).head(10)
        fig_imp_urg = px.bar(
            imp_urg.sort_values("urgencias"),
            x="urgencias", y="solicitante_importador",
            orientation="h",
            title="Importadores con más urgencias clínicas",
            color_discrete_sequence=[COLORES["ALTA"]],
            template=TEMPLATE,
            text="urgencias",
        )
        fig_imp_urg.update_traces(textposition="outside")
        fig_imp_urg.update_layout(yaxis_title="", xaxis_title="Urgencias ALTA")

        top3_pct = top_imp.head(3)["solicitudes"].sum() / len(dff) * 100
        return html.Div([
            html.Div(
                f"⚠️  Los 3 principales importadores concentran el {top3_pct:.1f}% de todas las solicitudes — riesgo sistémico alto.",
                style={
                    "backgroundColor": "#FDECEA", "border": "1px solid #C0392B",
                    "borderRadius": "6px", "padding": "10px 16px",
                    "fontSize": "13px", "marginBottom": "16px", "color": "#7B241C",
                },
            ),
            fila(
                html.Div(grafica_container(fig_imp,     altura=500), style={"flex": "1", "minWidth": "300px"}),
                html.Div(grafica_container(fig_imp_urg, altura=500), style={"flex": "1", "minWidth": "300px"}),
            ),
        ])


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    app.run(debug=True)
