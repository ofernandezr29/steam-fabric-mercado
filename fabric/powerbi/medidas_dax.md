# Medidas DAX del modelo SM_Steam_Mercado

Las medidas se crean desde el modelo semántico con *Nueva medida*, sobre la tabla `silver_juegos`.
Debajo de cada una indicamos el formato que le hemos dado.

## Medidas de las tarjetas (KPI)

```dax
Juegos analizados =
COUNTROWS ( silver_juegos )
```
Formato: número entero con separador de miles.

```dax
Tasa de éxito =
DIVIDE (
    CALCULATE ( COUNTROWS ( silver_juegos ), silver_juegos[exito_comercial] = TRUE () ),
    [Juegos analizados]
)
```
Formato: porcentaje con un decimal. Consideramos éxito tener al menos 100.000 propietarios estimados.

```dax
% reseñas positivas =
AVERAGE ( silver_juegos[pct_positivas] )
```
Formato: porcentaje con un decimal. Solo cuentan los juegos con 10 reseñas o más, porque en el resto
la columna está vacía.

```dax
Precio medio (de pago) =
CALCULATE ( AVERAGE ( silver_juegos[precio_usd] ), silver_juegos[precio_usd] > 0 )
```
Formato: moneda en dólares con dos decimales.

```dax
Propietarios estimados =
SUM ( silver_juegos[propietarios_medio] )
```
Formato: decimal, mostrado en millones.

## Otras medidas usadas en los gráficos

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

## Relaciones

| Desde | Hacia | Cardinalidad | Filtro |
|---|---|---|---|
| gold_juego_genero[app_id] | silver_juegos[app_id] | Varios a uno | Ambas direcciones |
| gold_juego_genero[genero] | gold_resumen_genero[genero] | Varios a uno | Una dirección |

Con la primera relación en ambas direcciones, al elegir un género en la segmentación de
`gold_resumen_genero` se filtra la tabla puente y, a través de ella, también `silver_juegos`. Así
todas las medidas cambian según el género elegido.
