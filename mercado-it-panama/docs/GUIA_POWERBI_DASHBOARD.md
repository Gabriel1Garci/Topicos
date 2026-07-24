# Guía paso a paso: Dashboard en Power BI

> **Cómo usar esta guía:** son **34 pasos seguidos**. Hazlos en orden, de arriba
> hacia abajo, sin saltarte ninguno. Cada paso es una acción concreta.
>
> Al final hay **5 anexos** de consulta (qué datos hay, tabla de agregaciones,
> errores comunes, preguntas del profesor). **No los necesitas para construir** —
> están ahí para cuando algo falle o para preparar la sustentación.

## Vocabulario: las zonas de la pantalla

Ubica estas 5 zonas antes de empezar. La guía las nombra así todo el tiempo.

| Nombre en la guía | Dónde está | Qué es |
|---|---|---|
| **Lienzo** | El área blanca grande del centro | Donde se colocan los visuales |
| **Panel `Datos`** | Extremo derecho | La lista de tus 8 tablas y sus columnas |
| **Panel `Compilar`** | Junto al de `Datos` | Elegir el tipo de visual y colocar los campos |
| **Casillas** | Dentro de `Compilar`, al seleccionar un visual | Cajas con nombre (`Campos`, `Eje X`, `Eje Y`, `Leyenda`, `Valores`) donde sueltas los campos |
| **Pestañas de página** | Abajo a la izquierda | Como las hojas de Excel. El botón `+` agrega páginas |

> **Nota de versiones:** en Power BI reciente el panel se llama **`Compilar`**; en
> versiones anteriores se llamaba **`Visualizaciones`**. Es el mismo.

Y en el **extremo izquierdo** hay 3 iconos apilados: las vistas de trabajo —
`Informe` (arriba), `Tabla` (medio), `Modelo` (abajo).

### Cómo insertar un visual (lo harás ~20 veces)

Esta secuencia se repite en casi todos los pasos:

1. Clic en un área **vacía del lienzo** (para no modificar un visual existente)
2. En el panel `Datos`, **marca la casilla** ☐ de una de las columnas que necesitas
   → Power BI crea un visual automáticamente
3. Con ese visual seleccionado, en el panel `Compilar` **pasa el mouse** por los
   iconos de la cuadrícula superior: sale un globito con el nombre de cada tipo.
   Clic en el que necesites (`Tarjeta`, `Gráfico de anillos`, `Matriz`…)
4. Debajo de la cuadrícula aparecen las **casillas**. Arrastra ahí los demás campos
   desde el panel `Datos`
5. Para cambiar cómo se agrega un campo (**la agregación**), según tu versión:
   - **Versiones nuevas:** clic en la **`>`** a la derecha del campo dentro de la
     casilla → se abre un panelito con `Campo` y **`Resumen`** → despliega `Resumen`
     y elige (`Suma`, `Promedio`, `Recuento`, `Recuento distinto`…)
   - **Versiones anteriores:** pasa el mouse sobre el campo → **flechita ▾** a su
     derecha → clic → elige la agregación
6. Para renombrarlo: **doble clic** sobre su nombre dentro de la casilla → escribe
   el nuevo → Enter

> ⚠️ **Dos cosas que confunden mucho al principio:**
>
> **1. El nombre de las casillas cambia según el tipo de visual.** Una tarjeta tiene
> `Campos` (o `Valor`); un gráfico de barras tiene `Eje Y`, `Eje X` y `Leyenda`; una
> matriz tiene `Filas`, `Columnas` y `Valores`. Si la guía menciona una casilla que
> no ves, es porque **todavía no cambiaste el visual al tipo correcto**. Cambia
> primero el tipo, y después coloca los campos.
>
> **2. `Resumen` aparece gris (deshabilitado)** cuando el campo está en una casilla
> que no agrega, como `Categorías`, `Eje X` o `Filas`. Solo se activa en casillas de
> valores (`Valor`, `Valores`, `Campos`, `Eje Y` de un gráfico de barras). Si lo ves
> gris, arrastra el campo a la casilla de valores.

---

# PARTE 1 — Preparar los datos y el modelo

## Paso 1 — Desactivar la autodetección de relaciones

`Archivo` → `Opciones y configuración` → `Opciones` → sección `ARCHIVO ACTUAL` →
`Carga de datos`.

**Desmarca** la casilla `Detectar automáticamente nuevas relaciones después de la
carga de datos` → `Aceptar`.

> Si la dejas activa, Power BI inventa relaciones solo y te desarma el modelo
> estrella. Queremos crear cada una a mano.

## Paso 2 — Guardar el archivo

`Archivo` → `Guardar como` → `dashboard_mercado_it.pbix`.

## Paso 3 — Importar la primera tabla

`Inicio` → `Obtener datos` → `Texto/CSV` → navega a
`mercado-it-panama\data\powerbi\` → selecciona `dim_empresa.csv` → `Abrir`.

En la ventana de vista previa, **antes de cargar**, revisa arriba:
- `Origen del archivo` debe decir **`65001: Unicode (UTF-8)`**. Si no, cámbialo.
- `Delimitador`: `Coma`.

Pulsa **`Transformar datos`** (no `Cargar`).

## Paso 4 — Verificar los tipos y aplicar

Se abre el Editor de Power Query. Mira el **icono a la izquierda de cada nombre de
columna**:

| Icono | Significa |
|---|---|
| `1²3` | Número entero |
| `1.2` | Número decimal |
| `ABC` | Texto |
| 📅 | Fecha |
| `ABC/123` | Cualquiera — **hay que corregirlo** |

Para `dim_empresa` debe quedar: `id_empresa` = `1²3`, `nombre_empresa` = `ABC`.
Normalmente Power Query ya lo hizo solo (verás un paso `Tipo cambiado` en
`PASOS APLICADOS`, a la derecha). Si algo está mal, clic en el icono → elige el tipo.

`Inicio` → `Cerrar y aplicar`.

## Paso 5 — Importar las otras 7 tablas

Repite **Paso 3 y Paso 4** para cada una. Tipos esperados:

| Archivo | Tipos |
|---|---|
| `dim_ubicacion.csv` | `id_ubicacion` entero · `ubicacion` texto · `es_remoto` True/False |
| `dim_fuente.csv` | `id_fuente` entero · `fuente` texto |
| `dim_tecnologia.csv` | `id_tecnologia` entero · `tecnologia` texto · `categoria` texto |
| `dim_cluster.csv` | `id_cluster` entero · `nombre_perfil` texto |
| `dim_fecha.csv` | `id_fecha` entero · `fecha` **Fecha** · `anio` `mes` `trimestre` `dia` entero · `nombre_mes` texto |
| `fact_ofertas.csv` | todos los `id_*` entero · `num_tecnologias` entero · `titulo` texto · los 3 `salario_*` **Número decimal** |
| `bridge_oferta_tecnologia.csv` | `id_oferta` entero · `id_tecnologia` entero |

> **En `fact_ofertas` sí tendrás que intervenir:** las columnas `salario_min`,
> `salario_max` y `salario_promedio` están vacías, así que Power Query las marcará
> como `ABC/123`. Cámbialas a **Número decimal**.
>
> **En `dim_fecha`** hay una fila con `id_fecha = -1` y fecha vacía. **Déjala.** Es
> el miembro centinela para fechas nulas.

Al terminar debes tener **8 tablas** en el panel `Datos`.

## Paso 6 — Crear la columna `Clave Oferta`

`Inicio` → `Transformar datos` (vuelve al Editor de Power Query).

1. En `Consultas` (izquierda), selecciona **`fact_ofertas`**
2. Clic en el encabezado de la columna `titulo`
3. Con `Ctrl` presionado, clic en `id_empresa` (quedan las dos marcadas)
4. Pestaña `Agregar columna` → botón `Combinar columnas`
5. `Separador`: elige `--Personalizado--` y escribe ` | `
6. `Nombre de la nueva columna`: `Clave Oferta`
7. `Aceptar`

> Si avisa que hay que cambiar el tipo de `id_empresa`, acepta.

Al final de la tabla aparece la columna nueva con valores tipo
`analista de qa (canales digitales) | 11`.

**Para qué sirve:** el pipeline corrió 3 veces, así que la misma vacante está
repetida. `id_oferta` cambia en cada corrida y no sirve para identificarla; título
+ empresa sí. Con esto podremos contar ofertas **reales** (148) y no filas (409).

## Paso 7 — Crear la columna `tiene_tecnologia`

Sigues en Power Query, con `fact_ofertas` seleccionada.

1. `Agregar columna` → `Columna condicional`
2. `Nombre de la nueva columna`: `tiene_tecnologia`
3. `Si` → columna `num_tecnologias` · operador `es mayor que` · valor `0`
4. `Entonces` → `1`
5. `De lo contrario` → `0`
6. `Aceptar`
7. Cambia el tipo de esa columna a `Número entero` (clic en el icono `ABC/123`)
8. `Inicio` → `Cerrar y aplicar`

**Para qué sirve:** al sacarle el promedio da directamente el % de ofertas donde se
detectó alguna tecnología. Es un indicador de **calidad del dato**.

## Paso 8 — Crear las 7 relaciones del modelo estrella

Ve a la vista **`Modelo`** (tercer icono de la barra izquierda, el de las cajas
conectadas).

Acomoda las tablas: `fact_ofertas` al centro, las dimensiones alrededor. Luego
**arrastra** el campo de la dimensión y suéltalo sobre el de la tabla de hechos:

| # | Arrastra desde | Suelta en |
|---|---|---|
| 1 | `dim_empresa[id_empresa]` | `fact_ofertas[id_empresa]` |
| 2 | `dim_ubicacion[id_ubicacion]` | `fact_ofertas[id_ubicacion]` |
| 3 | `dim_fuente[id_fuente]` | `fact_ofertas[id_fuente]` |
| 4 | `dim_cluster[id_cluster]` | `fact_ofertas[id_cluster]` |
| 5 | `dim_fecha[id_fecha]` | `fact_ofertas[id_fecha_scrape]` |
| 6 | `dim_tecnologia[id_tecnologia]` | `bridge_oferta_tecnologia[id_tecnologia]` |
| 7 | `fact_ofertas[id_oferta]` | `bridge_oferta_tecnologia[id_oferta]` |

Todas deben quedar **`Uno a varios (1:*)`** con dirección de filtro **`Única`**.
Para verificar: doble clic sobre la línea de relación.

## Paso 9 — Revisar que no sobren relaciones

Cuenta las líneas del diagrama: deben ser **exactamente 7**. Si hay alguna que tú no
creaste, clic derecho sobre ella → `Eliminar`.

> El diagrama ya debería verse como una estrella. Tómale captura ahora: es evidencia
> del modelo dimensional.

---

# PARTE 2 — Página 1: Panorama del Mercado IT

**Qué cuenta esta página:** el tamaño y la forma del mercado. Cuántas vacantes hay,
quién contrata y dónde.

## Paso 10 — Crear y nombrar la página

Ve a la vista **`Informe`** (primer icono, arriba a la izquierda).

Abajo a la izquierda están las **pestañas de página** (como las hojas de Excel).
Doble clic sobre `Página 1` y escribe **`Panorama`** → Enter.

## Paso 11 — Insertar las 6 tarjetas de KPI

### La primera, con todo el detalle

**11.1** Clic en un área **vacía del lienzo** (el área blanca del centro).

**11.2** En el panel `Datos` (derecha), despliega `fact_ofertas` y **marca la
casilla** ☐ junto a **`Clave Oferta`**.

> Power BI crea solo un visual en el lienzo, probablemente una tabla. No importa:
> ahora le cambiamos el tipo.

> Si se abre un globo que dice `Sugerir un objeto visual`, ciérralo con la **X**.
> Es una sugerencia automática y no la necesitamos.

**11.3 Convierte el visual en tarjeta.** Con el visual **seleccionado** (se le ve el
borde), ve al panel `Compilar` y **pasa el mouse** por los iconos de la cuadrícula
superior, sin hacer clic. Sale un globito con el nombre de cada tipo.

Busca el que dice **`Tarjeta`** — es un rectángulo pequeño con `123` dentro. Clic.
Si no lo ves en la cuadrícula, pulsa el botón **`...`** al final para desplegar el
resto de los tipos.

> **Cambia el tipo ANTES de acomodar los campos.** Cada tipo de visual tiene sus
> propias casillas, y al cambiar de tipo los campos se reacomodan solos.

**11.4** Ahora, debajo de la cuadrícula, aparece la casilla de valores de la tarjeta
(se llama `Campos` o `Valor`, según tu versión) con `Clave Oferta` dentro.

Si `Clave Oferta` quedó en otra casilla (`Categorías`, por ejemplo), **arrástralo**
hasta la casilla de valores.

**11.5 Cambia la agregación.** Clic en la **`>`** que está a la derecha de
`Clave Oferta`, dentro de la casilla. Se abre un panelito con `Campo` y **`Resumen`**.

> En versiones anteriores no hay `>` sino una **flechita ▾** que abre el menú
> directamente. Es lo mismo.

**11.6** Despliega **`Resumen`** y elige **`Recuento distinto`**.

> Si `Resumen` está **gris**, el campo está en una casilla que no agrega. Arrástralo
> a la casilla de valores y vuelve a intentar.

**11.7** **La tarjeta debe mostrar `148`.** Si muestra 409, elegiste `Recuento` en
lugar de `Recuento distinto`.

**11.8** **Doble clic** sobre el nombre del campo dentro de la casilla → escribe
`Ofertas Únicas` → Enter.

### Las otras 5

Repite **11.1 a 11.8** cambiando el campo y la agregación:

| Tarjeta | Campo a marcar | Agregación | Renombrar a |
|---|---|---|---|
| 1 | `fact_ofertas[Clave Oferta]` | `Recuento distinto` | Ofertas Únicas |
| 2 | `fact_ofertas[id_empresa]` | `Recuento distinto` | Empresas Contratando |
| 3 | `bridge_oferta_tecnologia[id_tecnologia]` | `Recuento distinto` | Tecnologías Demandadas |
| 4 | `fact_ofertas[id_ubicacion]` | `Recuento distinto` | Ubicaciones Activas |
| 5 | `fact_ofertas[num_tecnologias]` | `Promedio` | Prom. Tecnologías por Oferta |
| 6 | `fact_ofertas[tiene_tecnologia]` | `Promedio` | % con Tecnología Detectada |

Colócalas en fila en la parte superior del lienzo.

### 11.9 — Poner título a cada tarjeta

Con una tarjeta seleccionada, ve al panel `Formato` (el **icono del pincel**, junto
a la cuadrícula de iconos en `Compilar`) → `General` → `Título` → actívalo con el
interruptor y escribe el nombre.

En ese mismo panel, baja el `Tamaño de fuente` del valor a ~28 px para que las 6
tarjetas quepan en fila.

### 11.10 — Formatear la tarjeta 6 como porcentaje

La tarjeta 6 mostrará algo como `0.38`. Para que diga `38%`:

1. En el panel `Datos`, despliega `fact_ofertas`
2. Haz **clic sobre el texto** `tiene_tecnologia` — sobre el **nombre**, no sobre la
   casilla ☐. El nombre queda resaltado
3. En la cinta de arriba aparece una pestaña nueva: **`Herramientas de columnas`**.
   Haz clic en ella
4. Busca el grupo **`Formato`**. Ahí hay un desplegable (dice `General` o
   `Número entero`) y unos botones pequeños: `$`, **`%`**, `,`
5. Clic en el botón **`%`**
6. La tarjeta pasa de `0.38` a `38%`

**Si el botón `%` está gris:** la columna quedó como número entero. En esa misma
cinta, grupo `Estructura`, cambia el desplegable **`Tipo de datos`** a
**`Número decimal`**, y vuelve al paso 5.

**Decimales:** en el grupo `Formato` hay un control `Posiciones decimales` (o botones
`.00` / `.0`). Ponlo en **1**.

### 11.11 — Dale presentación a la fila de KPIs

Con las 6 tarjetas puestas se ve plano. Esto lo arregla en ~10 minutos, todo con
botones. Hazlo ahora: motiva ver el avance.

**1. Tema de color.** Pestaña **`Ver`** → **`Temas`** → elige uno (`Innovar` o
`Ejecutivo`). Cambia toda la paleta de golpe.

**2. Fondo de página.** Clic en un área **vacía del lienzo** (sin seleccionar ningún
visual) → el panel `Formato` pasa a opciones de página → **`Fondo del lienzo`** →
`Color`: gris muy claro · `Transparencia`: **0%**.

> Con fondo gris y tarjetas blancas, las tarjetas "flotan". Es el truco que más
> cambia la percepción del dashboard.

**3. Cuerpo de las tarjetas.** Selecciona una tarjeta → panel `Formato`:
- **`Fondo`** → actívalo → `Color`: blanco
- **`Borde`** → actívalo → dentro, **`Radio de esquina`**: `8`
- **`Sombra`** (si tu versión la tiene) → actívala

**4. Copiar el formato a las otras 5.** Selecciona la tarjeta ya formateada →
cinta `Inicio` → botón **`Copiar formato`** (icono de **brocha**, grupo
`Portapapeles`) → clic sobre otra tarjeta. Repite.

**5. Colocar las tarjetas por números** (más fiable que arrastrar o usar `Alinear`).

> ⚠️ **No uses `Alinear` → `Distribuir horizontalmente` con las 6 seleccionadas.**
> Reparte las tarjetas dentro del espacio que ya ocupaba la selección; si son más
> anchas que ese espacio, **se solapan**. Si ya te pasó: `Ctrl + Z` varias veces.

Hazlo **de una en una**:

1. Clic en **una sola** tarjeta (con varias seleccionadas no aparecen estas opciones
   — el panel `Compilar` te avisa: *"seleccione un objeto visual a la vez"*)
2. En el panel `Formato`, clic en la **segunda pestaña**, junto a `Objeto visual`
   (según la versión dice `General`, `Propiedades` o sale truncada como `Pro...`)
3. Sección **`Tamaño`** → escribe `Alto` y `Ancho`
4. Sección **`Posición`** → escribe `Horizontal` y `Vertical`

| Tarjeta | Ancho | Alto | Horizontal | Vertical |
|---|---|---|---|---|
| Ofertas Únicas | 180 | 110 | 20 | 90 |
| Empresas Contratando | 180 | 110 | 210 | 90 |
| Tecnologías Demandadas | 180 | 110 | 400 | 90 |
| Ubicaciones Activas | 180 | 110 | 590 | 90 |
| Prom. Tecnologías por Oferta | 180 | 110 | 780 | 90 |
| % con Tecnología Detectada | 180 | 110 | 970 | 90 |

Mismo `Alto` y mismo `Vertical` = alineadas. `Horizontal` sube de 190 en 190 = espacio
idéntico entre ellas. La franja de `Vertical` 0 a 90 queda libre para el título.

> **Este método de posicionar por números sirve para todos los visuales del reporte.**
> Es más rápido y preciso que arrastrar, y evita que se solapen.

**6. Quitar títulos repetidos.** Si una tarjeta muestra su nombre dos veces (arriba
como título del visual y abajo como etiqueta), quita uno de los dos:

- **Para quitar la etiqueta de abajo** (dejando el título): `Formato` → pestaña
  `Objeto visual` → apaga el interruptor **`Etiqueta de categoría`** (tarjeta
  clásica) o **`Encabezado de categoría`** (tarjeta nueva)
- **Para quitar el título de arriba** (dejando la etiqueta): `Formato` → segunda
  pestaña → **`Título`** → apágalo

**7. Título de la página.** `Insertar` → **`Cuadro de texto`** → escribe
`Mercado Laboral IT en Panamá — Panorama general`. Colócalo arriba de las tarjetas,
tamaño ~20, negrita.

## Paso 12 — Gráfico de anillos: ofertas por fuente

`Insertar` → `Gráfico de anillos`
- `Leyenda`: `dim_fuente[fuente]`
- `Valores`: `fact_ofertas[Clave Oferta]` → flecha ▾ → `Recuento distinto`

**Para qué sirve:** demuestra que el pipeline es **multi-fuente**, que es requisito
del proyecto. Se ve que los datos vienen de dos portales y en qué proporción.

## Paso 13 — Barras: top 10 empresas que más contratan

`Insertar` → `Gráfico de barras agrupadas`
- `Eje Y`: `dim_empresa[nombre_empresa]`
- `Eje X`: `fact_ofertas[Clave Oferta]` → `Recuento distinto`

Ahora el filtro: panel `Filtros` (derecha) → sección `nombre_empresa` →
`Tipo de filtro`: `Filtrado N superior` → `Mostrar elementos`: `Superior` `10` →
arrastra `fact_ofertas[Clave Oferta]` al cuadro `Por valor` → `Aplicar filtro`.

**Para qué sirve:** identifica a los empleadores reales del sector. Verás que
aparecen sobre todo **bancos y BPOs**, no empresas de software — es un hallazgo que
vale la pena mencionar.

## Paso 14 — Barras: distribución geográfica

`Insertar` → `Gráfico de barras agrupadas`
- `Eje Y`: `dim_ubicacion[ubicacion]`
- `Eje X`: `fact_ofertas[Clave Oferta]` → `Recuento distinto`

**Para qué sirve:** responde *¿dónde está el empleo IT?* Verás la concentración
abrumadora en Ciudad de Panamá.

## Paso 15 — Tabla de detalle

`Insertar` → `Tabla`. Arrastra estas columnas en orden:
`fact_ofertas[titulo]` · `dim_empresa[nombre_empresa]` · `dim_ubicacion[ubicacion]` ·
`dim_fuente[fuente]` · `fact_ofertas[num_tecnologias]`

**Para qué sirve:** permite bajar del agregado al dato individual.

## Paso 16 — Segmentaciones

`Insertar` → `Segmentación de datos`, dos veces:
- Una con `dim_fuente[fuente]`
- Otra con `dim_fecha[fecha]`

> En la de `fecha` aparecerá un valor `En blanco` (la fila centinela). En el panel
> `Filtros` de esa segmentación, desmárcalo.

---

# PARTE 3 — Página 2: Demanda Tecnológica

**Qué cuenta esta página:** qué habilidades pide el mercado. Es el corazón del
proyecto y donde se aprovecha la tabla puente.

## Paso 17 — Crear la página

Botón `+` abajo → doble clic en la pestaña nueva → **`Tecnologías`**.

## Paso 18 — Barras: top 15 tecnologías

`Insertar` → `Gráfico de barras agrupadas`
- `Eje Y`: `dim_tecnologia[tecnologia]`
- `Eje X`: `bridge_oferta_tecnologia[id_tecnologia]` → `Recuento` → renombra a
  `Menciones de Tecnología`

Filtro: panel `Filtros` → `tecnologia` → `Filtrado N superior` → `Superior` `15` →
`Por valor`: el mismo campo → `Aplicar filtro`.

**Para qué sirve:** es la respuesta directa a la pregunta del proyecto. Verás
arriba **sql (77), python (47), excel (38), azure (38), power bi (38)**.

> **Dato para defender:** que `sql`, `excel` y `power bi` estén tan arriba dice que
> el mercado panameño demanda más **perfiles de datos y análisis** que desarrollo
> puro. Eso es una conclusión, no solo un gráfico.

## Paso 19 — Treemap: composición por categoría

`Insertar` → `Treemap`
- `Categoría`: `dim_tecnologia[categoria]`
- `Valores`: `bridge_oferta_tecnologia[id_tecnologia]` → `Recuento`

**Para qué sirve:** agrupa las 45 tecnologías en 5 familias. Esa categoría viene de
`dim_tecnologia` — y es justamente **para qué existe una dimensión**: añadir
atributos que permiten agrupar.

## Paso 20 — Matriz: tecnología × fuente

**20.1** Inserta el visual: marca `dim_tecnologia[tecnologia]` en el panel `Datos` →
en `Compilar`, cambia el tipo a **`Matriz`** (icono de cuadrícula).

**20.2** Coloca los campos en sus casillas:
- `Filas`: `dim_tecnologia[tecnologia]`
- `Columnas`: `dim_fuente[fuente]`
- `Valores`: `bridge_oferta_tecnologia[id_tecnologia]` → con la `>` pon `Resumen` =
  `Recuento`

**20.3 — Aplicar la escala de colores (formato condicional).** Esto es lo que pinta
las celdas. Se hace desde el **panel `Formato`** (no desde el menú de la `>`):

1. Selecciona la matriz en el lienzo
2. En el panel `Formato` (derecha), asegúrate de estar en la pestaña
   **`Objeto visual`**
3. Baja hasta la sección **`Elementos de celda`** y haz clic para desplegarla
4. Dentro, en el desplegable **`Aplicar configuración a`**, deja tu campo de valores
   (`Recuento de id_tecnologia`)
5. Activa el interruptor **`Color de fondo`**
6. Aparece un botón **`fx`** al lado → haz clic en él
7. Se abre el cuadro **`Color de fondo`**. Configúralo así:
   - **`Estilo de formato`**: **`Degradado`**
     *(en versiones nuevas "Escala de colores" se llama así)*
   - **`Aplicar a`**: `Solo valores`
   - **`Resumen`**: `Recuento`
   - **`¿Cómo dar formato a los valores vacíos?`**: `Como cero`
   - **`Mínimo`**: `Valor más bajo` · **`Máximo`**: `Valor más alto`
   - *(opcional)* cambia los colores con los cuadritos junto a Mínimo/Máximo
8. Clic en **`Aceptar`**

Las celdas se pintan: más menciones = más oscuro.

> **Guarda este procedimiento.** Los pasos 26 y 31-B usan la misma escala de colores
> en una matriz. Cuando la guía diga "aplica la escala de colores (como en 20.3)",
> repite: panel `Formato` → `Objeto visual` → `Elementos de celda` → activa
> `Color de fondo` → `fx` → `Estilo de formato` = `Degradado` → `Aceptar`.

**Para qué sirve:** compara los dos portales. Si piden tecnologías distintas,
justifica haber usado dos fuentes en vez de una.

## Paso 21 — Columnas apiladas al 100%: categoría por fuente

`Insertar` → `Gráfico de columnas apiladas al 100%`
- `Eje X`: `dim_fuente[fuente]`
- `Leyenda`: `dim_tecnologia[categoria]`
- `Eje Y`: `bridge_oferta_tecnologia[id_tecnologia]` → `Recuento`

## Paso 22 — Tabla: participación de cada tecnología

**22.1 Arma la tabla:**
1. Clic en área vacía del lienzo
2. Marca `dim_tecnologia[tecnologia]` en el panel `Datos`
3. Con el visual seleccionado, en `Compilar` cambia el tipo a **`Tabla`**
4. Marca también `bridge_oferta_tecnologia[id_tecnologia]`; cae como valor
5. Con la `>` de ese campo, pon `Resumen` = **`Recuento`**

Ya tienes dos columnas: la tecnología y su conteo. Falta el porcentaje.

**22.2 Añade la columna de porcentaje.** Usa la medida (es el método fiable entre
versiones):

1. En el panel `Datos`, **clic derecho** sobre la tabla `bridge_oferta_tecnologia` →
   **`Nueva medida`**
2. En la barra de fórmulas pega esto y pulsa Enter:

```dax
% del Total =
DIVIDE(
    COUNTROWS(bridge_oferta_tecnologia),
    CALCULATE(COUNTROWS(bridge_oferta_tecnologia), ALL(dim_tecnologia))
)
```

3. La medida `% del Total` aparece en el panel `Datos` (con icono de calculadora).
   Selecciónala y, en la cinta `Herramientas de medidas`, clic en el botón **`%`**
4. **Arrastra** `% del Total` a la casilla de valores de la tabla

> **Alternativa sin fórmula** (si tu versión la conserva): arrastra
> `bridge_oferta_tecnologia[id_tecnologia]` **una segunda vez** a la tabla → clic en
> su **`>`** → busca **`Mostrar el valor como`** → `Porcentaje del total general`.
> Si ese menú no existe en tu versión, usa la medida de arriba.

**Para qué sirve:** convierte conteos en peso relativo. "sql aparece 77 veces" dice
poco; "sql concentra el 12.5% de la demanda" es un indicador.

## Paso 23 — Segmentación por categoría

`Insertar` → `Segmentación de datos` con `dim_tecnologia[categoria]`.

---

# PARTE 4 — Página 3: Perfiles Tecnológicos (Machine Learning)

**Qué cuenta esta página:** conecta el dashboard con el requisito de ML. La columna
`id_cluster` **no existía en los datos originales**: la produjo el modelo K-Means.

## Paso 24 — Crear la página

Botón `+` → renombra a **`Perfiles ML`**.

## Paso 25 — Anillo: reparto por perfil

`Insertar` → `Gráfico de anillos`
- `Leyenda`: `dim_cluster[nombre_perfil]`
- `Valores`: `fact_ofertas[id_oferta]` → `Recuento`

## Paso 26 — Matriz: huella tecnológica de cada perfil

`Insertar` → `Matriz`
- `Filas`: `dim_cluster[nombre_perfil]`
- `Columnas`: `dim_tecnologia[categoria]`
- `Valores`: `bridge_oferta_tecnologia[id_tecnologia]` → `Recuento`
- Aplica la escala de colores **como en el paso 20.3** (`Formato condicional` →
  `Color de fondo` → `Estilo de formato` = `Degradado` → `Aceptar`)

**Para qué sirve:** muestra en qué se diferencian los grupos que encontró el
algoritmo. Sin esto, los clusters son números sin significado.

## Paso 27 — Barras: tecnologías dominantes por perfil

`Insertar` → `Gráfico de barras agrupadas`
- `Eje Y`: `dim_tecnologia[tecnologia]`
- `Eje X`: `bridge_oferta_tecnologia[id_tecnologia]` → `Recuento`
- `Leyenda`: `dim_cluster[nombre_perfil]`

**Filtro top 10** (para quedarte solo con las 10 tecnologías más mencionadas):
1. Selecciona el gráfico
2. Panel `Filtros` → sección **`tecnologia`** (la del `Eje Y`)
3. `Tipo de filtro`: **`Filtrado N superior`**
4. `Mostrar elementos`: **`Superior`** `10`
5. En `Por valor`, arrastra `bridge_oferta_tecnologia[id_tecnologia]`
6. `Aplicar filtro`

## Paso 28 — Columnas: densidad tecnológica

`Insertar` → `Gráfico de columnas agrupadas`
- `Eje X`: `fact_ofertas[num_tecnologias]`
- `Eje Y`: `fact_ofertas[id_oferta]` → `Recuento`
- `Leyenda`: `dim_cluster[nombre_perfil]`

**Para qué sirve:** muestra cuántas tecnologías pide cada vacante. La barra del `0`
es alta: son ofertas donde no se detectaron tecnologías (perfiles de gestión y
soporte, o descripciones cortas). **Explicarlo es mejor que esconderlo.**

## Paso 29 — Cuadro de texto explicando el modelo

`Insertar` → `Cuadro de texto`. Pega esto:

> **Modelo aplicado: K-Means (clustering, aprendizaje no supervisado).**
> Se eligió porque **no existen etiquetas previas** de "tipo de puesto": el objetivo
> es que los datos revelen por sí solos qué familias de perfiles existen. Con
> etiquetas sería clasificación; sin ellas, es agrupamiento.
> Cada oferta se convierte en un **vector binario one-hot** de tecnologías
> (`MultiLabelBinarizer`): una posición por tecnología, con 1 si la oferta la pide.
> K-Means asigna cada vector al **centroide** más cercano e itera hasta estabilizar.
> El número de grupos *k* se elige con el **método del codo** sobre la **inercia**
> (suma de distancias al cuadrado de cada punto a su centroide), probando k = 2..8.
> Resultado: 2 perfiles, nombrados por sus dos tecnologías más frecuentes.
> Como técnica secundaria se implementó una **regresión RandomForest** de salarios
> (métricas MAE y R²), que no llega a ejecutarse porque los portales panameños no
> publican salario en el listado de resultados.

## Paso 30 — Tabla de ofertas del perfil

`Insertar` → `Tabla` con `fact_ofertas[titulo]`, `dim_empresa[nombre_empresa]`,
`fact_ofertas[num_tecnologias]`.

Al hacer clic en un perfil del anillo, esta tabla se filtra sola — eso es el
**filtrado cruzado** que dan las relaciones del modelo.

---

# PARTE 5 — Página 4: Evolución y Asistente IA

**Qué cuenta esta página:** cómo cambia la demanda en el tiempo, y cubre el
requisito de LLM.

## Paso 31 — Crear la página y los 2 visuales temporales

Botón `+` → renombra a **`Evolución e IA`**.

**Visual A** — `Insertar` → `Gráfico de líneas y columnas agrupadas`

Las casillas de este visual en tu versión se llaman `Eje X`, `Eje Y de columna`,
`Eje Y de línea` y `Leyenda de columna`. Colócalos así:

- **`Eje X`**: `dim_fecha[fecha]`
  > ⚠️ Al marcar `fecha`, Power BI mete una **jerarquía de fechas** entera
  > (`fecha`, `Año`, `Trimestre`, `Mes`, `Día`) en el `Eje X`. **Quita las 4 de
  > más:** clic en la **`X`** junto a `Año`, `Trimestre`, `Mes` y `Día`, dejando
  > solo `fecha`.
- **`Eje Y de columna`**: `fact_ofertas[Clave Oferta]` → con la `>`, `Resumen` =
  `Recuento distinto`
- **`Eje Y de línea`**: `bridge_oferta_tecnologia[id_tecnologia]` → `Resumen` =
  `Recuento distinto`
- Deja vacías `Leyenda de columna`, `Múltiplos pequeños` e `Información sobre
  herramientas`
- En el panel `Filtros` del visual, sección `fecha`, quita el valor `En blanco`

**Visual B** — `Insertar` → `Matriz`
- `Filas`: `dim_tecnologia[tecnologia]`
- `Columnas`: `dim_fecha[fecha]`
- `Valores`: `bridge_oferta_tecnologia[id_tecnologia]` → `Recuento`
- Aplica la escala de colores **como en el paso 20.3**

**Para qué sirve:** el visual B es el germen del análisis de **skills emergentes**.
Se lee de izquierda a derecha qué tecnología ganó o perdió presencia entre capturas.

## Paso 32 — Visual de Preguntas y respuestas

`Insertar` → `Preguntas y respuestas`.

Escribes una pregunta en lenguaje natural y devuelve una visualización. Prueba:
- `cuántas ofertas por fuente`
- `top 5 empresas`
- `recuento de id_tecnologia por categoria`

**Entrénalo:** `Modelado` → `Preguntas y respuestas` →
`Configuración de preguntas y respuestas` → pestaña `Sinónimos`:

| Campo | Sinónimos |
|---|---|
| `dim_tecnologia[tecnologia]` | `skill`, `habilidad`, `herramienta` |
| `dim_empresa[nombre_empresa]` | `compañía`, `contratante`, `empleador` |
| `fact_ofertas` | `vacantes`, `puestos`, `empleos` |
| `dim_cluster[nombre_perfil]` | `perfil`, `familia de puestos` |

Deja una pregunta ya escrita en el visual para la presentación.

## Paso 33 — Narrativa inteligente

`Insertar` → `Narrativa inteligente`.

Genera un párrafo en lenguaje natural describiendo los datos de la página, y se
actualiza al mover los filtros. Para añadir valores dinámicos: clic dentro del texto
→ botón `+ Valor` → escribe una pregunta → `Guardar`.

> **Con los pasos 32 y 33 cubres el requisito de LLM dentro de Power BI.** Y en el
> proyecto Python está la pestaña `Asistente IA` de Streamlit, que usa **Ollama con
> `llama3.2:3b` local** (código en `src/llm/ollama_cliente.py`).

---

# PARTE 6 — Acabado

## Paso 34 — Formato, interacciones y navegación

**34.1 Tema.** `Vista` → `Temas` → elige uno (p. ej. `Innovar`).

**34.2 Títulos.** En cada página, `Insertar` → `Cuadro de texto` con el título
arriba a la izquierda.

**34.3 Interacciones.** Selecciona un visual → pestaña `Formato` →
`Editar interacciones`. Aparecen iconos sobre los demás visuales:
🔍 filtrar · 📊 resaltar · 🚫 ninguna.
Configúralo al menos en `Panorama`: que el anillo de fuentes **filtre** la tabla.

**34.4 Navegación.** `Insertar` → `Botones` → `Navegador` → `Navegador de páginas`.
Crea un botón por página. Cópialo y pégalo en las 4.

**34.5** Guarda (`Ctrl+S`).

---

## Paso extra (opcional) — La única medida DAX

Todo lo anterior salió con botones. Esta no, porque necesita **rankear** empresas y
sumar solo las 5 primeras, y eso no existe como opción de menú.

En la página `Panorama`: `Inicio` → `Nueva medida` → pega y Enter:

```dax
Concentración Top 5 Empresas =
VAR Top5 =
    TOPN(5, VALUES(dim_empresa[nombre_empresa]),
         CALCULATE(DISTINCTCOUNT(fact_ofertas[Clave Oferta])), DESC)
VAR OfertasTop5 =
    SUMX(Top5, CALCULATE(DISTINCTCOUNT(fact_ofertas[Clave Oferta])))
VAR OfertasTotales =
    CALCULATE(DISTINCTCOUNT(fact_ofertas[Clave Oferta]), ALL(dim_empresa))
RETURN
    DIVIDE(OfertasTop5, OfertasTotales)
```

Formato: `Herramientas de medidas` → `Formato: Porcentaje`, 1 decimal.
Ponla en una `Tarjeta` en la página `Panorama`.

**Para qué sirve:** responde *¿el mercado IT panameño está dominado por unas pocas
empresas?* Si el Top 5 concentra un porcentaje alto, un egresado depende de pocos
empleadores. Es un indicador de **estructura de mercado**, no un conteo.

**Línea por línea, para la sustentación:**
- `VALUES(...)` → la lista de empresas visibles
- `TOPN(5, ..., DESC)` → se queda con las 5 que más publican
- `SUMX(Top5, ...)` → recorre esas 5 y suma sus ofertas
- `CALCULATE(..., ALL(dim_empresa))` → el total ignorando el filtro de empresa
- `DIVIDE` → la proporción

---

## Checklist antes de entregar

- [ ] Las 8 tablas cargadas, con acentos correctos ("Panamá", no "PanamÃ¡")
- [ ] 7 relaciones creadas a mano, ninguna de más
- [ ] La vista `Modelo` se ve como una estrella
- [ ] Columnas `Clave Oferta` y `tiene_tecnologia` creadas en Power Query
- [ ] La tarjeta `Ofertas Únicas` muestra **148** (no 409)
- [ ] Los campos están **renombrados** (no "Recuento distinto de Clave Oferta")
- [ ] 4 páginas con nombre propio y navegación entre ellas
- [ ] Segmentaciones funcionando (mueve una y verifica que todo reacciona)
- [ ] Ninguna tarjeta muestra `(En blanco)`
- [ ] Sabes explicar cada visual (Anexo D)

---
---

# ANEXOS (material de consulta — no son pasos)

## Anexo A — Qué datos hay realmente

Verificado sobre los CSV del repositorio.

| Tabla | Filas | Observación |
|---|---:|---|
| `fact_ofertas` | 409 | **148 ofertas únicas** repetidas en 3 capturas (factor ×2.76) |
| `bridge_oferta_tecnologia` | 616 | Relación oferta ↔ tecnología (N:M) |
| `dim_empresa` | 45 | — |
| `dim_tecnologia` | 45 | 38 tienen al menos una oferta |
| `dim_ubicacion` | 13 | Todas en Panamá |
| `dim_fecha` | 4 | 3 fechas de captura + 1 centinela "sin fecha" |
| `dim_fuente` | 2 | konzerta (295 filas), computrabajo (114 filas) |
| `dim_cluster` | 2 | Perfiles descubiertos por K-Means |

**Integridad referencial: 0 claves huérfanas.** El modelo importa sin errores.

### Lo que NO se puede mostrar (y por qué)

1. **Salario** — vacío en las 409 filas. Los portales no lo publican en el listado.
2. **Fecha de publicación** — `id_fecha_publicacion` vale `-1` en todas las filas.
3. **`antiguedad_dias`** — la columna no existe en estos CSV.
4. **% Remoto** — `es_remoto` es `False` en las 13 ubicaciones.
5. **62% de las ofertas sin tecnología detectada** — por eso existe el KPI
   `% con Tecnología Detectada`: hace explícita la cobertura en vez de esconderla.

> No incluyas KPIs de salario, antigüedad ni % remoto. Saldrían en blanco.

## Anexo B — Catálogo de agregaciones

La técnica siempre es la misma: arrastra el campo a la casilla del panel `Compilar`
→ flechita ▾ a la derecha del campo → elige la agregación → renombra con doble clic.

| Indicador | Campo | Agregación | Qué responde |
|---|---|---|---|
| Ofertas Únicas | `fact_ofertas[Clave Oferta]` | `Recuento distinto` | ¿Cuántas vacantes reales hay? |
| Total Registros | `fact_ofertas[id_oferta]` | `Recuento` | ¿Cuántas observaciones acumuló el pipeline? |
| Empresas Contratando | `fact_ofertas[id_empresa]` | `Recuento distinto` | ¿Cuántas empresas contratan IT? |
| Ubicaciones Activas | `fact_ofertas[id_ubicacion]` | `Recuento distinto` | ¿Dónde se concentra la demanda? |
| Capturas Realizadas | `fact_ofertas[id_fecha_scrape]` | `Recuento distinto` | ¿Cuántos cortes temporales hay? |
| Menciones de Tecnología | `bridge[id_tecnologia]` | `Recuento` | ¿Cuántas veces se pide una tecnología? |
| Tecnologías Demandadas | `bridge[id_tecnologia]` | `Recuento distinto` | ¿Cuántas tecnologías distintas se piden? |
| Prom. Tecnologías por Oferta | `fact_ofertas[num_tecnologias]` | `Promedio` | ¿Qué tan exigente es una vacante típica? |
| % con Tecnología Detectada | `fact_ofertas[tiene_tecnologia]` | `Promedio` | ¿Qué tan confiable es el análisis tecnológico? |

## Anexo C — Errores comunes

| Síntoma | Causa | Solución |
|---|---|---|
| Los acentos salen rotos | Origen no es UTF-8 | Power Query → paso `Origen` → `65001: Unicode (UTF-8)` |
| Una tarjeta muestra `(En blanco)` | Campo de salario o antigüedad | No los uses: los CSV no tienen esos datos |
| Los conteos salen ×3 | Usaste `Recuento` en vez de `Recuento distinto` | Cambia la agregación de `Clave Oferta` |
| Aparece una relación que no creaste | Autodetección activada | Elimínala; revisa el Paso 1 |
| Los meses salen en orden alfabético | Ordenación por texto | `nombre_mes` → `Ordenar por columna` → `mes` |
| El gráfico muestra tecnologías con 0 | Se listan las 45 del diccionario | Aplica filtro `N superior` |
| Un valor `En blanco` en la segmentación de fecha | Fila centinela `id_fecha = -1` | Desmárcalo en `Filtros` del visual |
| La leyenda dice "Recuento distinto de…" | No renombraste el campo | Doble clic sobre el nombre en la casilla del panel `Compilar` |
| No encuentro el panel `Visualizaciones` | Tu versión lo llama `Compilar` | Es el mismo panel, junto al de `Datos` |
| No encuentro `Insertar` → `Tarjeta` | La galería está en el panel `Compilar` | Marca una columna en `Datos`, y luego cambia el tipo de visual desde la cuadrícula de iconos |

## Anexo D — Preguntas que te van a hacer

### Sobre el modelo de datos

**¿Por qué un modelo estrella y no una sola tabla con todo?**
Evita repetir datos y acelera las consultas. El nombre de una empresa se guarda
**una vez** en `dim_empresa`; los hechos solo guardan su `id`. Además, cada
dimensión se vuelve un filtro del dashboard.

**¿Cuál es la tabla de hechos y cuáles las dimensiones?**
`fact_ofertas` es la de hechos: guarda los **eventos medibles** (cada oferta
capturada) y las claves foráneas. Las dimensiones guardan los **atributos
descriptivos** por los que filtramos y agrupamos.

**¿Qué es `bridge_oferta_tecnologia` y por qué existe?**
Es una **tabla puente**. Una oferta pide varias tecnologías y una tecnología aparece
en varias ofertas: relación **muchos a muchos**, que un modelo estrella no
representa directamente. La puente la descompone en dos relaciones 1-a-muchos.
Tiene 616 filas, una por par oferta-tecnología.

**¿Por qué las relaciones son de dirección única?**
Para que el filtro fluya de la dimensión hacia los hechos y no al revés. La
dirección bidireccional puede crear ambigüedad y dar resultados incorrectos.

**¿Qué es la fila con `id_fecha = -1`?**
Un **miembro centinela** para las fechas nulas. Sin ella, las ofertas sin fecha
tendrían una clave huérfana y se perderían al filtrar. Es la forma estándar de
manejar nulos en un modelo dimensional.

### Sobre los datos

**¿De dónde salen?**
De dos portales panameños, con técnicas distintas: **Konzerta** por scraping con
Playwright (es una SPA, el contenido lo renderiza JavaScript) y **Computrabajo
Panamá** con requests + BeautifulSoup (renderiza en el servidor). El pipeline en
Python los normaliza a un esquema común, extrae tecnologías, corre el ML y exporta
los 8 CSV.

**¿Por qué `Total Registros` (409) y `Ofertas Únicas` (148) no coinciden?**
El pipeline guarda un **snapshot cada vez que corre**, y corrió 3 veces (17, 18 y 23
de julio). El grano de la tabla de hechos es **oferta-captura**, no oferta. Por eso
creamos `Clave Oferta` (título + empresa) y contamos valores distintos.

**¿Por qué no hay salarios?**
Los portales panameños **no publican el salario en el listado de resultados**. El
pipeline tiene el parser y la regresión programados, pero la columna llega vacía.
Preferimos no mostrar un KPI en blanco antes que inventar el dato.

**¿Por qué el 62% de las ofertas no tiene tecnologías?**
Computrabajo no expone la descripción en el listado (solo el título), y buena parte
de las vacantes IT panameñas son de gestión, auditoría o soporte, donde no se
nombran tecnologías concretas. Por eso incluimos el KPI de cobertura.

### Sobre el Machine Learning

**¿Por qué K-Means y no un modelo de clasificación?**
Porque **no tenemos etiquetas**. Nadie marcó qué oferta es "backend" o "data". Con
etiquetas sería clasificación (supervisado); sin ellas, es agrupamiento (no
supervisado), y K-Means es el algoritmo estándar.

**¿Cómo se representa una oferta para el algoritmo?**
Como un **vector binario one-hot** de tecnologías: una posición por tecnología, con
1 si la oferta la menciona. Así dos ofertas que piden lo mismo quedan cerca.

**¿Cómo eligieron el número de grupos?**
Con el **método del codo**: se prueba k de 2 a 8, se mide la **inercia** y se busca
dónde deja de bajar fuerte. Dio k = 2.

**¿Qué significan los clusters?**
Se nombran por sus dos tecnologías más frecuentes: uno gira en torno a
`sql, python` (perfil técnico-analítico) y otro a `sql, excel` (análisis de
negocio).

### Sobre el dashboard

**¿Por qué esos KPIs y no otros?**
Cada uno responde una pregunta distinta: cuántas vacantes hay, quién contrata,
dónde, qué se pide, qué tan exigentes son y qué tan confiable es el dato. Ninguno
está por rellenar.

**¿Escribieron código o lo hicieron con la herramienta?**
Los indicadores se crearon con **agregaciones desde el panel de campos**; las dos
columnas de apoyo con `Combinar columnas` y `Columna condicional` de Power Query —
todo desde la interfaz. Solo se escribió DAX para `Concentración Top 5 Empresas`,
porque requiere rankear y eso no existe como opción de menú. Los `PASOS APLICADOS`
de Power Query documentan la secuencia.

**¿Dónde está el LLM?**
En Power BI: `Preguntas y respuestas` (consulta en lenguaje natural sobre el modelo)
y `Narrativa inteligente` (resúmenes automáticos). En el proyecto Python: la pestaña
`Asistente IA` de Streamlit usa **Ollama con `llama3.2:3b` local** para consultas,
resumen ejecutivo y análisis de skills emergentes.

## Anexo E — Cómo dejar rastro del trabajo manual

1. **Guarda versiones intermedias**: `dashboard_v1_modelo.pbix` (solo relaciones),
   `dashboard_v2_kpis.pbix`, `dashboard_v3_paginas.pbix`, `dashboard_final.pbix`.
2. **Captura de la vista `Modelo`** con la estrella armada.
3. **Captura de `PASOS APLICADOS`** de Power Query en `fact_ofertas`: se ve
   `Origen → Encabezados promovidos → Tipo cambiado → Columnas combinadas →
   Columna condicional`. Es la evidencia más directa de trabajo manual.
4. **Captura de `Editar interacciones`** activo.
5. Súbelas a `docs/capturas/` y enlázalas desde el README.
