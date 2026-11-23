// =====================================================================
//  Consulta: silver_juegos            (Dataflow Gen2: DF_Steam_Limpieza)
//  Destino:  tabla Lakehouse "silver_juegos" (Reemplazar)
//  Fuente:   Files/bronze/steam_games.csv
//  Depende de la consulta "estrategia_generos" (cruce de fuentes)
// =====================================================================
let
    // ---- 1. ORIGEN ---------------------------------------------------
    // Opción A (recomendada): Obtener datos > Lakehouse > LH_Steam > Files >
    //   bronze > steam_games.csv  y sustituir la línea "Binario" por los
    //   pasos de navegación generados (el último devuelve el binario).
    // Opción B: leer directamente desde GitHub (ya apunta a este repositorio).
    Binario = Web.Contents("https://raw.githubusercontent.com/ofernandezr29/steam-fabric-mercado/main/data/steam_games.csv"),

    Csv = Csv.Document(Binario, [Delimiter = ",", Columns = 24, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Cabeceras = Table.PromoteHeaders(Csv, [PromoteAllScalars = true]),

    // ---- 2. NOMBRES DE COLUMNA EN ESPAÑOL Y SIN ESPACIOS ----------------
    Renombradas = Table.RenameColumns(Cabeceras, {
        {"AppID", "app_id"}, {"Name", "nombre"}, {"Release date", "fecha_txt"},
        {"Estimated owners", "propietarios_rango"}, {"Peak CCU", "pico_ccu"},
        {"Required age", "edad_requerida"}, {"Price", "precio_txt"},
        {"Discount", "descuento_pct"}, {"DLC count", "num_dlc"},
        {"Windows", "windows"}, {"Mac", "mac"}, {"Linux", "linux"},
        {"Metacritic score", "metacritic"}, {"User score", "user_score"},
        {"Positive", "resenas_positivas"}, {"Negative", "resenas_negativas"},
        {"Achievements", "logros"}, {"Recommendations", "recomendaciones"},
        {"Average playtime forever", "tiempo_medio_min"},
        {"Median playtime forever", "tiempo_mediano_min"},
        {"Developers", "desarrolladores"}, {"Publishers", "editores"},
        {"Genres", "generos"}, {"Supported languages", "idiomas_txt"}}),

    // ---- 3. TEXTO: quitar espacios sobrantes y convertir "" en null -----
    ColumnasTexto = {"nombre", "fecha_txt", "propietarios_rango", "precio_txt",
                     "desarrolladores", "editores", "generos", "idiomas_txt"},
    TextoLimpio = Table.TransformColumns(Renombradas,
        List.Transform(ColumnasTexto, (c) => {c, each
            if _ = null or Text.Trim(_) = "" then null else Text.Trim(_), type nullable text})),

    // ---- 4. NULOS: un juego sin nombre no es identificable -> se elimina --
    SinNombreNulo = Table.SelectRows(TextoLimpio, each [nombre] <> null),

    // ---- 5. TIPOS NUMÉRICOS (cultura en-US: punto decimal) -------------
    Enteros = Table.TransformColumnTypes(SinNombreNulo, {
        {"app_id", Int64.Type}, {"pico_ccu", Int64.Type}, {"edad_requerida", Int64.Type},
        {"descuento_pct", Int64.Type}, {"num_dlc", Int64.Type}, {"metacritic", Int64.Type},
        {"user_score", Int64.Type}, {"resenas_positivas", Int64.Type},
        {"resenas_negativas", Int64.Type}, {"logros", Int64.Type},
        {"recomendaciones", Int64.Type}, {"tiempo_medio_min", Int64.Type},
        {"tiempo_mediano_min", Int64.Type}}, "en-US"),

    // ---- 6. DUPLICADOS: una fila por app_id ----------------------------
    SinDuplicados = Table.Distinct(Enteros, {"app_id"}),

    // ---- 7. FECHAS: tres formatos distintos en origen -------------------
    //   "Aug 1, 2023" (original) | "2023-08-01" (ISO) | "Aug 2023" (solo mes)
    ConFecha = Table.AddColumn(SinDuplicados, "fecha_lanzamiento", each
        let t = [fecha_txt] in
            try Date.FromText(t, [Format = "MMM d, yyyy", Culture = "en-US"])
            otherwise try Date.FromText(t, [Format = "yyyy-MM-dd", Culture = "en-US"])
            otherwise try Date.FromText(t, [Format = "MMM yyyy", Culture = "en-US"])
            otherwise null, type nullable date),

    // ---- 8. FUERA DE RANGO: fechas vacías o posteriores a 2026 -----------
    FechasValidas = Table.SelectRows(ConFecha, each
        [fecha_lanzamiento] <> null and Date.Year([fecha_lanzamiento]) <= 2026),

    // ---- 9. GÉNEROS: nulos -> "Sin género" y género principal -----------
    GenerosSinNulos = Table.ReplaceValue(FechasValidas, null, "Sin género",
        Replacer.ReplaceValue, {"generos"}),
    Secundarios = {"Indie", "Early Access", "Free To Play"},
    ConGeneroPrincipal = Table.AddColumn(GenerosSinNulos, "genero_principal", each
        let
            lista = List.Select(List.Transform(Text.Split([generos], ","), Text.Trim), each _ <> ""),
            principales = List.Select(lista, each not List.Contains(Secundarios, _))
        in
            if List.Count(principales) > 0 then principales{0}
            else if List.Count(lista) > 0 then lista{0} else "Sin género", type text),

    // ---- 10. FILTRO: quitar software que no es videojuego ---------------
    NoJuegos = {"Utilities", "Design & Illustration", "Animation & Modeling", "Education",
                "Video Production", "Game Development", "Audio Production",
                "Software Training", "Photo Editing", "Web Publishing", "Accounting",
                "Movie", "Documentary", "Episodic", "Tutorial", "360 Video"},
    SoloJuegos = Table.SelectRows(ConGeneroPrincipal, each not List.Contains(NoJuegos, [genero_principal])),

    // ---- 11. PRECIO: nulos y valores fuera de rango (< 0 o > 1000 $) ------
    PrecioNum = Table.AddColumn(SoloJuegos, "precio_num", each
        try Number.FromText([precio_txt], "en-US") otherwise null, type nullable number),
    EstadoPrecio = Table.AddColumn(PrecioNum, "estado_precio", each
        if [precio_num] = null then "Nulo"
        else if [precio_num] < 0 or [precio_num] > 1000 then "Fuera de rango"
        else "OK", type text),
    Precio = Table.AddColumn(EstadoPrecio, "precio_usd", each
        if [estado_precio] = "OK" then [precio_num] else null, type nullable number),
    RangoPrecio = Table.AddColumn(Precio, "rango_precio", each
        let p = [precio_usd] in
            if p = null then "Desconocido"
            else if p = 0 then "0. Gratis"
            else if p < 5 then "1. < 5 $"
            else if p < 10 then "2. 5-9,99 $"
            else if p < 20 then "3. 10-19,99 $"
            else if p < 40 then "4. 20-39,99 $"
            else "5. >= 40 $", type text),

    // ---- 12. PLATAFORMAS: True/TRUE/true/1/yes/Y -> verdadero -----------
    Verdaderos = {"TRUE", "1", "YES", "Y"},
    Plataformas = Table.TransformColumns(RangoPrecio, List.Transform({"windows", "mac", "linux"},
        (c) => {c, each _ <> null and List.Contains(Verdaderos, Text.Upper(Text.Trim(_))), type logical})),
    NumPlataformas = Table.AddColumn(Plataformas, "num_plataformas", each
        Number.From([windows]) + Number.From([mac]) + Number.From([linux]), Int64.Type),

    // ---- 13. PUNTUACIONES: 0 significa "sin puntuación" -> null ----------
    PuntuacionesNulas = Table.ReplaceValue(NumPlataformas, 0, null,
        Replacer.ReplaceValue, {"metacritic", "user_score"}),

    // ---- 14. PROPIETARIOS: "20000 - 50000" -> mínimo, máximo y medio -----
    PropMin = Table.AddColumn(PuntuacionesNulas, "propietarios_min", each
        Int64.From(Text.BeforeDelimiter([propietarios_rango], " - ")), Int64.Type),
    PropMax = Table.AddColumn(PropMin, "propietarios_max", each
        Int64.From(Text.AfterDelimiter([propietarios_rango], " - ")), Int64.Type),
    PropMedio = Table.AddColumn(PropMax, "propietarios_medio", each
        ([propietarios_min] + [propietarios_max]) / 2, type number),
    Exito = Table.AddColumn(PropMedio, "exito_comercial", each
        [propietarios_min] >= 100000, type logical),

    // ---- 15. RESEÑAS -----------------------------------------------------
    TotalResenas = Table.AddColumn(Exito, "total_resenas", each
        [resenas_positivas] + [resenas_negativas], Int64.Type),
    PctPositivas = Table.AddColumn(TotalResenas, "pct_positivas", each
        if [total_resenas] >= 10 then [resenas_positivas] / [total_resenas] else null,
        type nullable number),

    // ---- 16. COLUMNAS DE FECHA E IDIOMAS --------------------------------
    Anio = Table.AddColumn(PctPositivas, "anio_lanzamiento", each Date.Year([fecha_lanzamiento]), Int64.Type),
    Mes = Table.AddColumn(Anio, "mes_lanzamiento", each Date.Month([fecha_lanzamiento]), Int64.Type),
    Idiomas = Table.AddColumn(Mes, "num_idiomas", each
        if [idiomas_txt] = null or [idiomas_txt] = "[]" then 0
        else List.Count(Text.Split([idiomas_txt], ",")), Int64.Type),

    // ---- 17. CRUCE CON LA SEGUNDA FUENTE (datos internos) ---------------
    ConClave = Table.AddColumn(Idiomas, "genero_clave", each Text.Upper([genero_principal]), type text),
    Cruce = Table.NestedJoin(ConClave, {"genero_clave"}, estrategia_generos, {"genero_clave"},
        "estrategia", JoinKind.LeftOuter),
    Expandida = Table.ExpandTableColumn(Cruce, "estrategia",
        {"coste_desarrollo_eur", "meses_desarrollo", "experiencia_equipo", "prioridad_estrategica"}),
    PrioridadSinNulos = Table.ReplaceValue(Expandida, null, "Sin datos",
        Replacer.ReplaceValue, {"prioridad_estrategica"}),

    // ---- 18. SELECCIÓN FINAL Y TIPOS DEFINITIVOS ------------------------
    Final = Table.SelectColumns(PrioridadSinNulos, {
        "app_id", "nombre", "fecha_lanzamiento", "anio_lanzamiento", "mes_lanzamiento",
        "precio_usd", "estado_precio", "rango_precio", "descuento_pct", "num_dlc",
        "windows", "mac", "linux", "num_plataformas", "num_idiomas",
        "propietarios_min", "propietarios_max", "propietarios_medio", "exito_comercial",
        "pico_ccu", "edad_requerida", "metacritic", "user_score",
        "resenas_positivas", "resenas_negativas", "total_resenas", "pct_positivas",
        "logros", "recomendaciones", "tiempo_medio_min", "tiempo_mediano_min",
        "desarrolladores", "editores", "generos", "genero_principal",
        "coste_desarrollo_eur", "meses_desarrollo", "experiencia_equipo", "prioridad_estrategica"}),
    Tipos = Table.TransformColumnTypes(Final, {
        {"coste_desarrollo_eur", Int64.Type}, {"meses_desarrollo", Int64.Type},
        {"experiencia_equipo", Int64.Type}, {"prioridad_estrategica", type text},
        {"metacritic", Int64.Type}, {"user_score", Int64.Type}})
in
    Tipos
