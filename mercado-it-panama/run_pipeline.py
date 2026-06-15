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
    print("\n[1/3] Scrapeando Konzerta Panama (5 páginas)...")
    from src.ingesta.scraper_konzerta import scrapear_konzerta
    ofertas_kz = scrapear_konzerta(max_paginas=5)
    print(f"      OK Konzerta: {len(ofertas_kz)} ofertas")

    # ── Paso 2: Scraper Computrabajo Panamá ───────────────────
    print("\n[2/3] Scrapeando Computrabajo Panama...")
    from src.ingesta.scraper_computrabajo import scrapear_computrabajo
    ofertas_ct = scrapear_computrabajo(max_paginas=2)
    print(f"      OK Computrabajo: {len(ofertas_ct)} ofertas")
    if len(ofertas_ct) == 0:
        print("      (Nota: Computrabajo usa JS — pipeline continua con otras fuentes)")

    # ── Paso 3: Procesamiento + ML ────────────────────────────
    print("\n[3/3] Procesamiento, transformacion y ML...")
    from src.procesamiento.transformacion import construir_dataset_unificado
    from src.ml.analisis import ejecutar_analisis_completo
    from src.config import OFERTAS_CSV

    df = construir_dataset_unificado()
    resultados_ml = ejecutar_analisis_completo(df)
    df.to_csv(OFERTAS_CSV, index=False)

    print(f"      OK Dataset unificado: {len(df)} ofertas")
    print(f"      OK Fuentes: {df['fuente'].value_counts().to_dict()}")
    print(f"      OK Clusters encontrados: {len(resultados_ml.get('clusters', {}))}")

    reg = resultados_ml.get("regresion")
    if reg:
        print(f"      OK Regresion salario — MAE: ${reg['mae']:,.0f} | R2: {reg['r2']:.3f}")
    else:
        print("      INFO Regresion omitida (pocos datos salariales)")

    print("\n" + "=" * 60)
    print("  Pipeline completado con exito.")
    print(f"  Dataset: {OFERTAS_CSV}")
    print("  Dashboard: streamlit run dashboard/app.py")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
