# Proyecto de Cloud Computing · Entrega

**Inteligencia de mercado en Steam con Microsoft Fabric** · Curso 2026-2027

**Equipo:** _Nombre 1_ · _Nombre 2_

Repositorio: https://github.com/ofernandezr29/steam-fabric-mercado

## Contenido del ZIP

| Carpeta | Entregable | Contenido |
|---|---|---|
| `Entregable_1_Guion/` | 1. Guion de laboratorio | `Guion_laboratorio.pdf`: caso de uso, datos, arquitectura, desarrollo paso a paso, resultados y justificación |
| `Entregable_2_Datasets/` | 2. Datasets | `steam_games.csv`, `estrategia_generos.csv` (sintético), `registro_problemas_inyectados.csv`, script de generación y `Descripcion_datasets.pdf` |
| `Entregable_3_Codigo/` | 3. Código / notebooks | Notebook PySpark, consultas Power Query M del Dataflow Gen2, consultas SQL, `Medidas_DAX.pdf` y scripts auxiliares |
| — | 4. Workspace de Fabric | Compartido con la profesora en Microsoft Fabric (área de trabajo `WS_Steam_Mercado`) |

## Elementos del workspace de Fabric

| Elemento | Tipo |
|---|---|
| `LH_Steam` | Lakehouse (bronze en Files; silver y gold como tablas Delta) |
| `DF_Steam_Limpieza` | Dataflow Gen2 |
| `NB_Steam_Gold` | Notebook PySpark |
| `PL_Steam_Mercado` | Data Pipeline (2 copias → Dataflow → Notebook → actualización del modelo) |
| `SM_Steam_Mercado` | Modelo semántico Direct Lake |
| Informe *Mercado Steam* | Cuadro de mando Power BI |

## Ficheros de código

| Fichero | Uso |
|---|---|
| `notebooks/NB_Steam_Gold.ipynb` | Importar en Fabric (capa gold y control de calidad) |
| `dataflow/01_estrategia_generos.pq` | Pegar en el editor avanzado del Dataflow Gen2 |
| `dataflow/02_silver_juegos.pq` | Pegar en el editor avanzado del Dataflow Gen2 |
| `sql/preguntas_negocio.sql` | Ejecutar en el punto de conexión SQL del Lakehouse |
| `scripts/02_validar_local.py` | Réplica local de la lógica para comprobar resultados esperados |
| `scripts/03_generar_notebook.py` | Genera el notebook desde código legible |
| `scripts/04_exportar_pdf.py` | Genera los PDF de la documentación |
