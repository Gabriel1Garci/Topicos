# src/ml/analisis.py
"""
Análisis de Machine Learning sobre el dataset de ofertas IT.
Técnica principal: K-Means clustering por perfil tecnológico.
Técnica secundaria: Regresión RandomForest de salarios (si hay suficientes datos).
Sin LLMs — requisito del curso.
"""
import logging
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

logger = logging.getLogger(__name__)

COLUMNA_CLUSTER = "cluster"
MIN_MUESTRAS_REGRESION = 20


def _parsear_tecnologias(valor) -> list:
    """Convierte string 'python|react|aws' a lista ['python', 'react', 'aws']."""
    if isinstance(valor, list):
        return valor
    if not valor or (isinstance(valor, float)):
        return []
    return [t.strip() for t in str(valor).split("|") if t.strip()]


def preparar_features_tecnologias(df: pd.DataFrame) -> tuple:
    """
    Convierte la columna 'tecnologias' en matriz one-hot.
    Retorna (X: np.ndarray, nombres_columnas: list[str]).
    """
    tech_listas = df["tecnologias"].apply(_parsear_tecnologias).tolist()
    mlb = MultiLabelBinarizer()
    X = mlb.fit_transform(tech_listas)
    return X.astype(float), list(mlb.classes_)


def _seleccionar_k_optimo(X: np.ndarray, k_min: int = 2, k_max: int = 8) -> int:
    """Método del codo para seleccionar k óptimo."""
    k_max = min(k_max, len(X) - 1)
    if k_max < k_min:
        return k_min
    inercias = []
    rango_k = range(k_min, k_max + 1)
    for k in rango_k:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X)
        inercias.append(km.inertia_)
    diffs = [inercias[i] - inercias[i + 1] for i in range(len(inercias) - 1)]
    k_optimo = list(rango_k)[diffs.index(max(diffs))]
    logger.info(f"K óptimo (método del codo): {k_optimo}")
    return k_optimo


def aplicar_kmeans(
    X: np.ndarray,
    nombres_tech: list,
    n_clusters: int = None,
) -> tuple:
    """
    Aplica K-Means al espacio de tecnologías.
    Retorna (etiquetas: np.ndarray, resumen: dict).
    resumen[cluster_id] = {n_ofertas, tecnologias_top, nombre_sugerido}
    """
    if n_clusters is None:
        n_clusters = _seleccionar_k_optimo(X)

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    etiquetas = km.fit_predict(X)

    resumen = {}
    for cluster_id in range(n_clusters):
        mask = etiquetas == cluster_id
        if mask.sum() == 0:
            continue
        frecuencias = X[mask].sum(axis=0)
        top_indices = np.argsort(frecuencias)[::-1][:5]
        top_techs = [nombres_tech[i] for i in top_indices if frecuencias[i] > 0]
        resumen[cluster_id] = {
            "n_ofertas": int(mask.sum()),
            "tecnologias_top": top_techs,
            "nombre_sugerido": ", ".join(top_techs[:2]) if top_techs else f"Cluster {cluster_id}",
        }
        logger.info(f"Cluster {cluster_id}: {mask.sum()} ofertas — top: {top_techs[:3]}")

    return etiquetas, resumen


def aplicar_regresion_salario(df: pd.DataFrame) -> dict | None:
    """
    Predice salario promedio usando tecnologías + ubicación.
    Retorna dict con métricas {mae, r2, n_muestras}, o None si hay pocos datos.
    """
    df_sal = df.dropna(subset=["salario_min", "salario_max"]).copy()

    if len(df_sal) < MIN_MUESTRAS_REGRESION:
        logger.info(
            f"Regresión omitida: {len(df_sal)} muestras con salario "
            f"(mínimo: {MIN_MUESTRAS_REGRESION})."
        )
        return None

    df_sal["salario_promedio"] = (df_sal["salario_min"] + df_sal["salario_max"]) / 2
    y = df_sal["salario_promedio"].values

    X_tech, _ = preparar_features_tecnologias(df_sal)
    X_ubic = pd.get_dummies(df_sal["ubicacion"].fillna("desconocido"), prefix="ubic")
    X = np.hstack([X_tech, X_ubic.values])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    modelo = RandomForestRegressor(n_estimators=100, random_state=42)
    modelo.fit(X_train, y_train)
    y_pred = modelo.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    logger.info(f"Regresión salario — MAE: {mae:.0f} USD | R²: {r2:.3f}")

    return {"mae": mae, "r2": r2, "n_muestras": len(df_sal)}


def ejecutar_analisis_completo(df: pd.DataFrame) -> dict:
    """
    Ejecuta clustering + regresión. Añade columna 'cluster' al DataFrame.
    Retorna dict con resultados para el dashboard.
    """
    resultados = {}

    X, nombres_tech = preparar_features_tecnologias(df)

    if len(df) < 2:
        logger.warning("Muy pocas muestras para clustering.")
        df[COLUMNA_CLUSTER] = 0
        resultados["clusters"] = {0: {"n_ofertas": len(df), "tecnologias_top": [], "nombre_sugerido": "General"}}
    else:
        etiquetas, resumen = aplicar_kmeans(X, nombres_tech)
        df[COLUMNA_CLUSTER] = etiquetas
        resultados["clusters"] = resumen

    resultados["regresion"] = aplicar_regresion_salario(df)
    resultados["n_tecnologias"] = len(nombres_tech)

    return resultados
