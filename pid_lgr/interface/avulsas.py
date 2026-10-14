"""Ferramentas avulsas: discretizar uma G(s) e Ziegler-Nichols (1º e 2º métodos)."""

import math

from ..formatacao.latex import razao_latex
from ..formatacao.numero import fixo_latex, numero_latex
from ..nucleo import polinomio as P
from ..nucleo.entrada import interpretar_polinomio, interpretar_numero
from ..projeto.discretizacao import discretizar
from ..projeto.ziegler_nichols import primeiro_metodo, segundo_metodo, ponto_critico
from .documento import Documento
from .passos import renderizar_discretizacao

N = numero_latex

NOMES = {
    "discretizar": "Discretização de G(s)",
    "zn1": "Ziegler-Nichols, 1º método",
    "zn2": "Ziegler-Nichols, 2º método",
}

METODOS_AVULSOS = {
    "euler": "Euler ou Forward",
    "euler-atraso": "Backward",
    "tustin": "Tustin (trapezoidal)",
    "degrau": "Invariância ao degrau (SOZ)",
}


def _numero(texto):
    return interpretar_numero(str(texto or ""), math.nan)


def _cabecalho(doc, texto):
    doc.enunciado("Ferramenta avulsa").paragrafo(texto)


def _discretizacao(doc, valores):
    numerador = interpretar_polinomio(valores["numerador"])
    denominador = interpretar_polinomio(valores["denominador"])
    periodo = _numero(valores["periodo"])
    if not numerador or not denominador or all(v == 0 for v in denominador):
        raise ValueError("confira o numerador e o denominador de $G(s)$.")
    if not periodo > 0:
        raise ValueError("o período de amostragem $T$ precisa ser positivo.")
    resultado = {"alvo": "planta", **discretizar(numerador, denominador, valores["metodo"], periodo)}
    _cabecalho(doc, f"**Discretizar** $G(s) = {razao_latex(numerador, denominador)}$ com $T = {N(periodo)}\\,\\text{{s}}$.")
    renderizar_discretizacao(doc.secao(f"**Discretização:** {resultado['metodo']['nome']}", True), resultado)


def _tempo(valor):
    return N(valor) if math.isfinite(valor) else "\\infty"


def _tabela(doc, linhas):
    corpo = " \\\\ ".join(
        " & ".join([f"\\text{{{l['tipo']}}}", N(l["kp"]), _tempo(l["ti"]), N(l["td"]), N(l["ki"]), N(l["kd"])])
        for l in linhas
    )
    doc.formula(
        "\\begin{array}{l|c|c|c|c|c} \\text{Controlador} & K_P & \\tau_i & \\tau_d & K_i = K_P/\\tau_i & "
        f"K_d = K_P\\,\\tau_d \\\\ \\hline {corpo} \\end{{array}}"
    )
    pid = linhas[2]
    doc.separador()
    doc.paragrafo("**PID sintonizado:**")
    doc.formula(
        f"G_c(s) = K_P\\left(1 + \\frac{{1}}{{\\tau_i s}} + \\tau_d s\\right) = {N(pid['kp'])} + "
        f"\\frac{{{N(pid['ki'])}}}{{s}} + {N(pid['kd'])}\\,s"
    )
    doc.formula(f"G_c(s) = {razao_latex([pid['kd'], pid['kp'], pid['ki']], [1, 0])}")
    doc.aviso(
        "informacao",
        "Ziegler-Nichols dá só a sintonia inicial, pensada para cerca de $25\\%$ de sobressinal. "
        "Ajuste fino costuma ser necessário.",
    )


def _primeiro(doc, valores):
    atraso, constante = _numero(valores["L"]), _numero(valores["T"])
    if not (atraso > 0 and constante > 0):
        raise ValueError("informe o atraso $L$ e a constante de tempo $T$, ambos positivos.")
    _cabecalho(
        doc,
        f"**Primeiro método de Ziegler-Nichols** com $L = {N(atraso)}\\,\\text{{s}}$ e $T = {N(constante)}\\,\\text{{s}}$, "
        "tirados da curva em S.",
    )
    corpo = doc.secao("**Tabela do 1º método**", True)
    corpo.formula(
        "\\begin{array}{l|c|c|c} \\text{Controlador} & K_P & \\tau_i & \\tau_d \\\\ \\hline \\text{P} & T/L & \\infty & 0 "
        "\\\\ \\text{PI} & 0{,}9\\,T/L & L/0{,}3 & 0 \\\\ \\text{PID} & 1{,}2\\,T/L & 2L & 0{,}5L \\end{array}"
    )
    corpo.formula(f"\\frac{{T}}{{L}} = \\frac{{{N(constante)}}}{{{N(atraso)}}} = {N(constante / atraso)}")
    corpo.separador()
    _tabela(corpo, primeiro_metodo(atraso, constante))


def _ponto_critico(doc, valores, coeficientes):
    ganho, periodo = _numero(valores["kcr"]), _numero(valores["pcr"])
    if ganho > 0 and periodo > 0:
        return {"ganhoCritico": ganho, "periodoCritico": periodo}
    if coeficientes is None or any(item is None for item in coeficientes):
        raise ValueError("informe $K_{cr}$ e $P_{cr}$, ou preencha $G(s)$ e $H(s)$ no formulário do projeto.")
    nG, dG, nH, dH = coeficientes
    numerador, denominador = P.multiplicar(nG, nH), P.multiplicar(dG, dH)
    critico = ponto_critico(numerador, denominador)
    if not critico:
        raise ValueError(
            "o LGR de $G(s)H(s)$ não cruza o eixo $j\\omega$, então não há ganho crítico e o 2º método não se aplica."
        )
    corpo = doc.secao("**Ganho e período críticos pelo modelo**", True)
    corpo.formula(f"G(s)H(s) = {razao_latex(numerador, denominador)}")
    corpo.paragrafo("O LGR cruza o eixo $j\\omega$ onde a fase de $G(j\\omega)H(j\\omega)$ vale $-180^\\circ$:")
    corpo.formula(
        f"\\angle G(j\\omega_{{cr}})H(j\\omega_{{cr}}) = -180^\\circ \\;\\Rightarrow\\; "
        f"\\omega_{{cr}} = {fixo_latex(critico['omega'])}\\;\\text{{rad/s}}"
    )
    corpo.formula(
        f"K_{{cr}} = \\frac{{1}}{{|G(j\\omega_{{cr}})H(j\\omega_{{cr}})|}} = {N(critico['ganhoCritico'])}, \\qquad "
        f"P_{{cr}} = \\frac{{2\\pi}}{{\\omega_{{cr}}}} = {N(critico['periodoCritico'])}\\;\\text{{s}}"
    )
    return critico


def _segundo(doc, valores, coeficientes):
    ganho, periodo = _numero(valores["kcr"]), _numero(valores["pcr"])
    if ganho > 0 and periodo > 0:
        texto = (f"**Segundo método de Ziegler-Nichols** com $K_{{cr}} = {N(ganho)}$ e "
                 f"$P_{{cr}} = {N(periodo)}\\,\\text{{s}}$.")
    else:
        texto = "**Segundo método de Ziegler-Nichols**, com $K_{cr}$ e $P_{cr}$ tirados de $G(s)H(s)$."
    _cabecalho(doc, texto)
    critico = _ponto_critico(doc, valores, coeficientes)
    corpo = doc.secao("**Tabela do 2º método**", True)
    corpo.formula(
        "\\begin{array}{l|c|c|c} \\text{Controlador} & K_P & \\tau_i & \\tau_d \\\\ \\hline \\text{P} & 0{,}5\\,K_{cr} & "
        "\\infty & 0 \\\\ \\text{PI} & 0{,}45\\,K_{cr} & P_{cr}/1{,}2 & 0 \\\\ \\text{PID} & 0{,}6\\,K_{cr} & "
        "0{,}5\\,P_{cr} & 0{,}125\\,P_{cr} \\end{array}"
    )
    corpo.separador()
    _tabela(corpo, segundo_metodo(critico["ganhoCritico"], critico["periodoCritico"]))


def calcular_ferramenta(escolhida, valores, coeficientes=None):
    doc = Documento()
    try:
        if escolhida == "discretizar":
            _discretizacao(doc, valores)
        elif escolhida == "zn1":
            _primeiro(doc, valores)
        else:
            _segundo(doc, valores, coeficientes)
    except (ValueError, ZeroDivisionError, ArithmeticError) as falha:
        doc.aviso("erro", f"Não foi possível calcular: {falha}")
    return doc
