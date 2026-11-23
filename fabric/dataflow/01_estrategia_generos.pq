let
    // Sustituir por los pasos de navegación al fichero en LH_Steam/Files/bronze
    Binario = Web.Contents("https://raw.githubusercontent.com/ofernandezr29/steam-fabric-mercado/main/data/estrategia_generos.csv"),
    Csv = Csv.Document(Binario, [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Cabeceras = Table.PromoteHeaders(Csv, [PromoteAllScalars = true]),
    GeneroLimpio = Table.TransformColumns(Cabeceras, {{"genero", each
        let t = Text.Trim(_) in if Text.Lower(t) = t then Text.Proper(t) else t, type text}}),
    Tipos = Table.TransformColumnTypes(GeneroLimpio, {
        {"coste_desarrollo_eur", Int64.Type},
        {"meses_desarrollo", Int64.Type},
        {"experiencia_equipo", Int64.Type},
        {"prioridad_estrategica", type text}}, "en-US"),
    ConClave = Table.AddColumn(Tipos, "genero_clave", each Text.Upper([genero]), type text)
in
    ConClave
