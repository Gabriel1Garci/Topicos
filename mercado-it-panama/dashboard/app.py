# dashboard/app.py
"""
Dashboard interactivo del Mercado Laboral IT en Panamá.
Ejecutar con: streamlit run dashboard/app.py
"""
import sys
from pathlib import Path
from collections import Counter
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.decomposition import PCA
from sklearn.preprocessing import MultiLabelBinarizer

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import OFERTAS_CSV
from src.config import OFERTAS_HISTORICO_CSV
from src.llm.ollama_cliente import (
    consulta_natural, generar_resumen, skills_emergentes, ollama_disponible,
)

ASSETS_DIR = Path(__file__).parent / "assets"

st.set_page_config(
    page_title="Mercado IT Panamá",
    page_icon=str(ASSETS_DIR / "favicon.png"),
    layout="wide",
)

# ── Estilo: tarjetas redondeadas, nav en pastilla, lavanda + dorado ──────────
st.markdown("""
<style>
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {
    font-weight: 700 !important;
    letter-spacing: -0.01em;
}

/* Fondo: manchas de luz lavanda/dorado sobre negro, para que el vidrio
   tenga algo debajo que desenfocar */
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(650px circle at 12% 8%, rgba(185,166,242,0.18), transparent 60%),
        radial-gradient(550px circle at 92% 85%, rgba(242,199,68,0.14), transparent 60%),
        #0E0E13;
}

/* Glassmorfismo: vidrio esmerilado compartido por tarjetas KPI, gráficas y nav */
[data-testid="stMetric"],
[data-testid="stPlotlyChart"],
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.055);
    backdrop-filter: blur(18px) saturate(160%);
    -webkit-backdrop-filter: blur(18px) saturate(160%);
    border: 1px solid rgba(255,255,255,0.12);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.08), 0 8px 24px rgba(0,0,0,0.35);
}

/* Tarjetas KPI */
[data-testid="stMetric"] {
    border-radius: 18px;
    padding: 16px 20px 12px;
}
[data-testid="stMetricLabel"] {
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-size: 0.72rem !important;
    color: #9C9AAE !important;
}
[data-testid="stMetricValue"] {
    font-variant-numeric: tabular-nums;
    font-weight: 800;
    color: #F2F1F7;
}

/* Cada gráfica vive dentro de una tarjeta redondeada, como el mock */
[data-testid="stPlotlyChart"] {
    border-radius: 18px;
    padding: 10px 6px;
}
[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid rgba(242,241,247,0.08);
}

hr { border-color: rgba(242,241,247,0.10) !important; }

[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(18px) saturate(160%);
    -webkit-backdrop-filter: blur(18px) saturate(160%);
    border-right: 1px solid rgba(242,241,247,0.10);
}

/* Nav en pastilla: pestaña activa = pastilla blanca, igual que el mock */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    border-radius: 100px;
    padding: 4px;
    gap: 2px;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 100px !important;
    padding: 8px 20px !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] p {
    font-size: 0.92rem;
    font-weight: 600;
    color: #9C9AAE;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: transparent !important;
    box-shadow: none !important;
}
[data-testid="stTabs"] [aria-selected="true"] p { color: #B9A6F2 !important; font-weight: 700; }
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background: transparent !important; }
[data-testid="stTabs"] [data-baseweb="tab-border"] { display: none !important; }

/* Animaciones sutiles (respeta accesibilidad si el usuario pide menos movimiento) */
@media (prefers-reduced-motion: no-preference) {
    [data-testid="stTabs"] [data-baseweb="tab"] {
        transition: background 0.2s ease, color 0.2s ease;
    }
    [data-testid="stMetric"],
    [data-testid="stPlotlyChart"] {
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    [data-testid="stMetric"]:hover,
    [data-testid="stPlotlyChart"]:hover {
        transform: translateY(-3px);
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.1), 0 14px 32px rgba(0,0,0,0.45);
    }
    [data-testid="stMainBlockContainer"] {
        animation: entrada 0.5s ease both;
    }
    @keyframes entrada {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
}
</style>
""", unsafe_allow_html=True)

# Colores compartidos entre gráficas: la misma fuente siempre tiene el mismo
# color, sin importar en qué chart aparezca (consistencia visual).
COLOR_FUENTES = {"konzerta": "#B9A6F2", "computrabajo": "#F2C744", "kaggle": "#7FD8C4"}
PLOT_LINE = "rgba(242,241,247,0.10)"


def aplicar_tema(fig):
    """Aplica el look oscuro lavanda/dorado del dashboard a una figura Plotly."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="-apple-system, Segoe UI, sans-serif", color="#F2F1F7", size=13),
        margin=dict(t=30, b=10, l=10, r=10),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor=PLOT_LINE, zerolinecolor=PLOT_LINE)
    fig.update_yaxes(gridcolor=PLOT_LINE, zerolinecolor=PLOT_LINE)
    return fig

# ── Carga de datos ──────────────────────────────────────────────────────────

@st.cache_data
def cargar_datos():
    if not OFERTAS_CSV.exists():
        st.error("No se encontró el dataset. Ejecuta primero: python run_pipeline.py")
        st.stop()
    df = pd.read_csv(OFERTAS_CSV, parse_dates=["fecha"], date_format="mixed")

    def parsear_techs(val):
        if pd.isna(val) or val == "":
            return []
        return [t.strip() for t in str(val).split("|") if t.strip()]

    df["tecnologias"] = df["tecnologias"].apply(parsear_techs)
    if "cluster" not in df.columns:
        df["cluster"] = 0
    return df

df = cargar_datos()

# ── Sidebar: Filtros ─────────────────────────────────────────────────────────

st.sidebar.title("Filtros")

fuentes_disp = sorted(df["fuente"].dropna().unique())
fuentes_sel = st.sidebar.multiselect("Fuente de datos", fuentes_disp, default=fuentes_disp)

todas_techs = sorted({t for ts in df["tecnologias"] for t in ts})
techs_sel = st.sidebar.multiselect("Tecnología", todas_techs, default=[])

ubicaciones = sorted(df["ubicacion"].dropna().unique())
ubicacion_sel = st.sidebar.multiselect("Ubicación", ubicaciones, default=[])

sal_max_global = int(df["salario_max"].dropna().max()) if df["salario_max"].notna().any() else 10000
sal_rango = st.sidebar.slider("Salario máximo (USD)", 0, sal_max_global, (0, sal_max_global))

# Aplicar filtros
df_f = df[df["fuente"].isin(fuentes_sel)].copy()
if techs_sel:
    df_f = df_f[df_f["tecnologias"].apply(lambda ts: any(t in ts for t in techs_sel))]
if ubicacion_sel:
    df_f = df_f[df_f["ubicacion"].isin(ubicacion_sel)]
mask_sal = (
    df_f["salario_max"].isna() |
    ((df_f["salario_max"] >= sal_rango[0]) & (df_f["salario_max"] <= sal_rango[1]))
)
df_f = df_f[mask_sal]

# ── Header ───────────────────────────────────────────────────────────────────

st.title("Mercado Laboral IT en Panamá")
st.caption("Análisis de ofertas de trabajo · Proyecto Universitario UTP-FISC | Gestión de la Información · Grupo 4")

tab_dash, tab_ia = st.tabs(["📊 Dashboard", "🤖 Asistente IA"])

with tab_dash:
    # ── Métricas resumen ─────────────────────────────────────────────────────────

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Ofertas", len(df_f))
    c2.metric("Fuentes", df_f["fuente"].nunique())
    c3.metric("Tecnologías únicas", len({t for ts in df_f["tecnologias"] for t in ts}))
    sal_prom = df_f["salario_min"].mean()
    c4.metric("Salario prom. (USD)", f"${sal_prom:,.0f}" if not pd.isna(sal_prom) else "N/D")

    st.divider()

    # ── Gráficas (2 columnas) ─────────────────────────────────────────────────────

    col_izq, col_der = st.columns(2)

    # 1. Top tecnologías
    with col_izq:
        st.subheader("Top Tecnologías Demandadas")
        conteo = Counter(t for ts in df_f["tecnologias"] for t in ts)
        if conteo:
            df_t = pd.DataFrame(conteo.most_common(20), columns=["tecnologia", "ofertas"])
            fig1 = px.bar(
                df_t, x="ofertas", y="tecnologia", orientation="h",
                color="ofertas", color_continuous_scale=["#2A2A38", "#B9A6F2"],
            )
            fig1.update_layout(yaxis={"categoryorder": "total ascending"}, height=450, showlegend=False)
            fig1.update_layout(coloraxis_showscale=False)
            st.plotly_chart(aplicar_tema(fig1), use_container_width=True)
        else:
            st.info("Sin datos con el filtro actual.")

    # 2. Distribución de salarios
    with col_der:
        st.subheader("Distribución de Salarios")
        df_sal = df_f.dropna(subset=["salario_min", "salario_max"]).copy()
        if len(df_sal) > 0:
            df_sal["salario_promedio"] = (df_sal["salario_min"] + df_sal["salario_max"]) / 2
            fig2 = px.histogram(
                df_sal, x="salario_promedio", nbins=20, color="fuente",
                labels={"salario_promedio": "Salario USD", "count": "Ofertas"},
                color_discrete_map=COLOR_FUENTES,
            )
            st.plotly_chart(aplicar_tema(fig2), use_container_width=True)
        else:
            st.info("Sin datos salariales para este filtro.")

    st.divider()
    col_izq2, col_der2 = st.columns(2)

    # 3. Ofertas por fuente
    with col_izq2:
        st.subheader("Ofertas por Fuente")
        cf = df_f["fuente"].value_counts().reset_index()
        cf.columns = ["fuente", "cantidad"]
        fig3 = px.pie(cf, names="fuente", values="cantidad", hole=0.45,
                      color="fuente", color_discrete_map=COLOR_FUENTES)
        st.plotly_chart(aplicar_tema(fig3), use_container_width=True)

    # 4. Clusters PCA 2D
    with col_der2:
        st.subheader("Clusters de Perfiles Tecnológicos")
        df_cl = df_f[df_f["tecnologias"].apply(len) > 0].copy()
        if len(df_cl) >= 4:
            mlb = MultiLabelBinarizer()
            X = mlb.fit_transform(df_cl["tecnologias"].tolist())
            if X.shape[1] >= 2:
                pca = PCA(n_components=2, random_state=42)
                coords = pca.fit_transform(X)
                df_cl["pca_x"] = coords[:, 0]
                df_cl["pca_y"] = coords[:, 1]

                # Etiqueta cada cluster con sus tecnologías más frecuentes en vez
                # del número crudo (0, 1...), que no dice qué se está comparando.
                nombres_cluster = {}
                for cid, grupo in df_cl.groupby("cluster"):
                    top = Counter(t for ts in grupo["tecnologias"] for t in ts).most_common(2)
                    etiqueta = ", ".join(t for t, _ in top) if top else "sin tecnologías"
                    nombres_cluster[cid] = f"Cluster {int(cid)} · {etiqueta}"
                df_cl["perfil"] = df_cl["cluster"].map(nombres_cluster)

                paleta_clusters = ["#B9A6F2", "#F2C744", "#7FD8C4", "#F28FA0", "#7A93F2", "#F2A65A"]
                fig4 = px.scatter(
                    df_cl, x="pca_x", y="pca_y", color="perfil",
                    hover_data={"titulo": True, "fuente": True, "pca_x": False, "pca_y": False},
                    labels={"perfil": "Perfil tecnológico", "pca_x": "Componente PCA 1", "pca_y": "Componente PCA 2"},
                    color_discrete_sequence=paleta_clusters,
                )
                fig4.update_traces(marker=dict(size=11, opacity=0.85, line=dict(width=1, color="rgba(255,255,255,0.4)")))
                fig4.update_layout(legend_title_text="Perfil (K-Means)")
                st.plotly_chart(aplicar_tema(fig4), use_container_width=True)
                st.caption(
                    "Cada punto es una oferta, ubicada según qué tan parecidas son sus "
                    "tecnologías (reducidas a 2 ejes con PCA). El color agrupa las ofertas "
                    "que K-Means detectó como el mismo perfil tecnológico."
                )
            else:
                st.info("Pocas tecnologías para PCA.")
        else:
            st.info("Necesitas más datos para visualizar clusters.")

    # 5. Tendencia temporal
    st.subheader("Tendencia de Publicaciones")
    df_fechas = df_f.dropna(subset=["fecha"]).copy()
    if len(df_fechas) > 1:
        df_fechas["mes"] = df_fechas["fecha"].dt.to_period("M").dt.to_timestamp()
        tend = df_fechas.groupby(["mes", "fuente"]).size().reset_index(name="ofertas")
        fig5 = px.line(tend, x="mes", y="ofertas", color="fuente", markers=True,
                       labels={"mes": "Mes", "ofertas": "Nº de ofertas"},
                       color_discrete_map=COLOR_FUENTES)
        st.plotly_chart(aplicar_tema(fig5), use_container_width=True)
    else:
        st.info("Sin suficientes datos temporales.")

    st.divider()

    # ── Tabla filtrable ───────────────────────────────────────────────────────────

    st.subheader(f"Ofertas ({len(df_f)} resultados)")
    cols_mostrar = [c for c in ["titulo", "empresa", "ubicacion", "fuente", "salario_min", "salario_max", "fecha"] if c in df_f.columns]
    st.dataframe(
        df_f[cols_mostrar].sort_values("fecha", ascending=False, na_position="last"),
        use_container_width=True,
        height=300,
    )

with tab_ia:
    st.subheader("Asistente IA (Ollama local)")
    if not ollama_disponible():
        st.warning(
            "Ollama no está corriendo. Inícialo con `ollama serve` y descarga el "
            "modelo con `ollama pull llama3.2:3b` para usar el asistente.",
            icon=":material/power_off:",
        )
    else:
        st.success("Ollama conectado", icon=":material/check_circle:")

    st.markdown("#### Consulta en lenguaje natural")
    pregunta = st.text_input(
        "Pregúntale a los datos",
        placeholder="Ej: ¿cuáles son las 5 tecnologías más demandadas?",
    )
    if st.button("Preguntar", icon=":material/search:") and pregunta:
        with st.spinner("Pensando..."):
            st.info(consulta_natural(pregunta, df_f))

    st.divider()
    st.markdown("#### Resumen ejecutivo")
    if st.button("Generar resumen del mercado", icon=":material/summarize:"):
        with st.spinner("Generando resumen..."):
            st.write(generar_resumen(df_f))

    st.divider()
    st.markdown("#### Skills emergentes")
    if st.button("Analizar skills emergentes", icon=":material/trending_up:"):
        with st.spinner("Analizando tendencia entre snapshots..."):
            if OFERTAS_HISTORICO_CSV.exists():
                hist = pd.read_csv(OFERTAS_HISTORICO_CSV)
                st.write(skills_emergentes(hist))
            else:
                st.info("Aún no hay histórico. Corre el pipeline al menos una vez.")

st.caption("Proyecto: Análisis del Mercado Laboral IT en Panamá · UTP-FISC · Gestión de la Información · Grupo 4")
