"""Resposta ao degrau exata em espaço de estados e as métricas de desempenho."""

import math

import numpy as np

from ..nucleo import polinomio as P
from ..nucleo.matriz import exponencial
from .especificacoes import CONSTANTES_DE_ACOMODACAO

AMOSTRAS = 1600
CONSTANTES_DE_TEMPO = 7
MULTIPLO_MINIMO = 2.5
MULTIPLO_MAXIMO = 25


def realizar_em_espaco_de_estados(numerador, denominador):
    den = P.normalizar(denominador)
    ordem = len(den) - 1
    a = [v / den[0] for v in den]
    num = P.preencher([v / den[0] for v in P.normalizar(numerador)], ordem + 1)
    direto = num[0]
    saida = np.array([valor - direto * a[i + 1] for i, valor in enumerate(num[1:])], dtype=float)

    estados = np.zeros((ordem, ordem))
    for j in range(ordem):
        estados[0, j] = -a[j + 1]
    for i in range(1, ordem):
        estados[i, i - 1] = 1.0
    return {"estados": estados, "saida": saida, "direto": direto, "ordem": ordem}


def discretizar_estados(estados, ordem, passo):
    aumentada = np.zeros((ordem + 1, ordem + 1))
    aumentada[:ordem, :ordem] = estados * passo
    aumentada[0, ordem] = passo
    exp = exponencial(aumentada)
    return {"transicao": exp[:ordem, :ordem], "entrada": exp[:ordem, ordem]}


def valor_final(numerador, denominador):
    return P.avaliar(numerador, 0) / P.avaliar(denominador, 0)


def horizonte_de_simulacao(polos, sigma):
    base = CONSTANTES_DE_ACOMODACAO[2] / sigma
    relevantes = [-item["ponto"].real for item in polos if item["classe"] != "cancelado"]
    lento = min(relevantes) if relevantes else math.inf
    estimado = CONSTANTES_DE_TEMPO / lento if lento else math.inf
    return min(max(estimado, MULTIPLO_MINIMO * base), MULTIPLO_MAXIMO * base)


def simular_degrau(numerador, denominador, duracao):
    r = realizar_em_espaco_de_estados(numerador, denominador)
    ordem = r["ordem"]
    passo = duracao / (AMOSTRAS - 1)
    tempos = np.arange(AMOSTRAS) * passo
    saidas = np.empty(AMOSTRAS)
    if ordem == 0:
        saidas[:] = r["direto"]
        return {"tempos": tempos, "saidas": saidas, "duracao": duracao}

    d = discretizar_estados(r["estados"], ordem, passo)
    transicao, entrada = d["transicao"], d["entrada"]
    estado = np.zeros(ordem)
    for k in range(AMOSTRAS):
        saidas[k] = r["direto"] + float(estado @ r["saida"])
        estado = transicao @ estado + entrada
    return {"tempos": tempos, "saidas": saidas, "duracao": duracao}


def _acomodacao(tempos, normalizadas, faixa):
    ultima = len(normalizadas) - 1
    for k in range(ultima, -1, -1):
        excesso = abs(normalizadas[k] - 1) - faixa
        if excesso <= 0:
            continue
        if k == ultima:
            return math.inf
        seguinte = abs(normalizadas[k + 1] - 1) - faixa
        return tempos[k] + ((tempos[k + 1] - tempos[k]) * excesso) / (excesso - seguinte)
    return 0.0


def medir_resposta(simulacao, final):
    if not math.isfinite(final) or abs(final) < 1e-12:
        return None
    tempos, saidas = simulacao["tempos"], simulacao["saidas"]
    normalizadas = saidas / final
    indice_pico = int(np.argmax(normalizadas))
    sobressinal = max(0.0, (normalizadas[indice_pico] - 1) * 100)
    return {
        "valorFinal": final,
        "pico": float(saidas[indice_pico]),
        "tempoDePico": float(tempos[indice_pico]) if sobressinal > 0 else None,
        "sobressinal": sobressinal,
        "acomodacao2": float(_acomodacao(tempos, normalizadas, 0.02)),
        "acomodacao5": float(_acomodacao(tempos, normalizadas, 0.05)),
    }
