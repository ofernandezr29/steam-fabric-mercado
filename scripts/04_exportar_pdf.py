"""
04_exportar_pdf.py
------------------
Convierte ficheros Markdown del proyecto a PDF (Markdown -> HTML con estilos ->
PDF con Microsoft Edge en modo headless). Los diagramas ```mermaid se dibujan.

Uso:
    python -I scripts/04_exportar_pdf.py <entrada.md> <salida.pdf> ["Título"]
"""
import html
import os
import re
import subprocess
import sys
import tempfile

import markdown

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

CSS = """
@page { size: A4; margin: 18mm 16mm; }
body { font-family: 'Segoe UI', Calibri, Arial, sans-serif; font-size: 10.5pt;
       line-height: 1.45; color: #1d1d1f; }
h1 { color: #1f4e79; font-size: 22pt; border-bottom: 3px solid #1f4e79; padding-bottom: 6px; }
h2 { color: #1f4e79; font-size: 15pt; margin-top: 26px; border-bottom: 1px solid #c9d6e3;
     padding-bottom: 3px; page-break-after: avoid; }
h3 { color: #2e75b6; font-size: 12pt; margin-top: 18px; page-break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 9pt;
        page-break-inside: avoid; }
th { background: #1f4e79; color: #fff; text-align: left; }
th, td { border: 1px solid #c9d6e3; padding: 4px 6px; vertical-align: top; }
tr:nth-child(even) td { background: #f3f7fb; }
code { font-family: Consolas, monospace; font-size: 9pt; background: #eef2f6;
       padding: 1px 3px; border-radius: 3px; }
pre { background: #f5f7f9; border: 1px solid #dde3ea; padding: 8px; font-size: 8.5pt;
      white-space: pre-wrap; page-break-inside: avoid; }
pre code { background: none; padding: 0; }
blockquote { border-left: 4px solid #2e75b6; background: #eef5fc; margin: 10px 0;
             padding: 6px 12px; }
.mermaid { text-align: center; margin: 14px 0; page-break-inside: avoid; }
a { color: #2e75b6; text-decoration: none; }
hr { border: none; border-top: 1px solid #c9d6e3; margin: 20px 0; }
"""


ES_LISTA = re.compile(r"^\s*(?:[-*]|\d+\.)\s")


def normalizar_listas(texto):
    """Python-Markdown exige línea en blanco antes de una lista y 4 espacios
    de sangría en sublistas; GitHub no. Se adapta el texto fuera de bloques de código."""
    salida, en_codigo, anterior = [], False, ""
    for linea in texto.splitlines():
        if linea.lstrip().startswith("```"):
            en_codigo = not en_codigo
        elif not en_codigo and ES_LISTA.match(linea):
            sangria = len(linea) - len(linea.lstrip())
            if 0 < sangria < 4:
                linea = "    " + linea.lstrip()
            if anterior.strip() and not ES_LISTA.match(anterior) and not anterior.startswith(" "):
                salida.append("")
        salida.append(linea)
        anterior = linea
    return "\n".join(salida)


def md_a_html(texto, titulo):
    texto = normalizar_listas(texto)
    cuerpo = markdown.markdown(texto, extensions=["tables", "fenced_code", "sane_lists"])
    cuerpo = re.sub(
        r'<pre><code class="language-mermaid">(.*?)</code></pre>',
        lambda m: f'<div class="mermaid">{html.unescape(m.group(1))}</div>',
        cuerpo, flags=re.S)
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>{html.escape(titulo)}</title><style>{CSS}</style>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
</head><body>{cuerpo}
<script>mermaid.initialize({{startOnLoad: true, theme: 'neutral', securityLevel: 'loose'}});</script>
</body></html>"""


def main():
    entrada, salida = sys.argv[1], sys.argv[2]
    titulo = sys.argv[3] if len(sys.argv) > 3 else os.path.basename(entrada)
    with open(entrada, encoding="utf-8") as f:
        documento = md_a_html(f.read(), titulo)
    with tempfile.TemporaryDirectory() as tmp:
        ruta_html = os.path.join(tmp, "doc.html")
        with open(ruta_html, "w", encoding="utf-8") as f:
            f.write(documento)
        subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        "--virtual-time-budget=20000", f"--user-data-dir={tmp}\\perfil",
                        f"--print-to-pdf={os.path.abspath(salida)}",
                        "file:///" + ruta_html.replace("\\", "/")],
                       check=True, capture_output=True, timeout=180)
    print(f"PDF generado: {salida} ({os.path.getsize(salida) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
