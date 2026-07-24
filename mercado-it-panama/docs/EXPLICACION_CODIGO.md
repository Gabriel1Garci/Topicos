# Explicación del código (el proyecto de Python)

> Recorrido por el código que genera los datos del dashboard. Pensado para entender
> qué hace cada archivo sin ser el autor. En sencillo y con los términos técnicos.

---

## Cómo está organizado el proyecto

```
mercado-it-panama/
├── run_pipeline.py            ← el "botón de arranque": corre todo en orden
├── src/
│   ├── config.py              ← configuración: rutas, diccionario de tecnologías
│   ├── ingesta/               ← los scrapers (recogen datos de internet)
│   │   ├── scraper_konzerta.py
│   │   └── scraper_computrabajo.py
│   ├── procesamiento/         ← limpieza y armado de los datos
│   │   ├── limpieza.py
│   │   ├── extraccion_tecnologias.py
│   │   ├── transformacion.py
│   │   └── modelo_estrella.py
│   ├── ml/
│   │   └── analisis.py        ← el Machine Learning (K-Means)
│   └── llm/
│       └── ollama_cliente.py  ← el asistente de IA (LLM)
├── dashboard/app.py           ← dashboard alternativo en Streamlit
└── data/                      ← los datos (raw → processed → powerbi)
```

La idea: cada carpeta es una etapa. Los datos entran crudos por `ingesta`, pasan por
`procesamiento`, se analizan en `ml`, y salen como CSV para Power BI.

---

## `run_pipeline.py` — el orquestador

Es el archivo que se ejecuta con `python run_pipeline.py`. No hace el trabajo pesado:
**llama a los demás en orden**. Como un director de orquesta.

Su lógica, en 4 pasos:
1. **Scrapea Konzerta** (`scrapear_konzerta`)
2. **Scrapea Computrabajo** (`scrapear_computrabajo`)
3. **Procesa + ML:** une las fuentes (`construir_dataset_unificado`), corre el K-Means
   (`ejecutar_analisis_completo`) y guarda el histórico (`anexar_historico`)
4. **Genera el modelo estrella** (`construir_modelo_estrella`) → los 8 CSV para Power BI

> **Concepto técnico:** esto es un **pipeline ETL** (Extract, Transform, Load):
> Extraer (scrapers) → Transformar (limpieza, unificación, ML) → Cargar (CSV del
> modelo estrella).

---

## `src/config.py` — la configuración central

Guarda en un solo lugar las cosas que usan todos los módulos:
- **Rutas** de las carpetas (`data/raw`, `data/processed`, `data/powerbi`).
- **`TECH_DICT`** — el **diccionario maestro de tecnologías**: ~45 tecnologías con sus
  variantes de escritura (ej. `"node.js": ["node.js", "nodejs", "node"]`). Es lo que
  usa el detector de tecnologías.
- **`TECH_CATEGORIAS`** — a qué familia pertenece cada tecnología (lenguaje, framework,
  base de datos, cloud/devops, otro).
- **Config de Ollama** (el LLM): la URL y el modelo (`llama3.2:3b`).

> **Por qué tener un config:** si mañana cambia una ruta o se agrega una tecnología, se
> edita **un solo archivo** en vez de buscar por todo el código. Buena práctica.

---

## Los scrapers (`src/ingesta/`)

Recogen las ofertas de los portales. Ambos tienen la misma estructura: abrir el sitio,
leer las ofertas, guardarlas en `data/raw/`. Si fallan, **devuelven lista vacía** en
vez de romper el pipeline (*degradación elegante*).

### `scraper_konzerta.py`
- **Problema:** Konzerta es una *SPA* (la página se arma con JavaScript). Un lector
  simple vería la página vacía.
- **Solución:** usa **Playwright**, que abre un Chrome real por debajo, espera a que
  carguen las ofertas, y las lee con `page.evaluate()` (ejecuta JavaScript dentro del
  navegador para sacar los datos).
- Por cada oferta saca: título, empresa, ubicación, fecha, descripción, modalidad.
- Recorre varias páginas de resultados (paginación).

### `scraper_computrabajo.py`
- **Más simple:** Computrabajo manda las ofertas ya en el HTML (*renderizado en
  servidor*). No hace falta navegador.
- Usa **requests** (baja la página) + **BeautifulSoup** (lee el HTML).
- Busca las tarjetas de oferta con selectores CSS (`article.box_offer`, etc.) y saca
  título, empresa, ubicación, salario y fecha.
- Detalle técnico: fuerza codificación UTF-8 para que los acentos ("Panamá") no se
  rompan.

> **Concepto técnico:** *web scraping*. La diferencia clave entre los dos scrapers es
> **SSR vs SPA** (renderizado en servidor vs en el navegador). Por eso uno necesita
> Playwright y el otro no. Es un buen punto para la sustentación.

---

## El procesamiento (`src/procesamiento/`)

### `limpieza.py`
Funciones para dejar el texto presentable:
- `limpiar_texto()` — quita HTML, espacios de más, pasa a minúsculas.
- `parsear_salario()` — intenta sacar números de salario de textos variados
  ("B/. 1,500 - 2,000", "$2500").
- `eliminar_duplicados_nulos()` — quita ofertas sin título o repetidas.

### `extraccion_tecnologias.py`
El corazón de "detectar qué tecnologías pide una oferta". La función
`extraer_tecnologias(texto)` recorre el `TECH_DICT` y busca cada tecnología en el texto
con **expresiones regulares** (regex), respetando límites de palabra (para que "go" no
se confunda dentro de "google").

> **Importante para el 2° parcial:** esto **reemplaza a un LLM**. En vez de pedirle a
> una IA que extraiga las tecnologías, se hace con búsqueda de diccionario. Es más
> simple, gratis y explicable.

### `transformacion.py`
Toma las salidas de los dos scrapers (que tienen formatos distintos) y las **unifica a
un esquema común**: mismas columnas para todas (título, empresa, ubicación,
tecnologías, fecha, fuente…). Luego junta todo en un solo DataFrame y lo guarda.

También tiene `anexar_historico()`: cada corrida agrega su "foto" al histórico
acumulado. Por eso hay 3 fechas de captura.

> **Concepto técnico:** *normalización a esquema común*. Datos heterogéneos (de fuentes
> distintas) → un formato homogéneo. Es lo que permite analizarlos juntos.

### `modelo_estrella.py`
Convierte el dataset unificado en las **8 tablas del modelo estrella** (dimensiones +
hechos + puente) y las guarda como CSV en `data/powerbi/`.

Cómo lo hace:
- Crea cada **dimensión** sacando los valores únicos (todas las empresas distintas, todas
  las ubicaciones…) y les da un **id** (clave *surrogate*, un número correlativo).
- Crea la **tabla de hechos** reemplazando cada texto por su id (la oferta ya no dice
  "Banco General" sino el id que apunta a `dim_empresa`).
- Crea la **tabla puente** oferta↔tecnología (una fila por cada par).
- Maneja los nulos con un **miembro centinela** (`id_fecha = -1` para "sin fecha").

> **Concepto técnico:** *dimensional modeling*. Claves surrogate, tabla de hechos,
> dimensiones y bridge para el muchos-a-muchos. Este archivo es literalmente el que
> construye lo que importaste en Power BI.

---

## El Machine Learning (`src/ml/analisis.py`)

Hace el **clustering K-Means**. Pasos del código:

1. **`preparar_features_tecnologias()`** — convierte la lista de tecnologías de cada
   oferta en un **vector one-hot** con `MultiLabelBinarizer` de scikit-learn (una
   columna por tecnología, 1 o 0).
2. **`_seleccionar_k_optimo()`** — aplica el **método del codo**: prueba k de 2 a 8,
   mide la **inercia** de cada uno, y elige dónde deja de mejorar. Dio k=2.
3. **`aplicar_kmeans()`** — corre K-Means con ese k y etiqueta cada oferta con su
   cluster. Además saca las tecnologías top de cada grupo (para nombrarlos).
4. **`aplicar_regresion_salario()`** — la técnica secundaria (RandomForest para predecir
   salario). Solo corre si hay ≥20 ofertas con salario; como no las hay, se omite.

> **Librería:** scikit-learn (`KMeans`, `MultiLabelBinarizer`, `RandomForestRegressor`).
> Es la librería estándar de ML en Python.

---

## El LLM (`src/llm/ollama_cliente.py`)

Conecta con **Ollama**, un programa que corre modelos de IA **localmente** (en la misma
PC, sin internet ni pagar API). El modelo usado es `llama3.2:3b`.

Funciones principales:
- **`consulta_natural()`** — le pasas una pregunta en español y un resumen de los datos,
  y el LLM responde.
- **`generar_resumen()`** — pide al LLM un resumen ejecutivo del mercado.
- **`skills_emergentes()`** — compara dos capturas y pregunta al LLM qué tecnologías
  están creciendo.

**Detalle importante:** todo tiene *degradación elegante*. Si Ollama no está corriendo,
las funciones devuelven un mensaje de aviso en vez de romperse (`ollama_disponible()`
verifica primero).

> **Concepto técnico:** *LLM local* vs API en la nube. Ventaja: privado y gratis.
> Se comunica por HTTP con el servicio de Ollama (`requests.post` al endpoint
> `/api/generate`).

---

## `dashboard/app.py` — el dashboard de Streamlit

Es un **segundo dashboard** (aparte del de Power BI), hecho en Python con Streamlit.
Tiene dos pestañas:
- **Dashboard:** gráficas con Plotly (top tecnologías, salarios, clusters…).
- **Asistente IA:** la interfaz para hablar con el LLM (Ollama).

> Se levanta con `streamlit run dashboard/app.py`. Es donde vive el LLM "real" del
> proyecto, y complementa al dashboard de Power BI.

---

## Resumen: quién hace qué

| Archivo | Qué hace | Tecnología clave |
|---|---|---|
| `run_pipeline.py` | Orquesta todo en orden | — |
| `config.py` | Rutas y diccionario de tecnologías | — |
| `scraper_konzerta.py` | Scrapea Konzerta (SPA) | Playwright |
| `scraper_computrabajo.py` | Scrapea Computrabajo (SSR) | requests + BeautifulSoup |
| `limpieza.py` | Limpia texto y salarios | regex |
| `extraccion_tecnologias.py` | Detecta tecnologías (reemplaza LLM) | regex + diccionario |
| `transformacion.py` | Unifica al esquema común | pandas |
| `modelo_estrella.py` | Construye las 8 tablas para Power BI | pandas |
| `analisis.py` | K-Means (clustering) | scikit-learn |
| `ollama_cliente.py` | Asistente IA | Ollama (LLM local) |
| `dashboard/app.py` | Dashboard alternativo + chat IA | Streamlit + Plotly |
