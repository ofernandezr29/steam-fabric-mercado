"""
03_generar_notebook.py
----------------------
Genera fabric/notebooks/NB_Steam_Gold.ipynb (notebook PySpark para Fabric)
a partir de las celdas definidas aquí, para mantenerlo legible en git.

Uso:
    python -I scripts/03_generar_notebook.py fabric/notebooks/NB_Steam_Gold.ipynb
"""
import json
import sys

CELDAS = [
    ("md", """# NB_Steam_Gold — capa gold y control de calidad

Notebook ejecutado por el pipeline **PL_Steam_Mercado** después del Dataflow Gen2.

* **Entrada:** tabla `silver_juegos` (creada por el Dataflow) y `Files/bronze/steam_games.csv`.
* **Salida (tablas Delta en LH_Steam):**
  * `gold_juego_genero` — una fila por juego y género (un juego tiene varios géneros).
  * `gold_resumen_genero` — KPIs por género + índice de oportunidad + datos internos.
  * `gold_calidad_datos` — recuento de problemas de calidad detectados y corregidos.

> Requisito: añadir el Lakehouse **LH_Steam** como *lakehouse predeterminado* del notebook."""),

    ("code", """# Parámetros (el pipeline puede sobrescribirlos: marcar esta celda como "parameter cell")
anio_ini_recientes = 2023
anio_fin_recientes = 2025
min_juegos_genero = 500"""),

    ("code", """from pyspark.sql import functions as F

GENEROS_NO_JUEGO = ["Utilities", "Design & Illustration", "Animation & Modeling", "Education",
                    "Video Production", "Game Development", "Audio Production",
                    "Software Training", "Photo Editing", "Web Publishing", "Accounting",
                    "Movie", "Documentary", "Episodic", "Tutorial", "360 Video", "Sin género"]

silver = spark.read.table("silver_juegos")
print(f"Filas en silver_juegos: {silver.count():,}")"""),

    ("md", """## 1. Tabla puente juego–género
La columna `generos` contiene listas como `"Action,Adventure,Indie"`. Para analizar por género
sin duplicar juegos en el modelo de Power BI, se separa en una tabla puente."""),

    ("code", """juego_genero = (silver
    .select("app_id", F.explode(F.split("generos", ",")).alias("genero"))
    .withColumn("genero", F.trim("genero"))
    .filter((F.col("genero") != "") & (~F.col("genero").isin(GENEROS_NO_JUEGO)))
    .dropDuplicates(["app_id", "genero"]))

juego_genero.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("gold_juego_genero")
print(f"gold_juego_genero: {juego_genero.count():,} filas")
display(juego_genero.groupBy("genero").count().orderBy(F.desc("count")))"""),

    ("md", """## 2. Resumen por género e índice de oportunidad

* **tasa_exito** = % de juegos del género con ≥ 100.000 propietarios estimados.
* **cuota_lanzamientos_recientes** = % de los lanzamientos de los años recientes que pertenecen al género (saturación).
* **indice_oportunidad** = tasa_exito / cuota_lanzamientos_recientes → alto = mucho éxito con poca competencia."""),

    ("code", """jg = juego_genero.join(silver.select("app_id", "anio_lanzamiento", "exito_comercial",
                                     "pct_positivas", "precio_usd", "propietarios_medio"), "app_id")

total_recientes = silver.filter(F.col("anio_lanzamiento").between(anio_ini_recientes, anio_fin_recientes)).count()

resumen = (jg.groupBy("genero").agg(
        F.countDistinct("app_id").alias("num_juegos"),
        F.avg(F.col("exito_comercial").cast("double")).alias("tasa_exito"),
        F.avg("pct_positivas").alias("pct_positivas_medio"),
        F.percentile_approx("propietarios_medio", 0.5).alias("propietarios_mediano"),
        F.avg(F.when(F.col("precio_usd") > 0, F.col("precio_usd"))).alias("precio_medio_pago"),
        F.countDistinct(F.when(F.col("anio_lanzamiento").between(anio_ini_recientes, anio_fin_recientes),
                               F.col("app_id"))).alias("lanzamientos_recientes"))
    .withColumn("cuota_lanzamientos_recientes", F.col("lanzamientos_recientes") / F.lit(total_recientes))
    .withColumn("indice_oportunidad", F.col("tasa_exito") / F.col("cuota_lanzamientos_recientes"))
    .filter(F.col("num_juegos") >= min_juegos_genero))

estrategia = spark.read.table("dim_estrategia_generos").drop("genero_clave")
resumen = resumen.join(estrategia, "genero", "left")

resumen.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("gold_resumen_genero")
display(resumen.orderBy(F.desc("indice_oportunidad")))"""),

    ("md", """## 3. Control de calidad: bronze vs. silver
Se cuentan en el CSV original (bronze) los problemas que el Dataflow ha tratado, para dejar
constancia en una tabla que también se muestra en el cuadro de mando."""),

    ("code", """bronze = (spark.read.option("header", True).option("multiLine", True)
          .option("escape", '"').csv("Files/bronze/steam_games.csv"))

n_bronze = bronze.count()
precio = F.col("Price").cast("double")
verdaderos_falsos = ["True", "False"]

metricas = [
    ("Filas en bronze (CSV original)", n_bronze),
    ("Registros duplicados (app_id repetido)", n_bronze - bronze.select("AppID").distinct().count()),
    ("Juegos sin nombre (nulos)", bronze.filter(F.col("Name").isNull() | (F.trim("Name") == "")).count()),
    ("Precio nulo", bronze.filter(F.col("Price").isNull()).count()),
    ("Precio fuera de rango (<0 o >1000)", bronze.filter((precio < 0) | (precio > 1000)).count()),
    ("Fecha en formato ISO (inconsistente)", bronze.filter(F.col("Release date").rlike(r"^\\d{4}-\\d{2}-\\d{2}$")).count()),
    ("Fecha posterior a 2026", bronze.filter(F.regexp_extract("Release date", r"(\\d{4})", 1).cast("int") > 2026).count()),
    ("Booleano Mac/Linux mal escrito", bronze.filter(~F.col("Mac").isin(verdaderos_falsos) | ~F.col("Linux").isin(verdaderos_falsos)).count()),
    ("Filas en silver (tras limpieza)", silver.count()),
]
calidad = spark.createDataFrame(metricas, "metrica string, valor long")
calidad.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("gold_calidad_datos")
display(calidad)"""),
]


def main():
    salida = sys.argv[1]
    nb = {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"name": "synapse_pyspark", "display_name": "Synapse PySpark",
                           "language": "Python"},
            "language_info": {"name": "python"},
        },
        "cells": [],
    }
    for i, (tipo, texto) in enumerate(CELDAS):
        lineas = texto.splitlines(keepends=True)
        celda = {"cell_type": "markdown" if tipo == "md" else "code",
                 "id": f"celda-{i:02d}", "metadata": {}, "source": lineas}
        if tipo == "code":
            celda.update({"execution_count": None, "outputs": []})
            if i == 1:
                celda["metadata"] = {"tags": ["parameters"]}
        nb["cells"].append(celda)
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    print(f"Notebook escrito en {salida}")


if __name__ == "__main__":
    main()
