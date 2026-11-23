"""Replica en pandas la limpieza del Dataflow y los cálculos del notebook
para saber qué resultados deben salir en Fabric.

Uso: python 02_validar_local.py data
"""
import sys
import os
import numpy as np
import pandas as pd

GENEROS_NO_JUEGO = {
    "Utilities", "Design & Illustration", "Animation & Modeling", "Education",
    "Video Production", "Game Development", "Audio Production",
    "Software Training", "Photo Editing", "Web Publishing", "Accounting",
    "Movie", "Documentary", "Episodic", "Tutorial", "360 Video",
}
GENEROS_SECUNDARIOS = {"Indie", "Early Access", "Free To Play"}
VERDADEROS = {"TRUE", "1", "YES", "Y"}
ANIO_MAX = 2026


def a_fecha(s):
    s = str(s).strip()
    for fmt in ("%b %d, %Y", "%Y-%m-%d", "%b %Y"):
        try:
            return pd.to_datetime(s, format=fmt)
        except (ValueError, TypeError):
            pass
    return pd.NaT


def genero_principal(generos):
    lista = [g.strip() for g in generos.split(",") if g.strip()]
    for g in lista:
        if g not in GENEROS_SECUNDARIOS:
            return g
    return lista[0] if lista else "Sin género"


def silver(carpeta):
    df = pd.read_csv(os.path.join(carpeta, "steam_games.csv"), dtype=str,
                     keep_default_na=False, na_values=[""])
    pasos = {"filas_bronze": len(df)}

    df = df[df["Name"].notna() & (df["Name"].str.strip() != "")]
    pasos["tras_quitar_nombre_nulo"] = len(df)
    for c in ["Name", "Developers", "Publishers"]:
        df[c] = df[c].str.strip()
    df = df.drop_duplicates(subset="AppID", keep="first")
    pasos["tras_quitar_duplicados"] = len(df)

    df["fecha"] = df["Release date"].map(a_fecha)
    df = df[df["fecha"].notna() & (df["fecha"].dt.year <= ANIO_MAX)]
    pasos["tras_filtrar_fechas"] = len(df)

    df["Genres"] = df["Genres"].fillna("Sin género")
    df["genero_principal"] = df["Genres"].map(genero_principal)
    df = df[~df["genero_principal"].isin(GENEROS_NO_JUEGO)]
    pasos["tras_quitar_software"] = len(df)

    precio = pd.to_numeric(df["Price"], errors="coerce")
    df["estado_precio"] = np.select(
        [precio.isna(), (precio < 0) | (precio > 1000)], ["Nulo", "Fuera de rango"], "OK")
    df["precio_usd"] = precio.where(df["estado_precio"] == "OK")

    for c in ["Windows", "Mac", "Linux"]:
        df[c] = df[c].str.strip().str.upper().isin(VERDADEROS)
    df["num_plataformas"] = df[["Windows", "Mac", "Linux"]].sum(axis=1)

    own = df["Estimated owners"].str.split(" - ", expand=True).astype("int64")
    df["propietarios_min"], df["propietarios_max"] = own[0], own[1]
    df["propietarios_medio"] = (own[0] + own[1]) / 2
    df["exito_comercial"] = df["propietarios_min"] >= 100000

    pos = df["Positive"].astype(int)
    neg = df["Negative"].astype(int)
    df["total_resenas"] = pos + neg
    df["pct_positivas"] = (pos / df["total_resenas"]).where(df["total_resenas"] >= 10)

    p = df["precio_usd"]
    df["rango_precio"] = np.select(
        [p.isna(), p == 0, p < 5, p < 10, p < 20, p < 40],
        ["Desconocido", "0. Gratis", "1. < 5 $", "2. 5-9,99 $", "3. 10-19,99 $", "4. 20-39,99 $"],
        "5. >= 40 $")
    df["anio"] = df["fecha"].dt.year
    return df, pasos


def gold(df):
    jg = df[["AppID", "Genres"]].assign(genero=df["Genres"].str.split(",")).explode("genero")
    jg["genero"] = jg["genero"].str.strip()
    jg = jg[~jg["genero"].isin(GENEROS_NO_JUEGO | {"Sin género"}) & (jg["genero"] != "")]
    jg = jg.merge(df[["AppID", "anio", "exito_comercial", "pct_positivas",
                      "precio_usd", "propietarios_medio"]], on="AppID")

    recientes = jg[jg["anio"].between(2023, 2025)]
    total_rec = df["anio"].between(2023, 2025).sum()
    r = jg.groupby("genero").agg(
        num_juegos=("AppID", "nunique"),
        tasa_exito=("exito_comercial", "mean"),
        pct_positivas_medio=("pct_positivas", "mean"),
        propietarios_mediano=("propietarios_medio", "median"),
    )
    r["precio_medio_pago"] = jg[jg["precio_usd"] > 0].groupby("genero")["precio_usd"].mean()
    r["lanzamientos_2023_2025"] = recientes.groupby("genero")["AppID"].nunique()
    r["cuota_lanzamientos_recientes"] = r["lanzamientos_2023_2025"] / total_rec
    r["indice_oportunidad"] = r["tasa_exito"] / r["cuota_lanzamientos_recientes"]
    return jg, r[r["num_juegos"] >= 500].sort_values("indice_oportunidad", ascending=False)


def main():
    carpeta = sys.argv[1] if len(sys.argv) > 1 else "data"
    df, pasos = silver(carpeta)
    print("== Recuento por etapa (Dataflow) ==")
    for k, v in pasos.items():
        print(f"  {k:28s} {v:>9,}")
    print("\n== Estado del precio ==\n", df["estado_precio"].value_counts().to_string())
    print(f"\nRango de años: {df['anio'].min()} - {df['anio'].max()}")
    print(f"Lanzamientos por año (últimos):\n{df['anio'].value_counts().sort_index().tail(8).to_string()}")

    print("\n== KPIs globales ==")
    print(f"  Juegos analizados:        {len(df):,}")
    print(f"  % reseñas positivas medio: {df['pct_positivas'].mean():.1%}")
    print(f"  Tasa de éxito comercial:  {df['exito_comercial'].mean():.2%}")
    print(f"  Precio medio (de pago):    {df.loc[df['precio_usd'] > 0, 'precio_usd'].mean():.2f} $")

    jg, r = gold(df)
    pd.set_option("display.width", 200)
    print("\n== P1: Géneros (gold_resumen_genero) ==")
    print(r.round(3).to_string())

    print("\n== P2: Rango de precio ==")
    print(df.groupby("rango_precio").agg(
        juegos=("AppID", "count"), tasa_exito=("exito_comercial", "mean"),
        pct_positivas=("pct_positivas", "mean")).round(3).to_string())

    print("\n== P3: Número de plataformas ==")
    print(df.groupby("num_plataformas").agg(
        juegos=("AppID", "count"), tasa_exito=("exito_comercial", "mean"),
        pct_positivas=("pct_positivas", "mean")).round(3).to_string())

    print("\n== P4: Mes de lanzamiento (2015-2024) ==")
    m = df[df["anio"].between(2015, 2024)]
    print(m.groupby(m["fecha"].dt.month).agg(
        juegos=("AppID", "count"), tasa_exito=("exito_comercial", "mean")).round(3).to_string())


if __name__ == "__main__":
    main()
