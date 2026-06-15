# src/config.py
from pathlib import Path

# Rutas base
BASE_DIR = Path(__file__).parent.parent
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"

# Archivos de ingesta
REMOTIVE_RAW = DATA_RAW / "remotive_raw.json"
COMPUTRABAJO_RAW = DATA_RAW / "computrabajo_raw.json"
KONZERTA_RAW = DATA_RAW / "konzerta_raw.json"
KAGGLE_EJEMPLO = DATA_RAW / "ejemplo_kaggle.csv"

# Dataset final
OFERTAS_CSV = DATA_PROCESSED / "ofertas.csv"
OFERTAS_PARQUET = DATA_PROCESSED / "ofertas.parquet"

# Diccionario maestro de tecnologias
# Clave: nombre canonico (lo que se guarda en el dataset)
# Valor: lista de variantes a matchear (regex word-boundary, case-insensitive)
TECH_DICT = {
    # Lenguajes
    "python": ["python"],
    "java": ["java"],
    "javascript": ["javascript", "js"],
    "typescript": ["typescript", "ts"],
    "php": ["php"],
    "c#": ["c#", "csharp", "c sharp"],
    "go": ["golang", "go"],
    "ruby": ["ruby"],
    "kotlin": ["kotlin"],
    "swift": ["swift"],
    # Frameworks web/backend
    "react": ["react\\.js", "reactjs", "react"],
    "angular": ["angular"],
    "vue": ["vue\\.js", "vuejs", "vue"],
    "laravel": ["laravel"],
    "django": ["django"],
    "spring": ["spring boot", "spring"],
    "node.js": ["node\\.js", "nodejs", "node"],
    ".net": ["\\.net", "dotnet"],
    "flask": ["flask"],
    "fastapi": ["fastapi"],
    # Bases de datos
    "mysql": ["mysql"],
    "mariadb": ["mariadb"],
    "postgresql": ["postgresql", "postgres"],
    "mongodb": ["mongodb", "mongo"],
    "redis": ["redis"],
    "sql server": ["sql server", "mssql", "sqlserver"],
    "oracle": ["oracle"],
    "sqlite": ["sqlite"],
    # Cloud / DevOps
    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "gcp": ["gcp", "google cloud"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],
    "git": ["git"],
    "jenkins": ["jenkins"],
    "terraform": ["terraform"],
    "linux": ["linux", "ubuntu", "debian"],
    # Otros
    "rest": ["rest api", "restful"],
    "graphql": ["graphql"],
    "html": ["html"],
    "css": ["css"],
    "sql": ["sql"],
    "power bi": ["power bi", "powerbi"],
    "tableau": ["tableau"],
    "excel": ["excel"],
}
