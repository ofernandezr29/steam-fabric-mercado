# Medidas DAX del modelo semántico `SM_Steam_Mercado`

Crea primero una tabla vacía para agrupar las medidas: en el modelo semántico,
**Inicio > Nueva medida** sobre la tabla `silver_juegos` (o crea una tabla `_Medidas`).
Copia cada bloque como una medida nueva y asígnale el formato indicado.

## KPIs (tarjetas)

```dax
Juegos analizados =
COUNTROWS ( silver_juegos )
```
Formato: número entero, separador de miles.

```dax
Tasa de éxito =
DIVIDE (
    CALCULATE ( COUNTROWS ( silver_juegos ), silver_juegos[exito_comercial] = TRUE () ),
    [Juegos analizados]
)
```
Formato: porcentaje, 1 decimal. *Éxito = ≥ 100.000 propietarios estimados.*

```dax
% reseñas positivas =
AVERAGE ( silver_juegos[pct_positivas] )
```
Formato: porcentaje, 1 decimal. (Solo cuenta juegos con ≥ 10 reseñas; el resto es nulo.)

```dax
Precio medio (de pago) =
CALCULATE ( AVERAGE ( silver_juegos[precio_usd] ), silver_juegos[precio_usd] > 0 )
```
Formato: moneda $ (USD), 2 decimales.

```dax
Propietarios estimados =
SUM ( silver_juegos[propietarios_medio] )
```
Formato: número decimal, unidades abreviadas (M).

## Medidas auxiliares para los gráficos

```dax
Lanzamientos recientes (2023-2025) =
CALCULATE ( [Juegos analizados], silver_juegos[anio_lanzamiento] >= 2023, silver_juegos[anio_lanzamiento] <= 2025 )
```

```dax
Variación lanzamientos vs. año anterior =
VAR anio = MAX ( silver_juegos[anio_lanzamiento] )
VAR actual = [Juegos analizados]
VAR anterior = CALCULATE ( [Juegos analizados], silver_juegos[anio_lanzamiento] = anio - 1 )
RETURN DIVIDE ( actual - anterior, anterior )
```
Formato: porcentaje.

```dax
Juegos con éxito =
CALCULATE ( [Juegos analizados], silver_juegos[exito_comercial] = TRUE () )
```

## Relaciones del modelo

| Desde (muchos)              | Hacia (uno)                    | Cardinalidad | Dirección de filtro |
|-----------------------------|--------------------------------|--------------|---------------------|
| `gold_juego_genero[app_id]` | `silver_juegos[app_id]`        | *:1          | **Ambas**           |
| `gold_juego_genero[genero]` | `gold_resumen_genero[genero]`  | *:1          | Única               |

Con esto, una segmentación por `gold_resumen_genero[genero]` filtra `gold_juego_genero`
y, gracias a la dirección "Ambas", también `silver_juegos` (todas las medidas responden al género).
