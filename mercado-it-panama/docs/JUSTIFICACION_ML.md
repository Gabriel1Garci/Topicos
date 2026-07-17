# Justificación del Modelo de Machine Learning

## Problema
Queremos (1) descubrir qué perfiles tecnológicos existen en el mercado IT de Panamá
y (2) estimar el salario según tecnologías y ubicación. Son dos problemas distintos:
uno no supervisado (agrupar sin etiquetas) y uno supervisado (predecir un número).

## Técnica principal: K-Means (clustering)
**Por qué es la adecuada:** no tenemos etiquetas de "tipo de puesto"; queremos que los
datos revelen agrupaciones por sí mismos. K-Means agrupa las ofertas según las
tecnologías que comparten (codificadas one-hot con `MultiLabelBinarizer`), descubriendo
familias como frontend, backend, data o devops.

**Conceptos:**
- *One-hot de tecnologías*: cada oferta es un vector binario (tiene o no cada tecnología).
- *Método del codo*: probamos k=2..8 y elegimos el k donde la inercia deja de bajar
  fuerte (mayor caída marginal). Implementado en `_seleccionar_k_optimo`.
- *Inercia*: suma de distancias al cuadrado de cada punto a su centroide.

**Resultados:** cada cluster reporta nº de ofertas y sus tecnologías top, que usamos
como "nombre de perfil" en `dim_cluster`.

## Técnica secundaria: Regresión RandomForest
**Por qué:** el salario es numérico y depende de forma no lineal de muchas tecnologías y
la ubicación. RandomForest maneja bien no linealidades e interacciones sin escalar datos.
Se ejecuta solo si hay ≥20 ofertas con salario.

**Métricas:**
- *MAE* (Error Absoluto Medio): en promedio, cuántos dólares nos equivocamos.
- *R²*: proporción de la variación del salario explicada por el modelo (1.0 = perfecto).

## Limitaciones
El volumen y la calidad salarial de las fuentes locales limitan la regresión; por eso el
clustering es la técnica principal y la regresión es complementaria.
