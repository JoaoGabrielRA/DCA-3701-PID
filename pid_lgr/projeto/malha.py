"""Malha aberta G(s)H(s), malha fechada com o controlador e os pontos que enquadram os gráficos."""

import math

from ..nucleo import polinomio as P
from ..nucleo.raizes import raizes, ordenar_para_exibicao
from .controladores import (
    numerador_do_controlador,
    denominador_do_controlador,
    zeros_fixos_como_pontos,
    polos_fixos_como_pontos,
)

TOLERANCIA_DE_CANCELAMENTO = 1e-6
RAZAO_DE_DOMINANCIA = 5
TOLERANCIA_RELATIVA = 1e-3


def _cancelamentos(polos, zeros):
    escala = max([1.0] + [abs(z) for z in polos + zeros])
    usados = set()
    pares = []
    for polo in polos:
        indice = next(
            (j for j, zero in enumerate(zeros)
             if j not in usados and abs(polo - zero) < TOLERANCIA_DE_CANCELAMENTO * escala),
            -1,
        )
        if indice >= 0:
            usados.add(indice)
            pares.append(polo)
    return pares


def montar_malha_aberta(nG, dG, nH, dH):
    numerador = P.normalizar(P.multiplicar(nG, nH))
    denominador = P.normalizar(P.multiplicar(dG, dH))
    zeros = ordenar_para_exibicao(raizes(numerador))
    polos = ordenar_para_exibicao(raizes(denominador))
    return {
        "numerador": numerador,
        "denominador": denominador,
        "zeros": zeros,
        "polos": polos,
        "ganho": numerador[0] / denominador[0],
        "cancelamentos": _cancelamentos(polos, zeros),
    }


def _classificar(polo, desejado, zeros, escala):
    tolerancia = TOLERANCIA_RELATIVA * escala
    if polo.real >= -1e-9:
        return "instavel"
    if abs(polo - desejado) < tolerancia or abs(polo - desejado.conjugate()) < tolerancia:
        return "desejado"
    if any(abs(polo - zero) < tolerancia for zero in zeros):
        return "cancelado"
    if polo.real <= desejado.real * RAZAO_DE_DOMINANCIA:
        return "rapido"
    return "influente"


def analisar_malha_fechada(entrada, controlador, zero, kc, desejado):
    nG, dG, nH, dH = entrada["nG"], entrada["dG"], entrada["nH"], entrada["dH"]
    numerador_controlador = P.escalar(numerador_do_controlador(controlador, zero["valor"]), kc)
    denominador_controlador = denominador_do_controlador(controlador, zero["valor"])

    numerador_direto = P.multiplicar(numerador_controlador, nG)
    numerador_aberto = P.multiplicar(numerador_direto, nH)
    denominador_aberto = P.multiplicar(P.multiplicar(denominador_controlador, dG), dH)

    caracteristica = P.normalizar(P.somar(denominador_aberto, numerador_aberto))
    numerador = P.normalizar(P.multiplicar(numerador_direto, dH))
    zeros = ordenar_para_exibicao(raizes(numerador))
    encontrados = ordenar_para_exibicao(raizes(caracteristica))

    escala = max([1.0, abs(desejado)] + [abs(z) for z in encontrados])
    polos = [
        {
            "ponto": ponto,
            "classe": _classificar(ponto, desejado, zeros, escala),
            "razao": ponto.real / desejado.real,
        }
        for ponto in encontrados
    ]

    return {
        "numeradorControlador": numerador_controlador,
        "denominadorControlador": denominador_controlador,
        "numeradorAberto": P.normalizar(numerador_aberto),
        "denominadorAberto": P.normalizar(denominador_aberto),
        "caracteristica": caracteristica,
        "numerador": numerador,
        "zeros": zeros,
        "polos": polos,
        "estavel": all(item["classe"] != "instavel" for item in polos),
        "dominante": all(item["classe"] in ("desejado", "cancelado", "rapido") for item in polos),
    }


def pontos_notaveis(projeto, malha_fechada=False, polo_do_controlador=True, zero_do_controlador=True):
    pontos = []

    def acrescentar(lista):
        for ponto in lista or []:
            if ponto is not None and math.isfinite(ponto.real) and math.isfinite(ponto.imag):
                pontos.append(complex(ponto))

    acrescentar(projeto["malhaAberta"]["polos"])
    acrescentar(projeto["malhaAberta"]["zeros"])
    if projeto.get("desempenho"):
        polo = projeto["desempenho"]["polo"]
        acrescentar([polo, polo.conjugate()])
    if polo_do_controlador and projeto.get("controlador"):
        acrescentar(polos_fixos_como_pontos(projeto["controlador"]))
        acrescentar(zeros_fixos_como_pontos(projeto["controlador"]))
    if zero_do_controlador and projeto.get("zero"):
        acrescentar([projeto["zero"]["ponto"]])
    if malha_fechada and projeto.get("malhaFechada"):
        acrescentar([item["ponto"] for item in projeto["malhaFechada"]["polos"]])
        acrescentar(projeto["malhaFechada"]["zeros"])
    return pontos


def raio_de_interesse(pontos):
    return max([1.0] + [abs(p) for p in pontos])
