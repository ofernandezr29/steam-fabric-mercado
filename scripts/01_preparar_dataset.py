"""Genera los CSV del proyecto a partir de games.csv (Kaggle).

Uso: python 01_preparar_dataset.py games.csv data
"""
import sys
import os
import numpy as np
import pandas as pd

SEMILLA = 2627
rng = np.random.default_rng(SEMILLA)

COLUMNAS = [
    "AppID", "Name", "Release date", "Estimated owners", "Peak CCU",
    "Required age", "Price", "Discount", "DLC count", "Windows", "Mac", "Linux",
    "Metacritic score", "User score", "Positive", "Negative", "Achievements",
    "Recommendations", "Average playtime forever", "Median playtime forever",
    "Developers", "Publishers", "Genres", "Supported languages",
]


def leer_games(ruta):
    with open(ruta, encoding="utf-8") as f:
        cabecera = f.readline().strip().split(",")
    # La cabecera original junta "Discount" y "DLC count" en una sola columna
    i = cabecera.index("DiscountDLC count")
    cabecera[i:i + 1] = ["Discount", "DLC count"]
    return pd.read_csv(ruta, names=cabecera, skiprows=1, low_memory=False,
                       dtype={"Price": "object", "Windows": "object",
                              "Mac": "object", "Linux": "object"})


def inyectar_problemas(df):
    registro = []
    n = len(df)

    def marca(idx, tipo, columna, antes, despues):
        for i, a, d in zip(idx, antes, despues):
            registro.append({"AppID": df.at[i, "AppID"], "tipo": tipo,
                             "columna": columna, "valor_original": a,
                             "valor_inyectado": d})

    idx = rng.choice(n, int(n * 0.002), replace=False)
    marca(idx, "nulo", "Name", df.loc[idx, "Name"], [None] * len(idx))
    df.loc[idx, "Name"] = None

    idx = rng.choice(n, int(n * 0.01), replace=False)
    marca(idx, "nulo", "Price", df.loc[idx, "Price"], [None] * len(idx))
    df.loc[idx, "Price"] = None

    idx = rng.choice(n, int(n * 0.003), replace=False)
    malos = np.where(rng.random(len(idx)) < 0.5,
                     -rng.integers(1, 60, len(idx)).astype(float),
                     rng.integers(1500, 99999, len(idx)).astype(float))
    marca(idx, "fuera_de_rango", "Price", df.loc[idx, "Price"], malos)
    df.loc[idx, "Price"] = malos.astype(str)

    idx = rng.choice(n, int(n * 0.001), replace=False)
    futuras = [f"Jan {rng.integers(1, 28)}, {rng.integers(2031, 2099)}" for _ in idx]
    marca(idx, "fuera_de_rango", "Release date", df.loc[idx, "Release date"], futuras)
    df.loc[idx, "Release date"] = futuras

    idx = rng.choice(n, int(n * 0.03), replace=False)
    iso = []
    for v in df.loc[idx, "Release date"]:
        d = pd.to_datetime(v, format="%b %d, %Y", errors="coerce")
        iso.append(d.strftime("%Y-%m-%d") if pd.notna(d) else v)
    marca(idx, "inconsistencia", "Release date", df.loc[idx, "Release date"], iso)
    df.loc[idx, "Release date"] = iso

    variantes_v = ["TRUE", "true", "1", "yes", "Y"]
    variantes_f = ["FALSE", "false", "0", "no", "N"]
    for col in ["Mac", "Linux"]:
        idx = rng.choice(n, int(n * 0.05), replace=False)
        nuevos = [rng.choice(variantes_v) if str(v) == "True" else rng.choice(variantes_f)
                  for v in df.loc[idx, col]]
        marca(idx, "inconsistencia", col, df.loc[idx, col], nuevos)
        df.loc[idx, col] = nuevos

    for col in ["Developers", "Publishers"]:
        idx = rng.choice(n, int(n * 0.02), replace=False)
        nuevos = ["  " + str(v) + " " if pd.notna(v) else v for v in df.loc[idx, col]]
        df.loc[idx, col] = nuevos

    idx = rng.choice(n, int(n * 0.015), replace=False)
    dup = df.loc[idx].copy()
    for a in dup["AppID"]:
        registro.append({"AppID": a, "tipo": "duplicado", "columna": "*",
                         "valor_original": "", "valor_inyectado": "fila repetida"})
    df = pd.concat([df, dup], ignore_index=True)
    df = df.sample(frac=1, random_state=SEMILLA).reset_index(drop=True)

    return df, pd.DataFrame(registro)


def estrategia_generos():
    filas = [
        ("Action", 420000, 18, 4, "Media"),
        ("Adventure", 260000, 14, 5, "Alta"),
        ("Casual", 90000, 6, 4, "Media"),
        ("Indie", 150000, 10, 5, "Media"),
        ("RPG", 550000, 24, 3, "Alta"),
        ("Simulation", 300000, 16, 3, "Media"),
        ("Strategy", 350000, 18, 4, "Alta"),
        ("Racing", 480000, 20, 1, "Baja"),
        ("Sports", 450000, 18, 1, "Baja"),
        ("Massively Multiplayer", 1500000, 36, 1, "Baja"),
        ("Free To Play", 200000, 12, 2, "Media"),
        ("Early Access", 120000, 8, 3, "Media"),
    ]
    df = pd.DataFrame(filas, columns=["genero", "coste_desarrollo_eur",
                                      "meses_desarrollo", "experiencia_equipo",
                                      "prioridad_estrategica"])
    df.loc[df["genero"] == "Casual", "genero"] = " casual "
    return df


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    origen, salida = sys.argv[1], sys.argv[2]
    os.makedirs(salida, exist_ok=True)

    df = leer_games(origen)[COLUMNAS]
    print(f"Filas originales: {len(df):,}")
    df, registro = inyectar_problemas(df)
    print(f"Filas tras inyectar duplicados: {len(df):,}")

    df.to_csv(os.path.join(salida, "steam_games.csv"), index=False, encoding="utf-8")
    registro.to_csv(os.path.join(salida, "registro_problemas_inyectados.csv"),
                    index=False, encoding="utf-8")
    estrategia_generos().to_csv(os.path.join(salida, "estrategia_generos.csv"),
                                index=False, encoding="utf-8")
    print(registro["tipo"].value_counts().to_string())
    tam = os.path.getsize(os.path.join(salida, "steam_games.csv")) / 1e6
    print(f"steam_games.csv: {tam:.1f} MB")


if __name__ == "__main__":
    main()
