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

st.set_page_config(
    page_title="Mercado IT Panamá",
    page_icon="💻",
    layout="wide",
)

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

st.title("💻 Mercado Laboral IT en Panamá")
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
                color="ofertas", color_continuous_scale="Blues",
            )
            fig1.update_layout(yaxis={"categoryorder": "total ascending"}, height=450, showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)
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
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sin datos salariales para este filtro.")

    st.divider()
    col_izq2, col_der2 = st.columns(2)

    # 3. Ofertas por fuente
    with col_izq2:
        st.subheader("Ofertas por Fuente")
        cf = df_f["fuente"].value_counts().reset_index()
        cf.columns = ["fuente", "cantidad"]
        fig3 = px.pie(cf, names="fuente", values="cantidad",
                      color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig3, use_container_width=True)

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
                df_cl["cluster_str"] = df_cl["cluster"].astype(str)
                fig4 = px.scatter(
                    df_cl, x="pca_x", y="pca_y", color="cluster_str",
                    hover_data={"titulo": True, "fuente": True, "pca_x": False, "pca_y": False},
                    labels={"cluster_str": "Cluster", "pca_x": "PCA 1", "pca_y": "PCA 2"},
                )
                st.plotly_chart(fig4, use_container_width=True)
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
                       labels={"mes": "Mes", "ofertas": "Nº de ofertas"})
        st.plotly_chart(fig5, use_container_width=True)
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
    st.subheader("🤖 Asistente IA (Ollama local)")
    if not ollama_disponible():
        st.warning(
            "Ollama no está corriendo. Inícialo con `ollama serve` y descarga el "
            "modelo con `ollama pull llama3.2:3b` para usar el asistente."
        )
    else:
        st.success("Ollama conectado ✔")

    st.markdown("#### Consulta en lenguaje natural")
    pregunta = st.text_input(
        "Pregúntale a los datos",
        placeholder="Ej: ¿cuáles son las 5 tecnologías más demandadas?",
    )
    if st.button("Preguntar") and pregunta:
        with st.spinner("Pensando..."):
            st.info(consulta_natural(pregunta, df_f))

    st.divider()
    st.markdown("#### Resumen ejecutivo")
    if st.button("Generar resumen del mercado"):
        with st.spinner("Generando resumen..."):
            st.write(generar_resumen(df_f))

    st.divider()
    st.markdown("#### Skills emergentes")
    if st.button("Analizar skills emergentes"):
        with st.spinner("Analizando tendencia entre snapshots..."):
            if OFERTAS_HISTORICO_CSV.exists():
                hist = pd.read_csv(OFERTAS_HISTORICO_CSV)
                st.write(skills_emergentes(hist))
            else:
                st.info("Aún no hay histórico. Corre el pipeline al menos una vez.")

st.caption("Proyecto: Análisis del Mercado Laboral IT en Panamá · UTP-FISC · Gestión de la Información · Grupo 4")
