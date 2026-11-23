# Proyecto de Cloud Computing: entrega

**Análisis del mercado de videojuegos en Steam con Microsoft Fabric.** Curso 2026-2027

Autores: Marc Pich y Odei Fernández

Repositorio: https://github.com/ofernandezr29/steam-fabric-mercado

## Contenido

**Entregable_1_Guion**

- `Guion_laboratorio.pdf`: caso de uso, descripción de los datos, arquitectura, desarrollo paso a
  paso con capturas, resultados y justificación.

**Entregable_2_Datasets**

- `steam_games.csv`: dataset principal (catálogo de Steam con los problemas de calidad añadidos).
- `estrategia_generos.csv`: datos internos del estudio, sintéticos.
- `registro_problemas_inyectados.csv`: lista de los valores que se han modificado.
- `01_preparar_dataset.py`: script que genera los tres ficheros a partir del dataset de Kaggle.
- `Descripcion_datasets.pdf`: variables y procedimiento de generación.

**Entregable_3_Codigo**

- `notebooks/NB_Steam_Gold.ipynb`: notebook PySpark que crea la capa gold.
- `dataflow/01_estrategia_generos.pq` y `dataflow/02_silver_juegos.pq`: código M de las dos
  consultas del Dataflow Gen2.
- `sql/preguntas_negocio.sql`: consultas de las preguntas de negocio.
- `Medidas_DAX.pdf`: medidas y relaciones del modelo semántico.
- `scripts/`: scripts auxiliares (validación en local, generación del notebook y de los PDF).

**Entregable 4.** El área de trabajo `WS_Steam_Mercado` está compartida con la profesora en
Microsoft Fabric. Contiene:

| Elemento | Tipo |
|---|---|
| LH_Steam | Lakehouse |
| DF_Steam_Limpieza | Dataflow Gen2 |
| NB_Steam_Gold | Notebook |
| PL_Steam_Mercado | Pipeline |
| SM_Steam_Mercado | Modelo semántico |
| Mercado Steam | Informe de Power BI |
