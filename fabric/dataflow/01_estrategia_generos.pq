// =====================================================================
//  Consulta: estrategia_generos       (Dataflow Gen2: DF_Steam_Limpieza)
//  Destino:  tabla Lakehouse "dim_estrategia_generos" (Reemplazar)
//  Fuente:   Files/bronze/estrategia_generos.csv  (datos internos sintéticos)
// =====================================================================
let
    // ---- 1. ORIGEN ---------------------------------------------------
    // Opción A (recomendada): conectar con  Obtener datos > Lakehouse >
    //   LH_Steam > Files > bronze > estrategia_generos.csv
    //   y sustituir la línea "Binario" por los pasos de navegación que
    //   genera Fabric (el último debe devolver el contenido binario).
    // Opción B: leer directamente desde GitHub (ya apunta a este repositorio).
    Binario = Web.Contents("https://raw.githubusercontent.com/ofernandezr29/steam-fabric-mercado/main/data/estrategia_generos.csv"),

    Csv = Csv.Document(Binario, [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Cabeceras = Table.PromoteHeaders(Csv, [PromoteAllScalars = true]),

    // ---- 2. LIMPIEZA: espacios y mayúsculas incoherentes (" casual ") ---
    GeneroLimpio = Table.TransformColumns(Cabeceras, {{"genero", each
        let t = Text.Trim(_) in if Text.Lower(t) = t then Text.Proper(t) else t, type text}}),

    // ---- 3. TIPOS ------------------------------------------------------
    Tipos = Table.TransformColumnTypes(GeneroLimpio, {
        {"coste_desarrollo_eur", Int64.Type},
        {"meses_desarrollo", Int64.Type},
        {"experiencia_equipo", Int64.Type},
        {"prioridad_estrategica", type text}}, "en-US"),

    // ---- 4. CLAVE DE CRUCE (sin distinguir mayúsculas) -------------------
    ConClave = Table.AddColumn(Tipos, "genero_clave", each Text.Upper([genero]), type text)
in
    ConClave
