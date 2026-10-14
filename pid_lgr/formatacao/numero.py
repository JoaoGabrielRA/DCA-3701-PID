"""Números formatados como no JavaScript original (toPrecision, toFixed)."""

import math

import numpy as np


def limpar(valor):
    return 0.0 if valor == 0 else float(valor)


def _como_js(valor):
    """String(Number) do JavaScript: decimal até 1e21 e acima de 1e-7, exponencial fora disso."""
    if valor == 0:
        return "0"
    absoluto = abs(valor)
    if 1e-7 <= absoluto < 1e21:
        return np.format_float_positional(valor, trim="-")
    texto = repr(valor)
    mantissa, expoente = texto.split("e")
    if mantissa.endswith(".0"):
        mantissa = mantissa[:-2]
    return f"{mantissa}e{int(expoente):+d}"


def formatar_g(valor, precisao=6):
    v = limpar(valor)
    if not math.isfinite(v):
        return "infinito" if v > 0 else "-infinito"
    if v == 0:
        return "0"
    return _como_js(float(f"{v:.{precisao}g}"))


def fixo(valor, casas=4):
    v = limpar(valor)
    if not math.isfinite(v):
        return "infinito" if v > 0 else "-infinito"
    texto = f"{v:.{casas}f}"
    return texto[1:] if texto.startswith("-") and float(texto) == 0 else texto


def numero_latex(valor, precisao=6):
    v = limpar(valor)
    if not math.isfinite(v):
        return "\\infty" if v > 0 else "-\\infty"
    texto = formatar_g(v, precisao)
    if "e" not in texto:
        return texto
    mantissa, expoente = texto.split("e")
    return f"{mantissa} \\times 10^{{{int(expoente)}}}"


def fixo_latex(valor, casas=4):
    v = limpar(valor)
    if not math.isfinite(v):
        return "\\infty" if v > 0 else "-\\infty"
    return fixo(float(f"{v:.{casas}f}"), casas)
