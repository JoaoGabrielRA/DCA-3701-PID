"""Exponencial de matriz por Taylor com escalonamento e quadraturas."""

import math

import numpy as np

ORDEM_DE_TAYLOR = 18
NORMA_ALVO = 0.5


def exponencial(a):
    a = np.asarray(a, dtype=float)
    ordem = a.shape[0]
    norma = float(np.max(np.sum(np.abs(a), axis=1))) if ordem else 0.0
    quadraturas = math.ceil(math.log2(norma / NORMA_ALVO)) if norma > NORMA_ALVO else 0
    reduzida = a * 2.0 ** -quadraturas

    soma = np.eye(ordem)
    termo = np.eye(ordem)
    for k in range(1, ORDEM_DE_TAYLOR + 1):
        termo = (termo @ reduzida) / k
        soma = soma + termo

    for _ in range(quadraturas):
        soma = soma @ soma
    return soma
