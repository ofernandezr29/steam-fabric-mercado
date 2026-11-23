-- P1. Géneros: éxito frente a saturación
SELECT  genero,
        num_juegos,
        CAST(tasa_exito * 100 AS DECIMAL(5,1))                    AS tasa_exito_pct,
        CAST(cuota_lanzamientos_recientes * 100 AS DECIMAL(5,1))  AS cuota_reciente_pct,
        CAST(indice_oportunidad AS DECIMAL(6,2))                  AS indice_oportunidad,
        coste_desarrollo_eur,
        experiencia_equipo,
        prioridad_estrategica
FROM    gold_resumen_genero
ORDER BY indice_oportunidad DESC;


-- P2. Rango de precio
SELECT  rango_precio,
        COUNT(*)                                                         AS juegos,
        CAST(AVG(CAST(exito_comercial AS FLOAT)) * 100 AS DECIMAL(5,1))  AS tasa_exito_pct,
        CAST(AVG(pct_positivas) * 100 AS DECIMAL(5,1))                   AS pct_positivas_medio,
        CAST(AVG(tiempo_mediano_min) / 60.0 AS DECIMAL(6,1))             AS horas_juego_medianas_media
FROM    silver_juegos
WHERE   rango_precio <> 'Desconocido'
GROUP BY rango_precio
ORDER BY rango_precio;


-- P3. Plataformas
SELECT  num_plataformas,
        CASE num_plataformas WHEN 1 THEN 'Solo una (normalmente Windows)'
                             WHEN 2 THEN 'Dos plataformas'
                             ELSE 'Windows + Mac + Linux' END            AS descripcion,
        COUNT(*)                                                         AS juegos,
        CAST(AVG(CAST(exito_comercial AS FLOAT)) * 100 AS DECIMAL(5,1))  AS tasa_exito_pct,
        CAST(AVG(pct_positivas) * 100 AS DECIMAL(5,1))                   AS pct_positivas_medio
FROM    silver_juegos
GROUP BY num_plataformas
ORDER BY num_plataformas;


-- P4a. Lanzamientos por año
SELECT  anio_lanzamiento, COUNT(*) AS lanzamientos
FROM    silver_juegos
WHERE   anio_lanzamiento BETWEEN 2010 AND 2025
GROUP BY anio_lanzamiento
ORDER BY anio_lanzamiento;

-- P4b. Éxito por mes (hasta 2024, los juegos más nuevos aún no han llegado a 100.000 propietarios)
SELECT  mes_lanzamiento,
        COUNT(*)                                                         AS lanzamientos,
        CAST(AVG(CAST(exito_comercial AS FLOAT)) * 100 AS DECIMAL(5,1))  AS tasa_exito_pct
FROM    silver_juegos
WHERE   anio_lanzamiento BETWEEN 2015 AND 2024
GROUP BY mes_lanzamiento
ORDER BY mes_lanzamiento;


-- Principales editores en Strategy
SELECT TOP 10 s.editores,
        COUNT(*)                         AS juegos,
        SUM(s.propietarios_medio)        AS propietarios_estimados
FROM    silver_juegos s
JOIN    gold_juego_genero g ON g.app_id = s.app_id
WHERE   g.genero = 'Strategy' AND s.editores IS NOT NULL
GROUP BY s.editores
ORDER BY propietarios_estimados DESC;


SELECT * FROM gold_calidad_datos;
