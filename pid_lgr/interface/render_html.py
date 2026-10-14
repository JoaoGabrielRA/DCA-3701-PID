"""Relatório HTML autossuficiente (KaTeX + SVG) pronto para imprimir ou salvar em PDF pelo navegador."""

import html
import io

import matplotlib.pyplot as plt

from ..autoria import AUTOR, DISCIPLINA

KATEX = "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist"

ESTILO = """
:root { --texto:#16202b; --medio:#46535f; --suave:#6b7885; --borda:#dde3ea; --destaque:#2b6cd9; }
* { box-sizing: border-box; }
body { margin: 0; background: #f4f6f9; color: var(--texto);
       font: 15px/1.55 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
main { max-width: 900px; margin: 0 auto; padding: 24px 16px 48px; }
header.capa { border-bottom: 2px solid var(--destaque); margin-bottom: 20px; padding-bottom: 10px; }
header.capa h1 { font-size: 22px; margin: 0 0 4px; }
header.capa p { margin: 0; color: var(--medio); font-size: 13px; }
.barra { display: flex; justify-content: flex-end; margin-bottom: 12px; }
.barra button { background: var(--destaque); color: #fff; border: 0; border-radius: 6px; padding: 8px 14px;
                font: inherit; cursor: pointer; }
.enunciado { background: #fff; border: 1px solid var(--borda); border-left: 4px solid var(--destaque);
             border-radius: 8px; padding: 12px 16px; margin: 0 0 14px; }
.etiqueta { text-transform: uppercase; letter-spacing: .06em; font-size: 11px; color: var(--suave);
            font-weight: 600; margin: 0 0 6px; }
details { background: #fff; border: 1px solid var(--borda); border-radius: 8px; margin: 0 0 12px; }
summary { cursor: pointer; padding: 10px 16px; font-size: 15px; }
.corpo { padding: 4px 16px 14px; }
.formula { overflow-x: auto; padding: 4px 0; }
.aviso { border-left: 4px solid; border-radius: 6px; padding: 8px 12px; margin: 10px 0; }
.aviso-sucesso { background: #e7f6ec; border-color: #1f9d55; }
.aviso-atencao { background: #fdf3e2; border-color: #e08b1a; }
.aviso-erro { background: #fdeaea; border-color: #d0342c; }
.aviso-informacao { background: #eaf1fd; border-color: #2b6cd9; }
hr { border: 0; border-top: 1px solid var(--borda); margin: 14px 0; }
.colunas { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; }
.figura svg { width: 100%; height: auto; }
.questao { page-break-before: always; }
.questao:first-of-type { page-break-before: auto; }
@media print {
  body { background: #fff; }
  .barra { display: none; }
  details { border: 0; }
  details > summary { list-style: none; font-weight: 600; border-bottom: 1px solid var(--borda); }
  .figura, .aviso, .formula { break-inside: avoid; }
}
"""

SCRIPT = """
document.addEventListener('DOMContentLoaded', function () {
  renderMathInElement(document.body, {
    delimiters: [{left: '\\\\[', right: '\\\\]', display: true}, {left: '\\\\(', right: '\\\\)', display: false}],
    throwOnError: false, strict: 'ignore'
  });
});
window.addEventListener('beforeprint', function () {
  document.querySelectorAll('details').forEach(function (d) { d.open = true; });
});
"""


def _texto(conteudo):
    """Converte **negrito** e $latex$ para HTML com delimitadores do KaTeX."""
    partes = []
    for indice, bloco in enumerate(conteudo.split("$")):
        if indice % 2 == 1:
            partes.append(f"\\({html.escape(bloco)}\\)")
            continue
        for j, trecho in enumerate(bloco.split("**")):
            trecho = html.escape(trecho)
            partes.append(f"<strong>{trecho}</strong>" if j % 2 == 1 and trecho else trecho)
    return "".join(partes)


def _svg(fig):
    saida = io.StringIO()
    fig.savefig(saida, format="svg", bbox_inches="tight")
    plt.close(fig)
    texto = saida.getvalue()
    return texto[texto.find("<svg"):]


def _corpo(documento):
    partes = []
    for item in documento.itens:
        tipo = item[0]
        if tipo == "paragrafo":
            partes.append(f"<p>{_texto(item[1])}</p>")
        elif tipo == "formula":
            partes.append(f'<div class="formula">\\[{html.escape(item[1])}\\]</div>')
        elif tipo == "aviso":
            partes.append(f'<div class="aviso aviso-{item[1]}">{_texto(item[2])}</div>')
        elif tipo == "separador":
            partes.append("<hr>")
        elif tipo == "figura":
            partes.append(f'<div class="figura">{_svg(item[1])}</div>')
        elif tipo == "colunas":
            celulas = "".join(f"<div>{_corpo(celula)}</div>" for celula in item[1])
            partes.append(f'<div class="colunas">{celulas}</div>')
        elif tipo == "secao":
            _, titulo, _aberta, corpo = item
            partes.append(f'<details open><summary>{_texto(titulo)}</summary><div class="corpo">{_corpo(corpo)}</div></details>')
        elif tipo == "enunciado":
            _, etiqueta, corpo = item
            partes.append(
                f'<section class="enunciado"><p class="etiqueta">{html.escape(etiqueta)}</p>{_corpo(corpo)}</section>'
            )
    return "".join(partes)


def gerar_html(titulo, documentos):
    """``documentos`` é uma lista; cada um começa em página nova na impressão."""
    blocos = "".join(f'<div class="questao">{_corpo(doc)}</div>' for doc in documentos)
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="author" content="{html.escape(AUTOR)}">
<title>{html.escape(titulo)}</title>
<link rel="stylesheet" href="{KATEX}/katex.min.css">
<script defer src="{KATEX}/katex.min.js"></script>
<script defer src="{KATEX}/contrib/auto-render.min.js"></script>
<script>{SCRIPT}</script>
<style>{ESTILO}</style>
</head>
<body>
<main>
<div class="barra"><button type="button" onclick="window.print()">Imprimir / salvar em PDF</button></div>
<header class="capa">
<h1>{html.escape(titulo)}</h1>
<p>{html.escape(DISCIPLINA)} · {html.escape(AUTOR)}</p>
</header>
{blocos}
</main>
</body>
</html>
"""
