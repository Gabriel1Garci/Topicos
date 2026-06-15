# Guía de Inicio Rápido — Mercado IT Panamá

## ¿Qué hace este proyecto?

Analiza el mercado laboral de tecnología en Panamá. Descarga ofertas de empleo de múltiples fuentes, detecta las tecnologías más demandadas, agrupa los puestos por perfil usando Machine Learning y muestra todo en un dashboard interactivo.

**En concreto:**
- Extrae empleos IT de fuentes 100% panameñas: Konzerta Panamá, Computrabajo Panamá y un dataset CSV local
- Detecta tecnologías mencionadas en cada oferta (Python, React, AWS, Docker, etc.)
- Agrupa los puestos en clusters por perfil tecnológico (K-Means)
- Muestra gráficas, filtros y estadísticas en un dashboard web

---

## Requisitos previos

Antes de empezar, asegúrate de tener instalado:

| Requisito | Versión mínima | Verificar con |
|-----------|---------------|---------------|
| **Python** | 3.10 o superior | `python --version` |
| **Git** | cualquier versión reciente | `git --version` |
| **Conexión a internet** | para scrapear Konzerta y Computrabajo | — |

> El proyecto fue desarrollado en **Windows 10/11**. Todos los comandos son para PowerShell.

---

## Instalación (solo la primera vez)

```powershell
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd mercado-it-panama

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar el entorno virtual
.\venv\Scripts\activate

# 4. Instalar dependencias
pip install -r requirements.txt
```

Cuando el entorno está activo verás `(venv)` al inicio de la línea en la terminal.

---

## Cómo iniciar el proyecto

### Paso 1 — Activar el entorno virtual

Cada vez que abras una terminal nueva, debes activar el venv primero:

```powershell
.\venv\Scripts\activate
```

### Paso 2 — Correr el pipeline de datos

Descarga las ofertas, procesa los datos y ejecuta el ML:

```powershell
python run_pipeline.py
```

Verás algo como:

```
[1/3] Scrapeando Konzerta Panama (5 páginas)...   OK Konzerta: ~80 ofertas
[2/3] Scrapeando Computrabajo Panama...            OK Computrabajo: 0 ofertas (usa JS)
[3/3] Procesamiento, transformacion y ML...        OK Dataset: ~100 ofertas, 2 clusters
Pipeline completado con exito.
```

### Paso 3 — Abrir el dashboard

```powershell
streamlit run dashboard/app.py
```

Luego abrir en el navegador: **http://localhost:8501**

---

## Si algo falla

| Problema | Solución |
|----------|----------|
| `venv\Scripts\activate` no funciona | Ejecutar: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `ModuleNotFoundError` al correr el pipeline | El venv no está activo — ejecutar `.\venv\Scripts\activate` primero |
| Konzerta devuelve 0 ofertas | Problema de red o sitio caído — el pipeline continúa con las otras fuentes |
| Computrabajo devuelve 0 ofertas | Normal — el sitio usa JavaScript. El pipeline continúa con las otras fuentes |
| Puerto 8501 ocupado | Correr: `streamlit run dashboard/app.py --server.port 8502` |

---

## Estructura resumida

```
mercado-it-panama/
├── run_pipeline.py        ← punto de entrada principal
├── dashboard/app.py       ← dashboard web (Streamlit)
├── src/
│   ├── ingesta/           ← descarga datos (API, CSV, scraper)
│   ├── procesamiento/     ← limpieza y extracción de tecnologías
│   └── ml/                ← clustering y regresión
├── data/processed/
│   └── ofertas.csv        ← dataset generado por el pipeline
└── requirements.txt       ← dependencias Python
```

---

## Resumen en 3 comandos

```powershell
.\venv\Scripts\activate
python run_pipeline.py
streamlit run dashboard/app.py
```
