# Diseño: Modelo Estrella para Power BI + Integración de LLM (Gemini)

**Fecha:** 2026-07-16
**Grupo:** 4 — Análisis del Mercado Laboral IT en Panamá
**Contexto:** Continuación del Segundo Parcial (Proyecto Integrador, UTP-FISC)

## Problema

El proyecto ya cumple los requisitos base del parcial (pipeline con 3 fuentes,
procesamiento, K-Means + RandomForest, dashboard Streamlit y documentación). La
continuación del parcial agrega requisitos nuevos que aún faltan:

1. **Modelo estrella** para la estructura de datos usada en Power BI.
2. **Dashboards en Power BI** (los arma el grupo; el código produce los CSV a importar).
3. **Ampliar KPIs.**
4. **Integración de LLM** para interactuar con los datos (consultas en lenguaje
   natural, resúmenes, apoyo al análisis).
5. **Justificar** el modelo de ML elegido y explicar conceptos y resultados.

El dato actual se guarda en una sola tabla plana (`data/processed/ofertas.csv`),
con las tecnologías serializadas como string separado por `|`. Esa forma no permite
a Power BI modelar la relación N:M oferta↔tecnología ni construir KPIs limpios por
tecnología. Además, el scraping toma una "foto" del momento, sin variación temporal
para analizar tendencias ni skills emergentes.

## Decisiones tomadas (brainstorming)

- **LLM:** Google Gemini (gratis, API key sin tarjeta desde aistudio.google.com).
  Con *fallback*: si no hay `GEMINI_API_KEY`, el módulo avisa y el resto del proyecto
  sigue funcionando.
- **Funciones del LLM:** las cuatro — consultas en lenguaje natural, generación de
  resúmenes, extracción de skills con LLM (complementa el regex), y skills emergentes.
- **Dimensión temporal:** `fecha_scrape` + histórico acumulado. Cada corrida del
  pipeline agrega un snapshot fechado; con varias corridas se construye tendencia real.
- **Estructura de datos:** modelo estrella con tabla puente (no tabla plana).
- **Streamlit se mantiene** (requisito del parcial) y se le agrega una pestaña de IA.
  Power BI queda para las visualizaciones que arma el grupo con los CSV generados.

## Solución

### 1. Modelo estrella (salida en `data/powerbi/`)

Grano de la tabla de hechos: **una fila por oferta por snapshot**.

**Tabla de hechos**
- `fact_ofertas.csv` — `id_oferta` (surrogate), FKs (`id_empresa`, `id_ubicacion`,
  `id_fuente`, `id_fecha_scrape`, `id_fecha_publicacion`, `id_cluster`), medidas
  (`salario_min`, `salario_max`, `salario_promedio`, `num_tecnologias`).

**Tabla puente (resuelve N:M oferta↔tecnología)**
- `bridge_oferta_tecnologia.csv` — `id_oferta`, `id_tecnologia`.

**Dimensiones**
- `dim_empresa.csv` — `id_empresa`, `nombre_empresa`
- `dim_ubicacion.csv` — `id_ubicacion`, `ubicacion`, `es_remoto`
- `dim_fuente.csv` — `id_fuente`, `fuente`
- `dim_fecha.csv` — `id_fecha`, `fecha`, `anio`, `mes`, `nombre_mes`, `trimestre`, `dia`
- `dim_tecnologia.csv` — `id_tecnologia`, `tecnologia`, `categoria`
  (lenguaje / framework / base_datos / cloud_devops / otro — agrupado desde `TECH_DICT`)
- `dim_cluster.csv` — `id_cluster`, `nombre_perfil`, `descripcion` (perfiles del K-Means)

```
         dim_empresa   dim_ubicacion   dim_fuente
              \             |             /
               \            |            /
   dim_fecha ── fact_ofertas ── dim_cluster
                    |
           bridge_oferta_tecnologia
                    |
              dim_tecnologia
```

**Unidad nueva:** `src/procesamiento/modelo_estrella.py`
- Entrada: histórico de ofertas.
- Salida: los 8 CSV anteriores en `data/powerbi/`.
- Responsabilidad única: normalizar el dataset unificado en tablas dimensionales +
  hechos + puente, asignando IDs surrogate estables por dimensión.

### 2. Cambios en el pipeline

- Añadir campo **`fecha_scrape`** a cada oferta en la transformación.
- Acumular histórico en **`data/processed/ofertas_historico.csv`** (append por corrida;
  deduplicación *dentro* del mismo snapshot, no entre snapshots — cada snapshot es una foto).
- `data/processed/ofertas.csv` se mantiene como "última foto" (compatibilidad con el
  dashboard y ML actuales).
- Nuevo paso al final de `run_pipeline.py`: construir el modelo estrella.

### 3. Módulo LLM (`src/llm/`)

- `src/llm/gemini_cliente.py` — cliente único a Gemini; lee `GEMINI_API_KEY` del entorno;
  fallback claro si no está configurada.
- Funciones (todas sobre datos ya procesados, con estadísticas agregadas como contexto):
  1. `consulta_natural(pregunta)` — responde preguntas sobre el dataset en español.
  2. `generar_resumen()` — resumen ejecutivo del mercado.
  3. `extraer_skills_llm(texto)` — extracción de skills/salario del texto crudo;
     **paso opcional** del pipeline que complementa el regex, con **caché** para no gastar
     cuota; el regex (`extraccion_tecnologias.py`) sigue como respaldo y como camino por defecto.
  4. `skills_emergentes()` — compara conteos de tecnologías entre snapshots del histórico y
     Gemini explica cuáles crecen.

### 4. Dashboard Streamlit

- Se mantiene el dashboard actual.
- Se agrega pestaña **"Asistente IA"**: chat de consultas, botón de resumen ejecutivo, y
  vista de skills emergentes. Degrada con elegancia si no hay API key.

### 5. KPIs y documentación

- **KPIs base** calculados y disponibles como columnas/medidas para tarjetas en Power BI:
  total de ofertas, salario promedio y mediano, top tecnologías, % remoto, tecnologías por
  perfil, crecimiento de skills entre snapshots.
- **Docs:**
  - Justificación de por qué K-Means (clustering de perfiles) y RandomForest (regresión de
    salario) son adecuados, + explicación de conceptos y resultados (método del codo, MAE, R²).
  - Guía corta para importar los CSV en Power BI y crear las relaciones del modelo estrella.

## Manejo de errores

- **Sin API key:** el módulo LLM y la pestaña de IA muestran un aviso; el pipeline, el ML,
  el dashboard base y la generación del modelo estrella funcionan igual.
- **Cuota Gemini agotada / sin internet:** se captura la excepción y se informa al usuario;
  la extracción de skills cae al regex.
- **Histórico vacío / un solo snapshot:** skills emergentes informa que necesita ≥2 snapshots.
- **Fuentes vacías:** el modelo estrella genera tablas vacías con encabezados correctos
  (no rompe la importación en Power BI).

## Testing

- `modelo_estrella.py`: dado un dataset unificado de ejemplo, verificar que cada dimensión
  no tenga IDs duplicados, que las FKs de la tabla de hechos existan en sus dimensiones, y
  que la puente cubra todas las tecnologías de cada oferta.
- `gemini_cliente.py`: con la key ausente, las funciones retornan el mensaje de fallback sin
  lanzar excepción (mock del cliente Gemini; no se llama a la red en los tests).
- Mantener los 27 tests actuales en verde.

## Fuera de alcance (YAGNI)

- Construir los reportes de Power BI en sí (los arma el grupo en Power BI Desktop).
- Scheduling automático del pipeline.
- Fine-tuning o embeddings/RAG del LLM (basta con contexto agregado en el prompt).
