# run_pipeline.py
"""
Orquestador del pipeline completo: ingesta → procesamiento → ML → dataset final.
Uso: python run_pipeline.py
"""
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("pipeline")

sys.path.insert(0, str(Path(__file__).parent))


def main():
    print("\n" + "=" * 60)
    print("  PIPELINE: Mercado Laboral IT en Panamá")
    print("=" * 60)

    # ── Paso 1: Scraper Konzerta Panamá ───────────────────────
    print("\n[1/4] Scrapeando Konzerta Panama (5 páginas)...")
    from src.ingesta.scraper_konzerta import scrapear_konzerta
    ofertas_kz = scrapear_konzerta(max_paginas=5)
    print(f"      OK Konzerta: {len(ofertas_kz)} ofertas")

    # ── Paso 2: Scraper Computrabajo Panamá ───────────────────
    print("\n[2/4] Scrapeando Computrabajo Panama...")
    from src.ingesta.scraper_computrabajo import scrapear_computrabajo
    ofertas_ct = scrapear_computrabajo(max_paginas=2)
    print(f"      OK Computrabajo: {len(ofertas_ct)} ofertas")
    if len(ofertas_ct) == 0:
        print("      (Nota: Computrabajo usa JS — pipeline continua con otras fuentes)")

    # ── Paso 3: Procesamiento + ML ────────────────────────────
    print("\n[3/4] Procesamiento, transformacion y ML...")
    from src.procesamiento.transformacion import construir_dataset_unificado, anexar_historico
    from src.ml.analisis import ejecutar_analisis_completo
    from src.config import OFERTAS_CSV

    df = construir_dataset_unificado()
    resultados_ml = ejecutar_analisis_completo(df)   # añade columna 'cluster'
    df.to_csv(OFERTAS_CSV, index=False)
    anexar_historico(df)                             # acumula snapshot (con cluster)

    print(f"      OK Dataset unificado: {len(df)} ofertas")
    print(f"      OK Fuentes: {df['fuente'].value_counts().to_dict()}")
    print(f"      OK Clusters encontrados: {len(resultados_ml.get('clusters', {}))}")

    reg = resultados_ml.get("regresion")
    if reg:
        print(f"      OK Regresion salario — MAE: ${reg['mae']:,.0f} | R2: {reg['r2']:.3f}")
    else:
        print("      INFO Regresion omitida (pocos datos salariales)")

    # ── Paso 4: Modelo estrella para Power BI ─────────────────
    print("\n[4/4] Generando modelo estrella para Power BI...")
    from src.procesamiento.modelo_estrella import construir_modelo_estrella
    from src.config import DATA_POWERBI
    tablas = construir_modelo_estrella()
    print(f"      OK {len(tablas)} tablas escritas en {DATA_POWERBI}")

    print("\n" + "=" * 60)
    print("  Pipeline completado con exito.")
    print(f"  Dataset: {OFERTAS_CSV}")
    print("  Dashboard: streamlit run dashboard/app.py")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
