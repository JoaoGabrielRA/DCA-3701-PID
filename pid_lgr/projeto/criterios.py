"""Critérios de ângulo e de módulo aplicados no polo desejado."""

import cmath
import math

from .controladores import (
    livre_eh_polo,
    quantidade_livre,
    zeros_fixos_como_pontos,
    polos_fixos_como_pontos,
)

FOLGA_ANGULAR = 1e-6


def para_circunferencia(valor):
    return ((valor % 360) + 360) % 360


def argumento_graus(z):
    return math.degrees(cmath.phase(z)) if z != 0 else 0.0


def _contribuicao_angular(ponto, referencia, origem):
    diferenca = ponto - referencia
    return {"referencia": referencia, "origem": origem, "diferenca": diferenca, "angulo": argumento_graus(diferenca)}


def _contribuicao_de_modulo(ponto, referencia, origem):
    diferenca = ponto - referencia
    return {"referencia": referencia, "origem": origem, "diferenca": diferenca, "valor": abs(diferenca)}


def _polos_do_conjunto(malha_aberta, controlador, livre=None):
    livres = [livre] * controlador["polosLivres"] if livre is not None else []
    return (
        [{"ponto": p, "origem": "planta"} for p in malha_aberta["polos"]]
        + [{"ponto": p, "origem": "controlador"} for p in polos_fixos_como_pontos(controlador) + livres]
    )


def _zeros_conhecidos(malha_aberta, controlador):
    return (
        [{"ponto": z, "origem": "planta"} for z in malha_aberta["zeros"]]
        + [{"ponto": z, "origem": "controlador"} for z in zeros_fixos_como_pontos(controlador)]
    )


def _motivo_de_inviabilidade(por_singularidade):
    if por_singularidade < FOLGA_ANGULAR or 360 - por_singularidade < FOLGA_ANGULAR:
        return "semDeficiencia"
    if por_singularidade >= 180 - FOLGA_ANGULAR:
        return "excesso"
    return None


def criterio_de_angulo(polo, malha_aberta, controlador):
    contribuicao_zeros = [
        _contribuicao_angular(polo, item["ponto"], item["origem"])
        for item in _zeros_conhecidos(malha_aberta, controlador)
    ]
    contribuicao_polos = [
        _contribuicao_angular(polo, item["ponto"], item["origem"])
        for item in _polos_do_conjunto(malha_aberta, controlador)
    ]
    soma_zeros = sum(item["angulo"] for item in contribuicao_zeros)
    soma_polos = sum(item["angulo"] for item in contribuicao_polos)
    angulo_do_ganho = 180 if malha_aberta["ganho"] < 0 else 0
    fase = soma_zeros - soma_polos + angulo_do_ganho
    deficiencia = para_circunferencia(-180 - fase)
    exigido = para_circunferencia(-deficiencia) if livre_eh_polo(controlador) else deficiencia
    por_singularidade = exigido / quantidade_livre(controlador)
    motivo = _motivo_de_inviabilidade(por_singularidade)

    return {
        "contribuicaoZeros": contribuicao_zeros,
        "contribuicaoPolos": contribuicao_polos,
        "somaZeros": soma_zeros,
        "somaPolos": soma_polos,
        "anguloDoGanho": angulo_do_ganho,
        "fase": fase,
        "deficiencia": deficiencia,
        "exigido": exigido,
        "porSingularidade": por_singularidade,
        "viavel": motivo is None,
        "motivo": motivo,
    }


def localizar_zero(polo, angulo):
    sigma = -polo.real
    tangente = math.tan(math.radians(angulo["porSingularidade"]))
    afastamento = polo.imag / tangente
    valor = sigma + afastamento
    return {
        "sigma": sigma,
        "omegaD": polo.imag,
        "tangente": tangente,
        "afastamento": afastamento,
        "valor": valor,
        "ponto": complex(-valor, 0),
        "semiplanoDireito": valor < 0,
    }


def criterio_de_modulo(polo, malha_aberta, controlador, zero):
    zeros_do_controlador = [zero["ponto"]] * controlador["zeros"]
    distancias_zeros = [
        _contribuicao_de_modulo(polo, item["ponto"], item["origem"])
        for item in _zeros_conhecidos(malha_aberta, controlador)
    ] + [_contribuicao_de_modulo(polo, z, "controlador") for z in zeros_do_controlador]
    distancias_polos = [
        _contribuicao_de_modulo(polo, item["ponto"], item["origem"])
        for item in _polos_do_conjunto(malha_aberta, controlador, zero["ponto"])
    ]

    produto_zeros = math.prod(item["valor"] for item in distancias_zeros)
    produto_polos = math.prod(item["valor"] for item in distancias_polos)
    ganho_da_planta = abs(malha_aberta["ganho"])

    return {
        "distanciasZeros": distancias_zeros,
        "distanciasPolos": distancias_polos,
        "produtoZeros": produto_zeros,
        "produtoPolos": produto_polos,
        "ganhoDaPlanta": ganho_da_planta,
        "kc": produto_polos / (ganho_da_planta * produto_zeros),
    }
