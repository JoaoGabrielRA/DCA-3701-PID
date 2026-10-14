"""Tipo do sistema e constantes de erro estático Kp, Kv e Ka."""

import math

from ..nucleo import polinomio as P

FOLGA_RELATIVA = 1e-10


def _quase_zero(valor, escala):
    return abs(valor) < FOLGA_RELATIVA * max(escala, 1e-300)


def _retirar_integradores_comuns(numerador, denominador):
    num = P.normalizar(numerador)
    den = P.normalizar(denominador)
    escala_num = P.maior_coeficiente(num)
    escala_den = P.maior_coeficiente(den)
    while (
        len(num) > 1 and len(den) > 1
        and _quase_zero(num[-1], escala_num) and _quase_zero(den[-1], escala_den)
    ):
        num.pop()
        den.pop()
    return num, den


def _constante(num, den, ordem, tipo):
    if ordem < tipo:
        return math.inf
    if ordem > tipo:
        return 0.0
    return num[-1] / den[len(den) - 1 - tipo]


def _inverso(valor):
    if valor == 0:
        return math.inf
    return 1 / valor


def constantes_de_erro(numerador, denominador):
    num, den = _retirar_integradores_comuns(numerador, denominador)
    escala_den = P.maior_coeficiente(den)
    tipo = 0
    while tipo < len(den) - 1 and _quase_zero(den[len(den) - 1 - tipo], escala_den):
        tipo += 1

    kp = _constante(num, den, 0, tipo)
    kv = _constante(num, den, 1, tipo)
    ka = _constante(num, den, 2, tipo)
    return {
        "tipo": tipo,
        "kp": kp,
        "kv": kv,
        "ka": ka,
        "erroDegrau": 1 / (1 + kp),
        "erroRampa": _inverso(kv),
        "erroParabola": _inverso(ka),
    }
