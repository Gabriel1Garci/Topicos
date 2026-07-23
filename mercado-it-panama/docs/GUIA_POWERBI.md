# Guía: Importar el Modelo Estrella en Power BI

## 1. Generar los CSV
Corre el pipeline: `python run_pipeline.py`. Esto crea 8 CSV en `data/powerbi/`.

## 2. Importar en Power BI Desktop
`Inicio → Obtener datos → Texto/CSV` e importa las 8 tablas:
`dim_empresa, dim_ubicacion, dim_fuente, dim_fecha, dim_tecnologia, dim_cluster,
fact_ofertas, bridge_oferta_tecnologia`.

## 3. Crear las relaciones (vista Modelo)
Arrastra para crear estas relaciones (1 → muchos, dirección simple desde la dimensión
hacia la tabla de hechos):

| Dimensión (1) | Columna | Hechos (muchos) | Columna |
|---|---|---|---|
| dim_empresa | id_empresa | fact_ofertas | id_empresa |
| dim_ubicacion | id_ubicacion | fact_ofertas | id_ubicacion |
| dim_fuente | id_fuente | fact_ofertas | id_fuente |
| dim_cluster | id_cluster | fact_ofertas | id_cluster |
| dim_fecha | id_fecha | fact_ofertas | id_fecha_scrape |
| dim_fecha | id_fecha | fact_ofertas | id_fecha_publicacion (inactiva) |

Para la tabla puente (tecnologías):
- `dim_tecnologia (1) → bridge (muchos)` por `id_tecnologia`
- `fact_ofertas (1) → bridge (muchos)` por `id_oferta`

## 4. KPIs sugeridos (medidas DAX)
```
Total Ofertas = COUNTROWS(fact_ofertas)
Salario Promedio = AVERAGE(fact_ofertas[salario_promedio])
% Remoto = DIVIDE(CALCULATE(COUNTROWS(fact_ofertas), dim_ubicacion[es_remoto]=TRUE()), [Total Ofertas])
Tecnologías Únicas = DISTINCTCOUNT(bridge_oferta_tecnologia[id_tecnologia])
```

### KPIs adicionales
```
Salario Mediano = MEDIAN(fact_ofertas[salario_promedio])
Empresas Únicas = DISTINCTCOUNT(fact_ofertas[id_empresa])
% Ofertas con Salario Informado = DIVIDE(
    CALCULATE(COUNTROWS(fact_ofertas), NOT ISBLANK(fact_ofertas[salario_promedio])),
    [Total Ofertas]
)
Promedio Tecnologías por Oferta = AVERAGE(fact_ofertas[num_tecnologias])
Antigüedad Promedio (días) = AVERAGE(fact_ofertas[antiguedad_dias])
```
- *Salario Mediano* complementa el promedio: es menos sensible a salarios atípicos muy altos o bajos.
- *% Ofertas con Salario Informado* mide cuánta confianza dar al KPI de salario (si la fuente casi no publica salario, el promedio pesa menos).
- *Antigüedad Promedio* usa la nueva columna `antiguedad_dias` de `fact_ofertas` (días entre `fecha` de publicación y `fecha_scrape`); queda en blanco si falta alguna de las dos fechas.

## 5. Visualizaciones sugeridas
- Barras: top tecnologías (dim_tecnologia + conteo del bridge).
- Líneas: ofertas por mes (dim_fecha[nombre_mes] y dim_fecha[anio]) → tendencia temporal.
  (En Power BI, selecciona la columna `nombre_mes` → "Ordenar por columna" → `mes`, para que los
  meses aparezcan en orden cronológico y no alfabético.)
- Tarjetas: los KPIs de arriba.
- Segmentador por `dim_tecnologia[categoria]` y `dim_fuente[fuente]`.
